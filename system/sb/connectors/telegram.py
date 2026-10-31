"""Telegram Desktop dışa aktarımı (result.json; tek sohbet ya da tüm sohbetler) → messages (account=telegram)."""
from __future__ import annotations

import json
from pathlib import Path

from ._common import clean, ingest_messages, parse_iso, sid

ACCOUNT = "telegram"


def flatten(text) -> str:
    if isinstance(text, str):
        return text
    if isinstance(text, list):
        return "".join(p if isinstance(p, str) else str(p.get("text", "")) for p in text)
    return ""


def _chats(data: dict) -> list[dict]:
    if isinstance(data.get("chats"), dict):
        return data["chats"].get("list") or []
    if "messages" in data:
        return [data]
    return []


def _ms(m: dict) -> int | None:
    if m.get("date_unixtime"):
        try:
            return int(m["date_unixtime"]) * 1000
        except ValueError:
            pass
    return parse_iso(m.get("date", ""), None)


def parse(path, me: str | None = None) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    me_id = str((data.get("personal_information") or {}).get("user_id") or "")
    rows = []
    for chat in _chats(data):
        cid = str(chat.get("id", ""))
        thread = chat.get("name") or f"sohbet-{cid}"
        for m in chat.get("messages", []):
            if m.get("type") != "message":
                continue
            ms = _ms(m)
            if ms is None:
                continue
            body = clean(flatten(m.get("text")))
            att = [str(m[k]) for k in ("photo", "file") if m.get(k)]
            if m.get("media_type") and not m.get("file"):
                att.append(str(m["media_type"]))
            if not body and not att:
                continue
            sender = m.get("from") or m.get("actor") or ""
            from_id = str(m.get("from_id", ""))
            mine = (bool(me) and sender.strip().lower() == me.strip().lower()) or \
                   (bool(me_id) and from_id.endswith(me_id))
            rows.append({
                "account": ACCOUNT, "id": f"tg-{cid}-{m['id']}" if "id" in m else sid(thread, ms, sender, body),
                "thread_id": thread, "date_ms": ms,
                "from_addr": "me" if mine else (from_id or sender), "from_name": sender,
                "to_addrs": thread if mine else "", "subject": thread, "snippet": body[:200],
                "body": body, "labels": ["telegram", chat.get("type", "")], "attachments": att,
            })
    return rows


def run(path, con, dry_run: bool = False, me: str | None = None, **_) -> dict:
    return ingest_messages("telegram", parse(path, me=me), con, dry_run)
