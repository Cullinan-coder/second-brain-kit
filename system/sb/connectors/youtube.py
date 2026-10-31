"""Google Takeout YouTube: watch-history (.json/.html) ve subscriptions.csv → items (source=youtube)."""
from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

from ._common import clean, ingest_items, parse_iso, sid, text_date

_PREFIX = re.compile(r"^(?:Watched|Şunu izlediniz:?|İzlendi:?)\s+", re.I)
_HTML = re.compile(
    r'(?:Watched|Şunu izlediniz:?|İzlendi:?)(?:\s|&nbsp;)*<a href="([^"]+)">(.*?)</a>'
    r'(?:<br>\s*<a href="([^"]+)">(.*?)</a>)?<br>(.*?)</div>', re.S | re.I)


def _watch(title: str, url: str, ms, channel: str) -> dict:
    return {"source": "youtube", "id": sid("watch", url, ms or ""), "date_ms": ms, "kind": "watch",
            "title": clean(title), "url": url, "body": clean(f"{title} {channel}"), "meta": {"channel": channel}}


def _parse_json(path: Path) -> list[dict]:
    rows = []
    for e in json.loads(path.read_text(encoding="utf-8-sig")):
        url = e.get("titleUrl")
        if not url or not e.get("title"):
            continue
        ch = (e.get("subtitles") or [{}])[0].get("name", "")
        rows.append(_watch(_PREFIX.sub("", e["title"]), url, parse_iso(e.get("time", "")), ch))
    return rows


def _parse_html(path: Path) -> list[dict]:
    rows = []
    for m in _HTML.finditer(path.read_text(encoding="utf-8-sig", errors="replace")):
        url, title, _, channel, when = m.groups()
        rows.append(_watch(html.unescape(title), html.unescape(url), text_date(html.unescape(when)),
                           html.unescape(channel or "")))
    return rows


def _parse_subs(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.reader(f)):
            if i == 0 or len(r) < 3 or not r[0].strip():
                continue
            rows.append({"source": "youtube", "id": sid("sub", r[0]), "date_ms": None, "kind": "subscription",
                         "title": clean(r[2]), "url": r[1].strip(), "body": clean(r[2]),
                         "meta": {"channel": r[2].strip(), "channel_id": r[0].strip()}})
    return rows


def parse(path) -> list[dict]:
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".csv":
        return _parse_subs(path)
    return _parse_html(path) if ext in (".html", ".htm") else _parse_json(path)


def run(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("youtube", parse(path), con, dry_run)
