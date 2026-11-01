"""Discord veri paketi (klasör ya da zip: messages/c<id>/messages.json|csv + channel.json) → messages (account=discord)."""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import PurePosixPath

from ._common import ingest_messages, parse_iso
from .notes import iter_files, message_row, text_of

ACCOUNT = "discord"


def _rows(name: str, raw: bytes) -> list[dict]:
    if name.endswith(".json"):
        try:
            d = json.loads(text_of(raw))
        except ValueError:
            return []
        return d if isinstance(d, list) else []
    return list(csv.DictReader(io.StringIO(text_of(raw))))


def parse(path) -> list[dict]:
    files = {n: load for n, load, _ in iter_files(path)}
    out = []
    for name, load in files.items():
        p = PurePosixPath(name)
        if p.name not in ("messages.json", "messages.csv"):
            continue
        thread = p.parent.name
        ch = str(p.parent / "channel.json")
        if ch in files:
            try:
                c = json.loads(text_of(files[ch]()))
                thread = c.get("name") or ("DM " + ", ".join(c["recipients"]) if c.get("recipients") else thread)
            except ValueError:
                pass
        if re.fullmatch(r"c\d+", thread):
            thread = "kanal-" + thread[1:]
        for r in _rows(p.name, load()):
            body = r.get("Contents") or ""
            atts = [a for a in re.split(r"\s+", r.get("Attachments") or "") if a]
            if not body.strip() and not atts:
                continue
            out.append(message_row(ACCOUNT, thread, parse_iso(r.get("Timestamp") or ""), "me", True, body, atts,
                                   key=str(r.get("ID", "")), labels=["discord"]))
    return out


def run(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_messages("discord", parse(path), con, dry_run)
