"""WhatsApp 'Sohbeti dışa aktar' (.txt ya da .zip) → messages (account=whatsapp)."""
from __future__ import annotations

import re
import zipfile
from datetime import datetime
from pathlib import Path

from ._common import clean, ingest_messages, sid, to_ms

ACCOUNT = "whatsapp"
_DT = r"(\d{1,2})[./](\d{1,2})[./](\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp]\.?[Mm]\.?)?"
_ANDROID = re.compile(rf"^{_DT}\s+[-–]\s+(.*)$")
_IOS = re.compile(rf"^\[{_DT}\]\s+(.*)$")
_SYSTEM = re.compile(r"uçtan uca şifreli|end-to-end encrypted|güvenlik kodu|security code", re.I)
_MEDIA = [
    re.compile(r"<(?:Medya dahil edilmedi|Media omitted)>", re.I),
    re.compile(r"<attached:\s*([^>]+)>", re.I),
    re.compile(r"^(\S.*?\.\w{2,5}) \((?:dosya ekli|file attached)\)", re.I),
    re.compile(r"\b(?:image|video|audio|sticker|GIF|document|görsel|video|ses|çıkartma) (?:omitted|dahil edilmedi)\b", re.I),
]
_NAME = [r"^WhatsApp Chat with (.+)$", r"^WhatsApp Chat - (.+)$", r"^WhatsApp Sohbeti - (.+)$",
         r"^WhatsApp ile (.+) sohbeti$", r"^(.+) ile WhatsApp Sohbeti$"]


def chat_name(stem: str) -> str:
    stem = re.sub(r"\s*\(\d+\)$", "", stem)
    for pat in _NAME:
        m = re.match(pat, stem, re.I)
        if m:
            return m.group(1).strip()
    return "WhatsApp" if stem == "_chat" else stem


def _read(path: Path) -> tuple[str, str]:
    """(metin, sohbet adı)"""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".txt")]
            if not names:
                raise ValueError("zip içinde .txt yok")
            names.sort(key=lambda n: (not n.endswith("_chat.txt"), n))
            member = Path(names[0]).stem
            name = chat_name(path.stem) if member == "_chat" else chat_name(member)
            return z.read(names[0]).decode("utf-8-sig", "replace"), name
    return path.read_text(encoding="utf-8-sig", errors="replace"), chat_name(path.stem)


def _order(entries) -> bool:
    """True: gün/ay/yıl, False: ay/gün/yıl."""
    if any(int(e[0]) > 12 for e in entries):
        return True
    if any(int(e[1]) > 12 for e in entries):
        return False
    if any(e[6] for e in entries) or any(e[9] == "/" for e in entries):
        return False
    return True


def _entries(text: str) -> list[list]:
    out: list[list] = []
    text = text.replace(" ", " ").replace(" ", " ")
    for line in text.splitlines():
        line = line.replace("‎", "").replace("‏", "").replace("﻿", "")
        m = _ANDROID.match(line) or _IOS.match(line)
        if m:
            sep = re.search(r"[./]", line).group()
            out.append([*m.groups()[:7], m.group(8), "", sep])
            # indeks: 0 a,1 b,2 yıl,3 sa,4 dk,5 sn,6 ap,7 rest,8 -, 9 ayraç
        elif out:
            out[-1][7] += "\n" + line
    return out


def parse(path, me: str | None = None) -> list[dict]:
    path = Path(path)
    text, thread = _read(path)
    entries = _entries(text)
    dmy = _order(entries)
    rows, seen = [], {}
    for e in entries:
        a, b = int(e[0]), int(e[1])
        day, month = (a, b) if dmy else (b, a)
        year = int(e[2]) + (2000 if int(e[2]) < 100 else 0)
        h, mi, s = int(e[3]), int(e[4]), int(e[5] or 0)
        ap = (e[6] or "").lower().replace(".", "")
        if ap == "pm" and h < 12:
            h += 12
        elif ap == "am" and h == 12:
            h = 0
        try:
            ms = to_ms(datetime(year, month, day, h, mi, s))
        except ValueError:
            continue
        rest = e[7].strip()
        if _SYSTEM.search(rest.split("\n", 1)[0]) or ": " not in rest.split("\n", 1)[0]:
            continue
        sender, body = rest.split(": ", 1)
        attachments = []
        for pat in _MEDIA:
            for m in pat.finditer(body):
                attachments.append((m.group(1) if m.groups() else m.group(0)).strip("<> "))
            body = pat.sub("", body)
        body = clean(body)
        if not body and not attachments:
            continue
        key = (ms, sender, body, tuple(attachments))
        seen[key] = seen.get(key, 0) + 1
        mine = bool(me) and sender.strip().lower() == me.strip().lower()
        rows.append({
            "account": ACCOUNT, "id": sid(thread, *key, seen[key]), "thread_id": thread, "date_ms": ms,
            "from_addr": "me" if mine else sender, "from_name": sender,
            "to_addrs": thread if mine else (me or ""), "subject": thread, "snippet": body[:200],
            "body": body, "labels": ["whatsapp"], "attachments": attachments,
        })
    return rows


def run(path, con, dry_run: bool = False, me: str | None = None, **_) -> dict:
    return ingest_messages("whatsapp", parse(path, me=me), con, dry_run)
