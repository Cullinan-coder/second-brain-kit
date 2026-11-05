"""Kaynak tazeliği: manifest şeması, kayıt, tohum, durum, izlenen klasör (tanınan/tanınmayan/tekrar/yazılan), taşıma (silme yok)."""
import json
import os
import shutil
import sqlite3
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from sb import approvals, config, freshness, import_inbox, maildb, plugins

FX = Path(__file__).parent / "fixtures" / "connectors"
NOW = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc).astimezone()


@pytest.fixture
def env(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "00-Inbox").mkdir(parents=True)
    monkeypatch.setattr(config, "VAULT", vault)
    monkeypatch.setattr(config, "accounts", lambda: {})                      # gerçek accounts.yaml'a bağlı olma
    data = Path(config.DATA)
    con = maildb.connect(data / "mail.db")
    yield {"vault": vault, "data": data, "con": con, "inbox": vault / "00-Inbox" / "İçe aktar"}
    con.close()


def _ago(days):
    return (NOW - timedelta(days=days)).isoformat(timespec="seconds")


def _put(rec):
    d = {"version": 1, "seeded": "2026-11-01T00:00:00+03:00", "sources": rec, "hashes": {}, "steps": {}}
    freshness.path().write_text(json.dumps(d), encoding="utf-8")


# ------------------------------------------------------------------ manifest
def test_manifests_have_valid_refresh():
    assert plugins.validate() == []
    src = plugins.all("source")
    assert len(src) == 42
    for m in src:
        r = m["refresh"]
        assert r["mode"] in ("auto", "export", "manual") and r["every_days"] >= 1 and r["hint"]["tr"] and r["hint"]["en"]
    by = {m["id"]: m["refresh"] for m in src}
    assert by["whatsapp"]["mode"] == "export" and by["whatsapp"]["every_days"] == 30
    assert by["takeout"]["every_days"] == 60 and by["spotify"]["every_days"] == 180 and by["todoist"]["every_days"] == 7
    assert by["rss"]["mode"] == "manual" and by["clipboardline"]["mode"] == "auto"
    assert plugins.get("gmail", "module")["refresh"]["mode"] == "auto"


def test_refresh_schema_rejects_bad_and_defaults():
    m = dict(plugins.get("source:rss"))
    m["refresh"] = {"mode": "sometimes", "every_days": 0, "hint": {"tr": "x"}}
    errs = plugins.validate_manifest(m)
    assert any("refresh.mode" in e for e in errs) and any("every_days" in e for e in errs) and any("refresh.hint" in e for e in errs)
    m2 = dict(plugins.get("source:rss"))
    m2.pop("refresh")
    assert any("zorunlu" in e for e in plugins.validate_manifest(m2))
    r = plugins.refresh_of(m2)                                   # eksikse varsayılan
    assert r["mode"] == "manual" and r["every_days"] == 30 and r["hint"]["tr"] and r["hint"]["en"]


# ------------------------------------------------------------------ kayıt kancaları
def test_ingest_hook_records_and_dry_run_does_not(env):
    from sb.connectors import kindle
    kindle.run(FX / "My Clippings.txt", env["con"], dry_run=True)
    assert not freshness.path().exists()
    r = kindle.run(FX / "My Clippings.txt", env["con"])
    s = freshness.load()["sources"]["kindle"]
    assert s["last_read"] == r["okunan"] == 5 and s["last_new"] == 5 and s["total"] == 5 and s["last_ok"]
    kindle.run(FX / "My Clippings.txt", env["con"])               # ikinci: yeni 0, toplam aynı, zaman tazelenir
    assert freshness.load()["sources"]["kindle"]["total"] == 5


def test_messages_hook_and_takeout_key_mapping(env):
    from sb.connectors import whatsapp
    whatsapp.run(FX / "WhatsApp Chat with Deniz.txt", env["con"], me="Ben")
    assert freshness.load()["sources"]["whatsapp"]["total"] > 0
    freshness.record_ingest("activity", 3, 3)                     # Takeout alt kaynağı → takeout
    freshness.record_ingest("cargo", 3, 3)                        # manifestsiz: yazılmaz
    keys = set(freshness.load()["sources"])
    assert "takeout" in keys and "cargo" not in keys


def test_step_record_success_failure_and_last_failed(env, monkeypatch):
    freshness.record_step("drive", ["drive-sync"], 0, "ok", now=NOW - timedelta(days=3))
    freshness.record_step("drive", ["drive-sync"], 1, "invalid_grant", now=NOW)
    d = freshness.load()
    assert d["sources"]["drive"]["last_ok"].startswith("2026-11-02")      # başarısızlık son başarıyı silmez
    assert d["sources"]["drive"]["last_fail"]["msg"] == "invalid_grant"
    assert freshness.last_failed_step()["name"] == "drive"
    freshness.record_step("drive", ["drive-sync"], 0, "", now=NOW + timedelta(hours=1))
    assert freshness.last_failed_step() is None                           # sonradan başarılı oldu
    monkeypatch.setattr(config, "accounts", lambda: {"google": {"main": {"scopes": ["gmail"]}}, "imap": {"okul": {}}})
    assert freshness.step_keys(["mail-fetch", "main"]) == ["gmail"] and freshness.step_keys(["mail-fetch", "okul"]) == ["imap"]


def test_concurrent_records_do_not_lose_updates(env):
    import threading
    ts = [threading.Thread(target=freshness.record_ingest, args=("kindle", 1, 1)) for _ in range(12)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert freshness.load()["sources"]["kindle"]["total"] == 12


# ------------------------------------------------------------------ tohum
def _seed_db(con):
    old = "2026-10-20 10:00:00"
    con.execute("INSERT INTO items(source,id,date_ms,title,fetched_at) VALUES('spotify','a',1793489207872,'x',?)", (old,))
    con.execute("INSERT INTO items(source,id,date_ms,title,fetched_at) VALUES('spotify','b',1793489207873,'y','2026-11-01 08:00:00')")
    con.execute("INSERT INTO items(source,id,date_ms,title,fetched_at) VALUES('activity','a',1,'t',?)", (old,))
    con.execute("INSERT INTO items(source,id,date_ms,title,fetched_at) VALUES('cargo','a',1,'t',?)", (old,))
    con.execute("INSERT INTO messages(account,id,date_ms,subject,fetched_at) VALUES('whatsapp','1',1793460180000,'s','2026-10-31 18:00:00')")
    con.execute("INSERT INTO messages(account,id,date_ms,subject,fetched_at) VALUES('main','1',1793460180000,'s','2026-11-04 10:00:00')")
    con.commit()


def test_seed_from_history_and_idempotent(env, monkeypatch):
    monkeypatch.setattr(config, "accounts", lambda: {"google": {"main": {"scopes": ["gmail"]}}})
    _seed_db(env["con"])
    dry = freshness.seed(write=False)
    assert not freshness.path().exists() and set(dry["added"]) == {"spotify", "takeout", "whatsapp", "gmail"}
    r = freshness.seed()
    assert r["seeded"] and freshness.load()["seeded"]
    s = freshness.load()["sources"]
    assert s["spotify"]["total"] == 2 and s["spotify"]["via"] == "seed" and s["spotify"]["last_ok"].startswith("2026-11-01")
    assert "cargo" not in s
    assert freshness.seed()["seeded"] is False                    # ikinci çalıştırma: tohum yok
    freshness.record_ingest("spotify", 1, 1)                      # sonradan gelen gerçek içe aktarma tohumun üstüne yazar
    assert freshness.load()["sources"]["spotify"]["via"] == "ingest"


def test_seed_does_not_override_existing_and_waits_for_db(env, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path / "empty-data")           # arşiv henüz yok: işaretleme, sonra tohumlanabilsin
    assert freshness.seed() == {"seeded": False, "added": {}} and not freshness.path().exists()


# ------------------------------------------------------------------ durum
def test_status_states_thresholds_and_hint(env):
    _put({"whatsapp": {"last_ok": _ago(10), "total": 5},            # eşik 30 → taze
          "takeout": {"last_ok": _ago(90), "total": 5},             # eşik 60 → eskiyor (≤120)
          "spotify": {"last_ok": _ago(400), "total": 5},            # eşik 180 → bayat (>360)
          "todoist": {"last_ok": _ago(7.0), "total": 5}})           # eşik 7 → sınırda taze
    st = freshness.status(NOW)
    by = {s["source"]: s for s in st["sources"]}
    assert by["whatsapp"]["state"] == "taze" and by["takeout"]["state"] == "eskiyor" and by["spotify"]["state"] == "bayat"
    assert by["todoist"]["state"] == "taze" and by["spotify"]["threshold_days"] == 180 and by["spotify"]["age_days"] == 400
    assert by["takeout"]["hint"]["tr"] and by["takeout"]["hint"]["en"]
    assert st["counts"] == {"taze": 2, "eskiyor": 1, "bayat": 1, "hiç": 0} and st["stale"] == 2
    assert [s["source"] for s in st["sources"]][0] == "spotify"           # en bayat önce
    assert [s["source"] for s in freshness.stale_sources(1, NOW)] == ["spotify"]


def test_status_only_active_sources(env, monkeypatch):
    monkeypatch.setattr(config, "accounts", lambda: {})
    _put({})
    st = freshness.status(NOW)
    assert st["sources"] == []                                     # hiç kullanılmayan ihracat kaynakları görünmez, hesapsız otomatik de
    _put({"bank": {"last_ok": _ago(400)}})
    assert [s["source"] for s in freshness.status(NOW)["sources"]] == ["bank"]
    # otomatik kaynak: hesap bağlı + özellik açık + kayıt yok → "hiç"
    monkeypatch.setattr(config, "accounts", lambda: {"google": {"main": {"scopes": ["gmail"]}}})
    by = {s["source"]: s for s in freshness.status(NOW)["sources"]}
    assert by["gmail"]["state"] == "hiç" and by["gmail"]["age_days"] is None and by["calendar"]["state"] == "hiç"
    assert not ({"imap", "sms", "local_files", "projects"} & set(by))                    # hesap yok / yalnız kayıtla etkin
    # özelliği kapatılmış otomatik kaynak kaydı olsa da raporlanmaz
    from sb import features
    monkeypatch.setattr(features, "enabled", lambda k: k != "gmail")
    assert "gmail" not in {s["source"] for s in freshness.status(NOW)["sources"]}


def test_auto_grace_and_state_helper():
    assert freshness._state(1.4, 1, "auto") == "taze" and freshness._state(1.6, 1, "auto") == "eskiyor"
    assert freshness._state(2.6, 1, "auto") == "bayat" and freshness._state(None, 1, "auto") == "hiç"
    assert freshness._state(1.4, 1, "export") == "eskiyor"


def test_status_is_read_only_without_seed_write(env):
    _seed_db(env["con"])
    st = freshness.status(NOW)                                     # tohum bellekte
    assert {s["source"] for s in st["sources"]} >= {"spotify", "whatsapp"} and not freshness.path().exists()
    st2 = freshness.status(NOW, seed_write=True)
    assert freshness.path().exists() and freshness.load()["seeded"] and st2["seeded"]


def test_cli_status_json_and_seed(env, capsys):
    import argparse
    _seed_db(env["con"])
    assert freshness.cli(argparse.Namespace(action="status", json=True, dry_run=True)) == 0
    assert "sources" in json.loads(capsys.readouterr().out) and not freshness.path().exists()
    assert freshness.cli(argparse.Namespace(action="seed", json=False, dry_run=False)) == 0
    assert "Tohumlandı" in capsys.readouterr().out and freshness.load()["seeded"]


# ------------------------------------------------------------------ izlenen klasör
def _drop(env, name, src=None, content=None):
    env["inbox"].mkdir(parents=True, exist_ok=True)
    p = env["inbox"] / name
    if src:
        shutil.copy(FX / src, p)
    else:
        p.write_bytes(content if isinstance(content, bytes) else (content or "").encode())
    old = time.time() - 600
    os.utime(p, (old, old))
    return p


def _scan(env, **kw):
    return import_inbox.scan(env["vault"], env["con"], settle=5, probe=0, **kw)


def test_inbox_recognized_file_imported_and_moved_not_deleted(env):
    p = _drop(env, "My Clippings.txt", "My Clippings.txt")
    gi = env["vault"] / ".gitignore"
    res = _scan(env)
    assert [r["action"] for r in res] == ["imported"] and res[0]["source"] == "kindle" and res[0]["new"] == 5
    assert not p.exists()
    moved = list((env["inbox"] / "_işlendi").glob("*/My Clippings.txt"))
    assert len(moved) == 1 and moved[0].read_bytes() == (FX / "My Clippings.txt").read_bytes()      # silme yok: bayt bayt aynı
    assert "00-Inbox/İçe aktar/" in gi.read_text(encoding="utf-8").splitlines()
    s = freshness.load()["sources"]["kindle"]
    assert s["file"]["name"] == "My Clippings.txt" and s["file"]["read"] == 5 and s["total"] == 5
    assert env["con"].execute("SELECT COUNT(*) FROM items WHERE source='kindle'").fetchone()[0] == 5


def test_inbox_duplicate_not_imported_twice(env):
    _drop(env, "My Clippings.txt", "My Clippings.txt")
    _scan(env)
    _drop(env, "Clippings kopya.txt", "My Clippings.txt")                       # aynı içerik, farklı ad
    res = _scan(env)
    assert res[0]["action"] == "duplicate" and "zaten alınmıştı" in res[0]["message"]
    assert env["con"].execute("SELECT COUNT(*) FROM items WHERE source='kindle'").fetchone()[0] == 5
    assert freshness.load()["sources"]["kindle"]["total"] == 5
    assert len(list((env["inbox"] / "_işlendi").glob("*/*"))) == 2              # ikisi de saklandı


def test_inbox_unrecognized_moved_with_approval_card_and_assign(env):
    p = _drop(env, "gizemli.dat", content="merhaba dünya\n")
    res = _scan(env)
    assert res[0]["action"] == "unrecognized" and not p.exists()
    assert (env["inbox"] / "_tanınmadı" / "gizemli.dat").read_text(encoding="utf-8") == "merhaba dünya\n"
    cards = approvals.records(origin="içe-aktar")
    assert len(cards) == 1 and "kaynağını seç" in cards[0]["title"] and cards[0]["kind"] == "kaynak-sec"
    assert "kindle" in cards[0]["extra"]["kaynaklar"]
    # kullanıcı kaynağı seçer (içerik bir Kindle kırpma dosyası olsaydı): atama
    shutil.copy(FX / "My Clippings.txt", env["inbox"] / "_tanınmadı" / "gizemli.dat")
    r = import_inbox.assign("gizemli.dat", "kindle", env["vault"], env["con"])
    assert r["new"] == 5 and not (env["inbox"] / "_tanınmadı" / "gizemli.dat").exists()
    assert list((env["inbox"] / "_işlendi").glob("*/gizemli.dat"))
    with pytest.raises(FileNotFoundError):
        import_inbox.assign("yok.dat", "kindle", env["vault"], env["con"])
    shutil.copy(FX / "My Clippings.txt", env["inbox"] / "_tanınmadı" / "x.dat")
    with pytest.raises(ValueError):
        import_inbox.assign("x.dat", "yok", env["vault"], env["con"])


def test_inbox_unrecognized_card_not_duplicated(env):
    _drop(env, "a.dat", content="aynı içerik")
    _scan(env)
    _drop(env, "b.dat", content="aynı içerik")
    _scan(env)
    assert len(approvals.records(origin="içe-aktar")) == 1


def test_inbox_file_being_written_is_left_alone(env):
    p = env["inbox"] / "indiriliyor.zip"
    env["inbox"].mkdir(parents=True)
    p.write_bytes(b"PK")                                                           # az önce yazıldı → bekle
    res = import_inbox.scan(env["vault"], env["con"], settle=60, probe=0)
    assert res[0]["action"] == "waiting" and p.exists()
    q = _drop(env, "x.crdownload", content="abc")                                  # geçici uzantı
    assert import_inbox.is_settled(q, 0, 0) is False
    # boyut ölçümler arasında değişiyorsa kararlı değil
    big = _drop(env, "buyuyor.bin", content=b"a" * 10)

    def grow(_s):
        with open(big, "ab") as f:
            f.write(b"b" * 10)
    assert import_inbox.is_settled(big, 5, 0.01, sleep=grow) is False
    os.utime(big, (time.time() - 600,) * 2)
    assert import_inbox.is_settled(big, 5, 0.01, sleep=lambda s: None) is True
    assert freshness.load()["hashes"] == {}                                        # bekleyenler işlenmedi


def test_inbox_zip_bomb_rejected(env, monkeypatch):
    from sb import content
    monkeypatch.setattr(content, "MAX_ZIP_FILES", 3)
    p = env["inbox"] / "bomba.zip"
    env["inbox"].mkdir(parents=True)
    with zipfile.ZipFile(p, "w") as z:
        for i in range(6):
            z.writestr(f"{i}.txt", "x")
    os.utime(p, (time.time() - 600,) * 2)
    res = _scan(env)
    assert res[0]["action"] == "rejected" and "zip" in res[0]["message"]
    assert (env["inbox"] / "_tanınmadı" / "bomba.zip").exists()
    assert approvals.records(origin="içe-aktar")


def test_inbox_oversize_rejected(env, monkeypatch):
    monkeypatch.setattr(import_inbox, "MAX_BYTES", 10)
    _drop(env, "iri.txt", content="x" * 50)
    assert _scan(env)[0]["action"] == "rejected"
    assert (env["inbox"] / "_tanınmadı" / "iri.txt").exists()


def test_inbox_failed_import_goes_to_unrecognized(env, monkeypatch):
    from sb import connectors
    _drop(env, "My Clippings.txt", "My Clippings.txt")

    def boom(*a, **k):
        raise ValueError("bozuk")
    monkeypatch.setitem(connectors.REGISTRY, "kindle", boom)
    res = _scan(env)
    assert res[0]["action"] == "failed" and (env["inbox"] / "_tanınmadı" / "My Clippings.txt").exists()
    assert freshness.load()["hashes"] == {}                                        # başarısız dosya "alındı" sayılmaz


def test_inbox_directory_and_internal_folders_ignored(env):
    d = env["inbox"] / "Spotify Extended"
    d.mkdir(parents=True)
    shutil.copy(FX / "StreamingHistory0.json", d / "StreamingHistory0.json")
    (env["inbox"] / "_işlendi").mkdir()
    (env["inbox"] / ".gizli").write_text("x")
    old = time.time() - 600
    os.utime(d / "StreamingHistory0.json", (old, old))
    os.utime(d, (old, old))
    res = _scan(env)
    assert [(r["name"], r["action"], r.get("source")) for r in res] == [("Spotify Extended", "imported", "spotify")]
    assert (env["inbox"] / "_işlendi").is_dir() and (env["inbox"] / ".gizli").exists()


def test_inbox_missing_folder_is_not_created_by_loop_scan(env):
    assert import_inbox.scan(env["vault"], env["con"], create=False) == [] and not env["inbox"].exists()
    assert import_inbox.scan(env["vault"], env["con"]) == [] and env["inbox"].is_dir()      # CLI/günlük çalışma oluşturur


def test_runner_step_and_digest_section(env, monkeypatch):
    from sb import runner
    assert any(a == ["import-inbox"] for _n, a, _t in runner.DAILY_REST)
    from sb import features
    assert features.step_enabled(["import-inbox"])
    _put({"bank": {"last_ok": _ago(400), "total": 3}})
    monkeypatch.setattr(freshness, "_now", lambda: NOW)
    from sb import digest
    text = digest.build_daily(env["con"], env["vault"], NOW.date(), [], None, now=NOW.replace(tzinfo=None))
    assert "Eskiyen kaynaklar" in text and "bayat" in text


def test_doctor_check_reports_stale(env):
    from sb import doctor
    _put({"bank": {"last_ok": _ago(400), "total": 3}})
    st, label, hint = doctor.freshness_check()
    assert st == doctor.WARN and "1 bayat" in label and "sb today" in hint
    _put({"bank": {"last_ok": _ago(1), "total": 3}})
    assert doctor.freshness_check()[0] == doctor.OK
