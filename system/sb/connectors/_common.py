"""Bağlayıcıların ortak yardımcıları: tekil kimlik, tarih ayrıştırma, güvenli yazma, özet."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

from .. import maildb
from ..redact import redact

MONTHS = {m: i + 1 for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split())}
MONTHS.update({m: i + 1 for i, m in enumerate(
    "oca şub mar nis may haz tem ağu eyl eki kas ara".split())})


def sid(*parts) -> str:
    return hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]


def to_ms(dt: datetime, default_tz=None) -> int:
    """Saat dilimsiz zaman default_tz'de (None ise yerel saat) yorumlanır."""
    if dt.tzinfo is None and default_tz is not None:
        dt = dt.replace(tzinfo=default_tz)
    try:
        return int(dt.timestamp() * 1000)
    except (OSError, OverflowError):  # Windows 1970 öncesi yerel saati desteklemez
        aware = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        return int((aware - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds() * 1000)


def parse_iso(s: str, default_tz=timezone.utc) -> int | None:
    try:
        return to_ms(datetime.fromisoformat(str(s).strip().replace("Z", "+00:00")), default_tz)
    except ValueError:
        return None


_TIME = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp]\.?[Mm]\.?)?")
_TZ = re.compile(r"(?:GMT|UTC)\s*([+-])(\d{2}):?(\d{2})")


def text_date(s: str) -> int | None:
    """'October 31, 2026 2:05:00 PM', '31 Ekim 2026 Cuma 14:05:00', 'Oct 31, 2026, 2:05 PM GMT+03:00' gibi metin tarihleri."""
    tz = None
    m = _TZ.search(s)
    if m:
        off = timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))
        tz = timezone(off if m.group(1) == "+" else -off)
        s = s[:m.start()] + s[m.end():]
    t = _TIME.search(s)
    h = mi = sec = 0
    if t:
        h, mi, sec = int(t.group(1)), int(t.group(2)), int(t.group(3) or 0)
        ap = (t.group(4) or "").lower().replace(".", "")
        if ap == "pm" and h < 12:
            h += 12
        elif ap == "am" and h == 12:
            h = 0
        s = s[:t.start()] + " " + s[t.end():]
    y = re.search(r"\b(19|20)\d{2}\b", s)
    if not y:
        return None
    year = int(y.group())
    s = s[:y.start()] + " " + s[y.end():]
    month = next((MONTHS[w.lower()[:3]] for w in re.findall(r"[^\W\d_]+", s)
                  if len(w) >= 3 and w.lower()[:3] in MONTHS), None)
    d = re.search(r"\b(\d{1,2})\b", s)
    if not month or not d:
        return None
    try:
        return to_ms(datetime(year, month, int(d.group(1)), h, mi, sec), tz)
    except ValueError:
        return None


def day(ms: int | None) -> str | None:
    if not ms:
        return None
    return (datetime(1970, 1, 1) + timedelta(milliseconds=ms)).strftime("%Y-%m-%d")


def _summary(kaynak, rows, titles, new) -> dict:
    ds = [r["date_ms"] for r in rows if r.get("date_ms")]
    uniq = list(dict.fromkeys(t for t in titles if t))
    return {"kaynak": kaynak, "okunan": len(rows), "yeni": new,
            "tarih_min": day(min(ds)) if ds else None, "tarih_max": day(max(ds)) if ds else None,
            "ornek": uniq[:3]}


def ingest_messages(kaynak: str, rows: list[dict], con, dry_run: bool = False) -> dict:
    new = 0
    for r in rows:
        if con.execute("SELECT 1 FROM messages WHERE account = ? AND id = ?", (r["account"], r["id"])).fetchone():
            continue
        new += 1
        if not dry_run:
            maildb.insert(con, r)
    if not dry_run:
        con.commit()
    return _summary(kaynak, rows, [r.get("subject") for r in rows], new)


def ingest_items(kaynak: str, rows: list[dict], con, dry_run: bool = False, refresh: bool = False) -> dict:
    """refresh=True: var olan kaydın tarih/başlık/meta alanını günceller (yeni sayılmaz)."""
    new = 0
    for r in rows:
        exists = con.execute("SELECT 1 FROM items WHERE source = ? AND id = ?", (r["source"], r["id"])).fetchone()
        if exists:
            if refresh and not dry_run:
                meta = r.get("meta")
                con.execute("UPDATE items SET date_ms = ?, title = ?, meta = ? WHERE source = ? AND id = ?",
                            (r.get("date_ms"), r.get("title"),
                             json.dumps(meta, ensure_ascii=False) if meta is not None else None,
                             r["source"], r["id"]))
            continue
        new += 1
        if not dry_run:
            maildb.insert_item(con, r)
    if not dry_run:
        con.commit()
    return _summary(kaynak, rows, [r.get("title") for r in rows], new)


def clean(text: str | None) -> str:
    return redact(text or "").strip()
