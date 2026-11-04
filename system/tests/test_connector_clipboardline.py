"""ClipBoardLine bağlayıcısı: örnek library.json (apps/clipboardline/windows/lib/model.cjs biçimi), sır süzgeci, tekrar önleme, salt okunurluk."""
import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

import pytest

from sb import brain, maildb
from sb.connectors import REGISTRY, clipboardline

FIX = Path(__file__).parent / "fixtures" / "connectors" / "clipboardline_library.json"
SECRETS = ["sk-proj-abcdefghijklmnopqrstuvwx1234", "TR33 0006 1005 1978 6457 8413 26", "4242 4242 4242 4242", "10000000146", "hunter2parola"]


@pytest.fixture
def data(tmp_path):
    d = tmp_path / "ClipBoardLine"
    d.mkdir()
    shutil.copy(FIX, d / "library.json")
    (d / "media").mkdir()
    return d


@pytest.fixture
def con(tmp_path):
    c = maildb.connect(tmp_path / "mail.db")
    yield c
    c.close()


def rows(con):
    return {r[0]: r for r in con.execute("SELECT id, kind, title, url, body, meta, date_ms FROM items WHERE source = 'clipboardline'")}


def test_parse_everything_into_the_brain(data, con):
    r = clipboardline.run(data, con)
    # 11 kayıt: 5 sır, 1 çöp, 1 tanınmayan tür, 1 tekrar → 3 yeni
    assert r["yeni"] == 3 and r["tekrar"] == 1 and r["atlanan_sir"] == 5 and r["okunan"] == 4
    got = rows(con)
    assert set(got) == {"a0000000-0000-4000-8000-000000000001", "a0000000-0000-4000-8000-000000000002", "a0000000-0000-4000-8000-000000000003"}
    text = got["a0000000-0000-4000-8000-000000000001"]
    assert text[1] == "text" and text[2].startswith("Toplantı notu") and text[6] == 1793700000000
    assert "Etiketler: toplanti" in text[4] and "Klasör: İş" in text[4]
    assert json.loads(text[5])["pinned"] is True
    link = got["a0000000-0000-4000-8000-000000000002"]
    assert link[1] == "link" and link[2] == "Yapay zekaya giriş" and link[3] == "https://example.com/makale/yapay-zeka"
    assert "Not: sonra oku" in link[4] and "Ayşe" in link[4]
    img = got["a0000000-0000-4000-8000-000000000003"]
    assert img[1] == "image" and "Elektrik faturası son ödeme tarihi 20 Kasım" in img[4]
    assert "Klasör: İş / Fatura" in img[4] and "Etiketler: makbuz" in img[4]               # iç içe klasör yolu


def test_secrets_are_skipped_and_never_written(data, con):
    clipboardline.run(data, con)
    dump = "\n".join(str(x) for x in con.execute("SELECT * FROM items"))
    fts = "\n".join(str(x) for x in con.execute("SELECT title, body FROM items_fts"))
    for s in SECRETS:
        assert s not in dump and s not in fts, s
    assert "zebra-desen" not in dump                                                       # çöpteki kayıt alınmadı


def test_idempotent_and_content_dedupe(data, con):
    clipboardline.run(data, con)
    n = con.execute("SELECT count(*) FROM items").fetchone()[0]
    r = clipboardline.run(data, con)
    assert r["yeni"] == 0 and r["guncellenen"] == 0 and con.execute("SELECT count(*) FROM items").fetchone()[0] == n
    # aynı metin, farklı kimlik → eklenmez (tekrar sayılır); ilk kayıt silinse bile yeni kopya içerik karmasıyla bilinir
    assert r["tekrar"] == 1


def test_changed_tags_and_ocr_update_record_and_fts(data, con):
    clipboardline.run(data, con)
    lib = json.loads((data / "library.json").read_text(encoding="utf-8"))
    lib["items"][0]["tags"].append("yenietiket")
    lib["items"][2]["ocrText"] += " ve kalıcı zeytin"
    (data / "library.json").write_text(json.dumps(lib), encoding="utf-8")
    r = clipboardline.run(data, con)
    assert r["yeni"] == 0 and r["guncellenen"] == 2
    hit = {x[0] for x in con.execute("SELECT i.id FROM items_fts f JOIN items i ON i.rowid = f.rowid WHERE items_fts MATCH 'yenietiket OR zeytin'")}
    assert hit == {"a0000000-0000-4000-8000-000000000001", "a0000000-0000-4000-8000-000000000003"}


def test_item_becoming_secret_or_trashed_is_removed(data, con):
    clipboardline.run(data, con)
    lib = json.loads((data / "library.json").read_text(encoding="utf-8"))
    lib["items"][1]["note"] = "şifre: 482913"                                              # sonradan sır girdi
    lib["items"][2]["trashedAt"] = 1793709999999                                           # sonradan çöpe atıldı
    (data / "library.json").write_text(json.dumps(lib), encoding="utf-8")
    r = clipboardline.run(data, con)
    assert r["silinmis"] == 2 and set(rows(con)) == {"a0000000-0000-4000-8000-000000000001"}


def test_library_is_read_only(data, con):
    f = data / "library.json"
    before = (hashlib.sha256(f.read_bytes()).hexdigest(), f.stat().st_mtime_ns, sorted(os.listdir(data)))
    os.chmod(f, stat.S_IREAD)
    try:
        clipboardline.run(data, con)
        clipboardline.run(f, con)                                                          # dosya yolu da kabul edilir
    finally:
        os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
    assert (hashlib.sha256(f.read_bytes()).hexdigest(), f.stat().st_mtime_ns, sorted(os.listdir(data))) == before


def test_reads_a_copy_not_the_original(data, con, monkeypatch):
    opened = []
    real = Path.read_text

    def spy(self, *a, **k):
        opened.append(str(self))
        return real(self, *a, **k)
    monkeypatch.setattr(Path, "read_text", spy)
    clipboardline.run(data, con)
    assert opened and all(str(data) not in p for p in opened)                              # orijinal değil, geçici kopya okundu


def test_locked_file_retries_then_reports(data, con, monkeypatch):
    monkeypatch.setattr(clipboardline.time, "sleep", lambda s: None)
    calls = []

    def locked(src, dst):
        calls.append(1)
        raise PermissionError("kullanımda")
    monkeypatch.setattr(clipboardline.shutil, "copyfile", locked)
    r = clipboardline.run(data, con)
    assert r["locked"] and "sonraki turda" in r["not"] and len(calls) == 3 and r["yeni"] == 0


def test_missing_corrupt_and_empty(tmp_path, con):
    assert "library.json yok" in clipboardline.run(tmp_path / "yok", con)["not"]
    d = tmp_path / "x"
    d.mkdir()
    (d / "library.json").write_text("{bozuk", encoding="utf-8")
    assert clipboardline.run(d, con)["error"]
    (d / "library.json").write_text(json.dumps({"schema": 1, "items": [], "folders": []}), encoding="utf-8")
    r = clipboardline.run(d, con)
    assert r["yeni"] == 0 and "toplama kapalı" in r["not"]


def test_dry_run_writes_nothing(data, con):
    r = clipboardline.run(data, con, dry_run=True)
    assert r["yeni"] == 3 and con.execute("SELECT count(*) FROM items").fetchone()[0] == 0


def test_registered_and_visible_to_brain_index(data, con):
    assert REGISTRY["clipboardline"] is clipboardline.run
    clipboardline.run(data, con)
    docs = list(brain.iter_items(con))
    assert any("Elektrik faturası" in str(d) for d in docs)                                # beyin dizini items'ı okuyor
