"""Bilgi kartları + SM-2 (sahte model, geçici kasa/DATA)."""
import json
from datetime import date, timedelta

import pytest

from sb import chat, flashcards, llm, vault_ops, webroutes
import sb.api_memory  # noqa: F401


@pytest.fixture
def vault(monkeypatch, tmp_path):
    v = tmp_path / "vault"
    (v / "40-Kaynaklar" / "Kavramlar").mkdir(parents=True)
    (v / "10-Dersler").mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", v)
    return v


def call(method, url, **data):
    r = webroutes.find(method, url)
    ctx = webroutes.Ctx(method, url, data=data if method == "POST" else {}, query={k: str(v) for k, v in data.items()} if method == "GET" else {},
                        session=chat.Session())
    code, body, _, _ = webroutes.call(r, ctx)
    return code, json.loads(body)


def test_sm2_progression():
    t0 = date(2026, 11, 1)
    c = {"ease": 2.5, "interval": 0, "reps": 0, "due": str(t0)}
    flashcards.sm2(c, 5, t0)
    assert (c["reps"], c["interval"], c["due"]) == (1, 1, "2026-11-02") and c["ease"] == 2.6
    flashcards.sm2(c, 4, t0)
    assert (c["reps"], c["interval"]) == (2, 6) and c["ease"] == 2.6
    flashcards.sm2(c, 4, t0)
    assert c["interval"] == round(6 * 2.6) and c["reps"] == 3
    flashcards.sm2(c, 1, t0)                                              # başarısız: baştan, yarın
    assert (c["reps"], c["interval"], c["due"]) == (0, 1, "2026-11-02")
    for _ in range(30):
        flashcards.sm2(c, 3, t0)
    assert c["ease"] >= 1.3
    with pytest.raises(ValueError):
        flashcards.sm2(c, 6)


def test_add_due_decks_endpoints():
    code, c = call("POST", "/api/v2/cards/add", deck="Fizik", front="Newton'un 2. yasası?", back="F = m·a")
    assert code == 200 and c["due"] == str(date.today()) and c["reps"] == 0
    assert call("POST", "/api/v2/cards/add", deck="Fizik", front="newton'un 2. yasası?", back="başka")[1]["id"] == c["id"]   # kopya yok
    assert call("POST", "/api/v2/cards/add", deck="Fizik", front="", back="x")[0] == 400
    assert call("POST", "/api/v2/cards/add", deck="Fizik", front="PIN", back="şifre 1234")[0] == 400
    call("POST", "/api/v2/cards/add", deck="Kimya", front="H2O?", back="su")
    assert [d for d in call("GET", "/api/v2/cards/decks")[1] if d["deck"] == "Fizik"] == [{"deck": "Fizik", "total": 1, "due": 1}]
    assert len(call("GET", "/api/v2/cards/due", limit=20)[1]) == 2
    assert len(call("GET", "/api/v2/cards/due", deck="Kimya")[1]) == 1
    code, r = call("POST", "/api/v2/cards/review", id=c["id"], grade=5)
    assert code == 200 and r["due"] == str(date.today() + timedelta(days=1))
    assert [x["deck"] for x in call("GET", "/api/v2/cards/due")[1]] == ["Kimya"]
    assert call("POST", "/api/v2/cards/review", id=c["id"], grade=9)[0] == 400
    assert call("POST", "/api/v2/cards/review", id="yok", grade=3)[0] == 404


def test_generate(vault, monkeypatch):
    (vault / "40-Kaynaklar" / "Kavramlar" / "Entropi.md").write_text("---\ntype: kaynak\n---\n# Entropi\nDüzensizliğin ölçüsüdür.\n", encoding="utf-8")
    (vault / "10-Dersler" / "Termodinamik.md").write_text("---\ntype: ders\n---\n# Termodinamik\nİkinci yasa: entropi artar.\n", encoding="utf-8")
    seen = []

    def fake(task, prompt, **kw):
        seen.append(kw)
        return json.dumps({"cards": [{"front": "Entropi nedir?", "back": "Düzensizlik ölçüsü"}, {"front": "İkinci yasa?", "back": "Entropi artar"},
                                     {"front": "", "back": "boş"}]}), "yerel"
    monkeypatch.setattr(llm, "complete", fake)
    code, r = call("POST", "/api/v2/cards/generate", path="40-Kaynaklar/Kavramlar/Entropi.md", n=5)
    assert code == 200 and len(r["added"]) == 2 and r["skipped"] == 1 and r["deck"] == "Entropi"
    assert r["added"][0]["source"] == "40-Kaynaklar/Kavramlar/Entropi.md" and seen[0]["private"] is True
    assert call("POST", "/api/v2/cards/generate", path="40-Kaynaklar/Kavramlar/Entropi.md")[1]["added"] == []   # tekrar kopyalamaz
    code, r = call("POST", "/api/v2/cards/generate", course="Termodinamik")
    assert code == 200 and r["deck"] == "Termodinamik"
    assert call("POST", "/api/v2/cards/generate", path="yok.md")[0] == 404
    assert call("POST", "/api/v2/cards/generate")[0] == 400
