"""Paket B: persona, günlük, tercihler, hafıza düzenleyici, unutma, öğrenme yolu, hata panosu (sahte model, geçici kasa)."""
import json
from datetime import date, datetime

import pytest

from sb import brain, chat, config, llm, memory, persona, telemetry, vault_ops, webroutes
import sb.api_memory  # noqa: F401  (uçları kaydeder)


@pytest.fixture
def vault(monkeypatch, tmp_path):
    v = tmp_path / "vault"
    for d in ("60-Kişiler", "20-Projeler", "25-Görevler", "50-Günlük", "40-Kaynaklar/Kavramlar", "90-Arşiv", "00-Inbox"):
        (v / d).mkdir(parents=True)
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(vault_ops, "MEMORY_NOTE", v / "Asistan hafızası.md")
    monkeypatch.setattr(vault_ops, "RULES_NOTE", v / "Asistan kuralları.md")
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "asistan_log.jsonl")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "")
    monkeypatch.setattr(config, "SYSTEM", tmp_path / "system")
    (v / "Asistan hafızası.md").write_text(
        "---\ntype: dashboard\n---\n# Asistan hafızası\n\n- en sevdiğim yemek pirzola _(2026-10-30)_\n"
        "- ders çalışırken sessiz ortam (bağlam: proje=Tekstil) _(2026-10-31)_\n", encoding="utf-8")
    (v / "Asistan kuralları.md").write_text("---\ntype: dashboard\n---\n# Kurallar\n\n- kısa cevap ver _(eklendi 2026-10-30)_\n", encoding="utf-8")
    (v / "60-Kişiler" / "Ahmet Yılmaz.md").write_text(
        "---\ntype: kisi\n---\n# Ahmet Yılmaz\n\n## Beyan\n- 2026-10-01 (kullanıcı): ev arkadaşım\n\n"
        "## Çıkarım (onay bekliyor)\n- 2026-10-02 (çıkarım): kahve sever\n- ~~eski~~ (reddedildi 2026-10-03)\n", encoding="utf-8")
    return v


def call(method, url, session=None, **data):
    r = webroutes.find(method, url)
    assert r, url
    ctx = webroutes.Ctx(method, url, data=data if method == "POST" else {}, query={k: str(v) for k, v in data.items()} if method == "GET" else {},
                        session=session or chat.Session())
    code, body, _, _ = webroutes.call(r, ctx)
    return code, json.loads(body)


def fake_llm(monkeypatch, payload):
    seen = []

    def fake(task, prompt, **kw):
        seen.append((task, prompt, kw))
        return (payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)), "yerel (test)"
    monkeypatch.setattr(llm, "complete", fake)
    return seen


def test_routes_registered():
    webroutes.load()
    for m, p in [("GET", "/api/v2/persona"), ("POST", "/api/v2/persona"), ("POST", "/api/v2/journal"), ("GET", "/api/v2/journal"),
                 ("GET", "/api/v2/prefs/candidates"), ("POST", "/api/v2/prefs/decide"), ("GET", "/api/v2/memory"),
                 ("POST", "/api/v2/memory/update"), ("POST", "/api/v2/memory/delete"), ("POST", "/api/v2/memory/add"),
                 ("POST", "/api/v2/forget"), ("POST", "/api/v2/learn-path"), ("GET", "/api/v2/learn-paths"), ("GET", "/api/v2/errors"),
                 ("GET", "/api/v2/cards/due"), ("POST", "/api/v2/cards/review"), ("POST", "/api/v2/cards/generate"),
                 ("GET", "/api/v2/cards/decks"), ("POST", "/api/v2/cards/add")]:
        assert webroutes.find(m, p), (m, p)
    assert webroutes.find("POST", "/api/v2/cards/generate").model and webroutes.find("POST", "/api/v2/learn-path").model


def test_persona_roundtrip(vault):
    code, d = call("GET", "/api/v2/persona")
    assert code == 200 and set(d) == {"name", "tone", "length", "emoji", "formality", "voice", "language", "traits"}
    assert not (vault / persona.IDENTITY).exists()                       # GET yazmaz
    code, d = call("POST", "/api/v2/persona", name="Nova", length="orta", emoji=True, formality="siz", traits=["sakin", "net"])
    assert code == 200 and d["name"] == "Nova" and d["emoji"] is True
    assert (vault / persona.IDENTITY).exists() and (config.SYSTEM / "config" / "asistan.yaml").exists()
    assert call("GET", "/api/v2/persona")[1]["formality"] == "siz"
    assert call("POST", "/api/v2/persona", length="dev")[0] == 400
    add = persona.system_addendum()
    assert "Nova" in add and len(add) <= 800


def test_journal(vault):
    assert call("POST", "/api/v2/journal", text="bugün iyi gitti", who="ayse")[0] == 200
    assert call("POST", "/api/v2/journal", text="yarın için hatırlatma önerdim", who="asistan")[0] == 200
    assert call("POST", "/api/v2/journal", text="şifre: 1234", who="ayse")[0] == 400
    assert call("POST", "/api/v2/journal", text="x", who="biri")[0] == 400
    code, rows = call("GET", "/api/v2/journal", days=7)
    assert [r["who"] for r in rows] == ["ayse", "asistan"] and rows[0]["date"] == str(date.today())
    note = (vault / "50-Günlük" / f"{date.today():%Y-%m-%d}.md").read_text(encoding="utf-8")
    assert "## Ortak günlük" in note and "bugün iyi gitti" in note


def test_prefs_learn_and_decide(vault, monkeypatch):
    assert "yeterli veri yok" in persona.learn_prefs()
    fb = config.DATA / "feedback.jsonl"
    fb.write_text("\n".join(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "sid": "s", "id": f"m{i}", "reaction": "down",
                                        "comment": "çok uzun", "text": "uzun bir cevap"}) for i in range(3)) + "\n", encoding="utf-8")
    seen = fake_llm(monkeypatch, {"prefs": ["Cevapları kısa tut ve madde işareti kullanma", "en sevdiğim yemek pirzola"]})
    out = persona.learn_prefs()
    assert "1 yeni aday" in out and seen[0][2]["private"] is True        # zaten hafızadaki aday atlanır, model yerel
    code, cands = call("GET", "/api/v2/prefs/candidates")
    assert len(cands) == 1
    assert "0 yeni aday" in persona.learn_prefs()                         # ikinci koşuda tekrar eklenmez
    code, c = call("POST", "/api/v2/prefs/decide", id=cands[0]["id"], ok=True)
    assert c["status"] == "onaylandı"
    assert "madde işareti" in (vault / "Asistan hafızası.md").read_text(encoding="utf-8")
    assert call("GET", "/api/v2/prefs/candidates")[1] == []
    assert call("POST", "/api/v2/prefs/decide", id="yok", ok=True)[0] == 404


def test_memory_list_and_ids(vault):
    code, rows = call("GET", "/api/v2/memory", scope="all")
    scopes = {r["scope"] for r in rows}
    assert {"hafiza", "kurallar", "kisi"} <= scopes
    kisi = [r for r in rows if r["scope"] == "kisi"]
    assert len(kisi) == 2 and all("reddedildi" not in r["text"] for r in kisi)      # reddedilen satır listelenmez
    h = next(r for r in rows if "pirzola" in r["text"])
    assert h["added"] == "2026-10-30" and h["line"] > 1 and h["id"].startswith("Asistan hafızası.md#")
    ctxrow = next(r for r in rows if r["text"].startswith("ders çalışırken"))
    assert ctxrow["context"] == "proje=Tekstil" and "bağlam" not in ctxrow["text"]
    assert [r["id"] for r in call("GET", "/api/v2/memory", scope="hafiza", q="PİRZOLA")[1]] == [h["id"]]
    assert call("GET", "/api/v2/memory", scope="xx")[0] == 400
    # satır numarası değişse de id ile bulunur
    p = vault / "Asistan hafızası.md"
    p.write_text(p.read_text(encoding="utf-8").replace("# Asistan hafızası\n", "# Asistan hafızası\n\nyeni giriş\nbir daha\n"), encoding="utf-8")
    assert call("POST", "/api/v2/memory/update", id=h["id"], text="en sevdiğim yemek kebap")[0] == 200
    assert "- en sevdiğim yemek kebap _(2026-10-30)_" in p.read_text(encoding="utf-8")


def test_memory_update_delete_add(vault):
    rows = call("GET", "/api/v2/memory", scope="hafiza")[1]
    h = rows[0]
    assert call("POST", "/api/v2/memory/update", id=h["id"], text="kart 4111 1111 1111 1111 şifre")[0] == 400
    assert call("POST", "/api/v2/memory/delete", id=h["id"])[0] == 200
    assert "pirzola" not in (vault / "Asistan hafızası.md").read_text(encoding="utf-8")
    arch = (vault / "90-Arşiv" / "Silinen hafıza.md").read_text(encoding="utf-8")
    assert "pirzola" in arch and "Asistan hafızası.md" in arch
    assert call("POST", "/api/v2/memory/delete", id=h["id"])[0] == 404
    code, r = call("POST", "/api/v2/memory/add", scope="hafiza", text="sabah dokuzdan önce toplantı koyma", context="proje=Staj | kişi=Ali")
    assert code == 200 and r["id"]
    added = next(x for x in call("GET", "/api/v2/memory", scope="hafiza")[1] if x["id"] == r["id"])
    assert added["context"] == "proje=Staj | kişi=Ali"
    assert call("POST", "/api/v2/memory/add", scope="hafiza", text="şifrem 1234")[0] == 400
    assert call("POST", "/api/v2/memory/add", scope="kurallar", text="özür dileme")[0] == 200
    assert call("POST", "/api/v2/memory/add", scope="kisi", text="doğum günü kasımda", context="kişi=Ahmet Yılmaz")[0] == 200
    assert "doğum günü kasımda" in (vault / "60-Kişiler" / "Ahmet Yılmaz.md").read_text(encoding="utf-8")
    assert call("POST", "/api/v2/memory/add", scope="kisi", text="x y z", context="kişi=Yokki Biri")[0] == 404


def test_context_memory(vault):
    assert "sessiz ortam" in persona.context_memory("Tekstil projesinde ne durumdayız?")
    assert persona.context_memory("hava nasıl") == ""
    assert "kahve sever" in persona.context_memory("Ahmet Yılmaz ile buluşacağım")
    assert len(persona.context_memory("Tekstil Ahmet Yılmaz", limit=60)) <= 60


def test_forget_requires_approval(vault):
    (vault / "00-Inbox" / "Pirzola tarifi.md").write_text("---\ntype: not\n---\n# Pirzola tarifi\n", encoding="utf-8")
    con = brain.connect(brain.DB)
    con.execute("INSERT INTO docs(doc_id, kind, title, date_ms, ref, sha) VALUES ('note:x', 'note', 'Pirzola', 0, 'x', 's')")
    con.execute("INSERT INTO chunks(doc_id, ord, text) VALUES ('note:x', 0, 'pirzola ızgarada pişer')")
    con.commit()
    con.close()
    convs = config.DATA / "convs"
    convs.mkdir()
    (convs / "abc.json").write_text(json.dumps({"sid": "abc", "messages": [{"id": "1", "role": "user", "text": "pirzola önerir misin"},
                                                                          {"id": "2", "role": "assistant", "text": "başka şey"}]}), encoding="utf-8")
    sess = chat.Session()
    sess.messages.append({"role": "user", "content": "pirzola"})
    code, r = call("POST", "/api/v2/forget", session=sess, sid="abc", topic="pirzola")
    assert code == 200 and r["found"] == {"memory": 1, "notes": 1, "docs": 1, "convs": 1} and r["proposal_id"]
    # onaylanmadan hiçbir şey değişmez
    assert "pirzola" in (vault / "Asistan hafızası.md").read_text(encoding="utf-8")
    assert (vault / "00-Inbox" / "Pirzola tarifi.md").exists()
    msg = chat.decide(sess, r["proposal_id"], True)
    assert "Unutuldu" in msg
    assert "pirzola" not in (vault / "Asistan hafızası.md").read_text(encoding="utf-8")
    assert not (vault / "00-Inbox" / "Pirzola tarifi.md").exists() and (vault / "90-Arşiv" / "00-Inbox" / "Pirzola tarifi.md").exists()
    con = brain.connect(brain.DB)
    assert con.execute("SELECT count(*) FROM docs").fetchone()[0] == 0 and con.execute("SELECT count(*) FROM chunks").fetchone()[0] == 0
    conv = json.loads((convs / "abc.json").read_text(encoding="utf-8"))
    assert conv["messages"][0]["text"] == "[unutuldu]" and conv["messages"][1]["text"] == "başka şey"
    assert sess.messages[0]["content"] == "[unutuldu]"


def test_forget_cancel_and_empty(vault):
    sess = chat.Session()
    code, r = call("POST", "/api/v2/forget", session=sess, topic="pirzola")
    assert r["proposal_id"]
    chat.decide(sess, r["proposal_id"], False)
    assert "pirzola" in (vault / "Asistan hafızası.md").read_text(encoding="utf-8")
    code, r = call("POST", "/api/v2/forget", session=sess, topic="hiçbirşeyyok")
    assert r["proposal_id"] is None and not any(r["found"].values())
    assert call("POST", "/api/v2/forget", session=sess, topic="a")[0] == 400


def test_daily_reflection(vault, monkeypatch):
    assert "veri yok" in persona.daily_reflection()
    memory.receipt("Paket B testleri yazıldı", project="second-brain", session="s1")
    seen = fake_llm(monkeypatch, "- Testler yazıldı\n- İyi gitti\n- Yarım kalan yok\n- Yarın commit\n- Dinlen\n- fazla satır")
    out = persona.daily_reflection()
    assert "5 madde" in out and seen[0][2]["private"] is True
    note = (vault / "50-Günlük" / f"{date.today():%Y-%m-%d}.md").read_text(encoding="utf-8")
    assert "## Yansıma" in note and "Testler yazıldı" in note and "fazla satır" not in note
    assert persona.reflection_of()["text"].startswith("- Testler")
    persona.daily_reflection(date.today())                                # ikinci koşu bölümü çoğaltmaz
    assert (vault / "50-Günlük" / f"{date.today():%Y-%m-%d}.md").read_text(encoding="utf-8").count("## Yansıma") == 1


def test_weekly_profile(vault, monkeypatch):
    memory.receipt("Bir iş yapıldı", project="x", session="s2")
    p = vault / "Asistan hafızası.md"
    p.write_text(p.read_text(encoding="utf-8") + f"- yeni bilgi _({date.today():%Y-%m-%d})_\n", encoding="utf-8")
    fake_llm(monkeypatch, {"learned": ["Sabah çalışmayı sever"], "changed": [], "suggestions": ["Sabah özeti gönder"]})
    out = persona.weekly_profile()
    assert "güncellendi" in out
    note = (vault / "40-Kaynaklar" / "Analiz" / "Beni tanı.md").read_text(encoding="utf-8")
    assert "yeni bilgi" in note and "Sabah çalışmayı sever" in note and "Sabah özeti gönder" in note
    monkeypatch.setattr(llm, "complete", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("model yok")))
    assert "güncellendi" in persona.weekly_profile()                      # model yoksa da kesin veriler yazılır


def test_learn_path(vault, monkeypatch):
    (vault / "20-Projeler" / "Python notları.md").write_text("---\ntype: proje\n---\n# Python notları\nlistelerle ilgili\n", encoding="utf-8")
    seen = fake_llm(monkeypatch, {"known": ["liste"], "missing": ["asyncio"],
                                  "steps": [{"title": "Fonksiyonlar", "why": "temel"}, {"title": "asyncio", "why": "eksik"}]})
    code, r = call("POST", "/api/v2/learn-path", topic="Python")
    assert code == 200 and r["path"] == "40-Kaynaklar/Öğrenme yolları/Python.md" and len(r["steps"]) == 2
    assert seen[0][2]["private"] is True
    text = (vault / r["path"]).read_text(encoding="utf-8")
    assert "- [ ] **asyncio**" in text and "[[Python notları]]" in text
    rows = call("GET", "/api/v2/learn-paths")[1]
    assert rows[0]["topic"] == "Python" and rows[0]["steps"] == 2
    fake_llm(monkeypatch, {"known": [], "missing": [], "steps": []})
    assert call("POST", "/api/v2/learn-path", topic="Boş")[0] == 502


def test_errors_board(vault):
    memory.error_log("Ollama bağlantı hatası", fix="ollama serve çalıştır")
    memory.error_log("Ollama bağlantı hatası")
    try:
        raise ValueError("kırık")
    except ValueError as e:
        telemetry.crash(e, "daily")
        telemetry.crash(e, "daily")
    telemetry.record("daily_step", "mail x", 10, ok=False)
    telemetry.record("daily_step", "index", 10, ok=True)
    code, rows = call("GET", "/api/v2/errors")
    assert code == 200
    by = {r["source"]: r for r in rows}
    assert by["katalog"]["count"] == 2 and by["katalog"]["fix"] == "ollama serve çalıştır"
    assert set(by["katalog"]) == {"key", "error", "fix", "count", "last", "source"}
    assert by["cokme"]["count"] == 2 and "kırık" in by["cokme"]["error"]
    assert by["runner"]["error"].endswith("mail x") and len(rows) == 3
