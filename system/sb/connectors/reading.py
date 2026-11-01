"""Pocket (ril_export.html / CSV) ve Raindrop (CSV) → items (kind=link, okuma listesi)."""
from __future__ import annotations

import html
import re
from pathlib import Path

from ._common import clean, ingest_items, parse_iso, sid
from .bank import pick, read_rows

_A = re.compile(r"<a\s+([^>]*?)>(.*?)</a>", re.S | re.I)
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def _item(source, url, title, ms, tags, extra=None) -> dict:
    meta = {"tags": tags, **(extra or {})}
    return {"source": source, "id": sid(source, url), "date_ms": ms, "kind": "link", "title": clean(title or url),
            "url": url, "body": clean(f"{title} {' '.join(tags)} {(extra or {}).get('note', '')}"), "meta": meta}


def _ts(v: str) -> int | None:
    v = (v or "").strip()
    if v.isdigit():
        return int(v) * 1000 if len(v) <= 11 else int(v)
    return parse_iso(v) if v else None


def parse_pocket(path) -> list[dict]:
    path = Path(path)
    rows = []
    if path.suffix.lower() in (".html", ".htm"):
        for m in _A.finditer(path.read_text(encoding="utf-8-sig", errors="replace")):
            at = dict(_ATTR.findall(m.group(1)))
            if not at.get("href", "").startswith("http"):
                continue
            tags = [t for t in at.get("tags", "").split(",") if t]
            rows.append(_item("pocket", html.unescape(at["href"]), html.unescape(m.group(2)),
                              _ts(at.get("time_added", "")), tags))
        return rows
    for r in read_rows(path):
        url = pick(r, ("url",))
        if url.startswith("http"):
            rows.append(_item("pocket", url, pick(r, ("title",)), _ts(pick(r, ("time_added",))),
                              [t.strip() for t in re.split(r"[|,]", pick(r, ("tags",))) if t.strip()],
                              {"status": pick(r, ("status",))}))
    return rows


def parse_raindrop(path) -> list[dict]:
    rows = []
    for r in read_rows(path):
        url = pick(r, ("url",))
        if url.startswith("http"):
            rows.append(_item("raindrop", url, pick(r, ("title",)), _ts(pick(r, ("created",))),
                              [t.strip() for t in pick(r, ("tags",)).split(",") if t.strip()],
                              {"folder": pick(r, ("folder",)), "note": clean(pick(r, ("note", "excerpt")))}))
    return rows


def run_pocket(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("pocket", parse_pocket(path), con, dry_run)


def run_raindrop(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("raindrop", parse_raindrop(path), con, dry_run)
