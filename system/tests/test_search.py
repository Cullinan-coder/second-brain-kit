"""Faz 1.6: gelişmiş arama — süzgeçler, kayıtlı aramalar, araştırma, hatırlama, ek/görsel, SSS, kayıt, kalite testi, MCP."""
import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from sb import brain, maildb, search

TODAY = date(2026, 10, 31)          # cumartesi
FIX = Path(__file__).parent / "fixtures" / "search_eval.yaml"


def fake_embed(model, texts, task=""):
    out = []
    for t in texts:
        v = np.zeros(64, dtype=np.float32)
        for w in t.lower().replace("search_document:", "").replace("search_query:", "").split():
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1
        out.append(v.tolist())
    return out


DOCS = [
    ("note:a.md", "note", "Tekstil iğne tespiti", 1767225600000, "a.md", "Santoni makinede akustik sensörle iğne kırığı tespiti. MEMS mikrofon 48 kHz."),
    ("note:b.md", "note", "Laravel kuyruk", 1767225600000, "b.md", "Laravel queue worker supervisor ile çalışır. Redis sürücüsü kuyruk."),
    ("mail:main:1", "mail", "Staj başvurusu", 1770000000000, "main:1", "ACME staj başvurunuz alındı, mülakat tarihi 12 Kasım.\nKimden: Ahmet Hoca"),
    ("chat:sms:ACME:2026-01-02", "chat", "Mülakat kodu", 1770000000000, "sms:ACME:2026-01-02", "ACME mülakat hatırlatma SMS mesajı yarın."),
    ("item:youtube:v1", "item", "Akustik sensör dersi", 1770000000000, "https://y/v1", "Akustik sensör videosu anlatımı ve MEMS mikrofon."),
]


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(brain, "VEC_NPY", tmp_path / "v.npy")
    monkeypatch.setattr(brain, "IDS_NPY", tmp_path / "i.npy")
    monkeypatch.setattr(brain, "_embed_model", lambda: "test:emb")
    brain._MATRIX.clear()
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(search, "VAULT", vault)
    monkeypatch.setattr(search, "QUESTIONS", tmp_path / "questions.jsonl")
    monkeypatch.setattr(search, "SAVED_STATE", tmp_path / "saved.json")
    commits = []
    monkeypatch.setattr(search, "_commit", lambda paths, msg: commits.append((paths, msg)) or "abc")
    con = brain.connect(tmp_path / "b.db")
    brain.index(con=con, docs=DOCS, embed=False, log=lambda *a: None)
    brain.embed_pending(con, embedder=fake_embed, log=lambda *a: None)
    monkeypatch.setattr(brain, "embed_pending", lambda *a, **k: 0)
    return type("E", (), {"con": con, "vault": vault, "commits": commits, "tmp": tmp_path})


def qv(text):
    return fake_embed("", ["search_query: " + text])[0]


# ------------------------------------------------------------ 140
def test_parse_dates():
    pf = lambda t: search.parse_filters(t, TODAY)
    assert pf("geçen ay faturalar")[1]["since"] == "2026-09-01" and pf("geçen ay faturalar")[1]["until"] == "2026-09-30"
    assert pf("geçen ay faturalar")[0] == "faturalar"
    assert pf("bu hafta toplantı")[1]["since"] == "2026-10-26" and pf("bu hafta toplantı")[1]["until"] == "2026-10-31"
    assert pf("geçen hafta rapor")[1]["since"] == "2026-10-19" and pf("geçen hafta rapor")[1]["until"] == "2026-10-25"
    f = pf("son 3 gün yazışma")[1]
    assert (f["since"], f["until"]) == ("2026-10-28", "2026-10-31")
    assert pf("2025'te başvuru")[1]["since"] == "2025-01-01" and pf("2025'te başvuru")[1]["until"] == "2025-12-31"
    assert pf("ekimde gelen faturalar")[0] == "faturalar"
    assert pf("ekimde gelen faturalar")[1]["since"] == "2026-10-01"
    assert pf("mart 2026 sınav")[1]["until"] == "2026-03-31" and pf("mart 2026 sınav")[0] == "sınav"
    assert pf("martta sınav")[1]["since"] == "2026-03-01"
    assert pf("aralıkta ödeme")[1]["since"] == "2025-12-01"          # gelecekteki ay → geçen yıl
    f = pf("dün gelen")[1]
    assert f["since"] == f["until"] == "2026-10-30"
    assert pf("hiçbir tarih yok")[1]["since"] is None
    assert search.parse_filters("geçen ay", date(2026, 1, 15))[1]["since"] == "2025-12-01"


def test_parse_kinds_and_person():
    q, f = search.parse_filters("geçen ay hocadan gelen mailler", TODAY)
    assert f["kinds"] == ["mail"] and f["not_account"] == search.MESSENGERS and q == "hoca"
    q, f = search.parse_filters("Ahmet hocadan gelen mailler", TODAY)
    assert f["person"] == "Ahmet" and "Ahmet" in q and f["kinds"] == ["mail"]
    assert search.parse_filters("Ayşe Yılmaz'dan mesajlar", TODAY)[1]["person"] == "Ayşe Yılmaz"
    assert search.parse_filters("TÜBİTAK ile ilgili notlarım", TODAY)[1]["person"] == "TÜBİTAK"
    assert search.parse_filters("sms ve whatsapp kod", TODAY)[1]["account"] == ["sms", "whatsapp"]
    assert search.parse_filters("pdf sözleşme", TODAY)[1]["kinds"] == ["file"]
    f = search.parse_filters("akustik videolar", TODAY)[1]
    assert f["kinds"] == ["item"] and f["account"] == ["youtube"]
    assert search.parse_filters("proje notlar", TODAY)[1]["kinds"] == ["note"]


def test_smart_find_passes_filters(env, monkeypatch):
    seen = {}
    monkeypatch.setattr(brain, "find", lambda q, **kw: seen.update(q=q, **kw) or [])
    search.smart_find("ekimde gelen mailler akustik", today=TODAY, con=env.con)
    assert seen["q"] == "akustik" and seen["kinds"] == ["mail"] and seen["since"] == "2026-10-01" and seen["until"] == "2026-10-31"
    assert [json.loads(l)["q"] for l in search.QUESTIONS.read_text(encoding="utf-8").splitlines()] == ["ekimde gelen mailler akustik"]


def test_smart_find_account_filter(env):
    hits = search.smart_find("mülakat mesajlar sms", con=env.con, query_vec=qv("mülakat"), log=False)
    assert hits and all(h["doc_id"].startswith("chat:sms:") for h in hits)
    hits = search.smart_find("mülakat mailler", con=env.con, query_vec=qv("mülakat"), log=False)
    assert hits and all(not h["doc_id"].startswith("chat:sms:") for h in hits)
    vids = search.smart_find("akustik videolar", con=env.con, query_vec=qv("akustik"), log=False)
    assert [h["doc_id"] for h in vids] == ["item:youtube:v1"]


# ------------------------------------------------------------ 141
def test_saved_searches(env, monkeypatch):
    toasts = []
    import sb.actions as actions
    monkeypatch.setattr(actions, "toast", lambda t, b: toasts.append((t, b)))
    search.add_saved("mülakat", alert=True)
    search.add_saved("laravel")
    note = (env.vault / search.SAVED_NOTE).read_text(encoding="utf-8")
    assert "- mülakat | uyar" in note and "- laravel" in note
    assert search.load_saved() == [{"query": "mülakat", "alert": True}, {"query": "laravel", "alert": False}]
    assert search.check_saved(con=env.con, query_vec=qv("x")) == []                 # ilk çalıştırma: taban çizgisi
    assert json.loads(search.SAVED_STATE.read_text(encoding="utf-8"))["mülakat"]["seen"]
    brain.index(con=env.con, docs=DOCS + [("mail:main:9", "mail", "Mülakat sonucu", 1770000000000, "main:9", "ACME mülakat sonucu açıklandı.")],
                embed=False, log=lambda *a: None)
    res = search.check_saved(con=env.con, query_vec=qv("x"))
    assert [r["query"] for r in res] == ["mülakat"] and [h["doc_id"] for h in res[0]["new"]] == ["mail:main:9"]
    assert len(toasts) == 1 and "Mülakat sonucu" in toasts[0][1]
    assert search.check_saved(con=env.con, query_vec=qv("x")) == []                 # artık görüldü
    monkeypatch.setattr(actions, "toast", lambda t, b: 1 / 0)                         # bildirim hatası sessiz
    brain.index(con=env.con, docs=DOCS + [("mail:main:10", "mail", "Mülakat 2", 1770000000000, "main:10", "ACME mülakat ikinci tur.")],
                embed=False, log=lambda *a: None)
    assert search.check_saved(con=env.con, query_vec=qv("x"))


# ------------------------------------------------------------ 142
def _fake_llm(monkeypatch, plan):
    from sb import llm
    calls = []

    def complete(task, prompt, **kw):
        calls.append((task, kw))
        if task == "research_plan":
            return json.dumps({"alt_sorular": plan}), "test"
        return "## Özet\nSensör iğne kırığını yakalar [1].", "test"
    monkeypatch.setattr(llm, "complete", complete)
    return calls


def test_research_report_and_web_privacy(env, monkeypatch):
    calls = _fake_llm(monkeypatch, ["akustik sensör iğne", "Ahmet Yılmaz mülakat", "ali@x.com staj"])
    sent = []
    monkeypatch.setattr(search, "web_search", lambda q, n=5: sent.append(q) or [{"title": "Web", "url": "http://w/1", "snippet": "MEMS"}])
    r = search.research("Akustik tespit nasıl çalışır?", web=True, con=env.con, query_vec=qv("akustik sensör iğne"))
    assert sent == ["akustik sensör iğne"]                                           # kişi adı ve e-posta içeren alt sorular gitmedi
    assert all(kw.get("private") for _, kw in calls)
    p = env.vault / r["path"]
    assert r["path"].startswith("40-Kaynaklar/Araştırmalar/") and p.exists()
    text = p.read_text(encoding="utf-8")
    assert "## Kaynaklar" in text and "- [1]" in text and "atlandı" in text
    assert env.commits and env.commits[0][0] == [r["path"]]


def test_research_no_web_by_default(env, monkeypatch):
    _fake_llm(monkeypatch, ["laravel kuyruk"])
    monkeypatch.setattr(search, "web_search", lambda *a, **k: pytest.fail("web çağrılmamalı"))
    r = search.research("Laravel kuyruk?", con=env.con, query_vec=qv("laravel kuyruk"))
    assert r["sources"] and (env.vault / r["path"]).exists()


# ------------------------------------------------------------ 143
def test_recall_cleans_and_limits(env, monkeypatch):
    seen = {}
    monkeypatch.setattr(brain, "find", lambda q, **kw: seen.update(q=q, **kw) or [])
    search.recall("galiba geçen ay bir akustik sensör vardı sanırım", today=TODAY, con=env.con)
    assert seen["q"] == "akustik sensör" and seen["k"] == 15 and seen["per_doc"] == 1 and seen["since"] == "2026-09-01"


def test_recall_results(env):
    hits = search.recall("galiba akustik sensör vardı", con=env.con, query_vec=qv("akustik sensör"))
    assert 1 <= len(hits) <= 5 and hits[0]["doc_id"] in ("note:a.md", "item:youtube:v1")


# ------------------------------------------------------------ 144
def test_attachment_search(tmp_path):
    from sb import content
    mc = maildb.connect(tmp_path / "mail.db")
    mc.executescript(content.SCHEMA)
    mc.execute("INSERT INTO messages(account, id, date_ms, subject, from_name, attachments) VALUES ('main','1',1770000000000,'Fatura','Şirket',?)",
               (json.dumps(["Ekim_Faturası.pdf", "logo.png"], ensure_ascii=False),))
    mc.execute("INSERT INTO messages(account, id, date_ms, subject, attachments) VALUES ('main','2',1770000000000,'x','[]')")
    mc.execute("INSERT INTO file_text(path, text) VALUES (?,?)", ("C:/belgeler/sözleşme.pdf", "Kira sözleşmesi fatura bedeli"))
    mc.execute("INSERT INTO file_text(path, text) VALUES (?,?)", ("C:/belgeler/fatura_ocak.pdf", "tutar 100 TL"))
    mc.commit()
    res = search.attachment_search("fatura", mail_con=mc)
    kinds = {(r["kind"], r["title"]) for r in res}
    assert ("ek", "Ekim_Faturası.pdf") in kinds and ("dosya", "sözleşme.pdf") in kinds and ("dosya", "fatura_ocak.pdf") in kinds
    assert not any(r["title"] == "logo.png" for r in res)
    assert search.attachment_search("yokböyle", mail_con=mc) == []


# ------------------------------------------------------------ 145
def test_image_index_and_search(env):
    att = env.vault / "_attachments" / "Gelen"
    att.mkdir(parents=True)
    (att / "fis.png").write_bytes(b"png-1")
    (att / "ekran.JPG").write_bytes(b"jpg-1")
    (att / "not.txt").write_text("x", encoding="utf-8")
    (env.vault / "_system").mkdir()
    (env.vault / "_system" / "gizli.png").write_bytes(b"x")
    calls = []

    def ocr(b):
        calls.append(b)
        return "Migros fiş toplam 245 TL" if b.startswith(b"png") else "Toplantı notları Kasım"
    r = search.index_images(env.vault, con=env.con, ocr=ocr, log=lambda *a: None)
    assert r["new"] == 2 and len(calls) == 2
    r = search.index_images(env.vault, con=env.con, ocr=ocr, log=lambda *a: None)
    assert r["new"] == 0 and r["skipped"] == 2 and len(calls) == 2                   # değişmeyen atlanır
    (att / "fis.png").write_bytes(b"png-2")
    assert search.index_images(env.vault, con=env.con, ocr=ocr, log=lambda *a: None)["new"] == 1
    hits = search.image_search("migros toplam", con=env.con)
    assert [h["path"] for h in hits] == ["_attachments/Gelen/fis.png"] and "Migros" in hits[0]["snippet"]
    assert search.image_search("toplantı", con=env.con)[0]["path"].endswith("ekran.JPG")


# ------------------------------------------------------------ 147
def test_build_faq(env):
    for q in ["tekstil projesinde akustik sensör nedir", "akustik sensör tekstil projesi", "Laravel kuyruk nasıl çalışır",
              "tekstil akustik sensör projesinde ne var"]:
        search._log_question(q)
    r = search.build_faq(answerer=lambda q: f"cevap: {q} [1]")
    assert len(r["items"]) == 2 and r["items"][0]["n"] == 3
    text = (env.vault / search.FAQ_NOTE).read_text(encoding="utf-8")
    assert "3 kez soruldu" in text and "cevap:" in text and text.startswith("---")


# ------------------------------------------------------------ 148
def test_save_results(env):
    hits = search.smart_find("akustik", con=env.con, query_vec=qv("akustik"), log=False)
    rel = search.save_results("akustik sensör: ne?", hits, today=TODAY)
    assert rel == "40-Kaynaklar/Aramalar/akustik sensör ne 2026-10-31.md"
    text = (env.vault / rel).read_text(encoding="utf-8")
    assert "[[a|Tekstil iğne tespiti]]" in text and "`https://y/v1`" in text and "type: kaynak" in text


# ------------------------------------------------------------ 149
def test_evaluate(env):
    r = search.evaluate(FIX, con=env.con, query_vec=qv("iğne kırığı akustik sensör"))
    assert r["n"] == 4 and r["misses"] == ["olmayan bir şey xyzzy"]
    assert 0.5 <= r["hit@5"] <= 0.75 and r["mrr"] > 0.3
    # tam kontrollü: sahte arayıcıyla hit@5 ve MRR
    ranked = {"a": ["x", "y", "note:a.md"], "b": ["Laravel kuyruk"], "c": []}
    f = lambda q: [{"doc_id": d, "title": d} for d in ranked[q]]
    import yaml
    p = env.tmp / "e.yaml"
    p.write_text(yaml.safe_dump([{"q": "a", "expect": "note:a.md"}, {"q": "b", "expect": ["laravel"]}, {"q": "c", "expect": ["z"]}]), encoding="utf-8")
    r = search.evaluate(p, finder=f)
    assert r["hit@5"] == round(2 / 3, 3) and r["mrr"] == round((1 / 3 + 1) / 3, 3)


# ------------------------------------------------------------ MCP
def test_mcp_brain_find_format(env, monkeypatch):
    from sb import mcp_server
    monkeypatch.setattr(brain, "find", lambda q, **kw: [{"doc_id": "note:a.md", "kind": "note", "title": "Başlık", "ref": "a.md", "score": 1,
                                                         "date": "2026-01-01", "text": "x " * 400 + " TC 10000000146"}])
    out = mcp_server.brain_find("akustik", kind="note", since="2025-01-01", k=3)
    first, second = out.split("\n")
    assert first == "[note] 2026-01-01 Başlık — a.md" and second.startswith("    x x") and len(second) <= 4 + 300
    monkeypatch.setattr(brain, "find", lambda q, **kw: [])
    assert mcp_server.brain_find("yok") == "Sonuç yok."
