"""Faz 1.4: kişi birleştirme önerisi/uygulama, kişi bahsedilme bölümü, k-means kümeleme, bağlantı önerisi."""
import numpy as np

from sb import brain, entities, vault_ops


def _vault(tmp_path, monkeypatch):
    v = tmp_path / "v"
    (v / "60-Kişiler").mkdir(parents=True)
    (v / "00-Inbox").mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    return v


def person(v, name, **fm):
    lines = "".join(f"{k}: {val}\n" for k, val in {"type": "kisi", "status": "aktif", "source": "contacts", **fm}.items())
    (v / "60-Kişiler" / f"{name}.md").write_text(f"---\n{lines}---\n# {name}\n\n## Bağlam\nnot {name}\n", encoding="utf-8")


def test_merge_candidates_proposals_and_apply(tmp_path, monkeypatch):
    v = _vault(tmp_path, monkeypatch)
    person(v, "Ali Talha Özturk", phone="['+905531274213']")
    person(v, "Ali Talha Öztürk", phone="['+90 553 127 42 13']", company="Teknobil", role="Öğrenci")
    person(v, "Nuran KUMAŞÇI")
    person(v, "Nuran Kumaşçı", email="['n@x.com']")
    person(v, "Başka Biri", phone="['+905000000000']")
    for i in range(6):                                          # aynı santral numarası: 6 kişi → aday değil
        person(v, f"Şirket Kişi{i}", phone="['+902120000000']")
    c = entities.merge_candidates(v)
    names = {(a.stem, b.stem, why) for a, b, why in c}
    assert ("Ali Talha Özturk", "Ali Talha Öztürk", "aynı ad, aynı telefon") in names
    assert any(a.stem.startswith("Nuran") and b.stem.startswith("Nuran") for a, b, _ in c) and len(c) == 2
    assert "2 yeni" in entities.write_merge_proposals(v)
    note = v / entities.MERGE_NOTE
    text = note.read_text(encoding="utf-8").replace("- [ ] [[Ali Talha Özturk]]", "- [x] [[Ali Talha Özturk]]").replace(
        "- [ ] [[Nuran KUMAŞÇI]]", "- [-] [[Nuran KUMAŞÇI]]")
    note.write_text(text, encoding="utf-8")
    out = entities.apply_merges(v)
    assert len(out) == 1 and "Arşivlendi" in out[0]
    kept = (v / "60-Kişiler" / "Ali Talha Öztürk.md").read_text(encoding="utf-8")
    assert "Ali Talha Özturk" in kept and "## Birleştirilen: Ali Talha Özturk" in kept           # takma ad + iz
    assert not (v / "60-Kişiler" / "Ali Talha Özturk.md").exists() and (v / "90-Arşiv" / "60-Kişiler" / "Ali Talha Özturk.md").exists()
    assert "işlendi" in note.read_text(encoding="utf-8")
    assert "0 yeni" in entities.write_merge_proposals(v)                                           # [-] reddedilen tekrar gelmez


def test_kmeans_and_cluster_notes(tmp_path, monkeypatch):
    v = _vault(tmp_path, monkeypatch)
    rng = np.random.default_rng(0)
    a, b = np.eye(8)[0], np.eye(8)[1]
    vecs = np.vstack([a + rng.normal(0, .05, 8) for _ in range(8)] + [b + rng.normal(0, .05, 8) for _ in range(8)])
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    lab, _ = entities.kmeans(vecs, 2)
    assert len(set(lab[:8])) == 1 and len(set(lab[8:])) == 1 and lab[0] != lab[8]
    keys = [(f"20-Projeler/p{i}.md", f"Proje {i}", "note", 0) for i in range(8)] +         [(f"C:/belge{i}.pdf", f"belge{i}.pdf", "file", 1767225600000) for i in range(8)]
    monkeypatch.setattr(entities, "doc_vectors", lambda kinds=None, con=None: (keys, vecs))
    out = entities.clusters(k=2, namer=lambda titles: {"ad": "Aynı Ad", "aciklama": "test kümesi"})
    files = sorted((v / entities.CLUSTERS).glob("*.md"))
    texts = [f.read_text(encoding="utf-8") for f in files]
    assert "2 kümeye" in out and len(files) == 2                                   # aynı ad: ikinci küme ezilmez
    assert any("[[20-Projeler/p" in t and "8 not" in t for t in texts) and any("📄 2026-01-01 belge" in t and "8 belge" in t for t in texts)


def test_suggest_links_skips_linked(tmp_path, monkeypatch):
    v = _vault(tmp_path, monkeypatch)
    (v / "20-Projeler").mkdir()
    for n, body in [("a", "[[b]]"), ("b", ""), ("c", ""), ("d", "")]:
        (v / "20-Projeler" / f"{n}.md").write_text(f"# {n}\n{body}\n", encoding="utf-8")
    vecs = np.array([[1, 0], [1, 0.01], [0.99, 0.02], [0, 1]], dtype=float)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    refs = [(f"20-Projeler/{n}.md", n) for n in "abcd"]
    monkeypatch.setattr(entities, "note_vectors", lambda con=None: (refs, vecs))
    out = entities.suggest_links(threshold=0.9)
    text = (v / entities.LINK_NOTE).read_text(encoding="utf-8")
    assert "2 bağlantı" in out and "[[20-Projeler/a|a]] ↔ [[20-Projeler/b|b]]" not in text and "|d]]" not in text


def test_mentions_section(tmp_path, monkeypatch):
    v = _vault(tmp_path, monkeypatch)
    person(v, "Ayşe Yılmaz")
    con = brain.connect(tmp_path / "b.db")
    docs = [("note:20-Projeler/x.md", "note", "Proje X", 1767225600000, "20-Projeler/x.md", "Toplantıda Ayşe Yılmaz sunum yaptı."),
            ("mail:main:1", "mail", "Davet", 1767225600000, "main:1", "Merhaba, Ayşe Yılmaz olarak yazıyorum."),
            ("note:20-Projeler/y.md", "note", "Proje Y", 1767225600000, "20-Projeler/y.md", "Ayşe ile ilgisi yok, Yılmaz başka.")]
    brain.index(con=con, docs=docs, embed=False, log=lambda *a: None)
    out = entities.write_mentions(con, vault=v)
    text = (v / "60-Kişiler" / "Ayşe Yılmaz.md").read_text(encoding="utf-8")
    assert "1 kişi" in out and "[[20-Projeler/x]]" in text and "mail: Davet" in text and "y]]" not in text


def test_merge_decision_rules():
    from sb.entities import merge_decision
    assert merge_decision("Havva nur (2)", "Havva Nur", "aynı ad, aynı telefon")[0]
    assert merge_decision("Burcu Kuaför", "Burcu", "aynı telefon")[0]
    assert merge_decision("Biyoloji Hocasi", "Nebi Acar", "aynı telefon")[0]
    assert not merge_decision("Cpt'Emu", "Melih Can", "aynı telefon")[0]
    assert not merge_decision("Protein tozu kom", "Zeus Nutration", "aynı telefon")[0]
