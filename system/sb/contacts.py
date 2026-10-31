"""Google Contacts (People API, contacts.readonly) → 60-Kişiler notları.

Her kişi bir not; `source: contacts`, `source_id` = People API resourceName (people/c...).
İletişim alanları (email, phone, company, role, linkedin) kaynağa aittir ve her çalıştırmada
güncellenir; status, tags, relation ve elle yazılan metin korunur. Kişinin mail adresleriyle
mail.db'de eşleşen son yazışmalar "Son mailler" otomatik bölümüne yazılır.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime

from .google_auth import service
from .notes import NoteSpec
from .redact import redact

FOLDER = "60-Kişiler"
FIELDS = "names,emailAddresses,phoneNumbers,organizations,urls,biographies,birthdays"
RECENT = 5


def fetch_all(alias: str = "main") -> list[dict]:
    api = service(alias, "people", "v1").people().connections()
    out, token = [], None
    while True:
        resp = api.list(resourceName="people/me", personFields=FIELDS, pageSize=1000, pageToken=token).execute()
        out += resp.get("connections", [])
        token = resp.get("nextPageToken")
        if not token:
            return out


def _first(person: dict, key: str, field: str) -> str:
    items = person.get(key) or []
    primary = next((i for i in items if i.get("metadata", {}).get("primary")), items[0] if items else {})
    return (primary.get(field) or "").strip()


def _all(person: dict, key: str, field: str) -> list[str]:
    seen, out = set(), []
    for i in person.get(key) or []:
        v = (i.get(field) or "").strip()
        if v and v.lower() not in seen:
            seen.add(v.lower())
            out.append(v)
    return out


def _title(person: dict) -> str:
    return (_first(person, "names", "displayName") or _first(person, "organizations", "name")
            or _first(person, "emailAddresses", "value") or _first(person, "phoneNumbers", "value"))


def _recent_mail(con: sqlite3.Connection | None, emails: list[str]) -> str:
    if not con or not emails:
        return "Mail eşleşmesi yok."
    like = "from_addr = ? OR to_addrs LIKE ? OR cc_addrs LIKE ?"
    rows = []
    for e in emails:
        rows += con.execute(
            f"SELECT date_ms, account, from_addr, subject FROM messages WHERE {like} ORDER BY date_ms DESC LIMIT ?",
            (e.lower(), f"%{e.lower()}%", f"%{e.lower()}%", RECENT),
        ).fetchall()
    rows = sorted({(r[0], r[1], r[2], r[3]) for r in rows}, reverse=True)[:RECENT]
    if not rows:
        return "Mail eşleşmesi yok."
    lines = []
    for d, acc, frm, subj in rows:
        way = "←" if frm in [e.lower() for e in emails] else "→"
        subj = redact((subj or "(konusuz)").replace("[[", "[ ["))[:90]
        lines.append(f"- {datetime.fromtimestamp(d / 1000):%Y-%m-%d} {way} {subj} ({acc})")
    return "\n".join(lines)


CALL_TYPES = {1: "gelen", 2: "giden", 3: "cevapsız", 5: "reddedildi", 6: "engellendi"}


def _recent_phone(con: sqlite3.Connection | None, phones: list[str]) -> str:
    keys = [k for k in {normalize_phone(p) for p in phones} if len(k) >= 7]
    if not con or not keys:
        return "Mesaj/arama eşleşmesi yok."
    q = ",".join("?" * len(keys))
    sms = con.execute(f"SELECT date_ms, from_addr, body FROM messages WHERE account = 'sms' AND thread_id IN ({q}) "
                      f"ORDER BY date_ms DESC LIMIT ?", (*keys, RECENT)).fetchall()
    calls = con.execute(f"SELECT date_ms, type, duration FROM calls WHERE phone_key IN ({q}) ORDER BY date_ms DESC LIMIT ?",
                        (*keys, RECENT)).fetchall()
    n_sms = con.execute(f"SELECT COUNT(*) FROM messages WHERE account = 'sms' AND thread_id IN ({q})", keys).fetchone()[0]
    n_calls = con.execute(f"SELECT COUNT(*) FROM calls WHERE phone_key IN ({q})", keys).fetchone()[0]
    if not n_sms and not n_calls:
        return "Mesaj/arama eşleşmesi yok."
    lines = [f"Toplam {n_sms} SMS, {n_calls} arama."]
    for d, frm, body in sms:
        way = "→" if frm == "me" else "←"
        text = redact(" ".join((body or "").split()).replace("[[", "[ ["))[:90]
        lines.append(f"- {datetime.fromtimestamp(d / 1000):%Y-%m-%d %H:%M} SMS {way} {text}")
    for d, typ, dur in calls:
        lines.append(f"- {datetime.fromtimestamp(d / 1000):%Y-%m-%d %H:%M} arama ({CALL_TYPES.get(typ, typ)}, {dur // 60} dk)")
    return "\n".join(lines)


def build_specs(people: list[dict], con: sqlite3.Connection | None = None) -> list[NoteSpec]:
    specs = []
    for p in people:
        title = _title(p)
        if not title:
            continue
        emails = _all(p, "emailAddresses", "value")
        phones = _all(p, "phoneNumbers", "value")
        urls = _all(p, "urls", "value")
        linkedin = next((u for u in urls if "linkedin.com" in u.lower()), None)
        bio = _first(p, "biographies", "value")
        specs.append(NoteSpec(
            folder=FOLDER,
            title=title,
            frontmatter={
                "type": "kisi", "status": "aktif", "tags": ["kisi"],
                "source": "contacts", "source_id": p["resourceName"], "due": None,
                "company": _first(p, "organizations", "name") or None,
                "role": _first(p, "organizations", "title") or None,
                "relation": None,
                "email": emails or None,
                "phone": phones or None,
                "linkedin": linkedin,
            },
            owned=("company", "role", "email", "phone", "linkedin"),
            rename=True,
            body=f"# {title}\n\n## Bağlam\n" + (f"{redact(bio)}\n" if bio else "") +
                 "\n## Etkileşimler\n\n## Son mailler\n<!-- sb:auto:mailler:start -->\n<!-- sb:auto:mailler:end -->\n"
                 "\n## Son mesajlar ve aramalar\n<!-- sb:auto:telefon:start -->\n<!-- sb:auto:telefon:end -->\n",
            auto={"mailler": _recent_mail(con, emails), "telefon": _recent_phone(con, phones)},
        ))
    return specs


def normalize_phone(s: str) -> str:
    """SMS/arama eşleştirmesi için: +90 5XX XXX XX XX → 5XXXXXXXXX."""
    d = re.sub(r"\D", "", s)
    return d[-10:] if len(d) >= 10 else d
