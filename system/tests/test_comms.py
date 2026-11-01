"""Paket C: iletişim (geçici maildb + geçici kasa; gerçek model/ağ/mail yok)."""
import json
from datetime import date, datetime, timedelta

import pytest

from sb import api_comms, chat, comms, convstore, llm, maildb, tasks, vault_ops, webroutes
from sb.notes import dump_note
from sb.webroutes import Ctx

ME = "ayse@example.com"
DAY = 86400000
NOW = int(datetime.now().timestamp() * 1000)


def call(method, path, data=None, query=None, session=None):
    r = webroutes.find(method, path)
    assert r is not None, path
    ctx = Ctx(method, path, data or {}, query or {}, b"", "", "s1", False, session if session is not None else chat.Session(), None, None)
    code, body, _, _ = webroutes.call(r, ctx)
    return code, json.loads(body)


def msg(mid, tid, ago_days, frm, to, subj="Konu", labels=(), account="main", cat=None, body="merhaba"):
    return {"account": account, "id": mid, "thread_id": tid, "date_ms": NOW - int(ago_days * DAY), "from_addr": frm, "from_name": "",
            "to_addrs": to, "cc_addrs": "", "subject": subj, "snippet": body, "body": body, "labels": list(labels), "attachments": [],
            "category": cat, "category_src": "rule"}


def person(vault, name, **fm):
    p = vault / "60-Kişiler" / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_note({"type": "kisi", "status": "aktif", **fm}, f"# {name}\n"), encoding="utf-8")


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", vault)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, m: "")
    monkeypatch.setattr(convstore, "notify", lambda *a, **k: {})
    db = tmp_path / "mail.db"
    monkeypatch.setattr(comms, "MAIL_DB", db)
    monkeypatch.setattr(comms, "own_addrs", lambda: {ME})
    con = maildb.connect(db)
    for m in [
        msg("a1", "T1", 5, ME, "ali@firma.com", "Teklif", ["SENT"]),                               # cevapsız, 5 gün
        msg("a2", "T2", 6, ME, "veli@firma.com", "Soru", ["SENT"]),
        msg("a3", "T2", 4, "veli@firma.com", ME, "Re: Soru"),                                       # cevaplanmış
        msg("a4", "T3", 1, ME, "x@firma.com", "Yeni", ["SENT"]),                                    # çok yeni
        msg("a5", "T4", 5, ME, "noreply@firma.com", "Otomatik", ["SENT"]),
        msg("n%d" % 0, "N0", 10, "bulten@shop.com", ME, "İndirim", ["UNREAD"], cat="reklam"),
        msg("p1", "5551112233", 200, "5551112233", "", "selam", ["SMS"], account="sms"),
        msg("h1", "H1", 20, ME, "hoca@uni.edu", "Rapor", ["SENT"], body="Sayın hocam, rapor ektedir. Saygılarımla"),
    ]:
        maildb.insert(con, m)
    for i in range(1, 6):
        maildb.insert(con, msg(f"n{i}", f"N{i}", i, "bulten@shop.com", ME, "İndirim", ["UNREAD"], cat="reklam"))
    con.execute("INSERT INTO calls(id,number,phone_key,date_ms,type,duration,contact_name) VALUES ('c1','+905551112233','5551112233',?,1,60,'Ayşe')",
                (NOW - 3600000,))
    con.commit()
    con.close()
    return vault


def fake_llm(monkeypatch, text):
    seen = []
    monkeypatch.setattr(llm, "complete", lambda task, prompt, **kw: seen.append((prompt, kw)) or (text, "fake"))
    return seen


def test_awaiting_filters(env):
    code, out = call("GET", "/api/v2/awaiting")
    ids = {i["id"] for i in out["items"]}
    assert code == 200 and "T1" in ids and "T2" not in ids and "T3" not in ids and "T4" not in ids
    assert {i["id"] for i in comms.awaiting(days=1)} >= {"T1", "T3"}


def test_followup_creates_task(env):
    person(env, "Ali Veli", email=["ali@firma.com"])
    code, out = call("POST", "/api/v2/followup", {"id": "T1", "days": 2})
    assert code == 200 and out["due"] == (date.today() + timedelta(days=2)).isoformat()
    assert "Ali Veli" in (env / out["task"]).read_text(encoding="utf-8")
    assert call("POST", "/api/v2/followup", {"id": "YOK"})[0] == 404


def test_mail_to_task(env):
    code, out = call("POST", "/api/v2/mail-to-task", {"message_id": "a1"})
    assert code == 200 and "mail.google.com" in out["link"]
    assert "Teklif" in (env / out["task"]).read_text(encoding="utf-8")
    assert call("POST", "/api/v2/mail-to-task", {"message_id": "yok"})[0] == 404


def test_draft_tone_from_note_and_history(env, monkeypatch):
    seen = fake_llm(monkeypatch, "Merhaba Ali,\nTeklif için teşekkürler.")
    person(env, "Ali Veli", email=["ali@firma.com"], ton="çok samimi")
    code, out = call("POST", "/api/v2/draft", {"to": "ali@firma.com", "subject": "Teklif", "context": "teşekkür et"})
    assert code == 200 and "çok samimi" in seen[0][0] and (env / out["path"]).exists() and seen[0][1].get("private") is True
    assert out["text"].startswith("Merhaba")
    assert "resmi" in comms.tone_for("hoca@uni.edu")                                                # geçmişten çıkarım
    assert call("POST", "/api/v2/draft", {"context": ""})[0] == 400


def test_thread_summary_and_translate(env, monkeypatch):
    fake_llm(monkeypatch, 'sonuç: {"summary": "Teklif bekleniyor", "decisions": ["Cuma"], "asks": ["Fiyat gönder"]}')
    code, out = call("GET", "/api/v2/thread-summary", query={"thread_id": "T2"})
    assert code == 200 and out["summary"] == "Teklif bekleniyor" and out["asks"] == ["Fiyat gönder"] and out["count"] == 2
    assert call("GET", "/api/v2/thread-summary", query={"thread_id": "yok"})[0] == 404
    fake_llm(monkeypatch, "Hello")
    assert call("POST", "/api/v2/translate", {"text": "Merhaba", "to": "en"})[1]["text"] == "Hello"


def test_dates(env):
    t = date.today()
    person(env, "Doğum Günü", dogum_gunu=date(1990, t.month, t.day) + timedelta(days=0))
    soon = t + timedelta(days=5)
    person(env, "Yakın", dogum_gunu=f"1985-{soon.month:02d}-{soon.day:02d}")
    person(env, "Uzak", dogum_gunu=(t + timedelta(days=100)).isoformat())
    items = call("GET", "/api/v2/dates", query={"days": 30})[1]["items"]
    assert [i["name"] for i in items] == ["Doğum Günü", "Yakın"] and items[1]["in_days"] == 5


def test_relationships(env):
    person(env, "Eski Dost", phone=["+90 555 111 22 33"])                                           # sms 200 gün, arama yakın -> listede değil
    person(env, "Hoca", email=["ali@firma.com"])                                                    # 5 gün
    person(env, "Uzak", email=["bulten@shop.com"])
    person(env, "Hiç", email=["hic@x.com"])
    names = {i["name"] for i in call("GET", "/api/v2/relationships", query={"days": 90})[1]["items"]}
    assert names == set()
    comms_ = comms.relationships(days=2)
    assert {i["name"] for i in comms_} == {"Hoca"}
    person(env, "Sadece Sms", phone=["5559998877"])
    con = maildb.connect(comms.MAIL_DB)
    maildb.insert(con, msg("s9", "5559998877", 150, "5559998877", "", "yok", ["SMS"], account="sms"))
    con.commit()
    out = call("GET", "/api/v2/relationships", query={"days": 90})[1]
    assert out["count"] == 1 and out["items"][0]["name"] == "Sadece Sms" and out["items"][0]["channel"] == "sms"


def test_newsletters_and_calls(env):
    out = call("GET", "/api/v2/newsletters")[1]
    assert out["count"] == 1 and out["items"][0]["unread_ratio"] == 1.0 and "çık" in out["items"][0]["suggest"]
    calls = call("GET", "/api/v2/calls/recent")[1]
    assert calls["count"] == 1 and calls["items"][0]["name"] == "Ayşe"


def test_bulk_draft_mail_and_whatsapp(env, monkeypatch):
    person(env, "Zeynep Kaya", email=["z@x.com"], phone=["+905551234567"])
    person(env, "Mert Can", email=["m@x.com"], phone=["+905557654321"])
    code, out = call("POST", "/api/v2/bulk-draft", {"names": ["Zeynep", "Yok Kişi"], "template": "Selam {ad}, bayramın kutlu olsun"})
    assert code == 200 and out["items"][0]["ok"] and "Selam Zeynep" in out["items"][0]["text"] and not out["items"][1]["ok"]
    assert (env / out["items"][0]["path"]).exists()
    s = chat.Session()
    code, out = call("POST", "/api/v2/bulk-draft", {"names": ["Zeynep", "Mert"], "template": "Selam {ad}", "channel": "whatsapp"}, session=s)
    assert code == 200 and len(out["proposals"]) == 2 and all(p["kind"] == "whatsapp" for p in out["proposals"])
    assert call("POST", "/api/v2/bulk-draft", {"names": [], "template": "x"})[0] == 400


def test_meeting_prep_and_after(env, monkeypatch):
    person(env, "Ali Veli", email=["ali@firma.com"])
    fake_llm(monkeypatch, "Gündem: teklif")
    code, out = call("POST", "/api/v2/meeting-prep", {"title": "Teklif toplantısı", "people": ["Ali Veli"]})
    note = (env / out["path"]).read_text(encoding="utf-8")
    assert code == 200 and "Gündem" in note and "Teklif" in note and out["path"].startswith("00-Inbox/Toplantı hazırlık/")
    fake_llm(monkeypatch, json.dumps({"summary": "Özet", "decisions": ["Cuma teslim"], "tasks": [{"title": "Teklifi gönder", "due": "2030-01-05"}, {"title": "Ara"}]}))
    code, out = call("POST", "/api/v2/meeting-after", {"text": "toplantı notları", "title": "Haftalık"})
    assert code == 200 and len(out["tasks"]) == 2 and all(t["ok"] for t in out["tasks"]) and out["decisions"] == ["Cuma teslim"]
    assert (env / tasks.FOLDER / "Teklifi gönder.md").exists()
    assert call("POST", "/api/v2/meeting-after", {"text": ""})[0] == 400


def test_no_send_code():
    import inspect
    src = inspect.getsource(comms) + inspect.getsource(api_comms)
    for bad in ("smtplib", "send_message", "users().messages", "trash", "modify("):
        assert bad not in src
