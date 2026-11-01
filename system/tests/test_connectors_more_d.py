"""Paket D: görev, okuma, konum, banka, öğrenme, ekran süresi içe aktarıcıları."""
import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from sb import maildb, tasks, vault_ops
from sb.connectors import bank, learning, places, reading, screentime, tasks_import
from sb.notes import split_note

FX = Path(__file__).parent / "fixtures" / "connectors"


@pytest.fixture
def con(tmp_path):
    c = maildb.connect(tmp_path / "mail.db")
    yield c
    c.close()


@pytest.fixture
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    v.mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    return v


def count(con, source):
    return con.execute("SELECT COUNT(*) FROM items WHERE source = ?", (source,)).fetchone()[0]


def twice(run, path, con):
    return run(path, con), run(path, con)


# ---- görevler
@pytest.mark.parametrize("name,src,titles", [
    ("d_todoist.csv", "todoist", {"Fatura ödemesini kontrol et", "Kitap iade et"}),
    ("d_ticktick.csv", "ticktick", {"Rapor taslağı"}),
    ("d_jira.csv", "jira", {"DEMO-12 Giriş hatası"}),
    ("d_linear.csv", "linear", {"ENG-7 Yeni panel"}),
    ("d_mstodo.json", "mstodo", {"Market alışverişi"}),
    ("d_trello.json", "trello", {"Sunum hazırla"}),
])
def test_gorev_acik_ve_tekrarsiz(vault, con, name, src, titles):
    rows = tasks_import.parse(FX / name)
    assert {r["title"] for r in rows} == titles and {r["src"] for r in rows} == {src}
    a = tasks_import.run(FX / name, con, me="Ayşe")
    assert a["yeni"] == len(titles)
    assert tasks_import.run(FX / name, con, me="Ayşe")["yeni"] == 0
    files = list((vault / tasks.FOLDER).glob("*.md"))
    assert len(files) == len(titles)
    fm = split_note(files[0].read_text(encoding="utf-8"))[0]
    assert fm["type"] == "gorev" and fm["owner"] == "Ayşe" and fm["source_id"].startswith(f"import:{src}:")


def test_gorev_ayrintilar_ve_dry_run(vault, con):
    assert tasks_import.run(FX / "d_trello.json", con, dry_run=True)["yeni"] == 1
    assert not (vault / tasks.FOLDER).exists()
    tasks_import.run(FX / "d_trello.json", con)
    p = next((vault / tasks.FOLDER).glob("*.md"))
    fm, body = split_note(p.read_text(encoding="utf-8"))
    assert fm["project"] == "Demo Pano" and str(fm["due"]) == "2026-11-08"
    assert "- [ ] Taslak" in body and "Görseller" not in body


# ---- okuma
def test_pocket_html_csv_raindrop(con):
    rows = reading.parse_pocket(FX / "d_ril_export.html")
    assert [r["title"] for r in rows] == ["Makale & Bir", "Makale İki"] and rows[0]["meta"]["tags"] == ["python", "ml"]
    assert rows[0]["date_ms"] == 1761900000000
    a, b = twice(reading.run_pocket, FX / "d_ril_export.html", con)
    assert (a["yeni"], b["yeni"], count(con, "pocket")) == (2, 0, 2)
    a, b = twice(reading.run_raindrop, FX / "d_raindrop.csv", con)
    assert (a["yeni"], b["yeni"]) == (2, 0)
    r = reading.parse_raindrop(FX / "d_raindrop.csv")[0]
    assert r["meta"]["tags"] == ["a", "b"] and r["meta"]["folder"] == "Okuma" and r["kind"] == "link"


# ---- konum
def test_foto_yan_dosyasi(con):
    r = places.parse_photos(FX / "d_photo.jpg.json")[0]
    assert r["title"] == "IMG_0001.jpg" and r["date_ms"] == 1761900000000 and r["meta"]["lat"] == 41.0082
    a, b = twice(places.run_photos, FX / "d_photo.jpg.json", con)
    assert (a["yeni"], b["yeni"]) == (1, 0)
    assert places.parse_photos(FX / "d_timeline.json") == []


def test_haritalar_uc_biçim(con):
    sem = places.parse_maps(FX / "d_maps_semantic.json")
    assert [r["kind"] for r in sem] == ["ziyaret", "hareket"]
    assert sem[0]["title"] == "Demo Kafe" and sem[0]["meta"]["minutes"] == 90 and sem[0]["meta"]["lat"] == 41.0082
    tl = places.parse_maps(FX / "d_timeline.json")
    assert [r["kind"] for r in tl] == ["ziyaret", "hareket"] and tl[0]["meta"]["lat"] == 41.01 and tl[1]["meta"]["meters"] == 4200
    rec = places.parse_maps(FX / "d_records.json")
    assert len(rec) == 1 and rec[0]["meta"]["points"] == 2
    a, b = twice(places.run_maps, FX / "d_maps_semantic.json", con)
    assert (a["yeni"], b["yeni"], count(con, "gmaps")) == (2, 0, 2)


# ---- banka
def test_banka_sayi_ve_basliklar(con):
    rows = bank.parse(FX / "d_bank.csv")
    assert [r["meta"]["amount"] for r in rows] == [-1234.56, 12500.0, -45.5, -45.5]
    assert len({r["id"] for r in rows}) == 4  # aynı gün aynı tutarlı iki satır korunur
    rows = bank.parse(FX / "d_bank_borc.csv")
    assert [r["meta"]["amount"] for r in rows] == [-250.75, 100.0] and rows[0]["kind"] == "islem"
    assert bank.num("1.234,56") == 1234.56 and bank.num("-1,234.56") == -1234.56 and bank.num("(50,00)") == -50.0


def test_banka_numara_saklanmaz(con):
    a, b = twice(bank.run, FX / "d_bank.csv", con)
    assert (a["yeni"], b["yeni"]) == (4, 0)
    dump = json.dumps([list(r) for r in con.execute("SELECT * FROM items WHERE source = 'bank'")], ensure_ascii=False)
    for secret in ("12345678", "4111", "TR3300", "9876543210", "19786457841326"):
        assert secret not in dump
    assert "IBAN gizlendi" in dump


# ---- öğrenme
def test_ogrenme(con):
    rows = learning.parse(FX / "d_coursera.csv", "coursera")
    assert rows[0]["meta"] == {"progress": 100.0, "completed": True} and rows[1]["meta"]["progress"] == 45.5
    assert rows[0]["date_ms"] and rows[1]["date_ms"] is None
    a, b = twice(learning.run_coursera, FX / "d_coursera.csv", con)
    assert (a["yeni"], b["yeni"]) == (2, 0)
    rows = learning.parse(FX / "d_udemy.json", "udemy")
    assert [r["meta"]["progress"] for r in rows] == [80.0, 100.0] and rows[1]["date_ms"]
    assert learning.run_udemy(FX / "d_udemy.json", con)["yeni"] == 2


# ---- ekran süresi
def test_ekran_suresi(con):
    assert screentime.seconds("01:30:00") == 5400 and screentime.seconds("45 dk") == 2700
    assert screentime.seconds("1h 30m") == 5400 and screentime.seconds("1800") == 1800
    rows = screentime.parse(FX / "d_screentime.csv")
    assert [(r["title"], r["meta"]["seconds"]) for r in rows] == [("Code", 5400), ("Chrome", 2700), ("Spotify", 1800)]
    a, b = twice(screentime.run, FX / "d_screentime.csv", con)
    assert (a["yeni"], b["yeni"], count(con, "screentime")) == (3, 0, 3)
