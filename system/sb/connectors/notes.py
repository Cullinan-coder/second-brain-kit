"""Not içe aktarıcıları → kasa notları `40-Kaynaklar/Notlar/<kaynak>/` (+ Paket M'nin ortak yardımcıları).

Kaynaklar: Google Keep (Takeout zip/klasör), Apple Notlar (.html/.txt klasörü), OneNote (.docx/.html), Evernote (.enex).
"""
from __future__ import annotations

import html
import io
import re
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from ._common import clean, sid


# ---- ortak: klasör ya da zip üzerinde dosya gezme
def iter_files(path) -> list[tuple[str, callable, float | None]]:
    """[(göreli/posix ad, bytes döndüren işlev, mtime epoch)] — path klasör, zip ya da tek dosya."""
    p = Path(path)
    out = []
    if p.is_dir():
        for f in sorted(p.rglob("*")):
            if f.is_file():
                out.append((f.relative_to(p).as_posix(), (lambda f=f: f.read_bytes()), f.stat().st_mtime))
    elif p.suffix.lower() == ".zip":
        z = zipfile.ZipFile(p)
        for i in z.infolist():
            if not i.is_dir():
                try:
                    ts = datetime(*i.date_time).timestamp()
                except (ValueError, OSError):
                    ts = None
                out.append((i.filename.replace("\\", "/"), (lambda n=i.filename, z=z: z.read(n)), ts))
    elif p.is_file():
        out.append((p.name, (lambda: p.read_bytes()), p.stat().st_mtime))
    return out


def text_of(raw: bytes) -> str:
    return raw.decode("utf-8-sig", "replace")


def fix_utf8(s):
    """Instagram gibi latin-1 kaçışlı bozuk UTF-8'i düzeltir."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def message_row(account, thread, ms, sender, mine, body, attachments=(), key="", labels=None):
    body = clean(body)
    return {
        "account": account, "id": sid(account, thread, ms or "", sender, body, key, *attachments), "thread_id": thread,
        "date_ms": ms, "from_addr": "me" if mine else sender, "from_name": sender,
        "to_addrs": thread if mine else "", "subject": thread, "snippet": body[:200], "body": body,
        "labels": labels or [account], "attachments": list(attachments),
    }


def html_text(h: str) -> str:
    h = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h\d|tr)>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", "", h))
    return "\n".join(ln.strip() for ln in h.replace("\xa0", " ").splitlines()).strip()


def docx_text(raw: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:(?:br|tab)\s*/>", " ", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml)).strip()


# ---- kasa yazımı
def write_notes(notes: list[dict], folder: str, source: str, account: str = "") -> list[str]:
    """notes: {title, body, date_ms, tags[], id, archived?, sub?}. Aynı source_id aynı dosyaya yazılır (kopyasız)."""
    from .. import vault_ops
    from ..notes import dump_note, safe_filename
    base = vault_ops.VAULT / "40-Kaynaklar" / folder
    written = []
    for n in notes:
        d = datetime.fromtimestamp(n["date_ms"] / 1000).date() if n.get("date_ms") else date.today()
        sub = base / n["sub"] if n.get("sub") else base
        sub.mkdir(parents=True, exist_ok=True)
        name = safe_filename(n["title"]) or f"{source} {n['id'][:8]}"
        sid_ = f"{source}:{account}:{n['id']}" if account else f"{source}:{n['id']}"
        p = sub / f"{name}.md"
        if p.exists() and sid_ not in p.read_text(encoding="utf-8"):
            p = sub / f"{name} ({n['id'][:8]}).md"
        fm = {"type": "kaynak", "status": "arsiv" if n.get("archived") else "aktif",
              "tags": [source, *[re.sub(r"\W+", "-", t.lower()).strip("-") for t in n.get("tags", []) if t]],
              "source": source, "source_id": sid_, "created": d, "updated": d, "due": None}
        p.write_text(dump_note(fm, f"# {n['title']}\n\n{n['body']}\n"), encoding="utf-8")
        written.append(vault_ops._rel(p))
    if written:
        vault_ops.commit(written, f"{source} notları: {len(written)}")
    return written


def _fmt(ms):
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")


def _finish(kaynak, notes, dry_run, folder=None):
    written = [] if dry_run else write_notes(notes, folder or f"Notlar/{kaynak}", kaynak)
    ds = [n["date_ms"] for n in notes if n.get("date_ms")]
    return {"kaynak": kaynak, "okunan": len(notes), "yeni": len(notes), "yazıldı": not dry_run and bool(written),
            "notlar": len(written), "tarih_min": _fmt(min(ds)) if ds else None, "tarih_max": _fmt(max(ds)) if ds else None,
            "ornek": [n["title"] for n in notes[:3]]}


# ---- Keep
def parse_keep(path) -> list[dict]:
    from .takeout import keep_notes
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            notes = keep_notes(z)
    else:  # klasör: Keep JSON'larını bellekte Takeout düzenine sok
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, load, _ in iter_files(p):
                if name.lower().endswith(".json"):
                    z.writestr(f"Takeout/Keep/{Path(name).name}", load())
        with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as z:
            notes = keep_notes(z)
    return [{**k, "tags": k["labels"]} for k in notes]


def run_keep(path, con=None, dry_run: bool = False, **_) -> dict:
    return _finish("keep", parse_keep(path), dry_run)


# ---- Apple Notlar / OneNote
def _doc_notes(path, exts) -> list[dict]:
    notes = []
    for name, load, mtime in iter_files(path):
        ext = Path(name).suffix.lower()
        if ext not in exts:
            continue
        raw = load()
        try:
            text = docx_text(raw) if ext == ".docx" else html_text(text_of(raw)) if ext in (".html", ".htm") else text_of(raw)
        except (zipfile.BadZipFile, KeyError):
            continue
        body = clean(text)
        if not body:
            continue
        parts = Path(name).parent.parts
        notes.append({"title": Path(name).stem[:80], "body": body, "date_ms": int(mtime * 1000) if mtime else None,
                      "tags": [], "id": sid(name, body), "sub": "/".join(parts)})
    return notes


def parse_apple(path):
    return _doc_notes(path, {".html", ".htm", ".txt"})


def parse_onenote(path):
    return _doc_notes(path, {".docx", ".html", ".htm"})


def run_apple(path, con=None, dry_run: bool = False, **_) -> dict:
    return _finish("apple-notlar", parse_apple(path), dry_run)


def run_onenote(path, con=None, dry_run: bool = False, **_) -> dict:
    return _finish("onenote", parse_onenote(path), dry_run)


# ---- Evernote
def _enex_date(s) -> int | None:
    try:
        return int(datetime.strptime(s.strip(), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000)
    except (ValueError, AttributeError):
        return None


def parse_enex(path) -> list[dict]:
    notes = []
    for name, load, _ in iter_files(path):
        if not name.lower().endswith(".enex"):
            continue
        try:
            root = ET.fromstring(load())
        except ET.ParseError:
            continue
        for n in root.iter("note"):
            title = (n.findtext("title") or "").strip()
            body = clean(html_text(n.findtext("content") or ""))
            if not body and not title:
                continue
            ms = _enex_date(n.findtext("created"))
            title = (title or next((l for l in body.splitlines() if l.strip()), "Evernote notu"))[:80]
            notes.append({"title": title, "body": body, "date_ms": ms, "tags": [t.text for t in n.findall("tag") if t.text],
                          "id": sid(title, ms or "", body)})
    return notes


def run_evernote(path, con=None, dry_run: bool = False, **_) -> dict:
    return _finish("evernote", parse_enex(path), dry_run)
