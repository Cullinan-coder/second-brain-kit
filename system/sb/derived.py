"""Mail/SMS arşivinden türetilen kaynaklar (kural tabanlı, model YOK): fatura (116) ve kargo (117) → `items`.

- Fatura: source `invoice`, kind `invoice`, meta {vendor, amount, currency, mail_id, account}.
- Kargo: source `cargo`, kind `shipment`, aynı takip numarası için TEK kayıt (en son durum); meta {carrier, tracking, status, mail_ids}.
- Kart/IBAN/TCKN meta'ya yazılmaz; gövde metni `redact`'tan geçer; takip numarası olarak maskelenecek bir değer kabul edilmez.
"""
from __future__ import annotations

import re
import sqlite3
import time

from . import maildb
from .redact import redact

# ------------------------------------------------------------------ tutar
INVOICE_RE = re.compile(r"fatura|e-?ar[şs]iv|invoice|receipt|[öo]deme\s+al[ıi]nd[ıi]|payment\s+received", re.I)
_NUM = r"\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?"
_CUR = r"TL|TRY|₺|\$|USD|€|EUR|£|GBP"
AMOUNT_RE = re.compile(rf"(?<![\w.,])(?:(?P<pc>{_CUR})\s?(?P<pn>{_NUM})|(?P<sn>{_NUM})\s?(?P<sc>{_CUR}))(?![\w])", re.I)
TOTAL_HINT_RE = re.compile(r"toplam|tutar|total|amount|[öo]denen|paid|[öo]deme", re.I)
CUR_NAMES = {"TL": "TRY", "TRY": "TRY", "₺": "TRY", "$": "USD", "USD": "USD", "€": "EUR", "EUR": "EUR", "£": "GBP", "GBP": "GBP"}


def parse_amount(s: str) -> float | None:
    """'1.234,56' (TR) ve '1,234.56' (EN) biçimlerini sayıya çevirir."""
    s = s.strip()
    if not re.fullmatch(_NUM, s):
        return None
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        thou = "." if dec == "," else ","
        return float(s.replace(thou, "").replace(dec, "."))
    for sep in (",", "."):
        if sep in s:
            parts = s.split(sep)
            if len(parts) > 2 or len(parts[-1]) == 3:      # binlik ayracı
                return float("".join(parts))
            return float(f"{parts[0]}.{parts[1]}")
    return float(s)


def find_amount(text: str) -> tuple[float, str] | None:
    """Metindeki tutarı bulur; 'toplam/tutar/total' ipucuna yakın olan önceliklidir."""
    found = []
    for m in AMOUNT_RE.finditer(text):
        num = parse_amount(m["pn"] or m["sn"])
        cur = CUR_NAMES.get((m["pc"] or m["sc"]).upper() if (m["pc"] or m["sc"]).isalpha() else (m["pc"] or m["sc"]))
        if num is None or cur is None or not (0 < num < 10_000_000):
            continue
        hinted = bool(TOTAL_HINT_RE.search(text[max(0, m.start() - 40):m.start()]))
        found.append((hinted, m.start(), num, cur))
    if not found:
        return None
    hinted = [f for f in found if f[0]]
    pick = (hinted or found)[0]
    return pick[2], pick[3]


def vendor_of(from_name: str, from_addr: str) -> str:
    name = re.sub(r"\s+", " ", (from_name or "")).strip(" \"'")
    if name and not re.fullmatch(r"(no-?reply|noreply|info|destek|support)", name, re.I) and "@" not in name:
        return name[:80]
    dom = (from_addr or "").split("@")[-1].lower()
    parts = [p for p in dom.split(".") if p]
    if len(parts) >= 3 and parts[-2] in ("com", "co", "org", "net", "gov", "edu"):
        return parts[-3]
    return parts[-2] if len(parts) >= 2 else dom


# ------------------------------------------------------------------ kargo
CARRIERS = [
    ("Yurtiçi Kargo", re.compile(r"yurti[çc]i", re.I)),
    ("Aras Kargo", re.compile(r"\baras\b", re.I)),
    ("MNG Kargo", re.compile(r"\bmng\b", re.I)),
    ("PTT Kargo", re.compile(r"\bptt\b", re.I)),
    ("Sürat Kargo", re.compile(r"s[üu]rat\s*kargo", re.I)),
    ("HepsiJet", re.compile(r"hepsi\s?jet", re.I)),
    ("Trendyol Express", re.compile(r"trendyol\s*express", re.I)),
    ("UPS", re.compile(r"\bUPS\b")),
    ("DHL", re.compile(r"\bDHL\b", re.I)),
    ("FedEx", re.compile(r"fedex", re.I)),
]
UPS_RE = re.compile(r"\b1Z[0-9A-Z]{16}\b")
S10_RE = re.compile(r"\b[A-Z]{2}\d{9}[A-Z]{2}\b")
LABELED_RE = re.compile(
    r"(?:takip\s*(?:no|numaras[ıi]|kodu)?|tracking\s*(?:number|no|code|id)?|g[öo]nderi\s*(?:no|numaras[ıi])|kargo\s*takip\s*(?:no)?)"
    r"\s*[:#\-]?\s*([A-Z0-9][A-Z0-9\-]{7,29})\b", re.I)
STATUS_RANK = [
    ("delivered", 4, re.compile(r"teslim\s+edildi|teslim\s+al[ıi]nd[ıi]|delivered", re.I)),
    ("out_for_delivery", 3, re.compile(r"da[ğg][ıi]t[ıi]ma\s+[çc][ıi]kt[ıi]|da[ğg][ıi]t[ıi]mda|out\s+for\s+delivery|kurye\s+(?:ile|da)", re.I)),
    ("shipped", 2, re.compile(r"yola\s+[çc][ıi]kt[ıi]|kargoya\s+verildi|g[öo]nderildi|shipped|in\s+transit|transfer\s+merkez", re.I)),
    ("preparing", 1, re.compile(r"haz[ıi]rlan[ıi]yor|preparing|label\s+created", re.I)),
]


def _status(subject: str, body: str) -> tuple[str, int] | None:
    for text in (subject, body[:800]):
        for name, rank, rx in STATUS_RANK:
            if rx.search(text):
                return name, rank
    return None


def _carrier(text: str) -> str | None:
    for name, rx in CARRIERS:
        if rx.search(text):
            return name
    return None


def find_tracking(text: str) -> str | None:
    for rx in (UPS_RE, S10_RE):
        m = rx.search(text)
        if m:
            return m.group(0)
    for m in LABELED_RE.finditer(text):
        t = m.group(1).upper()
        if re.search(r"\d", t) and len(re.sub(r"\D", "", t)) >= 6 and redact(t) == t:
            return t
    return None


# ------------------------------------------------------------------ çıkarım
def _rows(con: sqlite3.Connection, since_ms: int):
    return con.execute("SELECT account, id, date_ms, from_addr, from_name, subject, body FROM messages "   # kampanya mailleri fatura değil
                       "WHERE date_ms >= ? AND COALESCE(category, '') NOT IN ('reklam', 'spam') ORDER BY date_ms", (since_ms,)).fetchall()


def extract_invoice(row) -> dict | None:
    subject, body = row["subject"] or "", row["body"] or ""
    head = f"{subject}\n{body[:3000]}"
    if not INVOICE_RE.search(subject) and not INVOICE_RE.search(body[:2000]):
        return None
    amt = find_amount(head)
    if not amt:
        return None
    vendor = vendor_of(row["from_name"], row["from_addr"])
    return {"source": "invoice", "id": f"{row['account']}:{row['id']}", "date_ms": row["date_ms"], "kind": "invoice",
            "title": f"{vendor} · {amt[0]:.2f} {amt[1]}", "url": None,
            "body": redact(f"{subject}\n{body[:500]}"),
            "meta": {"vendor": vendor, "amount": amt[0], "currency": amt[1], "mail_id": row["id"], "account": row["account"]}}


def extract_shipments(rows) -> list[dict]:
    """Takip numarasına göre gruplar; en son mesajın durumu kazanır."""
    groups: dict[str, dict] = {}
    for r in rows:                         # tarihe göre artan
        subject, body = r["subject"] or "", r["body"] or ""
        text = f"{subject}\n{body[:3000]}"
        tracking = find_tracking(text)
        carrier = _carrier(f"{subject}\n{body[:1500]}\n{r['from_name'] or ''} {r['from_addr'] or ''}")
        st = _status(subject, body)
        if not tracking or not (carrier or UPS_RE.search(tracking) or S10_RE.fullmatch(tracking)):
            continue
        if not st and not carrier:
            continue
        g = groups.setdefault(tracking, {"carrier": carrier, "status": None, "rank": 0, "mail_ids": [], "date_ms": 0,
                                         "subject": subject})
        g["carrier"] = g["carrier"] or carrier or ("UPS" if UPS_RE.fullmatch(tracking) else None)
        g["mail_ids"].append(f"{r['account']}:{r['id']}")
        g["date_ms"], g["subject"] = r["date_ms"], subject
        if st:
            g["status"], g["rank"] = st
    out = []
    for tracking, g in groups.items():
        out.append({"source": "cargo", "id": tracking, "date_ms": g["date_ms"], "kind": "shipment",
                    "title": f"{g['carrier'] or 'Kargo'} {tracking} · {g['status'] or 'bilinmiyor'}", "url": None,
                    "body": redact(g["subject"]),
                    "meta": {"carrier": g["carrier"], "tracking": tracking, "status": g["status"] or "unknown",
                             "mail_ids": g["mail_ids"][-20:]}})
    return out


def derive(con: sqlite3.Connection, days: int = 365, dry_run: bool = False, now_ms: int | None = None) -> dict:
    """{"invoices": n, "invoice_total": {"TRY": x}, "shipments": n, "vendors": n}. dry_run: items'a yazmaz."""
    now = now_ms if now_ms is not None else int(time.time() * 1000)
    rows = _rows(con, now - days * 86_400_000)
    invoices = [i for i in (extract_invoice(r) for r in rows) if i]
    shipments = extract_shipments(rows)
    if not dry_run:
        for it in invoices + shipments:
            maildb.insert_item(con, it, update=True)
        con.commit()
    totals: dict[str, float] = {}
    for i in invoices:
        totals[i["meta"]["currency"]] = round(totals.get(i["meta"]["currency"], 0) + i["meta"]["amount"], 2)
    return {"invoices": len(invoices), "invoice_total": totals, "shipments": len(shipments),
            "vendors": len({i["meta"]["vendor"] for i in invoices})}


def cli(args) -> int:
    from .config import MAIL_DB
    if args.dry_run:                       # mail.db'ye hiç yazma: salt okunur aç
        con = sqlite3.connect(f"file:{MAIL_DB.as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
    else:
        con = maildb.connect(MAIL_DB)
    r = derive(con, days=args.days, dry_run=args.dry_run)
    tot = ", ".join(f"{v:.2f} {k}" for k, v in r["invoice_total"].items()) or "-"
    print(f"{'(dry-run) ' if args.dry_run else ''}{r['invoices']} fatura ({r['vendors']} satıcı, toplam {tot}) · {r['shipments']} kargo")
    return 0
