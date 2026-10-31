"""İş paketi 1.3: IMAP ön ayarları, CalDAV, GitHub derin tarama, fatura/kargo çıkarımı, SMS tazeliği. Ağ ve gerçek veri yok."""
import json
import time
from types import SimpleNamespace

import pytest

from sb import caldav, derived, github_deep, imap, maildb, sms


@pytest.fixture
def con(tmp_path):
    return maildb.connect(tmp_path / "mail.db")


# ---------------------------------------------------------------- IMAP ön ayarları
def test_imap_presets(monkeypatch):
    assert imap.resolve({"preset": "outlook", "email": "a@b"})["host"] == "outlook.office365.com"
    assert imap.resolve({"preset": "icloud", "host": "x.y"})["host"] == "x.y"
    assert imap.resolve({"host": "h"}) == {"host": "h"}
    with pytest.raises(SystemExit):
        imap.resolve({"preset": "yok"})

    class Bad:
        def __init__(self, host, port):
            self.host = host

        def login(self, *a):
            raise imap.imaplib.IMAP4.error("AUTHENTICATIONFAILED")

    monkeypatch.setattr(imap.imaplib, "IMAP4_SSL", Bad)
    monkeypatch.setattr(imap.keyring, "get_password", lambda *a: "x")
    monkeypatch.setattr(imap, "accounts", lambda: {"imap": {"ic": {"preset": "icloud", "email": "a@icloud.com"}}})
    with pytest.raises(SystemExit) as e:
        imap._connect("ic")
    assert "Uygulamaya Özel" in str(e.value)


# ---------------------------------------------------------------- CalDAV
ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:abc-1
SUMMARY:Final sınavı\\, Fizik
DTSTART;TZID=Europe/Istanbul:20261105T100000
DTEND;TZID=Europe/Istanbul:20261105T120000
LOCATION:B204
END:VEVENT
BEGIN:VEVENT
UID:abc-2
SUMMARY:Tatil
DTSTART;VALUE=DATE:20261110
END:VEVENT
END:VCALENDAR"""
VCF = """BEGIN:VCARD
VERSION:3.0
UID:u-1
FN:Ayşe Yılmaz
ORG:Acme;Satış
TEL;TYPE=CELL:+90 532 000 00 00
EMAIL:Ayse@Acme.com
END:VCARD
BEGIN:VCARD
FN:Veli
END:VCARD"""


def test_parse_events_and_contacts():
    ev = caldav.parse_events(ICS)
    assert [e["uid"] for e in ev] == ["abc-1", "abc-2"]
    assert ev[0]["summary"] == "Final sınavı, Fizik" and ev[0]["location"] == "B204"
    assert ev[0]["end_ms"] - ev[0]["start_ms"] == 2 * 3600 * 1000
    assert ev[1]["end_ms"] is None and ev[1]["start_ms"]
    cs = caldav.parse_contacts(VCF)
    assert cs[0]["name"] == "Ayşe Yılmaz" and cs[0]["emails"] == ["ayse@acme.com"] and cs[0]["org"] == "Acme Satış"
    assert len(cs) == 2


def _multistatus(*inner):
    return ('<?xml version="1.0"?><d:multistatus xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav" '
            'xmlns:cr="urn:ietf:params:xml:ns:carddav">' + "".join(inner) + "</d:multistatus>").encode()


def test_caldav_sync_mocked(monkeypatch, con):
    calls = []

    def fake(method, url, user, pw, body="", depth="0"):
        calls.append((method, url))
        assert method in ("PROPFIND", "REPORT")
        if "current-user-principal" in body:
            return _multistatus("<d:response><d:propstat><d:prop><d:current-user-principal><d:href>/123/principal/</d:href>"
                                "</d:current-user-principal></d:prop></d:propstat></d:response>")
        if "calendar-home-set" in body:
            return _multistatus("<d:response><d:propstat><d:prop><c:calendar-home-set><d:href>/123/calendars/</d:href>"
                                "</c:calendar-home-set></d:prop></d:propstat></d:response>")
        if "addressbook-home-set" in body:
            return _multistatus("<d:response><d:propstat><d:prop><cr:addressbook-home-set><d:href>/123/carddavhome/</d:href>"
                                "</cr:addressbook-home-set></d:prop></d:propstat></d:response>")
        if "resourcetype" in body:
            if "calendars" in url:
                return _multistatus("<d:response><d:href>/123/calendars/home/</d:href><d:propstat><d:prop><d:resourcetype>"
                                    "<d:collection/><c:calendar/></d:resourcetype></d:prop></d:propstat></d:response>",
                                    "<d:response><d:href>/123/calendars/</d:href><d:propstat><d:prop><d:resourcetype>"
                                    "<d:collection/></d:resourcetype></d:prop></d:propstat></d:response>")
            return _multistatus("<d:response><d:href>/123/carddavhome/card/</d:href><d:propstat><d:prop><d:resourcetype>"
                                "<d:collection/><cr:addressbook/></d:resourcetype></d:prop></d:propstat></d:response>")
        if "calendar-query" in body:
            return _multistatus(f"<d:response><d:propstat><d:prop><c:calendar-data>{ICS}</c:calendar-data></d:prop></d:propstat></d:response>")
        return _multistatus(f"<d:response><d:propstat><d:prop><cr:address-data>{VCF}</cr:address-data></d:prop></d:propstat></d:response>")

    monkeypatch.setattr(caldav, "_request", fake)
    monkeypatch.setattr(caldav.keyring, "get_password", lambda *a: "pw")
    monkeypatch.setattr(caldav, "accounts", lambda: {"imap": {"ic": {"preset": "icloud", "email": "a@icloud.com"}}})
    r = caldav.sync("ic", con, log=lambda *_: None)
    assert r == {"events": 2, "contacts": 2}
    assert con.execute("SELECT COUNT(*) FROM items WHERE source='icloud-cal' AND kind='event'").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM items WHERE source='icloud-contacts' AND kind='contact'").fetchone()[0] == 2
    caldav.sync("ic", con, log=lambda *_: None)                     # tekrar: çoğalmaz
    assert con.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 4


def test_caldav_readonly_methods():
    with pytest.raises(ValueError):
        caldav._request("PUT", "https://x", "u", "p")


def test_ics_url(monkeypatch, con):
    monkeypatch.setattr(caldav, "_get", lambda url: ICS.encode())
    assert caldav.sync_ics_url("outlook", "https://x/cal.ics", con, log=lambda *_: None) == 2
    assert con.execute("SELECT COUNT(*) FROM items WHERE source='outlook-cal'").fetchone()[0] == 2


# ---------------------------------------------------------------- GitHub
def test_github_deep(monkeypatch, con):
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def fake_gh(args):
        if args[0] == "repo":
            return json.dumps([{"nameWithOwner": "u/a", "isArchived": False}, {"nameWithOwner": "u/old", "isArchived": True}])
        path = args[1].split("?")[0]
        if path.endswith("/issues"):
            return json.dumps([{"number": 1, "title": "Hata", "body": "kart 4111 1111 1111 1111", "state": "open", "user": {"login": "u"},
                                "labels": [{"name": "bug"}], "html_url": "h1", "updated_at": now},
                               {"number": 2, "title": "PR gibi", "pull_request": {}, "updated_at": now}])
        if path.endswith("/pulls"):
            return json.dumps([{"number": 2, "title": "Özellik", "body": "", "state": "closed", "merged_at": now, "user": {"login": "u"},
                                "labels": [], "html_url": "h2", "updated_at": now}])
        if path.endswith("/issues/comments"):
            return json.dumps([{"id": i, "body": "yorum", "issue_url": "x/issues/1", "user": {"login": "v"}, "html_url": "c", "created_at": now}
                               for i in range(30)])
        if path.endswith("/commits"):
            return json.dumps([{"sha": "a" * 40, "html_url": "k", "commit": {"message": "ilk\n\ndetay", "author": {"date": now, "name": "U"}},
                                "author": {"login": "u"}}])
        return json.dumps([{"id": 9, "tag_name": "v1", "name": "Sürüm 1", "published_at": now, "body": "n", "html_url": "r"}])

    monkeypatch.setattr(github_deep, "_gh", fake_gh)
    monkeypatch.setattr(github_deep, "GITHUB_USER", "u")
    dry = github_deep.run(days=30, dry_run=True, con=con, log=lambda *_: None)
    assert dry == {"repos": 1, "issue": 1, "pr": 1, "comment": 20, "commit": 1, "release": 1}
    assert con.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0
    github_deep.run(days=30, con=con, log=lambda *_: None)
    row = con.execute("SELECT * FROM items WHERE kind='pr'").fetchone()
    assert row["source"] == "github" and json.loads(row["meta"])["state"] == "merged" and json.loads(row["meta"])["repo"] == "u/a"
    assert "4111" not in con.execute("SELECT body FROM items WHERE kind='issue'").fetchone()[0]


# ---------------------------------------------------------------- fatura / kargo
def test_parse_amount():
    assert derived.parse_amount("1.234,56") == 1234.56
    assert derived.parse_amount("1,234.56") == 1234.56
    assert derived.parse_amount("12,50") == 12.5
    assert derived.parse_amount("1.234") == 1234
    assert derived.parse_amount("12.00") == 12.0
    assert derived.find_amount("Toplam: 1.234,56 TL") == (1234.56, "TRY")
    assert derived.find_amount("Total $12.00") == (12.0, "USD")
    assert derived.find_amount("₺99,90") == (99.9, "TRY")
    assert derived.find_amount("fiyat yok") is None


def _msg(con, mid, subject, body, name="", addr="x@y.com", day=0):
    maildb.insert(con, {"account": "main", "id": mid, "date_ms": int(time.time() * 1000) - (10 - day) * 86_400_000,
                        "from_name": name, "from_addr": addr, "subject": subject, "body": body})


def test_derive(con):
    _msg(con, "1", "e-Arşiv faturanız", "Toplam tutar: 1.234,56 TL. Kart 4111 1111 1111 1111 TR330006100519786457841326",
         name="Trendyol", addr="no-reply@trendyol.com")
    _msg(con, "2", "Merhaba", "Hiçbir şey yok")
    _msg(con, "3", "Siparişiniz kargoya verildi", "Yurtiçi Kargo takip no: 123456789012 ile izleyin", day=1)
    _msg(con, "4", "Kargonuz teslim edildi", "Yurtiçi Kargo takip no: 123456789012", day=3)
    _msg(con, "5", "UPS", "Your package shipped. Tracking 1Z999AA10123456784", day=2)
    r = derived.derive(con, days=365, dry_run=True)
    assert r["invoices"] == 1 and r["shipments"] == 2 and r["invoice_total"] == {"TRY": 1234.56}
    assert con.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0
    derived.derive(con, days=365)
    inv = con.execute("SELECT * FROM items WHERE kind='invoice'").fetchone()
    meta = json.loads(inv["meta"])
    assert meta["vendor"] == "Trendyol" and meta["amount"] == 1234.56 and meta["currency"] == "TRY" and meta["mail_id"] == "1"
    assert "4111 1111" not in inv["body"] and "330006100519786457841326" not in inv["body"]
    ship = con.execute("SELECT * FROM items WHERE source='cargo' AND id='123456789012'").fetchone()
    sm = json.loads(ship["meta"])
    assert sm["status"] == "delivered" and sm["carrier"] == "Yurtiçi Kargo" and len(sm["mail_ids"]) == 2
    assert json.loads(con.execute("SELECT meta FROM items WHERE id='1Z999AA10123456784'").fetchone()[0])["carrier"] == "UPS"


# ---------------------------------------------------------------- SMS tazeliği
def test_sms_freshness(con):
    assert sms.freshness(con)["last_ms"] is None
    now = int(time.time() * 1000)
    maildb.insert(con, {"account": "sms", "id": "s", "date_ms": now - 3 * 86_400_000 - 1000, "subject": "x"})
    f = sms.freshness(con, now_ms=now)
    assert f["days_ago"] == 3 and f["count"] == 1
