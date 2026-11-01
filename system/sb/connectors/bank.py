"""Banka ekstresi CSV → items (source=bank, kind=islem). Hesap/kart no ve IBAN hiçbir alanda saklanmaz."""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from pathlib import Path

from ._common import clean, ingest_items, sid, to_ms

DATE_H = ("işlem tarihi", "islem tarihi", "tarih", "date", "valör", "valor")
DESC_H = ("açıklama", "aciklama", "işlem açıklaması", "description", "işlem", "islem")
AMT_H = ("tutar", "amount", "işlem tutarı", "islem tutari")
DEBIT_H = ("borç", "borc", "debit", "çıkan", "cikan")
CREDIT_H = ("alacak", "credit", "giren")
_LONG = re.compile(r"(?<!\d)\d[\d ./-]{7,}\d(?!\d)")
_IBAN = re.compile(r"\bTR\s?\d{2}(?:\s?[0-9A-Z]{4}){4,6}(?:\s?[0-9A-Z]{1,4})?\b", re.I)


def read_rows(path) -> list[dict]:
    """CSV'yi (ayraç ; , veya sekme) sözlük listesi olarak oku; başlıklar küçük harf."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1254", errors="replace")
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    first = lines[0]
    delim = max(";,\t", key=first.count)
    return [{(k or "").strip().lower().replace("i̇", "i"): (v or "").strip() for k, v in r.items()}
            for r in csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delim)]


def pick(row: dict, names) -> str:
    for n in names:
        if row.get(n):
            return row[n]
    return ""


def num(s: str) -> float | None:
    """Türk (1.234,56) ve uluslararası (1,234.56) sayı biçimi; işaret ve para birimi simgesi atılır."""
    s = re.sub(r"[^\d,.\-+()]", "", s or "")
    neg = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.strip("-+()")
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        tail = s.rsplit(",", 1)[1]
        s = s.replace(",", ".") if s.count(",") == 1 and len(tail) != 3 else s.replace(",", "")
    elif "." in s:
        tail = s.rsplit(".", 1)[1]
        if s.count(".") > 1 or len(tail) == 3:
            s = s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def date_ms(s: str) -> int | None:
    s = s.strip()
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return to_ms(datetime.strptime(s, fmt))
        except ValueError:
            pass
    return None


def scrub(text: str) -> str:
    text = _IBAN.sub("[IBAN gizlendi]", text)
    text = _LONG.sub("[no gizlendi]", text)
    return clean(text)


def parse(path) -> list[dict]:
    rows, seen = [], {}
    for r in read_rows(path):
        ms = date_ms(pick(r, DATE_H))
        desc = scrub(pick(r, DESC_H))
        amt = num(pick(r, AMT_H))
        if amt is None:
            c, d = num(pick(r, CREDIT_H)), num(pick(r, DEBIT_H))
            amt = (c or 0) - abs(d or 0) if (c is not None or d is not None) else None
        if ms is None or amt is None:
            continue
        key = (ms, desc, amt)
        seen[key] = seen.get(key, 0) + 1
        rows.append({"source": "bank", "id": sid("islem", ms, desc, amt, seen[key]), "date_ms": ms, "kind": "islem",
                     "title": desc, "url": None, "body": f"{desc} {amt:.2f}", "meta": {"amount": amt}})
    return rows


def run(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("bank", parse(path), con, dry_run)
