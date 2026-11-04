"""Nashi bağlayıcısı: örnek library.json (apps/nashi/windows/Nashi.Core/LibraryStore.cs biçimi), içerik çıkarma, sır süzgeci, salt okunurluk."""
import hashlib
import json
import os
import stat
from pathlib import Path

import pytest

from sb import maildb
from sb.connectors import REGISTRY, nashi

FIX = Path(__file__).parent / "fixtures" / "connectors" / "nashi_library.json"


@pytest.fixture
def data(tmp_path):
    files = tmp_path / "exports"
    files.mkdir()
    (files / "notlar.txt").write_text("Proje notları: lansman 12 Aralık, bütçe onaylandı.", encoding="utf-8")
    (files / "rapor.pdf").write_bytes(b"%PDF-sahte")
    (files / "foto.png").write_bytes(b"\x89PNG sahte")
    (files / "sifreler.txt").write_text("banka şifre: 482913 ve OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwx1234", encoding="utf-8")
    # silinmis.docx bilerek yok
    d = tmp_path / "Nashi"
    d.mkdir()
    (d / "library.json").write_text(FIX.read_text(encoding="utf-8").replace("{TMP}", str(files).replace("\\", "\\\\")), encoding="utf-8")
    return d


@pytest.fixture(autouse=True)
def fake_extract(monkeypatch):
    """pdf/görsel çıkarımını sahtele (gerçek pypdf/OCR yok); düz metin gerçek hat (content.extract)."""
    from sb import actions, content
    calls = []
    real = content.extract
    monkeypatch.setattr(content, "extract", lambda p: calls.append(("doc", p.name)) or ("PDF içeriği: sözleşme bedeli 5000 TL" if p.suffix == ".pdf" else real(p)))
    monkeypatch.setattr(actions, "ocr", lambda b: calls.append(("ocr", len(b))) or "Görselde yazan: toplantı odası B")
    return calls


@pytest.fixture
def con(tmp_path):
    c = maildb.connect(tmp_path / "mail.db")
    yield c
    c.close()


def rows(con):
    return {r[2]: r for r in con.execute("SELECT id, kind, title, body, meta, date_ms FROM items WHERE source = 'nashi'")}


def test_each_exported_file_becomes_a_record_with_content(data, con, fake_extract):
    r = nashi.run(data, con)
    assert r["yeni"] == 5 and r["icerikli"] == 3 and r["atlanan_sir"] == 1 and r["dosya_yok"] == 1
    got = rows(con)
    assert set(got) == {"rapor.pdf", "notlar.txt", "foto.png", "sifreler.txt", "silinmis.docx"}
    pdf = got["rapor.pdf"]
    assert pdf[1] == "pdf" and "Nashi · Convert to PDF · rapor.pdf" in pdf[3] and "sözleşme bedeli 5000 TL" in pdf[3]
    assert pdf[5] is not None and pdf[5] > 1_700_000_000_000
    assert "lansman 12 Aralık" in got["notlar.txt"][3]                                     # gerçek düz metin hattı
    assert "toplantı odası B" in got["foto.png"][3] and ("ocr", 10) in fake_extract       # görsel OCR
    meta = json.loads(got["silinmis.docx"][4])
    assert meta["exists"] is False and meta["action"] == "Clipboard import" and "Nashi · Clipboard import" in got["silinmis.docx"][3]


def test_secret_content_not_added_but_record_stays(data, con):
    nashi.run(data, con)
    dump = "\n".join(str(x) for x in con.execute("SELECT * FROM items")) + "\n".join(str(x) for x in con.execute("SELECT * FROM items_fts"))
    assert "482913" not in dump and "sk-proj-abcdefghijklmnopqrstuvwx1234" not in dump
    sec = rows(con)["sifreler.txt"]
    assert json.loads(sec[4])["secret"] is True and "sifreler.txt" in sec[3]


def test_idempotent_no_reextraction(data, con, fake_extract):
    nashi.run(data, con)
    n_calls = len(fake_extract)
    r = nashi.run(data, con)
    assert r["yeni"] == 0 and r["guncellenen"] == 0 and len(fake_extract) == n_calls and "yeni ya da değişen" in r["not"]


def test_changed_file_is_updated_and_searchable(data, con):
    nashi.run(data, con)
    f = Path(json.loads((data / "library.json").read_text(encoding="utf-8"))["Entries"][1]["Paths"][0])
    f.write_text("Yeni sürüm: kıvrımlı zürafa projesi", encoding="utf-8")
    r = nashi.run(data, con)
    assert r["guncellenen"] == 1 and r["yeni"] == 0
    assert con.execute("SELECT count(*) FROM items_fts WHERE items_fts MATCH 'zürafa'").fetchone()[0] == 1


def test_read_only_and_case_insensitive_keys(data, con):
    f = data / "library.json"
    lib = json.loads(f.read_text(encoding="utf-8"))
    lower = {"entries": [{"id": e["Id"], "created": e["Created"], "action": e["Action"], "paths": e["Paths"]} for e in lib["Entries"]]}
    f.write_text(json.dumps(lower), encoding="utf-8")
    before = (hashlib.sha256(f.read_bytes()).hexdigest(), f.stat().st_mtime_ns, sorted(os.listdir(data)))
    os.chmod(f, stat.S_IREAD)
    try:
        assert nashi.run(data, con)["yeni"] == 5
    finally:
        os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
    assert (hashlib.sha256(f.read_bytes()).hexdigest(), f.stat().st_mtime_ns, sorted(os.listdir(data))) == before


def test_locked_missing_corrupt(data, con, monkeypatch, tmp_path):
    monkeypatch.setattr(nashi.time, "sleep", lambda s: None)
    real = nashi.shutil.copyfile
    monkeypatch.setattr(nashi.shutil, "copyfile", lambda a, b: (_ for _ in ()).throw(PermissionError("kullanımda")))
    assert nashi.run(data, con)["locked"]
    monkeypatch.setattr(nashi.shutil, "copyfile", real)
    assert "library.json yok" in nashi.run(tmp_path / "yok", con)["not"]
    (data / "library.json").write_text("[bozuk", encoding="utf-8")
    assert nashi.run(data, con)["error"]


def test_dry_run_and_registry(data, con):
    assert nashi.run(data, con, dry_run=True)["yeni"] == 5 and con.execute("SELECT count(*) FROM items").fetchone()[0] == 0
    assert REGISTRY["nashi"] is nashi.run


def test_extraction_budget_per_run(data, con, monkeypatch):
    monkeypatch.setattr(nashi, "EXTRACT_PER_RUN", 1)
    r = nashi.run(data, con)
    assert r["icerikli"] == 1 and r["yeni"] == 5                                           # kalanların kaydı alınır, içerik sonraki turda
    done = 1
    for _ in range(5):
        r2 = nashi.run(data, con)
        assert r2["yeni"] == 0
        done += r2["icerikli"] + r2["atlanan_sir"]
    assert done == 4                                                                       # dört dosyanın dördü de sonunda işlendi
    assert nashi.run(data, con)["guncellenen"] == 0
