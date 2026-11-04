"""Nashi (resmî uygulama) → beyin arşivi (mail.db `items`, source=nashi). SALT OKUNUR.

Veri: `%LOCALAPPDATA%\\Nashi\\library.json` (biçim: apps/nashi/windows/Nashi.Core/LibraryStore.cs; System.Text.Json):
  {Appearance, Entries:[{Id(guid), Created(ISO), Action, Paths[]}], WindowManagementEnabled} — son 50 dışa aktarım/pano içe aktarımı.
Her (kayıt, yol) çifti bir arşiv satırıdır: yol, tür, zaman, işlem adı. Dosya hâlâ varsa desteklenen türlerde (pdf, docx, pptx, xlsx, txt/md/csv…,
görsellerde OCR) içeriği MEVCUT içerik çıkarma hattıyla (sb.content.extract, sb.actions.ocr) metne çevrilip satıra eklenir.
Sır içeren içerik satıra EKLENMEZ (yol/zaman kalır; sayısı raporlanır). Nashi'nin dosyasına yazılmaz: kopya okunur.
"""
from __future__ import annotations

import hashlib
import json
import ntpath
import shutil
import tempfile
import time
from pathlib import Path

from ..redact import contains_secret
from ._common import parse_iso, sid, sync_items

SOURCE = "nashi"
MAX_LIB = 4 * 1024 * 1024
BODY_MAX = 20000
MAX_FILE = 40 * 1024 * 1024
MAX_IMAGE = 25 * 1024 * 1024
IMAGE_EXT = {"png", "jpg", "jpeg", "bmp", "gif", "tif", "tiff", "webp"}
EXTRACT_PER_RUN = 40


def library_file(path) -> Path:
    p = Path(path)
    return p if p.is_file() else p / "library.json"


def _ci(d: dict, key: str):
    for k, v in d.items():
        if k.lower() == key.lower():
            return v
    return None


def read_library(path, retries: int = 3, wait: float = 0.5) -> dict:
    src = library_file(path)
    if not src.exists():
        raise FileNotFoundError(str(src))
    if src.stat().st_size > MAX_LIB:
        raise ValueError("library.json beklenenden büyük; okunmadı")
    last: Exception | None = None
    for _ in range(max(1, retries)):
        tmp = Path(tempfile.mkdtemp(prefix="sb-nashi-"))
        try:
            dst = tmp / "library.json"
            shutil.copyfile(src, dst)
            data = json.loads(dst.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict) or not isinstance(_ci(data, "Entries"), list):
                raise ValueError("library.json biçimi tanınmadı")
            return data
        except (PermissionError, OSError) as e:
            last = e
            time.sleep(wait)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    raise PermissionError(f"library.json kilitli ya da okunamadı: {last}")


def entries(path) -> list[dict]:
    out = []
    for e in _ci(read_library(path), "Entries") or []:
        if not isinstance(e, dict):
            continue
        paths = [p for p in (_ci(e, "Paths") or []) if isinstance(p, str) and p.strip()]
        eid, action = _ci(e, "Id"), _ci(e, "Action")
        if eid and paths and isinstance(action, str):
            out.append({"id": str(eid), "created": parse_iso(str(_ci(e, "Created") or "")), "action": action, "paths": paths})
    return out


def extract_text(p: Path) -> str:
    """Mevcut hat: belge türleri content.extract, görseller actions.ocr (yoksa boş)."""
    ext = p.suffix.lower().lstrip(".")
    from .. import content
    if ext in content.EXTS:
        return content.extract(p)
    if ext in IMAGE_EXT and p.stat().st_size <= MAX_IMAGE:
        from .. import actions
        return actions.ocr(p.read_bytes())
    return ""


def _h(parts) -> str:
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:24]


def build_rows(path, known: dict[str, str] | None = None, extractor=extract_text) -> tuple[list[dict], dict]:
    """known: {satır kimliği: hash}. Hash'i değişmeyen satırda içerik yeniden çıkarılmaz (ve satır döndürülmez)."""
    known = known or {}
    rows, st, budget = [], {"atlanan_sir": 0, "icerikli": 0, "dosya_yok": 0}, EXTRACT_PER_RUN
    for e in entries(path):
        for fp in e["paths"]:
            name = ntpath.basename(fp.rstrip("\\/")) or fp
            ext = ntpath.splitext(name)[1].lower().lstrip(".")
            p = Path(fp)
            try:
                exists, is_file = p.exists(), p.is_file()
                stt = p.stat() if exists else None
            except OSError:
                exists, is_file, stt = False, False, None
            rid = sid(e["id"], fp)
            h = _h([e["action"], fp, exists, stt.st_size if stt else 0, int(stt.st_mtime) if stt else 0])
            if known.get(rid) == h:
                continue
            if not exists:
                st["dosya_yok"] += 1
            text, secret = "", False
            if is_file and stt and stt.st_size <= MAX_FILE and budget <= 0:
                h += "+bekliyor"                                             # bu turun içerik payı doldu: kayıt alınır, içerik sonraki turda
            elif is_file and stt and stt.st_size <= MAX_FILE:
                budget -= 1
                try:
                    text = extractor(p) or ""
                except Exception:                                            # noqa: BLE001 — bozuk/şifreli dosya satırı düşürmesin
                    text = ""
                if text and contains_secret(text):
                    text, secret = "", True
                    st["atlanan_sir"] += 1
            if text:
                st["icerikli"] += 1
            head = f"Nashi · {e['action']} · {name}\n{fp}"
            body = (head + ("\n\n" + text.strip() if text.strip() else ""))[:BODY_MAX]
            meta = {"action": e["action"], "path": fp, "ext": ext, "exists": exists, "entry": e["id"], "content": bool(text),
                    "secret": secret, "size": stt.st_size if stt else None, "hash": h}
            rows.append({"source": SOURCE, "id": rid, "date_ms": e["created"], "kind": ext or ("klasör" if exists and not is_file else "dosya"),
                         "title": name[:200], "url": None, "body": body, "meta": meta})
    return rows, st


def run(path, con, dry_run: bool = False, **_) -> dict:
    known: dict[str, str] = {}
    for rid, meta in con.execute("SELECT id, meta FROM items WHERE source = ?", (SOURCE,)):
        try:
            m = json.loads(meta) if meta else {}
        except ValueError:
            m = {}
        if m.get("hash"):
            known[rid] = m["hash"]
    try:
        rows, st = build_rows(path, known, extractor=extract_text)
    except FileNotFoundError:
        return {"kaynak": SOURCE, "okunan": 0, "yeni": 0, "not": "library.json yok (Nashi henüz bir dosya işlememiş)"}
    except PermissionError as e:
        return {"kaynak": SOURCE, "okunan": 0, "yeni": 0, "locked": True, "not": f"kilitli, sonraki turda denenecek ({str(e)[:80]})"}
    except ValueError as e:
        return {"kaynak": SOURCE, "okunan": 0, "yeni": 0, "error": True, "not": str(e)[:120]}
    r = sync_items(SOURCE, rows, con, dry_run)
    r.update(st)
    if not rows:
        r["not"] = "yeni ya da değişen dışa aktarım yok"
    return r
