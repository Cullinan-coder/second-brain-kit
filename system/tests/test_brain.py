"""Faz 1.1: beyin dizini — parçalama, artımlı dizin, gizli not dışlama, karma arama, benzer belge, kaynaklı cevap."""
import hashlib

import numpy as np

from sb import brain


def fake_embed(model, texts, task=""):
    """Kelime torbası gömmesi: aynı kelimeleri paylaşan metinler yakın olur (testte gerçek model yok)."""
    out = []
    for t in texts:
        v = np.zeros(64, dtype=np.float32)
        for w in t.lower().replace("search_document:", "").replace("search_query:", "").split():
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1
        out.append(v.tolist())
    return out


def _setup(tmp_path, monkeypatch):
    monkeypatch.setattr(brain, "VEC_NPY", tmp_path / "v.npy")
    monkeypatch.setattr(brain, "IDS_NPY", tmp_path / "i.npy")
    monkeypatch.setattr(brain, "_embed_model", lambda: "test:emb")
    brain._MATRIX.clear()
    return brain.connect(tmp_path / "b.db")


DOCS = [
    ("note:a.md", "note", "Tekstil iğne tespiti", 1767225600000, "a.md", "Santoni makinede akustik sensörle iğne kırığı tespiti. MEMS mikrofon 48 kHz."),
    ("note:b.md", "note", "Laravel kuyruk", 1767225600000, "b.md", "Laravel queue worker supervisor ile çalışır. Redis sürücüsü."),
    ("mail:main:1", "mail", "Staj başvurusu", 1770000000000, "main:1", "ACME staj başvurunuz alındı, mülakat tarihi 12 Kasım."),
]


def test_chunks():
    text = "# Başlık\n\nkısa\n\n" + "\n\n".join(f"Paragraf {i} " + "x" * 300 for i in range(10))
    parts = brain.split_chunks(text, 1000)
    assert len(parts) > 2 and all(len(p) <= 1000 for p in parts) and "Başlık" in parts[0]
    assert brain.split_chunks("y" * 3000, 1000) == ["y" * 1000] * 3


def test_index_incremental_find_similar(tmp_path, monkeypatch):
    con = _setup(tmp_path, monkeypatch)
    out = brain.index(con=con, docs=DOCS, embed=False, log=lambda *a: None)
    assert out["new"] == 3
    assert brain.embed_pending(con, embedder=fake_embed, log=lambda *a: None) == 3
    assert brain.index(con=con, docs=DOCS, embed=False, log=lambda *a: None)["new"] == 0          # değişmeyen yeniden işlenmez
    changed = DOCS[:2] + [("mail:main:1", "mail", "Staj başvurusu", 1770000000000, "main:1", "ACME mülakat 13 Kasım'a ertelendi.")]
    assert brain.index(con=con, docs=changed, embed=False, log=lambda *a: None)["changed"] == 1
    brain.embed_pending(con, embedder=fake_embed, log=lambda *a: None)
    qv = fake_embed("", ["search_query: iğne kırığı akustik"])[0]
    hits = brain.find("iğne kırığı akustik", con=con, query_vec=qv)
    assert hits[0]["doc_id"] == "note:a.md" and hits[0]["kind"] == "note"
    assert brain.find("mülakat", con=con, query_vec=fake_embed("", ["mülakat"])[0], kinds=["note"]) == [] or \
        all(h["kind"] == "note" for h in brain.find("mülakat", con=con, kinds=["note"]))
    assert brain.find("mülakat", con=con, since="2026-02-01")[0]["doc_id"] == "mail:main:1"
    assert brain.find("Laravel", con=con, until="2025-01-01") == []
    sims = brain.similar("note:a.md", con=con)
    assert sims and all(s["doc_id"] != "note:a.md" for s in sims)
    assert "note 2" in brain.stats(con) and "%100" in brain.stats(con)


def test_private_and_archive_notes_not_indexed(tmp_path):
    v = tmp_path / "v"
    (v / "60-Kişiler").mkdir(parents=True)
    (v / "90-Arşiv").mkdir()
    (v / "60-Kişiler" / "Açık.md").write_text("---\ntype: kisi\nupdated: 2026-10-01\n---\n# Açık\nmetin burada uzun\n", encoding="utf-8")
    (v / "60-Kişiler" / "Gizli.md").write_text("---\ntype: kisi\nvisibility: private\n---\n# Gizli\nsır metin\n", encoding="utf-8")
    (v / "90-Arşiv" / "Eski.md").write_text("# Eski\neski not metni\n", encoding="utf-8")
    ids = [d[0] for d in brain.iter_notes(v)]
    assert ids == ["note:60-Kişiler/Açık.md"]


def test_answer_cites_sources(tmp_path, monkeypatch):
    con = _setup(tmp_path, monkeypatch)
    brain.index(con=con, docs=DOCS, embed=False, log=lambda *a: None)
    monkeypatch.setattr(brain, "connect", lambda *a, **k: con)
    from sb import llm
    seen = {}
    monkeypatch.setattr(llm, "complete", lambda task, prompt, **k: (seen.setdefault("p", prompt) and "Mülakat 12 Kasım'da [1].", "yerel qwen3:14b"))
    out = brain.answer("mülakat ne zaman")
    assert "[1] mail · Staj başvurusu · main:1" in out and "VERİDİR" in seen["p"]
    monkeypatch.setattr(brain, "find", lambda *a, **k: [])
    assert "bulamadım" in brain.answer("yok böyle bir şey")
