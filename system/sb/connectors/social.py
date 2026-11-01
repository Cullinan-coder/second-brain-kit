"""Instagram (bilgi indirme JSON) ve X/Twitter arşivi → mesajlar (Instagram DM) + gönderi items."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import PurePosixPath

from ._common import clean, ingest_items, ingest_messages, sid
from .notes import fix_utf8, iter_files, message_row, text_of

_INBOX = re.compile(r"messages/(?:inbox|e2ee_cutover|archived_threads)/[^/]+/message_\d+\.json$")
_POSTS = re.compile(r"(?:^|/)(?:posts|reels|stories)_?\d*\.json$")


def _json(txt):
    try:
        return json.loads(txt)
    except ValueError:
        return None


def parse_instagram(path, me: str | None = None) -> tuple[list[dict], list[dict]]:
    msgs, items = [], []
    for name, load, _ in iter_files(path):
        if not name.endswith(".json"):
            continue
        d = _json(text_of(load()))
        if _INBOX.search(name) and isinstance(d, dict):
            thread = fix_utf8(d.get("title")) or PurePosixPath(name).parent.name
            for m in d.get("messages") or []:
                sender = fix_utf8(m.get("sender_name")) or "?"
                body = fix_utf8(m.get("content") or "")
                atts = [PurePosixPath(x.get("uri", "")).name for k in ("photos", "videos", "audio_files") for x in m.get(k) or []]
                if not body.strip() and not atts:
                    continue
                mine = bool(me) and sender.strip().lower() == me.strip().lower()
                msgs.append(message_row("instagram", thread, m.get("timestamp_ms"), sender, mine, body, atts, labels=["instagram"]))
        elif _POSTS.search(name) and isinstance(d, list):
            for p in d:
                if not isinstance(p, dict):
                    continue
                media = p.get("media") or [{}]
                cap = fix_utf8(p.get("title") or (media[0] or {}).get("title") or "")
                ts = p.get("creation_timestamp") or (media[0] or {}).get("creation_timestamp")
                ms = int(ts) * 1000 if ts else None
                if not cap.strip():
                    continue
                items.append({"source": "instagram", "id": sid("ig", ms or "", cap), "date_ms": ms, "kind": "post",
                              "title": clean(cap)[:80], "url": None, "body": clean(cap), "meta": {"media": len(media)}})
    return msgs, items


def parse_x(path) -> list[dict]:
    items = []
    for name, load, _ in iter_files(path):
        if not re.search(r"(?:^|/)tweets?(?:-part\d+)?\.js$", name):
            continue
        txt = text_of(load()).strip()
        data = _json(txt[txt.index("["):]) if "[" in txt else None  # 'window.YTD.tweets.part0 =' atılır
        for t in data or []:
            t = t.get("tweet", t) if isinstance(t, dict) else {}
            body = t.get("full_text") or t.get("text") or ""
            if not body.strip():
                continue
            try:
                ms = int(datetime.strptime(t["created_at"], "%a %b %d %H:%M:%S %z %Y").timestamp() * 1000)
            except (KeyError, ValueError):
                ms = None
            tid = t.get("id_str") or t.get("id") or sid(ms, body)
            items.append({"source": "x", "id": str(tid), "date_ms": ms, "kind": "retweet" if body.startswith("RT @") else "tweet",
                          "title": clean(body)[:80], "url": None, "body": clean(body),
                          "meta": {"likes": t.get("favorite_count"), "retweets": t.get("retweet_count")}})
    return items


def run_instagram(path, con, dry_run: bool = False, me: str | None = None, **_) -> dict:
    msgs, items = parse_instagram(path, me=me)
    a = ingest_messages("instagram", msgs, con, dry_run)
    b = ingest_items("instagram", items, con, dry_run)
    return {**a, "okunan": a["okunan"] + b["okunan"], "yeni": a["yeni"] + b["yeni"], "mesaj": a["okunan"], "gönderi": b["okunan"],
            "ornek": (a["ornek"] + b["ornek"])[:3]}


def run_x(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("x", parse_x(path), con, dry_run)
