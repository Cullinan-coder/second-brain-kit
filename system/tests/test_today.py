"""`sb today`: biçim, bölümler, telefon için kırpma, API uçları."""
import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from sb import approvals, config, freshness, maildb, today, webroutes

NOW = datetime(2026, 11, 5, 9, 30)
TODAY = NOW.date()


def _note(vault, folder, name, due, status="aktif", typ="teslim", due_time=""):
    p = vault / folder
    p.mkdir(parents=True, exist_ok=True)
    (p / f"{name}.md").write_text(
        f"---\ntype: {typ}\nstatus: {status}\nsource: manual\nsource_id: \"\"\ndue: {due}\n"
        + (f"due_time: \"{due_time}\"\n" if due_time else "") + "---\n# x\n", encoding="utf-8")


@pytest.fixture
def env(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(config, "VAULT", vault)
    monkeypatch.setattr(config, "accounts", lambda: {})
    monkeypatch.setattr(config, "IMPORTANT_CATEGORIES", ("okul", "finans"))
    con = maildb.connect(Path(config.DATA) / "mail.db")
    yield {"vault": vault, "con": con}
    con.close()


def _msg(con, i, cat, subj, labels, days_ago=1, account="main"):
    ms = int((NOW - timedelta(days=days_ago)).timestamp() * 1000)
    con.execute("INSERT INTO messages(account,id,date_ms,from_addr,from_name,subject,labels,category) VALUES(?,?,?,?,?,?,?,?)",
                (account, str(i), ms, "hoca@okul.edu", "Hoca", subj, json.dumps(labels), cat))
    con.commit()


def _fill(env):
    v = env["vault"]
    _note(v, "10-Dersler/X", "Vize", TODAY.isoformat(), typ="sinav", due_time="10:00")
    _note(v, "10-Dersler/X", "Ödev 3", (TODAY + timedelta(days=3)).isoformat())
    _note(v, "20-Projeler", "Uzak iş", (TODAY + timedelta(days=9)).isoformat())          # 7 günden uzak
    _note(v, "10-Dersler/X", "Bitmiş", TODAY.isoformat(), status="tamamlandi")             # bitmiş
    _note(v, "10-Dersler/X", "Geçmiş", (TODAY - timedelta(days=1)).isoformat())            # geçmiş
    _msg(env["con"], 1, "okul", "Vize yeri", ["INBOX", "UNREAD"])
    _msg(env["con"], 2, "okul", "Okunmuş", ["INBOX"])
    _msg(env["con"], 3, "reklam", "İndirim", ["INBOX", "UNREAD"])
    _msg(env["con"], 4, "finans", "Fatura", ["INBOX", "UNREAD"], days_ago=2)
    _msg(env["con"], 5, "okul", "Eski", ["INBOX", "UNREAD"], days_ago=30)
    approvals.add("takvim", "Toplantı ekle", "ayrıntı gizli", ttl_hours=100)
    approvals.add("komut", "Komut", "rm ...", ttl_hours=100)


def test_build_shape_and_sections(env):
    _fill(env)
    freshness._update(lambda d: d["sources"].update({"bank": {"last_ok": (datetime.now(timezone.utc) - timedelta(days=400)).astimezone().isoformat(), "total": 3}}))
    freshness.record_step("drive", ["drive-sync"], 1, "invalid_grant")
    t = today.build(NOW, vault=env["vault"])
    assert set(t) == {"generated", "date", "remote", "deadlines", "approvals", "mail", "stale_sources", "last_failed_step"}
    assert t["date"] == "2026-11-05" and t["remote"] is False
    assert [r["title"] for r in t["deadlines"]["today"]] == ["Vize"]
    assert [r["title"] for r in t["deadlines"]["week"]] == ["Vize", "Ödev 3"]         # bitmiş/geçmiş/uzak yok
    assert t["deadlines"]["week"][0]["days_left"] == 0 and t["deadlines"]["week"][1]["days_left"] == 3
    assert t["deadlines"]["today"][0]["time"] == "10:00" and t["deadlines"]["today"][0]["type"] == "sinav"
    assert t["approvals"]["count"] == 2 and len(t["approvals"]["oldest"]) == 2
    assert t["approvals"]["oldest"][0]["title"] == "Toplantı ekle" and t["approvals"]["oldest"][0]["detail"] == "ayrıntı gizli"
    assert t["mail"]["count"] == 2                                                    # yalnız önemli + okunmamış + son 7 gün
    assert {m["subject"] for m in t["mail"]["items"]} == {"Vize yeri", "Fatura"}
    assert t["mail"]["items"][0]["subject"] == "Vize yeri" and t["mail"]["by_category"] == {"okul": 1, "finans": 1}
    s = t["stale_sources"]
    assert s["total"] == 1 and s["items"][0]["source"] == "bank" and s["items"][0]["state"] == "bayat" and s["items"][0]["hint"]["tr"]
    assert t["last_failed_step"]["name"] == "drive" and t["last_failed_step"]["tail"] == "invalid_grant"
    json.dumps(t, ensure_ascii=False)                                                 # JSON'a çevrilebilir


def test_build_limits_stale_to_five_and_oldest_three_approvals(env):
    for i in range(6):
        approvals.add("takvim", f"onay {i}", "d", ttl_hours=100)
    rec = {k: {"last_ok": (datetime.now(timezone.utc) - timedelta(days=500 + i)).astimezone().isoformat(), "total": 1}
           for i, k in enumerate(["bank", "spotify", "linkedin", "x", "discord", "slack", "notion"])}
    freshness._update(lambda d: d["sources"].update(rec))
    t = today.build(NOW, vault=env["vault"])
    assert t["approvals"]["count"] == 6 and [r["title"] for r in t["approvals"]["oldest"]] == ["onay 0", "onay 1", "onay 2"]
    assert t["stale_sources"]["total"] == 7 and len(t["stale_sources"]["items"]) == 5


def test_build_empty_everything(env):
    t = today.build(NOW, vault=env["vault"])
    assert t["deadlines"] == {"today": [], "week": []} and t["approvals"] == {"count": 0, "oldest": []}
    assert t["mail"]["count"] == 0 and t["stale_sources"] == {"total": 0, "items": []} and t["last_failed_step"] is None
    assert "yok" in today.render(t)


def test_remote_view_strips_sensitive_fields(env):
    _fill(env)
    freshness.record_step("drive", ["drive-sync"], 1, "C:\\Users\\ayse\\gizli yol hatası")
    t = today.build(NOW, remote=True, vault=env["vault"])
    assert t["remote"] is True and t["mail"]["count"] == 2 and t["mail"]["items"] == []        # sayı var, konu/gönderen yok
    assert t["approvals"]["count"] == 0                                                         # telefon bilgisayar kartlarını görmez
    assert "tail" not in (t["last_failed_step"] or {}) and t["last_failed_step"]["name"] == "drive"
    blob = json.dumps(t, ensure_ascii=False)
    assert "Hoca" not in blob and "Vize yeri" not in blob and "ayrıntı gizli" not in blob and "gizli yol" not in blob
    approvals.add("takvim", "Telefon kartı", "d", source="telefon", ttl_hours=10)
    p = today.build(NOW, remote=True, vault=env["vault"])["approvals"]
    assert p["count"] == 1 and "detail" not in p["oldest"][0]


def test_render_is_single_screen_text(env):
    _fill(env)
    text = today.render(today.build(NOW, vault=env["vault"]))
    assert text.splitlines()[0] == "BUGÜN — 2026-11-05"
    for needle in ("Vize", "Ödev 3", "Bekleyen onay: 2", "Önemli okunmamış mail (7 gün): 2", "Eskiyen kaynak: 0", "Son başarısız günlük adım: yok"):
        assert needle in text
    assert len(text.splitlines()) < 40


def test_cli_json_and_text(env, capsys, monkeypatch):
    monkeypatch.setattr(today, "build", lambda **k: {"x": 1})
    assert today.cli(argparse.Namespace(json=True)) == 0
    assert json.loads(capsys.readouterr().out) == {"x": 1}


def test_cli_registered_in_main():
    from sb import __main__ as m
    src = Path(m.__file__).read_text(encoding="utf-8")
    assert 'add_parser("today"' in src and 'add_parser("freshness"' in src and 'add_parser("import-inbox"' in src


def test_today_is_read_only(env):
    _fill(env)
    before = {p: p.read_bytes() for p in Path(config.DATA).rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl")}
    today.build(NOW, vault=env["vault"])
    after = {p: p.read_bytes() for p in Path(config.DATA).rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl")}
    assert before == after and not freshness.path().exists()


# ------------------------------------------------------------------ API
def _call(path, remote=False):
    r = webroutes.find("GET", path)
    assert r is not None and r.local_only is False and r.method == "GET"
    code, body, ctype, _ = webroutes.call(r, webroutes.Ctx(method="GET", path=path, remote=remote))
    assert code == 200 and ctype.startswith("application/json")
    return json.loads(body)


def test_api_today_and_freshness(env):
    _fill(env)
    freshness._update(lambda d: d["sources"].update({"bank": {
        "last_ok": (datetime.now(timezone.utc) - timedelta(days=400)).astimezone().isoformat(), "total": 3,
        "file": {"name": "ozel-banka-ekstresi.csv"}, "last_fail": {"ts": "x", "msg": "yol"}}}))
    t = _call("/api/v2/today")
    assert set(t) >= {"deadlines", "approvals", "mail", "stale_sources", "last_failed_step"} and t["remote"] is False
    f = _call("/api/v2/freshness")
    assert f["sources"][0]["source"] == "bank" and f["sources"][0]["file"]["name"] == "ozel-banka-ekstresi.csv"
    assert set(f) == {"generated", "seeded", "sources", "counts", "stale"}
    tr = _call("/api/v2/today", remote=True)
    assert tr["remote"] is True and tr["mail"]["items"] == []
    fr = _call("/api/v2/freshness", remote=True)
    assert "file" not in fr["sources"][0] and "last_fail" not in fr["sources"][0]
    assert "ozel-banka" not in json.dumps(fr)
