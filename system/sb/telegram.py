"""Telegram botu: sabah özeti/uyarı gönder, bota yazılanları 00-Inbox'a çek.

Token ve sohbet kimliği keyring'de (`telegram-bot`, `telegram-chat`). Sadece kayıtlı sohbetten gelen mesajlar işlenir.
Yalnızca standart kütüphane (urllib); Telegram API'ye başka hiçbir veri gönderilmez.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import keyring

from .config import KEYRING_SERVICE, VAULT
from .redact import redact

API = "https://api.telegram.org/bot{token}/{method}"
LIMIT = 3800          # Telegram mesaj sınırı 4096
INBOX = VAULT / "00-Inbox"


def _token() -> str:
    t = keyring.get_password(KEYRING_SERVICE, "telegram-bot")
    if not t:
        raise SystemExit("Telegram token yok. Rehber: _system/docs/telegram-kurulum.md")
    return t


def call(method: str, params: dict | None = None, timeout: int = 30) -> dict:
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(API.format(token=_token(), method=method), data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.loads(r.read())
    if not out.get("ok"):
        raise RuntimeError(f"Telegram hatası: {out}")
    return out["result"]


def chat_id() -> str | None:
    return keyring.get_password(KEYRING_SERVICE, "telegram-chat")


def split(text: str, limit: int = LIMIT) -> list[str]:
    parts, cur = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:
            if cur:
                parts.append(cur); cur = ""
            parts.append(line[:limit]); line = line[limit:]
        if len(cur) + len(line) > limit:
            parts.append(cur); cur = ""
        cur += line
    if cur.strip():
        parts.append(cur)
    return parts or [""]


def send(text: str) -> int:
    """Kayıtlı sohbete gönderir (uzunsa bölünür). Gönderilen parça sayısını döndürür."""
    cid = chat_id()
    if not cid:
        raise SystemExit("Telegram sohbeti bağlı değil: sb telegram-setup")
    chunks = split(redact(text))
    for c in chunks:
        call("sendMessage", {"chat_id": cid, "text": c, "disable_web_page_preview": "true"})
    return len(chunks)


def setup() -> str:
    """Bota yazılan son mesajdan sohbet kimliğini bulur ve kaydeder."""
    updates = call("getUpdates", {"timeout": 0})
    msgs = [u["message"] for u in updates if u.get("message")]
    if not msgs:
        raise SystemExit("Bota henüz mesaj yazılmamış. Telegram'da botuna 'merhaba' yazıp tekrar çalıştır.")
    last = msgs[-1]
    cid = str(last["chat"]["id"])
    keyring.set_password(KEYRING_SERVICE, "telegram-chat", cid)
    name = last["chat"].get("first_name") or last["chat"].get("username") or cid
    call("sendMessage", {"chat_id": cid, "text": f"Second Brain bağlandı ✅ ({name}). Buraya yazdığın her şey kasada 00-Inbox'a düşer."})
    return name


def pull(con) -> int:
    """Bota yazılan yeni mesajları 00-Inbox/telegram-YYYY-MM-DD.md dosyalarına ekler. Eklenen mesaj sayısı."""
    from . import maildb
    cid = chat_id()
    if not cid:
        return 0
    offset = int(maildb.get_state(con, "telegram:offset") or 0)
    updates = call("getUpdates", {"offset": offset + 1 if offset else 0, "timeout": 0})
    added = 0
    for u in updates:
        offset = max(offset, u["update_id"])
        m = u.get("message")
        if not m or str(m["chat"]["id"]) != cid:      # başka sohbetten gelen yok sayılır
            continue
        text = m.get("text") or m.get("caption")
        if not text:
            kind = next((k for k in ("voice", "photo", "document", "video", "audio") if k in m), "ek")
            text = f"({kind} gönderildi; Telegram'da duruyor, kasaya alınmadı)"
        when = datetime.fromtimestamp(m["date"])
        path = INBOX / f"telegram-{when:%Y-%m-%d}.md"
        if not path.exists():
            path.write_text(
                f"---\ntype: gunluk\nstatus: acik\ntags: [telegram, inbox]\nsource: telegram\nsource_id: telegram:{when:%Y-%m-%d}\n"
                f"created: {when:%Y-%m-%d}\nupdated: {when:%Y-%m-%d}\ndue:\n---\n# Telegram notları {when:%Y-%m-%d}\n\n",
                encoding="utf-8", newline="\n")
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"- {when:%H:%M} {redact(text).strip()}\n")
        added += 1
    maildb.set_state(con, "telegram:offset", str(offset))
    con.commit()
    return added
