"""Kindle 'My Clippings.txt' (EN/TR) → items (source=kindle; kind highlight/note/bookmark)."""
from __future__ import annotations

import re
from pathlib import Path

from ._common import clean, ingest_items, sid, text_date

_KIND = [("highlight", re.compile(r"highlight|vurgu", re.I)), ("note", re.compile(r"\bnote\b|notunuz", re.I)),
         ("bookmark", re.compile(r"bookmark|yer im", re.I))]
_LOC = re.compile(r"(?:Location|Konum)\s+([\d-]+)|(\d[\d-]*)'?\w*\s+konum", re.I)
_PAGE = re.compile(r"(?:page|sayfa)\s+(\d+)|(\d+)\.\s*sayfa", re.I)
_AUTHOR = re.compile(r"^(.*?)\s*\(([^()]*)\)\s*$")


def _title(line: str) -> tuple[str, str]:
    line = line.lstrip("\ufeff").strip()
    m = _AUTHOR.match(line)
    return (m.group(1).strip(), m.group(2).strip()) if m and m.group(1) else (line, "")


def parse(path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    rows = []
    for block in text.split("=========="):
        lines = [ln.rstrip() for ln in block.strip().splitlines()]
        if len(lines) < 2 or not lines[0].strip():
            continue
        book, author = _title(lines[0])
        meta_line = lines[1].strip()
        kind = next((k for k, rx in _KIND if rx.search(meta_line)), None)
        if not kind:
            continue
        body = clean("\n".join(lines[2:]))
        loc = _LOC.search(meta_line)
        page = _PAGE.search(meta_line)
        location = (loc.group(1) or loc.group(2)) if loc else None
        pg = (page.group(1) or page.group(2)) if page else None
        added = re.split(r"Added on|Eklenme:?", meta_line, maxsplit=1)
        ms = text_date(added[1]) if len(added) > 1 else None
        rows.append({
            "source": "kindle", "id": sid(book, kind, location or pg or "", body, ms or ""), "date_ms": ms,
            "kind": kind, "title": book, "url": None, "body": body,
            "meta": {"author": author, "location": location, "page": pg},
        })
    return rows


def run(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("kindle", parse(path), con, dry_run)
