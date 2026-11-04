"""Belge içerik arşivi: bilgisayardaki belgelerin METNİ → mail.db `file_text` + FTS5 arama.

Yapay zeka kullanmaz; yerelde çıkarır (pypdf, python-docx, python-pptx, openpyxl, ipynb JSON, düz metin).
Sadece değişen dosyalar yeniden işlenir (mtime). Metin git'e/telefona gitmez; derleme ve `sb search` kullanır.
"""
from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS file_text (
    path   TEXT PRIMARY KEY,
    mtime  REAL,
    chars  INTEGER,
    text   TEXT,
    error  TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS file_text_fts USING fts5(
    path, text, content='file_text', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS file_text_ai AFTER INSERT ON file_text BEGIN
    INSERT INTO file_text_fts(rowid, path, text) VALUES (new.rowid, new.path, new.text);
END;
CREATE TRIGGER IF NOT EXISTS file_text_ad AFTER DELETE ON file_text BEGIN
    INSERT INTO file_text_fts(file_text_fts, rowid, path, text) VALUES ('delete', old.rowid, old.path, old.text);
END;
"""
# json/html bilerek yok: çoğu veri dökümü ya da kazınmış sayfa (Workspace'te 100 binden fazla); metin arşivini şişirir.
EXTS = {"pdf", "docx", "pptx", "xlsx", "ipynb", "md", "txt", "csv", "py", "js", "ts", "tsx", "php", "cpp", "h", "java", "rtf"}
CODE = {"py", "js", "ts", "tsx", "php", "cpp", "h", "java", "csv", "txt"}   # kod/düz metin: daha kısa saklanır
CODE_CHARS = 30_000
MAX_BYTES = 40 * 1024 * 1024      # bundan büyük dosya atlanır
MAX_CHARS = 100_000               # dosya başına saklanan metin
TEXT_HEAD = 300_000               # düz metin dosyalarında okunacak bayt


MAX_UNZIPPED = 200 * 1024 * 1024  # docx/pptx/xlsx/zip: toplam açılmış boyut sınırı (zip bombası)
MAX_ZIP_FILES = 5000
MAX_MEMBER = 100 * 1024 * 1024    # tek üye sınırı
MAX_RATIO = 200                   # sıkıştırma oranı sınırı (büyük üyelerde); düz metin ~10x, sıfır dolgu ~1000x
RATIO_MIN_SIZE = 20 * 1024 * 1024


def guard_zip(p: Path) -> None:
    """Açmadan önce zip üst bilgisini denetler: toplam açılmış boyut, tek üye boyutu, sıkıştırma oranı ya da dosya sayısı
    aşılırsa ValueError (D-28)."""
    with zipfile.ZipFile(p) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_FILES:
            raise ValueError(f"zip çok fazla dosya içeriyor ({len(infos)}): çıkarma kesildi")
        if sum(i.file_size for i in infos) > MAX_UNZIPPED:
            raise ValueError("zip açılmış boyutu sınırı aşıyor: çıkarma kesildi")
        for i in infos:
            if i.file_size > MAX_MEMBER:
                raise ValueError(f"zip üyesi çok büyük ({i.filename}): çıkarma kesildi")
            if i.file_size > RATIO_MIN_SIZE and i.file_size > MAX_RATIO * max(i.compress_size, 1):
                raise ValueError(f"zip sıkıştırma oranı şüpheli ({i.filename}): zip bombası olabilir, çıkarma kesildi")


def _pdf(p: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(p))
    out = []
    for page in reader.pages[:60]:
        out.append(page.extract_text() or "")
        if sum(map(len, out)) > MAX_CHARS:
            break
    return "\n".join(out)


def _docx(p: Path) -> str:
    import docx
    guard_zip(p)
    d = docx.Document(str(p))
    parts = [para.text for para in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n".join(parts)


def _pptx(p: Path) -> str:
    from pptx import Presentation
    guard_zip(p)
    out = []
    for i, slide in enumerate(Presentation(str(p)).slides, 1):
        texts = [sh.text_frame.text for sh in slide.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()]
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            texts.append("[not] " + slide.notes_slide.notes_text_frame.text)
        out.append(f"--- slayt {i} ---\n" + "\n".join(texts))
    return "\n".join(out)


def _xlsx(p: Path) -> str:
    from openpyxl import load_workbook
    guard_zip(p)
    wb = load_workbook(str(p), read_only=True, data_only=True)
    out = []
    for ws in wb.worksheets[:10]:
        out.append(f"--- sayfa {ws.title} ---")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= 200:
                out.append("…")
                break
            out.append(" | ".join("" if v is None else str(v) for v in row))
    return "\n".join(out)


def _ipynb(p: Path) -> str:
    nb = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    out = []
    for c in nb.get("cells", []):
        src = "".join(c.get("source", []))
        out.append(("# [kod]\n" if c.get("cell_type") == "code" else "") + src)
    return "\n\n".join(out)


def _plain(p: Path) -> str:
    with open(p, "rb") as f:
        raw = f.read(TEXT_HEAD)
    for enc in ("utf-8", "cp1254", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


READERS = {"pdf": _pdf, "docx": _docx, "pptx": _pptx, "xlsx": _xlsx, "ipynb": _ipynb}


def extract(p: Path) -> str:
    ext = p.suffix.lower().lstrip(".")
    return READERS.get(ext, _plain)(p)


def sync(con: sqlite3.Connection, log=print, limit: int | None = None) -> tuple[int, int]:
    """local_files'taki belgelerden değişenlerin metnini çıkarır; silinenleri kaldırır."""
    con.executescript(SCHEMA)
    known = dict(con.execute("SELECT path, mtime FROM file_text"))
    rows = con.execute("SELECT path, ext, size, mtime FROM local_files").fetchall()
    todo = [(p, e, s, m) for p, e, s, m in rows if e in EXTS and s <= MAX_BYTES and known.get(p) != m]
    if limit:
        todo = todo[:limit]
    log(f"içerik: {len(todo)} belge işlenecek (toplam aday {sum(1 for r in rows if r[1] in EXTS)})")
    done = errors = 0
    for i, (path, ext, size, mtime) in enumerate(todo, 1):
        text, err = "", None
        try:
            # PDF'lerden gelen yarım (surrogate) karakterler SQLite'a yazılamaz; atılır.
            text = extract(Path(path))[:CODE_CHARS if ext in CODE else MAX_CHARS].encode("utf-8", "ignore").decode("utf-8")
        except (Exception, zipfile.BadZipFile) as e:  # bozuk/şifreli belge: hata kaydedilir, devam edilir
            err = f"{type(e).__name__}: {str(e)[:150]}"
            errors += 1
        con.execute("DELETE FROM file_text WHERE path = ?", (path,))
        con.execute("INSERT INTO file_text(path, mtime, chars, text, error) VALUES (?,?,?,?,?)",
                    (path, mtime, len(text), text, err))
        done += 1
        if i % 200 == 0:
            con.commit()
            log(f"  {i}/{len(todo)}")
    current = {r[0] for r in rows}
    stale = [p for p in known if p not in current]
    con.executemany("DELETE FROM file_text WHERE path = ?", [(p,) for p in stale])
    con.commit()
    log(f"içerik: {done} belge işlendi ({errors} okunamadı), {len(stale)} silinen kaldırıldı")
    return done, errors


def search(con: sqlite3.Connection, query: str, limit: int = 20, any_word: bool = False) -> list[tuple[str, str]]:
    """Belgeler + mailler/SMS + Drive adları içinde arar: (kaynak, satır) listesi.
    any_word=True: kelimelerden herhangi biri yeter (OR, en iyi eşleşen önce); varsayılan hepsi birden (AND)."""
    con.executescript(SCHEMA)
    out = []
    q = (" OR " if any_word else " ").join(f'"{w}"' for w in query.split())
    for path, snip in con.execute(
            "SELECT path, snippet(file_text_fts, 1, '«', '»', '…', 12) FROM file_text_fts WHERE file_text_fts MATCH ? "
            "ORDER BY rank LIMIT ?", (q, limit)):
        out.append(("dosya", f"{path}\n    {snip}"))
    for acc, subj, snip in con.execute(
            "SELECT m.account, m.subject, snippet(messages_fts, 1, '«', '»', '…', 12) FROM messages_fts "
            "JOIN messages m ON m.rowid = messages_fts.rowid WHERE messages_fts MATCH ? ORDER BY rank LIMIT ?", (q, limit)):
        out.append(("mail" if acc != "sms" else "sms", f"[{acc}] {subj}\n    {snip}"))
    words = query.split() if any_word else [query]
    clause = " OR ".join(["name LIKE ? OR text LIKE ?"] * len(words))
    params = [x for w in words for x in (f"%{w}%", f"%{w}%")]
    for name, path, link in con.execute(f"SELECT name, path, link FROM drive_files WHERE {clause} LIMIT ?", (*params, limit)):
        out.append(("drive", f"{path}/{name} {link}"))
    return out
