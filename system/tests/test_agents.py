import json

import pytest

from sb import agents, api_agents, brain, config, llm, vault_ops, worker
from sb.webroutes import ApiError, Ctx


@pytest.fixture
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    (v / "10-Dersler").mkdir(parents=True)
    (v / "10-Dersler" / "A.md").write_text("---\ntype: ders\n---\nDiziler.\n", encoding="utf-8")
    (v / "10-Dersler" / "P.md").write_text("---\nvisibility: private\n---\ngizli\n", encoding="utf-8")
    (v / "30-Kariyer").mkdir()
    (v / "30-Kariyer" / "x.md").write_text("özel", encoding="utf-8")
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "")
    monkeypatch.setattr(brain, "find", lambda q, k=10, **kw: [{"path": "10-Dersler/A.md", "text": "Diziler"},
                                                            {"path": "30-Kariyer/x.md", "text": "özel"}])
    monkeypatch.setattr(llm, "complete", lambda task, prompt, **kw: (f"CEVAP[{task}] " + prompt[:30], "fake"))
    from sb import search
    monkeypatch.setattr(search, "research", lambda q, web=False, **kw: {"report": "RAPOR", "sources": [{"path": "a.md"}], "web": web})
    return v


def _ctx(data=None):
    return Ctx(method="POST", path="/x", data=data or {}, query={})


def test_catalog_has_browser_soon():
    c = agents.catalog()
    assert len(c) == 6 and c[-1]["durum"] == "yakında" and c[0]["durum"] == "hazır"


def test_run_writes_single_note_and_logs(vault):
    r = agents.run("ders", "diziler nedir")
    notes = list((vault / agents.OUT_DIR).glob("*.md"))
    assert len(notes) == 1 and r["cikti"].startswith(agents.OUT_DIR)
    body = notes[0].read_text(encoding="utf-8")
    assert "10-Dersler/A.md" in body and "30-Kariyer" not in body  # klasör sınırı
    row = agents.runs()[0]
    assert row["ajan"] == "ders" and row["durum"] == "tamam" and row["model"] == "fake" and row["adim"] >= 2


def test_sandbox_denies_and_logs(vault):
    with pytest.raises(PermissionError):
        agents.Sandbox(agents.get("mail"), "t1").call("read_note", path="40-Kaynaklar/a.md")  # araç izinli değil
    with pytest.raises(PermissionError):
        agents.Sandbox(agents.get("mail"), "t1b").call("write_note", path="x.md")             # yazma aracı yok
    with pytest.raises(PermissionError):
        agents.Sandbox(agents.get("ders"), "t2").call("read_note", path="30-Kariyer/x.md")    # klasör dışı
    with pytest.raises(PermissionError):
        agents.Sandbox(agents.get("ders"), "t3").call("read_note", path="10-Dersler/../30-Kariyer/x.md")
    logged = [json.loads(x) for x in (config.DATA / "agent_runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert sum(1 for x in logged if x.get("olay") == "reddedildi") == 4


def test_private_note_not_read(vault):
    assert agents.Sandbox(agents.get("ders"), "t").call("read_note", path="10-Dersler/P.md") == ""


def test_research_agent_uses_wrapper(vault):
    r = agents.run("arastirmaci", "soru", web=True)
    assert "a.md" in (vault / r["cikti"]).read_text(encoding="utf-8") and r["model"] == "research"


def test_sensitive_and_empty_rejected(vault):
    with pytest.raises(ValueError):
        agents.run("ders", "")
    with pytest.raises(ValueError):
        agents.run("ders", "şifre 1234")
    with pytest.raises(KeyError):
        agents.run("yok", "x")


def test_flow_chains_output(vault):
    r = agents.run_flow("ders-arastir", "x")
    assert len(r["adimlar"]) == 2 and r["adimlar"][1]["ajan"] == "arastirmaci"


def test_code_bridge_only_queues(vault, monkeypatch):
    called = []
    monkeypatch.setattr(worker, "night_add", lambda t, w="": called.append((t, w)) or "Gece listesine eklendi")
    monkeypatch.setattr(worker, "night_plan", lambda: "plan")
    monkeypatch.setattr(worker, "night_start", lambda: called.append("START"))
    r = agents.code_bridge("refactor", "C:/x")
    assert r["ran"] is False and called == [("refactor", "C:/x")]
    monkeypatch.setattr(worker, "night_add", lambda t, w="": "Hata: boş")
    with pytest.raises(ValueError):
        agents.code_bridge("")


def test_night_report(vault, monkeypatch):
    n = vault / worker.NIGHT_NOTE
    n.parent.mkdir(parents=True, exist_ok=True)
    n.write_text("- [x] a\n- [!] b\n- [ ] c\n", encoding="utf-8")
    monkeypatch.setattr(vault_ops, "recent", lambda hours=26: [{"path": "p.md", "action": "update", "detail": "d"}])
    r = agents.night_report()
    assert (r["done"], r["failed"], r["pending"]) == (["a"], ["b"], ["c"]) and len(r["approvals"]) == 1


def test_routes(vault):
    assert len(api_agents._list(_ctx())) == 6
    assert api_agents._run(_ctx({"id": "ders", "input": "diziler"}))["durum"] == "tamam"
    with pytest.raises(ApiError) as e:
        api_agents._run(_ctx({"id": "yok", "input": "x"}))
    assert e.value.code == 404
    with pytest.raises(ApiError):
        api_agents._run(_ctx({"id": "ders", "input": ""}))
    assert api_agents._runs(_ctx())
