"""Beyin analizleri (madde 124-137): geçici kasa + geçici brain.db/mail.db + sahte gömmeler."""
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from sb import analysis, brain, content, maildb
from sb.notes import dump_note

TODAY = date(2026, 10, 31)


def mk(vault: Path, rel: str, fm: dict | None = None, body: str = "", **kw):
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    f = {"type": "kaynak", "status": "aktif", "tags": ["x"], "created": TODAY, "updated": TODAY}
    f.update(fm or {})
    p.write_text(dump_note(f, body or f"# {p.stem}\n"), encoding="utf-8")
    return p


def notes(vault):
    return analysis.load_notes(vault)


def add_doc(con, doc_id, kind, title, text, date_ms=None, ref=None, vec=None):
    con.execute("INSERT INTO docs(doc_id, kind, title, date_ms, ref, sha) VALUES (?,?,?,?,?,?)", (doc_id, kind, title, date_ms, ref or doc_id, "s"))
    cur = con.execute("INSERT INTO chunks(doc_id, ord, text) VALUES (?,?,?)", (doc_id, 0, text))
    if vec is not None:
        con.execute("INSERT INTO vecs(chunk_id, model, vec) VALUES (?,?,?)", (cur.lastrowid, "m", np.asarray(vec, dtype=np.float32).tobytes()))
    con.commit()


def ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day).timestamp() * 1000)


def test_classify_rules():
    c = analysis.classify_text
    assert c("Fatura_2026.pdf", "")[0] == "fatura"
    assert c("Ayşe CV.docx", "")[0] == "cv"
    assert c("x.pptx", "")[0] == "sunum"
    assert c("belge.pdf", "Sayın Yetkili, konu: izin. İlgi: dilekçe. Dekanlığı")[0] == "resmi yazı"
    assert c("hizmet.pdf", "Taraflar işbu sözleşme ile yükümlülük altına girer")[0] == "sözleşme"
    assert c("notlar.txt", "alışveriş listesi")[0] == "diğer"
    assert c("Odev3.pdf", "")[0] == "ödev/teslim"


def test_classify_docs_writes_table(tmp_path):
    con = brain.connect(tmp_path / "b.db")
    m = maildb.connect(tmp_path / "m.db")
    m.executescript(content.SCHEMA)
    m.execute("INSERT INTO file_text(path, mtime, chars, text) VALUES (?,?,?,?)", ("C:/x/Fatura 1.pdf", 1.7e9, 80, "fatura no 12 toplam tutar 100 TL " * 5))
    m.commit()
    add_doc(con, "note:40-Kaynaklar/Drive/Drive – Rapor.md", "note", "Drive – Rapor", "özet yöntem sonuç bulgular", 1, "40-Kaynaklar/Drive/Drive – Rapor.md")
    msg = analysis.write_classify(vault=tmp_path / "v", con=con, mcon=m)
    got = dict(con.execute("SELECT doc_id, cls FROM doc_class").fetchall())
    assert got["file:C:/x/Fatura 1.pdf"] == "fatura" and got["note:40-Kaynaklar/Drive/Drive – Rapor.md"] == "rapor"
    assert "2 belge" in msg and (tmp_path / "v/40-Kaynaklar/Analiz/Belge sınıfları.md").exists()


def test_duplicates_by_sha_and_embedding(tmp_path):
    con = brain.connect(tmp_path / "b.db")
    m = maildb.connect(tmp_path / "m.db")
    m.executescript(content.SCHEMA)
    body = "Bu bir sözleşme metnidir. " * 20
    for path, txt in [("C:/a/s.pdf", body), ("C:/b/s kopya.pdf", body.upper().replace("  ", " ")), ("C:/c/farkli.pdf", "bambaşka içerik " * 30)]:
        m.execute("INSERT INTO file_text(path, mtime, chars, text) VALUES (?,?,?,?)", (path, 1.0, len(txt), txt))
    m.commit()
    add_doc(con, "file:C:/c/farkli.pdf", "file", "farkli.pdf", "x", ref="C:/c/farkli.pdf", vec=[1, 0, 0])
    add_doc(con, "file:C:/d/f2.pdf", "file", "f2.pdf", "y", ref="C:/d/f2.pdf", vec=[1, 0.01, 0])
    add_doc(con, "file:C:/e/baska.pdf", "file", "baska.pdf", "z", ref="C:/e/baska.pdf", vec=[0, 1, 0])
    brain.build_matrix(con)
    groups = analysis.duplicate_groups(con, m)
    sets = [set(g["paths"]) for g in groups]
    assert {"C:/a/s.pdf", "C:/b/s kopya.pdf"} in sets
    assert {"C:/c/farkli.pdf", "C:/d/f2.pdf"} in sets
    assert not any("C:/e/baska.pdf" in s for s in sets)


def test_aging_threshold_and_exclusions(tmp_path):
    old = TODAY - timedelta(days=800)
    mk(tmp_path, "30-Kariyer/Eski.md", {"status": "arsiv", "updated": old})
    mk(tmp_path, "30-Kariyer/Aktif eski.md", {"status": "aktif", "updated": old})
    mk(tmp_path, "30-Kariyer/Yeni.md", {"status": "arsiv", "updated": TODAY - timedelta(days=100)})
    mk(tmp_path, "30-Kariyer/Bagli eski.md", {"status": "arsiv", "updated": old})
    mk(tmp_path, "30-Kariyer/Bagli yeni.md", body="bkz [[Bagli eski]]")
    res = [n.stem for n, _ in analysis.aging_notes(notes(tmp_path), TODAY)]
    assert res == ["Eski"]
    msg = analysis.write_aging(vault=tmp_path, today=TODAY)
    assert "1 not" in msg
    text = (tmp_path / "40-Kaynaklar/Analiz/Yaşlanan notlar.md").read_text(encoding="utf-8")
    assert "- [ ] [[30-Kariyer/Eski|Eski]]" in text
    assert (tmp_path / "30-Kariyer/Eski.md").exists()        # taşıma yok


def test_freshness_with_recent_mail(tmp_path):
    con = brain.connect(tmp_path / "b.db")
    mk(tmp_path, "20-Projeler/Alfa.md", {"type": "proje", "updated": TODAY - timedelta(days=90)})
    mk(tmp_path, "20-Projeler/Beta.md", {"type": "proje", "updated": TODAY - timedelta(days=90)})
    mk(tmp_path, "20-Projeler/Taze.md", {"type": "proje", "updated": TODAY - timedelta(days=5)})
    add_doc(con, "mail:main:1", "mail", "Alfa güncellemesi", "Alfa projesi için yeni fatura geldi", ms(TODAY - timedelta(days=10)))
    add_doc(con, "mail:main:2", "mail", "Beta eski", "Beta konusu", ms(TODAY - timedelta(days=200)))
    rows = {r["note"].stem: r for r in analysis.freshness(notes(tmp_path), con, TODAY)}
    assert set(rows) == {"Alfa", "Beta"}
    assert rows["Alfa"]["n"] == 1 and rows["Beta"]["n"] == 0


def test_conflicts_two_phones_and_due(tmp_path):
    mk(tmp_path, "60-Kişiler/Ali Veli.md", {"type": "kisi", "phone": ["+905321112233", "+905449998877"], "email": "a@x.com"})
    mk(tmp_path, "60-Kişiler/Tek Kisi.md", {"type": "kisi", "phone": ["+905321112233", "0532 111 22 33"]})
    mk(tmp_path, "20-Projeler/Odev.md", {"type": "proje", "due": date(2026, 11, 5)}, "Son teslim: 12.11.2026 olacak.")
    res = analysis.conflicts(notes(tmp_path))
    assert any("Ali Veli" in r and "telefon" in r for r in res)
    assert not any("Tek Kisi" in r for r in res)
    assert any("Odev" in r and "2026-11-12" in r for r in res)


def test_glossary_pattern_and_no_invention(tmp_path):
    for i in range(3):
        mk(tmp_path, f"10-Dersler/D{i}.md", body=f"Yapay Sinir Ağları (YSA) kullanıldı. YSA iyi. Ayrıca XYZ ve ABC kısaltmaları var {i}.")
    mk(tmp_path, "10-Dersler/Z.md", body="Bugün Rastgele Kelime Dizisi (ABC) yazdım.")
    rows = {a: (c, e) for a, c, e in analysis.glossary(notes(tmp_path))}
    assert rows["YSA"] == (3, "Yapay Sinir Ağları")
    assert rows["XYZ"][1] == ""                    # açılım uydurulmaz
    assert rows["ABC"][1] == ""                    # baş harfler tutmayan “açılım” reddedilir


def test_tag_groups(tmp_path):
    mk(tmp_path, "a.md", {"tags": ["Proje", "yapay-zeka"]})
    mk(tmp_path, "b.md", {"tags": ["proje", "yapayzeka", "kitap"]})
    mk(tmp_path, "c.md", {"tags": ["projeler", "proje", "kitap"]})
    freq, groups = analysis.tag_groups(notes(tmp_path))
    assert freq["proje"] == 2
    flat = [{t for t, _ in g} for g in groups]
    assert {"Proje", "proje", "projeler"} in flat and {"yapay-zeka", "yapayzeka"} in flat
    assert not any("kitap" in s for s in flat)


def test_quality_order(tmp_path):
    mk(tmp_path, "20-Projeler/Zengin.md", {"type": "proje"}, "uzun metin " * 200 + "[[Baska]]")
    mk(tmp_path, "20-Projeler/Baska.md", {"type": "proje"}, "[[Zengin]] " + "icerik " * 100)
    mk(tmp_path, "20-Projeler/Fakir.md", {"tags": [], "type": None, "status": None, "updated": TODAY - timedelta(days=900)}, "kisa")
    res = analysis.quality(notes(tmp_path), TODAY)
    assert res[0][1].stem == "Fakir" and res[0][0] < res[-1][0] <= 100


def test_pca_svg_no_external(tmp_path):
    rng = np.random.default_rng(1)
    x = rng.normal(size=(30, 8))
    xy = analysis.pca2d(x)
    assert xy.shape == (30, 2)
    svg = analysis.cluster_svg(xy, [i % 3 for i in range(30)], [f"Not <{i}>" for i in range(30)])
    assert svg.count("<circle") == 30 and "&lt;3&gt;" in svg
    for bad in ("http", "<script", "src=", "href="):
        assert bad not in svg


def test_cluster_map_html(tmp_path):
    con = brain.connect(tmp_path / "b.db")
    rng = np.random.default_rng(2)
    for i in range(14):
        base = np.zeros(6)
        base[i % 2] = 1
        add_doc(con, f"note:30-Kariyer/N{i}.md", "note", f"N{i}", f"metin {i}", ref=f"30-Kariyer/N{i}.md", vec=base + rng.normal(scale=0.05, size=6))
    brain.build_matrix(con)
    msg = analysis.write_map(vault=tmp_path / "v", con=con)
    html = (tmp_path / "v/40-Kaynaklar/Analiz/Küme haritası.html").read_text(encoding="utf-8")
    assert "14 not" in msg and html.count("<circle") == 14 and "<script" not in html and "http" not in html


def test_pipeline_rows(tmp_path):
    con = brain.connect(tmp_path / "b.db")
    m = maildb.connect(tmp_path / "m.db")
    m.executescript(content.SCHEMA)
    m.execute("INSERT INTO messages(account, id, date_ms, subject) VALUES ('main','1',1700000000000,'s')")
    m.execute("INSERT INTO messages(account, id, date_ms, subject) VALUES ('main','2',1700000001000,'s')")
    m.execute("INSERT INTO messages(account, id, date_ms, subject) VALUES ('sms','3',1700000001000,'s')")
    m.execute("INSERT INTO items(source, id, date_ms, title) VALUES ('invoice','1',1700000000000,'f')")
    m.commit()
    add_doc(con, "note:a.md", "note", "a", "metin", vec=[1, 0])
    add_doc(con, "mail:main:1", "mail", "m", "metin")
    mk(tmp_path / "v", "20-Projeler/P.md")
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "daily-1.log").write_text("[OK] a\n[HATA] b\nTraceback (most recent call last)\n", encoding="utf-8")
    (logs / "daily-2.log").write_text("[OK] a\n[HATA] b\nTraceback x\n", encoding="utf-8")
    rows = {(a, b): (c, d) for a, b, c, d in analysis.pipeline_rows(con, m, tmp_path / "v", logs)}
    assert rows[("mail.db messages", "main")][0] == 2 and rows[("mail.db messages", "sms")][0] == 1
    assert rows[("mail.db items", "invoice")][0] == 1
    assert rows[("brain.db", "note")][1].endswith("gömme %100") and rows[("brain.db", "mail")][1].endswith("gömme %0")
    assert rows[("kasa", "20-Projeler")][0] == 1
    assert rows[("günlük çalışma", "daily-2.log")][0] == 2


def test_run_all_continues_after_error():
    calls = []

    def ok(**kw):
        calls.append("ok")
        return "tamam"

    def bad(**kw):
        raise RuntimeError("patladı")

    out = analysis.run_all(log=lambda s: None, steps=[("a", bad), ("b", ok)])
    assert out["a"].startswith("HATA") and out["b"] == "tamam" and calls == ["ok"]


def test_trust_ordering(tmp_path):
    t = analysis.trust
    assert t("item:invoice:1") > t("mail:main:1") > t("mail:whatsapp:1") > t("item:spotify:1")
    assert t("note:40-Kaynaklar/Mail/x.md") == analysis.TRUST["derived"] < t("note:20-Projeler/x.md")
    con = brain.connect(tmp_path / "b.db")
    con.execute("CREATE TABLE doc_class (doc_id TEXT PRIMARY KEY, cls TEXT, why TEXT)")
    con.execute("INSERT INTO doc_class VALUES ('file:C:/a.docx', 'sözleşme', '')")
    assert t("file:C:/a.docx", con) >= 0.9 > t("file:C:/a.docx")


def test_topic_timeline_groups_by_month(tmp_path):
    con = brain.connect(tmp_path / "b.db")
    add_doc(con, "mail:main:1", "mail", "Kargo geldi", "tekstil makine kargo", ms(date(2026, 9, 3)))
    add_doc(con, "mail:main:2", "mail", "Fiyat teklifi", "tekstil makine teklif", ms(date(2026, 10, 7)))
    add_doc(con, "mail:main:3", "mail", "Alakasız", "başka konu", ms(date(2026, 10, 8)))
    tl = analysis.topic_timeline("tekstil", con)
    assert list(tl) == ["2026-10", "2026-09"] and tl["2026-10"][0]["title"] == "Fiyat teklifi"
    analysis.write_timeline("tekstil", vault=tmp_path / "v", con=con)
    assert "### 2026-09" in (tmp_path / "v/40-Kaynaklar/Analiz/Zaman çizelgesi - tekstil.md").read_text(encoding="utf-8")


def test_project_map_and_mermaid_limit(tmp_path):
    con = brain.connect(tmp_path / "b.db")
    v = tmp_path / "v"
    mk(v, "60-Kişiler/Ayşe Yılmaz.md", {"type": "kisi"})
    mk(v, "40-Kaynaklar/Teknolojiler/PyTorch.md")
    for i in range(30):
        mk(v, f"20-Projeler/Proje{i}.md", {"type": "proje", "technologies": [f"Tek{i}", "Python"]}, "[[PyTorch]]")
    add_doc(con, "mail:main:1", "mail", "x", "Proje3 için Ayşe Yılmaz yazdı", ms(TODAY))
    rows = analysis.project_map(v, con)
    r3 = next(r for r in rows if r["proje"] == "Proje3")
    assert r3["mail"] == 1 and r3["kisiler"][0][0] == "Ayşe Yılmaz" and "PyTorch" in r3["teknolojiler"]
    mm = analysis.mermaid(rows, 25)
    assert mm.startswith("```mermaid\ngraph LR") and mm.count('["') <= 25


def test_write_is_idempotent_and_dry_run_writes_nothing(tmp_path):
    v = tmp_path / "v"
    mk(v, "a.md", {"tags": ["Proje"]})
    mk(v, "b.md", {"tags": ["proje"]})
    assert "[dry-run]" in analysis.write_tags(vault=v, dry=True)
    assert not (v / "40-Kaynaklar/Analiz").exists()
    first = analysis.write_tags(vault=v)
    p = v / "40-Kaynaklar/Analiz/Etiket önerileri.md"
    assert "→" in first and p.exists()
    p.write_text(p.read_text(encoding="utf-8") + "\nelle yazılan not\n", encoding="utf-8")
    assert "değişmedi" in analysis.write_tags(vault=v)
    assert "elle yazılan not" in p.read_text(encoding="utf-8")
