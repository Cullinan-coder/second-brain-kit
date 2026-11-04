"""Veri yükleme: ham gövde yükleme (≤ 2 GB, `DATA/import_staging/<kaynak>/`), dry-run önizleme, içe aktarma, geçmiş.

Dosya adı temizlenir (yol bileşeni yok), kaynak kimliği manifestten doğrulanır, yazma hep hazırlık klasörünün içinde kalır.
İçe aktarma komutları `engine._run_capture/_run_stream` kapılarından geçer (testte taklit).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

try:
    from . import engine as E
except ImportError:                                           # pragma: no cover
    import engine as E  # type: ignore

MAX_UPLOAD = 2 * 1024 ** 3
SRC_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")
_BAD = re.compile(r"[^\w.\- ()+]", re.UNICODE)


def clean_name(name: str) -> str:
    n = re.split(r"[\\/]", str(name or ""))[-1].replace("\x00", "")
    n = _BAD.sub("_", n).strip(" .")
    n = re.sub(r"\.{2,}", ".", n)[:120]
    if not n or n in (".", ".."):
        raise ValueError("geçersiz dosya adı")
    return n


def _source(source: str) -> dict:
    if not SRC_RE.match(str(source or "")):
        raise ValueError("geçersiz kaynak")
    m = E.plugins_mod().get(source, "source")
    if not m:
        raise ValueError(f"bilinmeyen kaynak: {source}")
    return m


def staging(eng, source: str) -> Path:
    d = (eng.data / "import_staging" / source).resolve()
    root = (eng.data / "import_staging").resolve()
    if root not in d.parents:
        raise ValueError("geçersiz kaynak")
    return d


def upload(eng, source: str, name: str, rfile, length: int) -> dict:
    _source(source)
    fn = clean_name(name)
    if length <= 0:
        raise ValueError("boş ya da uzunluğu belirsiz yükleme")
    if length > MAX_UPLOAD:
        raise ValueError(f"dosya çok büyük (en çok {MAX_UPLOAD // 1024 ** 3} GB)")
    d = staging(eng, source)
    d.mkdir(parents=True, exist_ok=True)
    dest = (d / fn).resolve()
    if d not in dest.parents:
        raise ValueError("geçersiz dosya adı")
    tmp = dest.with_name(dest.name + ".part")
    got = 0
    try:
        with open(tmp, "wb") as f:
            while got < length:
                chunk = rfile.read(min(1 << 20, length - got))
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
        if got != length:
            raise ValueError("yükleme yarım kaldı")
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink()
    return {"ok": True, "source": source, "file": fn, "size": got}


def resolve_file(eng, source: str, file: str) -> Path:
    _source(source)
    p = (staging(eng, source) / clean_name(file)).resolve()
    if not p.is_file():
        raise ValueError("dosya yüklenmemiş: önce yükle")
    return p


def command(eng, m: dict, path: Path, dry: bool) -> list[str] | None:
    conn = (m.get("import") or {}).get("connector")
    if conn:
        return eng.sb_cmd("import", conn, str(path), *(["--dry-run"] if dry else []))
    if m["id"] == "history-import":
        return eng.sb_cmd("history-import", str(path), *([] if dry else ["--apply"]))
    if m["id"] == "takeout":
        return eng.sb_cmd("takeout", str(path), *(["--dry-run"] if dry else []))
    return None


def preview(eng, b: dict) -> dict:
    m = _source(str(b.get("source") or ""))
    p = resolve_file(eng, m["id"], str(b.get("file") or ""))
    cmd = command(eng, m, p, True)
    if not cmd:
        return {"ok": False, "source": m["id"], "file": p.name, "supported": False,
                "message": "Bu kaynağın içe aktarıcısı henüz yok; dosya hazır bekliyor."}
    rc, out = E._run_capture(cmd, 600)
    txt = E.redact(out.strip(), eng._secrets)[-4000:]
    n = re.search(r"okunan\s+(\d+)", txt)
    return {"ok": rc == 0, "source": m["id"], "file": p.name, "supported": True, "dry_run": True, "summary": txt,
            "read": int(n.group(1)) if n else None}


def _history_file(eng) -> Path:
    return eng.data / "setup_imports.json"


def history(eng) -> dict:
    try:
        return {"imports": json.loads(_history_file(eng).read_text(encoding="utf-8"))}
    except Exception:                                         # noqa: BLE001
        return {"imports": []}


_COUNT_RES = (re.compile(r"(?:yaz[ıi]lan|aktar[ıi]lan|eklenen|yeni|okunan)\s*:?\s*(\d+)", re.I),
              re.compile(r"(\d+)\s+(?:mesaj|kay[ıi]t|not|öğe|satır|yeni|dosya)", re.I))


def parse_count(lines) -> int | None:
    """Bağlayıcı çıktısından 'N mesaj/kayıt/...' sayısı (son eşleşme; yoksa None)."""
    best = None
    for ln in lines:
        for rx in _COUNT_RES:
            m = rx.search(str(ln))
            if m:
                best = int(m.group(1))
    return best


def _record(eng, source: str, file: str, ok: bool, note: str, count: int | None = None) -> None:
    items = history(eng)["imports"]
    items.append({"source": source, "file": file, "ok": ok, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "note": note[:200],
                  **({"count": count} if count is not None else {})})
    eng.data.mkdir(parents=True, exist_ok=True)
    _history_file(eng).write_text(json.dumps(items[-200:], ensure_ascii=False, indent=1), encoding="utf-8")


def run(eng, b: dict, wait: bool = False) -> bool:
    m = _source(str(b.get("source") or ""))
    p = resolve_file(eng, m["id"], str(b.get("file") or ""))
    cmd = command(eng, m, p, False)
    if not cmd:
        raise ValueError("Bu kaynağın içe aktarıcısı henüz yok")

    def work(pct):
        out: list[str] = []

        def lg(line):
            out.append(str(line))
            eng.log(line)
        rc = E._run_stream(cmd, lg)
        _record(eng, m["id"], p.name, rc == 0, f"çıkış kodu {rc}", parse_count(out) if rc == 0 else None)
        if rc:
            raise RuntimeError(f"içe aktarma başarısız (kod {rc})")
    return eng.run_job("import:" + m["id"], f"İçe aktarılıyor: {m['id']}", work, wait)
