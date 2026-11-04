"""ClipBoardLine (resmî uygulama) → beyin arşivi (mail.db `items`, source=clipboardline). SALT OKUNUR.

Veri: `%APPDATA%\\ClipBoardLine\\library.json` (biçim: apps/clipboardline/windows/lib/model.cjs `class Store`):
  {schema:1, items:[{id, kind: text|link|image, text, url, title, name, author, note, tags[], folderIds[], pinned,
   ocrText, createdAt(ms), updatedAt, trashedAt, ...}], folders:[{id, name, parentId}], settings}.
Uygulamanın dosyasına ASLA yazılmaz: dosya geçici klasöre kopyalanır, kopya okunur (kilitliyse birkaç kez denenir).
Her şey beyne girer (metin, bağlantı, görsel OCR metni, ad/etiket/klasör/not) AMA parola/anahtar/kart/IBAN/TCKN/OTP gibi sır içeren
kayıt ATLANIR (sayısı raporlanır, içeriği hiçbir yere yazılmaz). Çöpe atılan kayıtlar beyne alınmaz; önceden alınmışsa arşivden kaldırılır.
Tekrar önleme: kimlik + içerik karması (aynı metin farklı kimlikle gelirse bir kez); etiket/not/OCR değişince kayıt güncellenir.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import time
from pathlib import Path

from ..redact import contains_secret
from ._common import sync_items

MAX_LIB = 64 * 1024 * 1024
BODY_MAX = 20000
SOURCE = "clipboardline"


def library_file(path) -> Path:
    p = Path(path)
    return p if p.is_file() else p / "library.json"


def read_library(path, retries: int = 3, wait: float = 0.5) -> dict:
    """library.json'u geçici kopyadan okur. Dosya yoksa FileNotFoundError, kilitliyse PermissionError, biçim bozuksa ValueError."""
    src = library_file(path)
    if not src.exists():
        raise FileNotFoundError(str(src))
    if src.stat().st_size > MAX_LIB:
        raise ValueError("library.json beklenenden büyük; okunmadı")
    last: Exception | None = None
    for _ in range(max(1, retries)):
        tmp = Path(tempfile.mkdtemp(prefix="sb-clb-"))
        try:
            dst = tmp / "library.json"
            shutil.copyfile(src, dst)
            data = json.loads(dst.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict) or not isinstance(data.get("items"), list):
                raise ValueError("library.json biçimi tanınmadı")
            return data
        except (PermissionError, OSError) as e:
            last = e
            time.sleep(wait)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    raise PermissionError(f"library.json kilitli ya da okunamadı: {last}")


def _folder_paths(folders: list) -> dict[str, str]:
    byid = {f.get("id"): f for f in folders if isinstance(f, dict)}
    out = {}
    for fid, f in byid.items():
        names, seen, cur = [], set(), f
        while cur and cur.get("id") not in seen:
            seen.add(cur.get("id"))
            names.append(str(cur.get("name") or ""))
            cur = byid.get(cur.get("parentId"))
        out[fid] = " / ".join(reversed([n for n in names if n]))
    return out


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


def _h(parts) -> str:
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:24]


def _title(it: dict) -> str:
    kind = it.get("kind")
    t = _s(it.get("title")) or _s(it.get("name"))
    if kind == "link":
        return t or _s(it.get("url"))[:120] or "Bağlantı"
    if kind == "image":
        return t or "Görsel"
    first = next((ln.strip() for ln in _s(it.get("text")).splitlines() if ln.strip()), "")
    return t or first[:100] or "Metin"


def item_row(it: dict, folders: dict[str, str]) -> tuple[dict | None, bool, bool]:
    """(satır, sır_var, çöpte). Satır yalnız sırsız ve çöpte olmayan kayıt için dolu."""
    if not isinstance(it, dict) or not it.get("id") or it.get("kind") not in ("text", "link", "image"):
        return None, False, False
    if it.get("trashedAt"):
        return None, False, True
    tags = [t for t in (it.get("tags") or []) if isinstance(t, str) and t.strip()]
    fnames = [folders[f] for f in (it.get("folderIds") or []) if f in folders and folders[f]]
    parts = {"text": _s(it.get("text")), "url": _s(it.get("url")), "title": _s(it.get("title")), "name": _s(it.get("name")),
             "author": _s(it.get("author")), "note": _s(it.get("note")), "ocr": _s(it.get("ocrText"))}
    if contains_secret("\n".join([*parts.values(), *tags, *fnames])):
        return None, True, False
    body_parts = []
    if parts["text"]:
        body_parts.append(parts["text"])
    if parts["url"]:
        body_parts.append(parts["url"])
    if it["kind"] == "link" and parts["title"]:
        body_parts.append(f"Başlık: {parts['title']}" + (f" — {parts['author']}" if parts["author"] else ""))
    if it["kind"] == "image":
        if parts["name"] or parts["title"]:
            body_parts.append(f"Görsel: {parts['name'] or parts['title']}")
        if parts["ocr"]:
            body_parts.append("Görseldeki yazı (OCR):\n" + parts["ocr"])
    if parts["note"]:
        body_parts.append("Not: " + parts["note"])
    if tags:
        body_parts.append("Etiketler: " + ", ".join(tags))
    if fnames:
        body_parts.append("Klasör: " + "; ".join(fnames))
    created = it.get("createdAt")
    meta = {"kind": it["kind"], "pinned": bool(it.get("pinned")), "tags": tags, "folders": fnames, "ocr": bool(parts["ocr"]),
            "hash": _h([it["kind"], *parts.values(), sorted(tags), sorted(fnames), bool(it.get("pinned"))]),
            "chash": _h([it["kind"], parts["text"], parts["url"], parts["ocr"], _s(it.get("imageFile"))])}
    row = {"source": SOURCE, "id": str(it["id"]), "date_ms": int(created) if isinstance(created, (int, float)) else None,
           "kind": it["kind"], "title": _title(it)[:200], "url": parts["url"] or None, "body": "\n".join(body_parts)[:BODY_MAX], "meta": meta}
    return row, False, False


def parse(path) -> tuple[list[dict], dict]:
    """(satırlar, {atlanan_sir, ids_secret, ids_trashed}) — hiçbir yere yazmaz."""
    lib = read_library(path)
    folders = _folder_paths(lib.get("folders") or [])
    rows, secret, trashed = [], [], []
    for it in lib["items"]:
        row, sec, tr = item_row(it, folders)
        if row:
            rows.append(row)
        elif sec:
            secret.append(str(it.get("id")))
        elif tr:
            trashed.append(str(it.get("id")))
    return rows, {"atlanan_sir": len(secret), "ids_secret": secret, "ids_trashed": trashed}


def run(path, con, dry_run: bool = False, **_) -> dict:
    try:
        rows, st = parse(path)
    except FileNotFoundError:
        return {"kaynak": SOURCE, "okunan": 0, "yeni": 0, "not": "library.json yok (uygulama henüz açılıp veri tutmamış)"}
    except PermissionError as e:
        return {"kaynak": SOURCE, "okunan": 0, "yeni": 0, "locked": True, "not": f"kilitli, sonraki turda denenecek ({str(e)[:80]})"}
    except ValueError as e:
        return {"kaynak": SOURCE, "okunan": 0, "yeni": 0, "error": True, "not": str(e)[:120]}
    # sır içeren ya da çöpe atılan kayıt daha önce alındıysa arşivden kaldır (kullanıcının silme kararına saygı)
    drop = [i for i in st["ids_secret"] + st["ids_trashed"]
            if con.execute("SELECT 1 FROM items WHERE source = ? AND id = ?", (SOURCE, i)).fetchone()]
    if drop and not dry_run:
        con.executemany("DELETE FROM items WHERE source = ? AND id = ?", [(SOURCE, i) for i in drop])
    r = sync_items(SOURCE, rows, con, dry_run)
    r["atlanan_sir"] = st["atlanan_sir"]
    r["silinmis"] = len(drop)
    if not rows and not st["atlanan_sir"]:
        r["not"] = "uygulamada henüz kayıt yok (ClipBoardLine ayarlarında metin/görsel toplama kapalı olabilir)"
    return r
