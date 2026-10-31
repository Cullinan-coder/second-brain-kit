"""iCloud CalDAV/CardDAV (ve Outlook yayımlanmış ICS) → mail.db `items`. SALT OKUNUR.

- Yalnız PROPFIND ve REPORT (ve ICS için GET) kullanılır; PUT/DELETE/PROPPATCH hiçbir yerde yok.
- Kimlik: Basic auth, e-posta + UYGULAMAYA ÖZEL şifre (keyring: servis `second-brain`, anahtar `caldav-<takma ad>`).
- Olaylar `icloud-cal`/kind `event`, kişiler `icloud-contacts`/kind `contact`; `ics_url` verilen hesapta
  olaylar `<hesap>-cal` kaynağına yazılır (Outlook: Takvim → Paylaş → yayımla → ICS bağlantısı).
- Yalnız stdlib (urllib + xml.etree). Ağ çağrıları `_request` / `_get` üzerinden; testlerde taklit edilir.
"""
from __future__ import annotations

import base64
import hashlib
import re
import sqlite3
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import keyring

from . import maildb
from .config import KEYRING_SERVICE, TIMEZONE, accounts
from .ics import _unfold
from .redact import redact

DEFAULT_CAL = "https://caldav.icloud.com"
DEFAULT_CARD = "https://contacts.icloud.com"
NS = {"d": "DAV:", "c": "urn:ietf:params:xml:ns:caldav", "cr": "urn:ietf:params:xml:ns:carddav"}
TIMEOUT = 60


# ---------------------------------------------------------------- ağ
def _open(req: urllib.request.Request, user: str | None, password: str | None) -> bytes:
    if user:
        tok = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode()
        req.add_header("Authorization", f"Basic {tok}")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def _request(method: str, url: str, user: str, password: str, body: str = "", depth: str = "0") -> bytes:
    """PROPFIND/REPORT. Yönlendirmeyi (iCloud pXX- sunucuları) elle izler; yalnız salt okunur yöntemlere izin verir."""
    if method not in ("PROPFIND", "REPORT"):
        raise ValueError(f"izin verilmeyen yöntem: {method}")
    for _ in range(4):
        req = urllib.request.Request(url, data=body.encode("utf-8"), method=method)
        req.add_header("Content-Type", "application/xml; charset=utf-8")
        req.add_header("Depth", depth)
        try:
            return _open(req, user, password)
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location") if e.headers else None
            if e.code in (301, 302, 307, 308) and loc:
                url = urljoin(url, loc)
                continue
            if e.code == 401:
                raise SystemExit("CalDAV girişi reddedildi (401). iCloud için appleid.apple.com'dan UYGULAMAYA ÖZEL şifre "
                                 "üretip `sb set-secret caldav-<ad>` ile kaydet; normal Apple Kimliği şifresi çalışmaz.")
            raise
    raise SystemExit("CalDAV: çok fazla yönlendirme")


def _get(url: str) -> bytes:
    return _open(urllib.request.Request(url, method="GET"), None, None)


# ---------------------------------------------------------------- XML yardımcıları
def _hrefs(xml: bytes, path: str) -> list[str]:
    root = ET.fromstring(xml)
    return [(e.text or "").strip() for e in root.iterfind(path, NS) if (e.text or "").strip()]


def _discover_home(base: str, user: str, pw: str, prop: str, ns: str) -> str:
    """principal → *-home-set adresi."""
    body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:current-user-principal/></d:prop></d:propfind>'
    xml = _request("PROPFIND", base, user, pw, body)
    principal = _hrefs(xml, ".//d:current-user-principal/d:href")
    if not principal:
        raise SystemExit(f"CalDAV: kullanıcı ana dizini bulunamadı ({base})")
    principal_url = urljoin(base, principal[0])
    body = (f'<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:x="{ns}"><d:prop><x:{prop}/></d:prop></d:propfind>')
    xml = _request("PROPFIND", principal_url, user, pw, body)
    home = _hrefs(xml, f".//{{{ns}}}{prop}/d:href")
    if not home:
        raise SystemExit(f"CalDAV: {prop} bulunamadı")
    return urljoin(principal_url, home[0])


def _collections(home: str, user: str, pw: str, kind: str) -> list[str]:
    """Ana dizin altındaki takvim ('calendar') veya adres defteri ('addressbook') koleksiyonları."""
    body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>'
    xml = _request("PROPFIND", home, user, pw, body, depth="1")
    ns = NS["c"] if kind == "calendar" else NS["cr"]
    out = []
    for resp in ET.fromstring(xml).iterfind("d:response", NS):
        rt = resp.find(".//d:resourcetype", NS)
        if rt is not None and rt.find(f"{{{ns}}}{kind}") is not None:
            href = (resp.findtext("d:href", "", NS) or "").strip()
            if href:
                out.append(urljoin(home, href))
    return out


def _report_data(url: str, user: str, pw: str, kind: str) -> list[str]:
    if kind == "calendar":
        body = ('<?xml version="1.0"?><c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
                '<d:prop><c:calendar-data/></d:prop><c:filter><c:comp-filter name="VCALENDAR">'
                '<c:comp-filter name="VEVENT"/></c:comp-filter></c:filter></c:calendar-query>')
        tag = f"{{{NS['c']}}}calendar-data"
    else:
        body = ('<?xml version="1.0"?><cr:addressbook-query xmlns:d="DAV:" xmlns:cr="urn:ietf:params:xml:ns:carddav">'
                '<d:prop><cr:address-data/></d:prop></cr:addressbook-query>')
        tag = f"{{{NS['cr']}}}address-data"
    xml = _request("REPORT", url, user, pw, body, depth="1")
    return [e.text for e in ET.fromstring(xml).iter(tag) if e.text]


# ---------------------------------------------------------------- ayrıştırma
def _unescape(v: str) -> str:
    return (v.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")).strip()


def _to_ms(value: str, params: str) -> int | None:
    v = value.strip()
    try:
        if re.fullmatch(r"\d{8}", v):  # tüm gün
            dt = datetime.strptime(v, "%Y%m%d").replace(tzinfo=ZoneInfo(TIMEZONE))
        elif v.endswith("Z"):
            dt = datetime.strptime(v, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        else:
            tz = re.search(r"TZID=([^;:]+)", params)
            try:
                zone = ZoneInfo(tz.group(1).strip('"')) if tz else ZoneInfo(TIMEZONE)
            except Exception:
                zone = ZoneInfo(TIMEZONE)
            dt = datetime.strptime(v, "%Y%m%dT%H%M%S").replace(tzinfo=zone)
        return int(dt.timestamp() * 1000)
    except (ValueError, KeyError):
        return None


def _props(lines: list[str]) -> list[tuple[str, str, str]]:
    out = []
    for line in lines:
        if ":" not in line:
            continue
        head, value = line.split(":", 1)
        name, _, params = head.partition(";")
        out.append((name.upper(), params, value))
    return out


def parse_events(text: str) -> list[dict]:
    """VCALENDAR metninden VEVENT'ler: uid, summary, start_ms, end_ms, location."""
    events, cur = [], None
    for line in _unfold(text):
        if line.startswith("BEGIN:VEVENT"):
            cur = []
        elif line.startswith("END:VEVENT") and cur is not None:
            p: dict[str, tuple[str, str]] = {}
            for name, params, value in _props(cur):
                p.setdefault(name, (params, value))
            summary = _unescape(p.get("SUMMARY", ("", ""))[1])
            start = _to_ms(p["DTSTART"][1], p["DTSTART"][0]) if "DTSTART" in p else None
            end = _to_ms(p["DTEND"][1], p["DTEND"][0]) if "DTEND" in p else None
            uid = _unescape(p.get("UID", ("", ""))[1]) or hashlib.sha1(f"{summary}|{start}".encode()).hexdigest()[:20]
            events.append({"uid": uid, "summary": summary, "start_ms": start, "end_ms": end,
                           "location": _unescape(p.get("LOCATION", ("", ""))[1]),
                           "recurring": "RRULE" in p})
            cur = None
        elif cur is not None:
            cur.append(line)
    return events


def parse_contacts(text: str) -> list[dict]:
    """vCard metninden kişiler: uid, name, phones, emails, org."""
    out, cur = [], None
    for line in _unfold(text):
        if line.upper().startswith("BEGIN:VCARD"):
            cur = []
        elif line.upper().startswith("END:VCARD") and cur is not None:
            name, phones, emails, org, uid = "", [], [], "", ""
            for n, _params, value in _props(cur):
                if n == "FN" and not name:
                    name = _unescape(value)
                elif n == "TEL":
                    phones.append(value.strip())
                elif n == "EMAIL":
                    emails.append(value.strip().lower())
                elif n == "ORG" and not org:
                    org = _unescape(value.replace(";", " ")).strip()
                elif n == "UID" and not uid:
                    uid = value.strip()
            if name or phones or emails:
                uid = uid or hashlib.sha1(f"{name}|{phones}|{emails}".encode()).hexdigest()[:20]
                out.append({"uid": uid, "name": name or (emails or phones)[0], "phones": phones, "emails": emails, "org": org})
            cur = None
        elif cur is not None:
            cur.append(line)
    return out


# ---------------------------------------------------------------- kayıt
def _event_item(source: str, ev: dict, calendar: str = "") -> dict:
    when = datetime.fromtimestamp(ev["start_ms"] / 1000).strftime("%Y-%m-%d %H:%M") if ev["start_ms"] else ""
    body = " | ".join(x for x in (ev["summary"], when, ev["location"]) if x)
    return {"source": source, "id": ev["uid"], "date_ms": ev["start_ms"], "kind": "event",
            "title": ev["summary"] or "(başlıksız)", "url": None, "body": redact(body),
            "meta": {"end_ms": ev["end_ms"], "location": ev["location"], "calendar": calendar, "recurring": ev["recurring"]}}


def _contact_item(source: str, c: dict) -> dict:
    body = " | ".join(x for x in [c["name"], c["org"], *c["phones"], *c["emails"]] if x)
    return {"source": source, "id": c["uid"], "date_ms": None, "kind": "contact", "title": c["name"], "url": None,
            "body": body, "meta": {"phones": c["phones"], "emails": c["emails"], "org": c["org"]}}


def sync_ics_url(alias: str, url: str, con: sqlite3.Connection, log=print) -> int:
    """Yayımlanmış ICS bağlantısı (Outlook vb.) → `<alias>-cal` olayları."""
    events = parse_events(_get(url).decode("utf-8", "replace"))
    n = sum(maildb.insert_item(con, _event_item(f"{alias}-cal", ev), update=True) for ev in events)
    con.commit()
    log(f"[{alias}] ICS: {len(events)} olay ({n} yeni)")
    return len(events)


def sync(alias: str, con: sqlite3.Connection, log=print) -> dict:
    """Hesabın CalDAV/CardDAV (ve varsa ics_url) verisini items'a alır. {"events": n, "contacts": n}."""
    acc = (accounts().get("imap") or {}).get(alias)
    if not acc:
        raise SystemExit(f"Bilinmeyen hesap: {alias} (accounts.yaml imap bloğu)")
    totals = {"events": 0, "contacts": 0}
    if acc.get("ics_url"):
        totals["events"] += sync_ics_url(alias, acc["ics_url"], con, log)
    dav = acc.get("caldav")
    if dav is None and acc.get("preset") != "icloud":
        if not acc.get("ics_url"):
            raise SystemExit(f"{alias}: ne `caldav:` ne `ics_url:` var (accounts.yaml)")
        return totals
    dav = dav or {}
    password = keyring.get_password(KEYRING_SERVICE, f"caldav-{alias}")
    if not password:
        raise SystemExit(f"{alias} CalDAV şifresi yok. Çalıştır: uv run python -m sb set-secret caldav-{alias}  "
                         "(iCloud: uygulamaya özel şifre)")
    user = acc["email"]
    cal_src, card_src = "icloud-cal", "icloud-contacts"
    cal_home = _discover_home(dav.get("url", DEFAULT_CAL), user, password, "calendar-home-set", NS["c"])
    for cal in _collections(cal_home, user, password, "calendar"):
        for text in _report_data(cal, user, password, "calendar"):
            for ev in parse_events(text):
                maildb.insert_item(con, _event_item(cal_src, ev, cal.rstrip("/").rsplit("/", 1)[-1]), update=True)
                totals["events"] += 1
    con.commit()
    log(f"[{alias}] takvim: {totals['events']} olay")
    try:
        card_home = _discover_home(dav.get("carddav_url", DEFAULT_CARD), user, password, "addressbook-home-set", NS["cr"])
        for book in _collections(card_home, user, password, "addressbook"):
            for text in _report_data(book, user, password, "addressbook"):
                for c in parse_contacts(text):
                    maildb.insert_item(con, _contact_item(card_src, c), update=True)
                    totals["contacts"] += 1
        con.commit()
        log(f"[{alias}] kişiler: {totals['contacts']}")
    except urllib.error.HTTPError as e:
        log(f"[{alias}] kişiler alınamadı (HTTP {e.code}); takvim tamam")
    return totals


def cli(args) -> int:
    from .config import MAIL_DB
    con = maildb.connect(MAIL_DB)
    r = sync(args.alias, con)
    print(f"{args.alias}: {r['events']} olay, {r['contacts']} kişi")
    return 0
