import json
from datetime import date, datetime, timedelta

import pytest
import yaml

from sb import api_personal, chat, config, llm, maildb, personal, vault_ops, webroutes
from sb.webroutes import Ctx

TODAY = date(2026, 11, 1)
NOW = datetime(2026, 11, 1, 9, 0)


def ms(y, m, d):
    return int(datetime(y, m, d, 12).timestamp() * 1000)


class FakeCal:
    def __init__(self):
        self.added = []

    def add(self, ev, dry_run=True):
        self.added.append((ev, dry_run))
        return ["evt1"]


def call(method, path, data=None, session=None, calendar=None, **q):
    r = webroutes.find(method, path)
    assert r is not None, path
    code, body, _, _ = webroutes.call(r, Ctx(method=method, path=path, data=data or {}, query={k: str(v) for k, v in q.items()},
                                             session=session, calendar=calendar))
    return code, json.loads(body)


@pytest.fixture
def env(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    for d in ("40-Kaynaklar/Sağlık", "40-Kaynaklar/Tarifler", "50-Günlük", "60-Kişiler"):
        (v / d).mkdir(parents=True)
    sysdir = v / "_system"
    (sysdir / "config").mkdir(parents=True)
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(config, "SYSTEM", sysdir)
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "")
    db = tmp_path / "mail.db"
    monkeypatch.setattr(config, "MAIL_DB", db)
    return v


def _db(env, tmp_path=None):
    con = maildb.connect(config.MAIL_DB)
    for i, (d, amt) in enumerate([((2026, 8, 5), 99.0), ((2026, 9, 4), 99.0), ((2026, 10, 3), 99.0)]):
        maildb.insert_item(con, {"source": "invoice", "id": f"n{i}", "date_ms": ms(*d), "kind": "invoice", "title": "Netflix",
                                 "meta": {"vendor": "Netflix", "amount": amt, "currency": "TRY"}})
    maildb.insert_item(con, {"source": "invoice", "id": "t1", "date_ms": ms(2025, 12, 10), "kind": "invoice", "title": "Teknosa laptop",
                             "body": "Laptop faturası", "meta": {"vendor": "Teknosa", "amount": 30000.0, "currency": "TRY"}})
    maildb.insert_item(con, {"source": "invoice", "id": "m1", "date_ms": ms(2026, 10, 9), "kind": "invoice", "title": "Migros",
                             "meta": {"vendor": "Migros", "amount": 250.0, "currency": "TRY"}})
    sms = {"account": "sms", "id": "s1", "thread_id": "x", "date_ms": ms(2026, 10, 12), "from_addr": "BANKA", "from_name": "",
           "to_addrs": "", "cc_addrs": "", "subject": "harcama", "snippet": "", "labels": [], "attachments": [],
           "body": "4543 6000 0000 0004 nolu kartinizla Starbucks isyerinde 120,50 TL harcama yapildi.", "category": None, "category_src": None}
    maildb.insert(con, sms)
    maildb.insert(con, {**sms, "id": "s2", "body": "Dogrulama kodu 123456 harcama 50,00 TL"})
    con.commit()
    con.close()


def test_spending_and_budget(env):
    _db(env)
    (config.SYSTEM / "config" / "butce.yaml").write_text(yaml.safe_dump({"limitler": {"market": 200}}), encoding="utf-8")
    s = personal.spending("2026-10", TODAY)
    cats = {c["category"]: c for c in s["categories"]}
    assert cats["market"]["over"] is True and cats["yeme-icme"]["totals"]["TRY"] == 120.5
    assert s["count"] == 3 and "4543" not in json.dumps(s)          # 2. SMS (kod) sayılmaz, kart no yok
    code, out = call("GET", "/api/v2/spending", month="2026-10")
    assert code == 200 and out["month"] == "2026-10"
    assert call("GET", "/api/v2/spending", month="bozuk")[0] == 400


def test_subscriptions_and_warranties(env):
    _db(env)
    subs = personal.subscriptions(TODAY)
    assert [s["vendor"] for s in subs] == ["Netflix"] and subs[0]["next"] == "2026-11-02" and subs[0]["count"] == 3
    w = personal.warranties(TODAY)
    assert len(w) == 1 and w[0]["ends"] == "2027-12-10" and not w[0]["warn"]
    (config.SYSTEM / "config" / "butce.yaml").write_text("garanti_ay: 12\n", encoding="utf-8")
    w = personal.warranties(date(2026, 11, 20))
    assert w[0]["ends"] == "2026-12-10" and w[0]["warn"] is True
    assert call("GET", "/api/v2/subscriptions")[0] == 200 and call("GET", "/api/v2/warranties")[0] == 200


def test_no_mail_db_is_empty(env):
    assert personal.subscriptions(TODAY) == [] and personal.spending("2026-10", TODAY)["categories"] == []
    assert personal.maintenance(TODAY) == [] and personal.health(TODAY, NOW) == {"meds": [], "appointments": []}


def test_health_meds_and_proposal_only(env):
    (config.SYSTEM / "config" / "ilaclar.yaml").write_text(
        yaml.safe_dump({"ilaclar": [{"ad": "Vitamin D", "doz": "1 tablet", "saatler": ["08:00", "21:00"]}]}), encoding="utf-8")
    (env / "40-Kaynaklar" / "Sağlık" / "Dis randevusu.md").write_text(
        "---\nvisibility: private\nrandevu: 2026-11-05\nsaat: '14:30'\n---\n# Dis\n", encoding="utf-8")
    h = personal.health(TODAY, NOW)
    assert h["meds"][0]["next"] == "21:00" and h["appointments"][0]["days_left"] == 4
    cal, s = FakeCal(), chat.Session()
    code, out = call("POST", "/api/v2/health/remind", {"sid": "abcd1234", "kind": "med", "name": "vitamin d"}, session=s, calendar=cal)
    assert code == 200 and len(out["proposals"]) == 1 and cal.added == []
    s.proposals[next(iter(s.proposals))]["_run"]()
    ev = cal.added[0][0]
    assert ev.tag == "HATIRLATMA" and ev.reminders == (0, 10) and cal.added[0][1] is False
    assert call("POST", "/api/v2/health/remind", {"sid": "abcd1234", "kind": "med", "name": "yok"}, session=s)[0] == 404


def test_reading_list(env):
    assert personal.add_reading("Atomic Habits", "okunacak")["ok"]
    personal.add_reading("Dune filmi", "izlenecek")
    personal.add_reading("Sapiens", "okunacak")
    r = personal.reading_list(suggest=False)
    assert [i["title"] for i in r["okunacak"]] == ["Atomic Habits", "Sapiens"] and r["izlenecek"][0]["title"] == "Dune filmi"
    assert call("POST", "/api/v2/reading-list", {"title": "x", "kind": "bozuk"})[0] == 400
    assert call("POST", "/api/v2/reading-list", {"title": "Kart 4111 1111 1111 1111", "kind": "izlenecek"})[0] == 200
    assert "4111 1111" not in (env / personal.LISTE).read_text(encoding="utf-8")
    assert call("GET", "/api/v2/reading-list")[0] == 200


def test_meal_plan_and_trip_use_local_model(env, monkeypatch):
    (env / "40-Kaynaklar" / "Tarifler" / "Mercimek.md").write_text("# Mercimek\nMercimek, soğan.\n", encoding="utf-8")
    seen = []

    def fake(task, prompt, **kw):
        seen.append((task, prompt, kw))
        return "<think>x</think>Pzt: mercimek\n## Alışveriş listesi\n- mercimek", "yerel"
    monkeypatch.setattr(llm, "complete", fake)
    out = personal.meal_plan(3, TODAY)
    assert seen[0][2].get("private") is True and "Mercimek" in seen[0][1] and "think" not in out["text"]
    assert (env / out["path"]).exists() and "Alışveriş" in (env / out["path"]).read_text(encoding="utf-8")
    assert call("POST", "/api/v2/meal-plan", {"days": 99})[0] == 400
    t = personal.trip("Roma", "2026-12-01", "2026-12-04")
    assert t["path"].startswith("40-Kaynaklar/Seyahatler/") and seen[-1][0] == "trip_plan"
    assert call("POST", "/api/v2/trip", {"destination": "", "start": "x", "end": "y"})[0] == 400


def test_maintenance(env):
    (config.SYSTEM / "config" / "bakim.yaml").write_text(yaml.safe_dump({"bakimlar": [
        {"ad": "Araç yağ", "periyot_ay": 12, "son_tarih": "2025-11-20", "periyot_km": 10000, "son_km": 50000, "km": 59800},
        {"ad": "Kombi", "periyot_ay": 12, "son_tarih": "2026-06-01"}]}), encoding="utf-8")
    m = personal.maintenance(TODAY)
    assert m[0]["name"] == "Araç yağ" and m[0]["due"] == "2026-11-20" and m[0]["soon"] and m[0]["km_left"] == 200
    assert m[1]["soon"] is False
    assert call("GET", "/api/v2/maintenance")[0] == 200


def test_gifts_and_mood(env):
    (env / "60-Kişiler" / "Ayşe.md").write_text("---\ntype: kisi\ndogum: 1995-11-10\n---\n# Ayşe\n\n## Notlar\nx\n", encoding="utf-8")
    (env / "60-Kişiler" / "Ali.md").write_text("---\ntype: kisi\ndogum: 1990-03-01\n---\n# Ali\n", encoding="utf-8")
    personal.add_gift("Ayşe", "Kitap")
    r = personal.add_gift("ayşe", "Atkı")
    assert r["ideas"] == ["Kitap", "Atkı"]
    personal.add_gift("Ali", "Kulaklık")
    g = personal.gifts("", TODAY)
    assert [x["person"] for x in g] == ["Ayşe", "Ali"] and g[0]["days_left"] == 9
    assert call("POST", "/api/v2/gift", {"person": "Yok", "idea": "x"})[0] == 404
    assert call("GET", "/api/v2/gifts", person="Ali")[1][0]["ideas"] == ["Kulaklık"]
    personal.add_mood(4, "iyi gün", TODAY - timedelta(days=1))
    personal.add_mood(2, "", TODAY)
    personal.add_mood(4, "akşam", TODAY)
    m = personal.mood(30, TODAY)
    assert [s["level"] for s in m["series"]] == [4.0, 3.0] and m["average"] == 3.5
    with pytest.raises(ValueError):
        personal.add_mood(7)
    assert call("POST", "/api/v2/mood", {"level": 9})[0] == 400
    assert call("GET", "/api/v2/mood", days=7)[0] == 200
