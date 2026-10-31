"""SMS ve arama kaydı: SMS Backup & Restore'un Drive'a yüklediği XML yedekleri → mail.db.

- SMS'ler `messages` tablosuna `account='sms'` olarak girer; böylece kategorileme, mail indeksi
  ve tarih çıkarma aynı yoldan çalışır. `thread_id` = numaranın son 10 hanesi.
- Aramalar `calls` tablosuna girer.
- Drive sadece okunur (drive.readonly); telefondaki uygulamaya ya da Drive'a hiçbir şey yazılmaz.
"""
from __future__ import annotations

import hashlib
import io
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

from googleapiclient.http import MediaIoBaseDownload

from . import maildb
from .categorize import categorize
from .config import DATA
from .contacts import normalize_phone
from .google_auth import service

FOLDER = "SMSBackupRestore"
RAW = DATA / "raw" / "sms"
SENT_TYPES = {"2", "4", "5", "6"}     # gönderilen, giden kutusu, başarısız, sırada
MMS_SENT_BOX = {"2", "4"}


def _sid(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:20]


def sync_from_drive(con: sqlite3.Connection, alias: str = "main", log=print) -> tuple[int, int]:
    """Klasör(ler)deki henüz işlenmemiş her sms-*.xml / calls-*.xml yedeğini indirip içe aktarır.

    Birden fazla telefon aynı klasöre yedek atabilir; her dosya Drive kimliğiyle bir kez işlenir,
    kayıtlar zaten tekrarsız eklendiği için telefonlar arasında ortak mesajlar çoğalmaz.
    """
    drive = service(alias, "drive", "v3").files()
    # Uygulama klasöre bazen sonda boşlukla ad veriyor ("SMSBackupRestore "), bu yüzden "contains".
    folders = drive.list(q=f"name contains '{FOLDER}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                         fields="files(id)").execute().get("files", [])
    if not folders:
        raise SystemExit(f"Drive'da '{FOLDER}' klasörü yok. Telefon kurulumu: _system/docs/telefon-sms-kurulum.md")
    files = []
    for folder in folders:
        files += drive.list(q=f"'{folder['id']}' in parents and trashed = false", orderBy="modifiedTime",
                            fields="files(id,name,size,modifiedTime)", pageSize=1000).execute().get("files", [])
    RAW.mkdir(parents=True, exist_ok=True)
    totals = {"sms": 0, "calls": 0}
    for f in files:
        name = f["name"].lower()
        kind = next((k for k in totals if name.startswith(k + "-") and name.endswith(".xml")), None)
        if not kind or maildb.get_state(con, f"sms-file:{f['id']}"):
            continue
        path = RAW / f"{f['id']}-{f['name']}"
        buf = io.FileIO(path, "wb")
        dl = MediaIoBaseDownload(buf, drive.get_media(fileId=f["id"]), chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk()
        buf.close()
        added = import_sms(path, con) if kind == "sms" else import_calls(path, con)
        totals[kind] += added
        maildb.set_state(con, f"sms-file:{f['id']}", f["modifiedTime"])
        con.commit()
        log(f"{f['name']}: {added} yeni {'SMS' if kind == 'sms' else 'arama'}")
    return totals["sms"], totals["calls"]


def _sms_row(number: str, date_ms: int, sent: bool, body: str, name: str | None, mid: str) -> dict:
    key = normalize_phone(number)
    known = bool(name) and name not in ("(Unknown)", "null")
    msg = {
        "account": "sms", "id": mid, "thread_id": key or number, "date_ms": date_ms,
        "from_addr": "me" if sent else number, "from_name": "" if sent else (name if known else ""),
        "to_addrs": number if sent else "", "cc_addrs": "",
        "subject": " ".join(body.split())[:80], "snippet": body[:200], "body": body,
        "labels": ["SMS"] + (["SENT"] if sent else []), "attachments": [],
    }
    msg["category"], msg["category_src"] = categorize(msg), "rule"
    return msg


def _count(con: sqlite3.Connection, sql: str) -> int:
    return con.execute(sql).fetchone()[0]


def import_sms(path: Path, con: sqlite3.Connection) -> int:
    before = _count(con, "SELECT COUNT(*) FROM messages WHERE account = 'sms'")
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag == "sms":
            a = el.attrib
            body = a.get("body") or ""
            mid = _sid(a.get("address", ""), a.get("date", ""), a.get("type", ""), body)
            maildb.insert(con, _sms_row(a.get("address", ""), int(a.get("date") or 0), a.get("type") in SENT_TYPES,
                                        body, a.get("contact_name"), mid))
            el.clear()
        elif el.tag == "mms":
            a = el.attrib
            texts = [p.get("text", "") for p in el.iter("part") if p.get("ct") == "text/plain" and p.get("text")]
            if texts:
                body = "\n".join(texts)
                date = a.get("date", "0")
                date_ms = int(date) * (1000 if len(date) <= 10 else 1)
                mid = _sid(a.get("address", ""), date, a.get("msg_box", ""), body)
                maildb.insert(con, _sms_row(a.get("address", ""), date_ms, a.get("msg_box") in MMS_SENT_BOX,
                                            body, a.get("contact_name"), mid))
            el.clear()
    con.commit()
    return _count(con, "SELECT COUNT(*) FROM messages WHERE account = 'sms'") - before


def import_calls(path: Path, con: sqlite3.Connection) -> int:
    before = _count(con, "SELECT COUNT(*) FROM calls")
    for _, el in ET.iterparse(path, events=("end",)):
        if el.tag != "call":
            continue
        a = el.attrib
        number = a.get("number", "")
        con.execute(
            "INSERT OR IGNORE INTO calls(id, number, phone_key, date_ms, type, duration, contact_name) VALUES (?,?,?,?,?,?,?)",
            (_sid(number, a.get("date", ""), a.get("type", "")), number, normalize_phone(number), int(a.get("date") or 0),
             int(a.get("type") or 0), int(a.get("duration") or 0), a.get("contact_name")),
        )
        el.clear()
    con.commit()
    return _count(con, "SELECT COUNT(*) FROM calls") - before


def freshness(con: sqlite3.Connection, now_ms: int | None = None) -> dict:
    """SMS yedeğinin tazeliği: {"last_ms", "last", "days_ago", "count"}. Hiç SMS yoksa last_ms=None.

    `sb doctor` bunu kullanabilir (telefondaki zamanlanmış yedek durmuş mu?).
    """
    import time
    from datetime import datetime
    row = con.execute("SELECT MAX(date_ms), COUNT(*) FROM messages WHERE account = 'sms'").fetchone()
    last, count = row[0], row[1]
    if not last:
        return {"last_ms": None, "last": None, "days_ago": None, "count": 0}
    now = now_ms if now_ms is not None else int(time.time() * 1000)
    return {"last_ms": last, "last": datetime.fromtimestamp(last / 1000).strftime("%Y-%m-%d %H:%M"),
            "days_ago": max(0, (now - last) // 86_400_000), "count": count}
