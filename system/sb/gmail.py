"""Gmail → mail.db. SALT OKUNUR: sadece users.messages.list/get ve getProfile çağrılır."""
from __future__ import annotations

import base64
import html
import re
import sqlite3
import time
from email.utils import getaddresses, parseaddr

from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest

from . import ics, maildb
from .categorize import categorize
from .google_auth import service

BATCH = 25           # messages.get = 5 kota birimi; kullanıcı başına ~250 birim/sn sınırının altında kal
MAX_BODY = 20000
TAG_RE = re.compile(r"<[^>]+>")
STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def _decode(data: str | None) -> str:
    if not data:
        return ""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def _html_to_text(s: str) -> str:
    s = STYLE_RE.sub(" ", s)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", s, flags=re.I)
    s = html.unescape(TAG_RE.sub(" ", s))
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n\s*\n+", "\n\n", s)).strip()


def _walk(part: dict, plain: list[str], htmls: list[str], files: list[str]) -> None:
    mime = part.get("mimeType", "")
    if part.get("filename"):
        files.append(part["filename"])
    elif mime == "text/plain":
        plain.append(_decode(part.get("body", {}).get("data")))
    elif mime == "text/html":
        htmls.append(_decode(part.get("body", {}).get("data")))
    for p in part.get("parts", []) or []:
        _walk(p, plain, htmls, files)


def _ics_parts(part: dict) -> list[dict]:
    out = []
    if part.get("filename", "").lower().endswith(".ics") or part.get("mimeType") == "text/calendar":
        out.append(part.get("body", {}))
    for p in part.get("parts", []) or []:
        out += _ics_parts(p)
    return out


def attach_ics(gm, raw: dict, msg: dict) -> bool:
    """Ekteki .ics dosyalarını okuyup gövdeye özet olarak ekler (salt okunur attachments.get)."""
    texts = []
    for body in _ics_parts(raw.get("payload", {})):
        data = body.get("data")
        if not data and body.get("attachmentId"):
            data = _retry(gm.users().messages().attachments().get(
                userId="me", messageId=raw["id"], id=body["attachmentId"]).execute).get("data")
        summary = ics.summarize(_decode(data))
        if summary:
            texts.append(summary)
    if texts:
        msg["body"] = ("\n\n".join(texts) + "\n\n" + (msg.get("body") or ""))[:MAX_BODY]
    return bool(texts)


def parse_message(raw: dict, account: str) -> dict:
    payload = raw.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    plain, htmls, files = [], [], []
    _walk(payload, plain, htmls, files)
    body = "\n".join(p for p in plain if p.strip()) or _html_to_text("\n".join(htmls))
    from_name, from_addr = parseaddr(headers.get("from", ""))
    msg = {
        "account": account,
        "id": raw["id"],
        "thread_id": raw.get("threadId"),
        "date_ms": int(raw.get("internalDate", 0)),
        "from_addr": from_addr.lower(),
        "from_name": from_name,
        "to_addrs": ", ".join(a for _, a in getaddresses([headers.get("to", "")]) if a),
        "cc_addrs": ", ".join(a for _, a in getaddresses([headers.get("cc", "")]) if a),
        "subject": headers.get("subject", ""),
        "snippet": html.unescape(raw.get("snippet", "")),
        "body": body[:MAX_BODY],
        "labels": raw.get("labelIds", []),
        "attachments": files,
    }
    msg["category"] = categorize(msg)
    msg["category_src"] = "rule"
    return msg


def _list_ids(gm, query: str | None):
    req = gm.users().messages().list(userId="me", q=query, maxResults=500, includeSpamTrash=False)
    while req is not None:
        resp = _retry(req.execute)
        for m in resp.get("messages", []):
            yield m["id"]
        req = gm.users().messages().list_next(req, resp)


def _rate_limited(e: HttpError) -> bool:
    return e.resp.status == 429 or (e.resp.status == 403 and b"ateLimitExceeded" in (e.content or b""))


def _retry(fn, tries: int = 7):
    for i in range(tries):
        try:
            return fn()
        except HttpError as e:
            if (_rate_limited(e) or e.resp.status in (500, 503)) and i < tries - 1:
                time.sleep(min(2 ** (i + 1), 64))
                continue
            raise


def fetch(alias: str, con: sqlite3.Connection, full: bool = False, limit: int | None = None, log=print) -> int:
    """Yeni mesajları indirir. Tam tarama bir kez sınırsız bitene kadar (veya full=True)
    tüm kutu listelenir; sonra son görülen tarihten 2 gün öncesinden itibaren bakılır."""
    gm = service(alias, "gmail", "v1")
    profile = gm.users().getProfile(userId="me").execute()
    since = maildb.get_state(con, f"gmail:{alias}:max_date_ms")
    full_done = maildb.get_state(con, f"gmail:{alias}:full_done") == "1"
    query = None if full or not full_done or not since else f"after:{int(since) // 1000 - 2 * 86400}"
    known = maildb.known_ids(con, alias)
    log(f"[{alias}] {profile['emailAddress']}: kutuda ~{profile.get('messagesTotal')} mesaj, arşivde {len(known)}; sorgu: {query or 'tümü'}")
    todo = [i for i in _list_ids(gm, query) if i not in known]
    if limit:
        todo = todo[:limit]
    log(f"[{alias}] indirilecek: {len(todo)}")

    done = 0
    max_ms = int(since or 0)
    for start in range(0, len(todo), BATCH):
        chunk = todo[start:start + BATCH]
        results: dict[str, dict] = {}
        failed: list[str] = []

        def cb(req_id, resp, exc):
            if exc is not None:
                failed.append(req_id)
            else:
                results[req_id] = resp

        batch = BatchHttpRequest(callback=cb, batch_uri="https://www.googleapis.com/batch/gmail/v1")
        for mid in chunk:
            batch.add(gm.users().messages().get(userId="me", id=mid, format="full"), request_id=mid)
        _retry(batch.execute)
        if failed:  # kota aşımı: dakikalık pencere dolsun, sonra tek tek tekrar dene
            time.sleep(20)
        for mid in failed:
            time.sleep(0.3)
            results[mid] = _retry(gm.users().messages().get(userId="me", id=mid, format="full").execute)
        for raw in results.values():
            msg = parse_message(raw, alias)
            attach_ics(gm, raw, msg)
            maildb.insert(con, msg)
            max_ms = max(max_ms, msg["date_ms"])
        maildb.set_state(con, f"gmail:{alias}:max_date_ms", str(max_ms))
        con.commit()
        done += len(results)
        if done % 1000 < BATCH:
            log(f"[{alias}] {done}/{len(todo)}")
        time.sleep(1.0)
    if not limit:  # sınırlı deneme taramasından sonra artımlı moda geçme
        maildb.set_state(con, f"gmail:{alias}:full_done", "1")
        con.commit()
    log(f"[{alias}] bitti: {done} yeni mesaj")
    return done


def backfill_ics(alias: str, con: sqlite3.Connection, log=print) -> int:
    """Eskiden indirilmiş, .ics eki olan mesajlara takvim eki özetini ekler ve tarih çıkarmaya yeniden açar."""
    gm = service(alias, "gmail", "v1")
    rows = con.execute(
        "SELECT id, body FROM messages WHERE account = ? AND lower(attachments) LIKE '%.ics%' AND body NOT LIKE ?",
        (alias, f"%{ics.MARK}%"),
    ).fetchall()
    done = 0
    for r in rows:
        raw = _retry(gm.users().messages().get(userId="me", id=r["id"], format="full").execute)
        msg = {"body": r["body"]}
        if attach_ics(gm, raw, msg):
            con.execute("UPDATE messages SET body = ? WHERE account = ? AND id = ?", (msg["body"], alias, r["id"]))
            con.execute("DELETE FROM extractions WHERE account = ? AND id = ?", (alias, r["id"]))
            done += 1
    con.commit()
    log(f"[{alias}] {len(rows)} .ics ekli mesaj, {done} tanesine takvim özeti eklendi")
    return done
