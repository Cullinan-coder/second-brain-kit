"""RSS 2.0 / Atom akışları (config/rss.yaml) → items (source=rss, kind=article). Tek ağ kullanan bağlayıcı."""
from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

from .. import config
from ._common import clean, ingest_items, parse_iso, sid, to_ms

CONFIG = config.SYSTEM / "config" / "rss.yaml"
UA = "second-brain/1.0 (+kişisel okuyucu)"


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 - yalnız yapılandırmadaki adresler
        return r.read()


def load_config(path=None) -> dict:
    p = Path(path) if path else CONFIG
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(el, *names):
    for c in el:
        if _local(c.tag) in names:
            return c
    return None


def _text(el, *names) -> str:
    c = _child(el, *names)
    return (c.text or "").strip() if c is not None else ""


def _strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def _date(s: str) -> int | None:
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        return to_ms(dt, timezone.utc)
    except (TypeError, ValueError):
        return parse_iso(s)


def _link(el) -> str:
    for c in el:
        if _local(c.tag) == "link":
            if c.text and c.text.strip():
                return c.text.strip()
            if c.get("rel", "alternate") == "alternate" and c.get("href"):
                return c.get("href")
    return ""


def parse_feed(xml: bytes, feed: str, source: str = "rss", kind: str = "article") -> list[dict]:
    root = ET.fromstring(xml)
    entries = [e for e in root.iter() if _local(e.tag) in ("item", "entry")]
    rows = []
    for e in entries:
        link = _link(e)
        title = clean(_text(e, "title"))
        guid = _text(e, "guid", "id") or link or title
        body = clean(_strip_tags(_text(e, "encoded", "content", "summary", "description")))
        rows.append({"source": source, "id": sid(feed, guid), "date_ms": _date(_text(e, "pubDate", "published", "updated", "date")),
                     "kind": kind, "title": title, "url": link or None, "body": body, "meta": {"feed": feed}})
    return rows


def parse(path=None) -> list[dict]:
    rows = []
    for f in load_config(path).get("feeds") or []:
        url, name = (f, f) if isinstance(f, str) else (f.get("url"), f.get("name") or f.get("url"))
        if url:
            rows += parse_feed(_fetch(url), name)
    return rows


def run(path=None, con=None, dry_run: bool = False, **_) -> dict:
    if not load_config(path).get("feeds"):
        return {"kaynak": "rss", "okunan": 0, "yeni": 0, "not": "akış yok (config/rss.yaml)"}
    return ingest_items("rss", parse(path), con, dry_run)
