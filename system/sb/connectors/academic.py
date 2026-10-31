"""Akademik kaynaklar: arXiv sorguları (config/rss.yaml `arxiv:`), Zotero (zotero.sqlite) ve BibTeX (.bib) → items (kind=paper)."""
from __future__ import annotations

import re
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from . import rss
from ._common import clean, ingest_items, sid, to_ms

ARXIV_URL = "http://export.arxiv.org/api/query?search_query={q}&start=0&max_results=25&sortBy=submittedDate&sortOrder=descending"


def parse_arxiv(xml: bytes, query: str) -> list[dict]:
    import xml.etree.ElementTree as ET
    rows = []
    for e in ET.fromstring(xml).iter():
        if rss._local(e.tag) != "entry":
            continue
        abs_url = rss._text(e, "id")
        aid = re.sub(r"v\d+$", "", abs_url.rsplit("/abs/", 1)[-1])
        authors = [rss._text(a, "name") for a in e if rss._local(a.tag) == "author"]
        title = clean(re.sub(r"\s+", " ", rss._text(e, "title")))
        rows.append({"source": "arxiv", "id": aid, "date_ms": rss._date(rss._text(e, "published")), "kind": "paper",
                     "title": title, "url": abs_url or None,
                     "body": clean(re.sub(r"\s+", " ", rss._text(e, "summary"))),
                     "meta": {"authors": authors, "query": query}})
    return rows


def parse_arxiv_config(path=None) -> list[dict]:
    rows = []
    for q in rss.load_config(path).get("arxiv") or []:
        rows += parse_arxiv(rss._fetch(ARXIV_URL.format(q=quote(str(q)))), str(q))
    return rows


def run_arxiv(path=None, con=None, dry_run: bool = False, **_) -> dict:
    if not rss.load_config(path).get("arxiv"):
        return {"kaynak": "arxiv", "okunan": 0, "yeni": 0, "not": "sorgu yok (config/rss.yaml `arxiv:`)"}
    return ingest_items("arxiv", parse_arxiv_config(path), con, dry_run)


def _date_ms(s: str | None) -> int | None:
    m = re.search(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", s or "")
    if not m:
        return None
    try:
        return to_ms(datetime(int(m.group(1)), int(m.group(2) or 1) or 1, int(m.group(3) or 1) or 1))
    except ValueError:
        return None


def parse_zotero(path) -> list[dict]:
    path = Path(path)
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "z.sqlite"
        shutil.copy2(path, dst)
        con = sqlite3.connect(f"{dst.as_uri()}?mode=ro", uri=True)
        try:
            items = con.execute(
                "SELECT i.itemID, i.key FROM items i JOIN itemTypes t ON t.itemTypeID = i.itemTypeID "
                "WHERE t.typeName NOT IN ('attachment', 'note', 'annotation') "
                "AND i.itemID NOT IN (SELECT itemID FROM deletedItems)").fetchall()
            rows = []
            for iid, key in items:
                f = dict(con.execute(
                    "SELECT f.fieldName, v.value FROM itemData d JOIN fields f ON f.fieldID = d.fieldID "
                    "JOIN itemDataValues v ON v.valueID = d.valueID WHERE d.itemID = ?", (iid,)).fetchall())
                if not f.get("title"):
                    continue
                authors = [" ".join(x for x in (fn, ln) if x) for fn, ln in con.execute(
                    "SELECT c.firstName, c.lastName FROM itemCreators ic JOIN creators c ON c.creatorID = ic.creatorID "
                    "WHERE ic.itemID = ? ORDER BY ic.orderIndex", (iid,))]
                url = f.get("url") or (f"https://doi.org/{f['DOI']}" if f.get("DOI") else None)
                rows.append({"source": "zotero", "id": key, "date_ms": _date_ms(f.get("date")), "kind": "paper",
                             "title": clean(f["title"]), "url": url, "body": clean(f.get("abstractNote")),
                             "meta": {"authors": authors, "doi": f.get("DOI")}})
            return rows
        finally:
            con.close()


def _bib_value(s: str, i: int) -> tuple[str, int]:
    if i < len(s) and s[i] == "{":
        depth, j = 1, i + 1
        while j < len(s) and depth:
            depth += (s[j] == "{") - (s[j] == "}")
            j += 1
        return s[i + 1:j - 1], j
    if i < len(s) and s[i] == '"':
        j = s.index('"', i + 1) if '"' in s[i + 1:] else len(s) - 1
        return s[i + 1:j], j + 1
    m = re.match(r"[^,}\s]+", s[i:])
    return (m.group() if m else ""), i + (len(m.group()) if m else 0)


def parse_bibtex(path) -> list[dict]:
    s = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    rows = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", s):
        if m.group(1).lower() in ("comment", "string", "preamble"):
            continue
        fields, i = {}, m.end()
        while i < len(s):
            fm = re.compile(r"\s*,?\s*(\w+)\s*=\s*").match(s, i)
            if not fm:
                break
            val, i = _bib_value(s, fm.end())
            fields[fm.group(1).lower()] = re.sub(r"\s+", " ", val.replace("{", "").replace("}", "")).strip()
        if not fields.get("title"):
            continue
        authors = [a.strip() for a in re.split(r"\s+and\s+", fields.get("author", "")) if a.strip()]
        url = fields.get("url") or (f"https://doi.org/{fields['doi']}" if fields.get("doi") else None)
        rows.append({"source": "bibtex", "id": sid(m.group(2), fields["title"]),
                     "date_ms": _date_ms(fields.get("date") or fields.get("year")), "kind": "paper",
                     "title": clean(fields["title"]), "url": url, "body": clean(fields.get("abstract")),
                     "meta": {"authors": authors, "key": m.group(2), "type": m.group(1).lower()}})
    return rows


def parse(path) -> list[dict]:
    return parse_bibtex(path) if Path(path).suffix.lower() == ".bib" else parse_zotero(path)


def run(path, con, dry_run: bool = False, **_) -> dict:
    rows = parse(path)
    return ingest_items(rows[0]["source"] if rows else "zotero", rows, con, dry_run)
