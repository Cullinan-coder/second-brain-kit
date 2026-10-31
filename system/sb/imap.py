"""Şirket mailleri (IMAP) → mail.db. SALT OKUNUR.

- Klasörler `EXAMINE` ile açılır (imaplib `select(readonly=True)`); sunucu bayrak değiştirmez.
- Gövde `BODY.PEEK[]` ile alınır; mail "okundu" olarak işaretlenmez.
- STORE/COPY/MOVE/EXPUNGE/APPEND hiçbir yerde çağrılmaz.
Şifre keyring'de: servis `second-brain`, anahtar `imap-<hesap>`.
"""
from __future__ import annotations

import email
import email.policy
import imaplib
import re
import sqlite3
from email.utils import getaddresses, parseaddr, parsedate_to_datetime

import keyring

from . import ics, maildb
from .categorize import categorize
from .config import KEYRING_SERVICE, accounts
from .gmail import MAX_BODY, _html_to_text

SKIP_FOLDERS = re.compile(r"^(trash|junk|spam|deleted|çöp|gereksiz|drafts|taslak)", re.I)
LIST_RE = re.compile(r'\((?P<flags>[^)]*)\) "(?P<sep>[^"]*)" (?P<name>.+)')
CHUNK = 50


PRESETS = {
    "outlook": {"host": "outlook.office365.com", "port": 993},
    "icloud": {"host": "imap.mail.me.com", "port": 993},
}
LOGIN_HINTS = {
    "outlook": ("Outlook/Microsoft 365 girişi reddedildi. Kişisel hesapta IMAP açık olmalı ve (2 adımlı doğrulama varsa) "
                "uygulama şifresi kullanılmalı. Kurumsal M365'te temel kimlik doğrulama (şifre ile IMAP) çoğunlukla kapalıdır; "
                "OAuth2 gerekir ve bu henüz desteklenmiyor."),
    "icloud": ("iCloud girişi reddedildi. iCloud normal Apple Kimliği şifresiyle çalışmaz; appleid.apple.com → "
               "Oturum Açma ve Güvenlik → Uygulamaya Özel Şifreler'den üretilen şifre gerekir (sb set-secret imap-<ad>)."),
}


def resolve(acc: dict) -> dict:
    """`preset: outlook|icloud` verilmişse host/port öntanımlarını doldurur (açık yazılan değer ön ayarı ezer)."""
    preset = acc.get("preset")
    if not preset:
        return acc
    if preset not in PRESETS:
        raise SystemExit(f"Bilinmeyen IMAP ön ayarı: {preset} (geçerli: {', '.join(PRESETS)})")
    return {**PRESETS[preset], **acc}


def _connect(alias: str) -> imaplib.IMAP4_SSL:
    acc = resolve(accounts()["imap"][alias])
    password = keyring.get_password(KEYRING_SERVICE, f"imap-{alias}")
    if not password:
        raise SystemExit(f"{alias} şifresi yok. Çalıştır: uv run python -m sb set-secret imap-{alias}")
    conn = imaplib.IMAP4_SSL(acc["host"], acc.get("port", 993))
    try:
        conn.login(acc["email"], password)
    except imaplib.IMAP4.error as e:
        hint = LOGIN_HINTS.get(acc.get("preset", ""), "")
        raise SystemExit(f"[{alias}] IMAP girişi başarısız: {e}. {hint}".strip())
    return conn


def _folders(conn: imaplib.IMAP4_SSL) -> list[tuple[str, bool]]:
    """(klasör adı, gönderilmiş mi) listesi; çöp/spam/taslak atlanır."""
    typ, data = conn.list()
    out = []
    for raw in data or []:
        m = LIST_RE.match(raw.decode("utf-8", "replace"))
        if not m or "\\Noselect" in m["flags"]:
            continue
        name = m["name"].strip().strip('"')
        leaf = name.split(m["sep"])[-1] if m["sep"] else name
        if "\\Trash" in m["flags"] or "\\Junk" in m["flags"] or "\\Drafts" in m["flags"] or SKIP_FOLDERS.match(leaf):
            continue
        sent = "\\Sent" in m["flags"] or bool(re.match(r"^(sent|gönderilmiş|giden)", leaf, re.I))
        out.append((name, sent))
    return out


def _text(msg: email.message.EmailMessage) -> tuple[str, list[str]]:
    plain, htmls, files, cals = [], [], [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        fn = part.get_filename()
        if (fn or "").lower().endswith(".ics") or part.get_content_type() == "text/calendar":
            cals.append(ics.summarize((part.get_payload(decode=True) or b"").decode("utf-8", "replace")))
        if fn:
            files.append(fn)
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        try:
            content = part.get_content()
        except (LookupError, UnicodeDecodeError):
            content = (part.get_payload(decode=True) or b"").decode("utf-8", "replace")
        (plain if ctype == "text/plain" else htmls).append(content)
    body = "\n".join(p for p in plain if p.strip()) or _html_to_text("\n".join(htmls))
    body = "\n\n".join([c for c in cals if c] + [body])
    return body[:MAX_BODY], files


def parse_message(raw: bytes, alias: str, folder: str, uidvalidity: str, uid: str, sent: bool) -> dict:
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    from_name, from_addr = parseaddr(str(msg.get("From", "")))
    try:
        date_ms = int(parsedate_to_datetime(str(msg.get("Date"))).timestamp() * 1000)
    except (TypeError, ValueError, IndexError):
        date_ms = 0
    refs = str(msg.get("References", "")).split()
    msgid = str(msg.get("Message-ID", "")).strip()
    body, files = _text(msg)
    out = {
        "account": alias,
        "id": f"{folder}/{uidvalidity}/{uid}",
        "thread_id": refs[0] if refs else (str(msg.get("In-Reply-To", "")).strip() or msgid or f"{folder}/{uid}"),
        "date_ms": date_ms,
        "from_addr": from_addr.lower(),
        "from_name": from_name,
        "to_addrs": ", ".join(a for _, a in getaddresses([str(msg.get("To", ""))]) if a),
        "cc_addrs": ", ".join(a for _, a in getaddresses([str(msg.get("Cc", ""))]) if a),
        "subject": str(msg.get("Subject", "")),
        "snippet": re.sub(r"\s+", " ", body[:200]).strip(),
        "body": body,
        "labels": [folder] + (["SENT"] if sent else []),
        "attachments": files,
    }
    out["category"] = categorize(out)
    out["category_src"] = "rule"
    return out


def fetch(alias: str, con: sqlite3.Connection, limit: int | None = None, log=print) -> int:
    conn = _connect(alias)
    total = 0
    try:
        for folder, sent in _folders(conn):
            typ, _ = conn.select(f'"{folder}"', readonly=True)  # EXAMINE
            if typ != "OK":
                log(f"[{alias}] {folder}: açılamadı, atlandı")
                continue
            uidvalidity = (conn.response("UIDVALIDITY")[1] or [b"0"])[0].decode()
            key = f"imap:{alias}:{folder}:{uidvalidity}:last_uid"
            last = int(maildb.get_state(con, key) or 0)
            typ, data = conn.uid("search", None, f"UID {last + 1}:*")
            uids = [u for u in (data[0] or b"").split() if int(u) > last]
            if limit:
                uids = uids[: max(0, limit - total)]
            log(f"[{alias}] {folder}: {len(uids)} yeni")
            for i in range(0, len(uids), CHUNK):
                chunk = uids[i:i + CHUNK]
                typ, data = conn.uid("fetch", b",".join(chunk), "(UID BODY.PEEK[])")
                for item in data:
                    if not isinstance(item, tuple):
                        continue
                    m = re.search(rb"UID (\d+)", item[0])
                    if not m:
                        continue
                    maildb.insert(con, parse_message(item[1], alias, folder, uidvalidity, m.group(1).decode(), sent))
                    total += 1
                maildb.set_state(con, key, chunk[-1].decode())
                con.commit()
            if limit and total >= limit:
                break
    finally:
        try:
            conn.logout()
        except imaplib.IMAP4.error:
            pass
    log(f"[{alias}] bitti: {total} yeni mesaj")
    return total
