"""Notion 'Markdown & CSV' dışa aktarımı (zip/klasör) → `40-Kaynaklar/Notion/` notları + items (source=notion)."""
from __future__ import annotations

import csv
import io
import re
from pathlib import PurePosixPath
from urllib.parse import unquote

from ._common import clean, ingest_items, sid
from .notes import iter_files, text_of, write_notes

_HEX = re.compile(r"\s+[0-9a-f]{32}(?=\.\w+$|$)", re.I)
_ID = re.compile(r"([0-9a-f]{32})", re.I)
_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+\.(?:md|csv))\)")


def clean_name(s: str) -> str:
    return _HEX.sub("", s)


def _wiki(m):
    target = PurePosixPath(clean_name(unquote(m.group(2)))).stem
    return f"[[{target}]]" if m.group(1).strip() in ("", target) else f"[[{target}|{m.group(1)}]]"


def _csv_md(text: str) -> str:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return ""
    w = len(rows[0])
    line = lambda r: "| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in (r + [""] * w)[:w]) + " |"
    return "\n".join([line(rows[0]), "|" + " --- |" * w, *[line(r) for r in rows[1:]]])


def parse(path) -> list[dict]:
    out = []
    for name, load, mtime in iter_files(path):
        ext = PurePosixPath(name).suffix.lower()
        if ext not in (".md", ".csv") or "__MACOSX" in name:
            continue
        parts = [clean_name(x) for x in PurePosixPath(name).parts]
        stem = PurePosixPath(parts[-1]).stem
        text = text_of(load())
        body = clean(_LINK.sub(_wiki, text) if ext == ".md" else _csv_md(text))
        if ext == ".md":  # ilk başlık sayfa adıysa yinelenmesin
            body = re.sub(rf"\A#\s+{re.escape(stem)}\s*\n+", "", body)
        pid = _ID.search(PurePosixPath(name).name)
        out.append({"title": stem, "body": body, "date_ms": int(mtime * 1000) if mtime else None, "tags": [],
                    "id": pid.group(1).lower() if pid else sid(name), "sub": "/".join(parts[:-1])})
    return out


def run(path, con, dry_run: bool = False, **_) -> dict:
    pages = parse(path)
    items = [{"source": "notion", "id": p["id"], "date_ms": p["date_ms"], "kind": "page", "title": p["title"],
              "url": None, "body": p["body"], "meta": {"path": p["sub"]}} for p in pages]
    res = ingest_items("notion", items, con, dry_run)
    written = [] if dry_run else write_notes(pages, "Notion", "notion")
    return {**res, "notlar": len(written), "yazıldı": not dry_run and bool(written)}
