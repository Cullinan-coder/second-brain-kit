"""Slack çalışma alanı dışa aktarımı (klasör/zip: kanal klasörleri/YYYY-AA-GG.json, users.json) → messages (account=slack)."""
from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

from ._common import ingest_messages
from .notes import iter_files, message_row, text_of

ACCOUNT = "slack"
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")


def _load(files, name, default):
    try:
        return json.loads(text_of(files[name]()))
    except (KeyError, ValueError):
        return default


def parse(path, me: str | None = None) -> list[dict]:
    files = {n: load for n, load, _ in iter_files(path)}
    users = {u.get("id"): u.get("real_name") or u.get("name") or u.get("id") for u in _load(files, "users.json", [])
             if isinstance(u, dict)}
    out = []
    for name in files:
        p = PurePosixPath(name)
        if not _DAY.match(p.name) or len(p.parts) < 2:
            continue
        thread = p.parts[-2]
        for m in _load(files, name, []):
            if not isinstance(m, dict) or m.get("type", "message") != "message" or m.get("subtype") in ("channel_join", "channel_leave"):
                continue
            text = re.sub(r"<@(\w+)>", lambda x: "@" + str(users.get(x.group(1), x.group(1))), m.get("text") or "")
            text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"\2 (\1)", text)
            atts = [f.get("name") or f.get("title") or "" for f in m.get("files") or [] if isinstance(f, dict)]
            if not text.strip() and not atts:
                continue
            sender = users.get(m.get("user")) or m.get("user_name") or (m.get("user_profile") or {}).get("real_name") or m.get("user") or "bot"
            try:
                ms = int(float(m.get("ts")) * 1000)
            except (TypeError, ValueError):
                ms = None
            mine = bool(me) and sender.strip().lower() == me.strip().lower()
            out.append(message_row(ACCOUNT, thread, ms, sender, mine, text, atts, key=str(m.get("ts", "")), labels=["slack"]))
    return out


def run(path, con, dry_run: bool = False, me: str | None = None, **_) -> dict:
    return ingest_messages("slack", parse(path, me=me), con, dry_run)
