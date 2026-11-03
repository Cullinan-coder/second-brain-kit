"""Kurulum motoru + yerel sunucu (Paket S): gerçek ağ/kurulum/zamanlanmış görev yok; her şey taklit."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

SYSTEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SYSTEM))

from setup import engine as E  # noqa: E402
from setup import server as S  # noqa: E402

SECRET = "sk-TESTSECRET1234567890abcdef"


class FakeKeyring:
    def __init__(self):
        self.store = {}

    def set_password(self, svc, name, val):
        self.store[(svc, name)] = val

    def get_password(self, svc, name):
        return self.store.get((svc, name))


@pytest.fixture
def env(tmp_path, monkeypatch):
    kr = FakeKeyring()
    cmds = []
    monkeypatch.setattr(E, "_keyring", lambda: kr)
    monkeypatch.setattr(E, "kit_dir", lambda: None)
    monkeypatch.setattr(E, "_run_stream", lambda cmd, log, cwd=None: (cmds.append(cmd), log("$ " + " ".join(cmd)), log(f"çıktı {SECRET}"), 0)[-1])
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (0, " ✓ Profil\n ! Ollama   → kur\n\nSürüm 0.9.0 · 2 kontrol"))
    monkeypatch.setattr(E, "_trash", lambda: None)
    monkeypatch.setattr(E.shutil, "which", lambda n: None)
    vault = tmp_path / "vault"
    cfg = vault / "_system" / "config"
    cfg.mkdir(parents=True)
    (vault / "_system" / "pyproject.toml").write_text("[project]\nname='x'\n")
    (vault / "_system" / "sb").mkdir()
    (cfg / "profile.example.yaml").write_text("name: x\n")
    (cfg / "accounts.example.yaml").write_text("google: {}\nimap: {}\n")
    (vault / "20-Projeler").mkdir()
    (vault / "20-Projeler" / "not.md").write_text("benim notum")
    eng = E.Engine(vault, data=tmp_path / "data")
    return eng, kr, cmds, vault


def sel(vault, **extra):
    f = {"name": "Ayşe", "vault": str(vault), "imap_alias": "is", "imap_email": "a@b.com", "imap_host": "mail.b.com",
         "imap_password": "hunter2-gizli", "openai_key": SECRET, "gmail": "a@gmail.com"}
    f.update(extra)
    return {"preset": "ogrenci", "fields": f}


# -- hazır seçimler
def test_presets_map_to_real_modules():
    from sb import features
    assert set(E._ALL) == set(features.MODULES)               # motor listesi kasadaki MODULES ile aynı kalmalı
    for name, p in E.PRESETS.items():
        assert set(p["modules"]) == set(features.MODULES), name
    assert E.PRESETS["minimal"]["modules"]["assistant"] and not E.PRESETS["minimal"]["modules"]["gmail"]
    assert E.PRESETS["ogrenci"]["modules"]["courses"] and not E.PRESETS["ogrenci"]["modules"]["imap"]
    assert E.PRESETS["ajans"]["modules"]["imap"] and E.PRESETS["ajans"]["modules"]["projects"]
    assert E.PRESETS["bulut"]["local_model"] is False and E.PRESETS["tam"]["local_model"] is True
    assert E.PRESETS["tam"]["modules"]["gmail"] and not E.PRESETS["tam"]["modules"]["wake_word"]


def test_modules_meta_matches_features():
    from sb import features
    meta = E.modules_meta() if E.code_dir() else {}
    assert set(meta) == set(features.MODULES)
    assert meta["gmail"]["name"] == features.MODULES["gmail"][0] and meta["gmail"]["category"] == "Mail ve takvim"


def test_fields_depend_on_preset():
    keys = lambda p: {f["key"] for f in E.fields_for(E.preset_modules(p), E.PRESETS[p]["local_model"])}  # noqa: E731
    assert "imap_password" not in keys("ogrenci") and "imap_password" in keys("ajans")
    assert "anthropic_key" in keys("bulut") and "anthropic_key" not in keys("tam")
    assert {"name", "vault"} <= keys("minimal")
    assert all(f["secret"] == (f["kind"] == "secret") for f in E.fields_for(E.preset_modules("tam")))


# -- donanım
def test_hardware_recommend(monkeypatch):
    monkeypatch.setattr(E, "MAC", False)                                         # macOS CI: Apple Silicon yolu değil, NVIDIA yolu
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (0, "NVIDIA RTX 4080, 16376"))
    hw = E.hardware()
    assert hw["vram_gb"] == 16.0 and E.recommend(hw)["profile"] == "full"
    assert E.recommend({"vram_gb": None})["profile"] == "cloud"
    assert E.recommend({"vram_gb": 8})["profile"] == "medium" and E.recommend({"vram_gb": 6})["profile"] == "small"


# -- kurulum: sırlar
def test_secrets_only_in_keyring_never_in_files_or_log(env):
    eng, kr, cmds, vault = env
    assert eng.apply(sel(vault), wait=True)
    assert eng.error == ""
    assert kr.store[("second-brain", "imap-is")] == "hunter2-gizli" and kr.store[("second-brain", "api-openai")] == SECRET
    log = "\n".join(eng.progress()["log"])
    assert SECRET not in log and "hunter2-gizli" not in log and "***" in log
    blobs = [p.read_text(encoding="utf-8") for p in list((vault / "_system" / "config").iterdir()) + [eng.state_file]]
    assert all(SECRET not in b and "hunter2" not in b for b in blobs)
    assert "imap_password" not in eng.state_file.read_text(encoding="utf-8")
    assert "imap_password" not in eng.selection["fields"]
    feats = (vault / "_system" / "config" / "features.yaml").read_text(encoding="utf-8")
    assert "courses: true" in feats and "imap: false" in feats
    assert "is:" in (vault / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")


def test_no_keyring_fails_without_file_fallback(env, monkeypatch):
    eng, kr, cmds, vault = env
    monkeypatch.setattr(E, "_keyring", lambda: None)
    eng.apply(sel(vault), wait=True)
    assert "keyring" in eng.error and "hunter2" not in eng.error
    assert eng.progress()["steps"][2]["status"] == "error"
    for p in vault.rglob("*"):
        if p.is_file():
            assert "hunter2-gizli" not in p.read_text(encoding="utf-8", errors="ignore")


def test_redact():
    assert "abc" not in E.redact("anahtar abc kullan", ["abc"])
    assert E.redact(f"key {SECRET}") == "key ***"
    assert "gizli" not in E.redact("password=gizli")


# -- sürdürme
def test_resume_skips_done_steps(env):
    eng, kr, cmds, vault = env
    eng.save_state(["vault", "config"])
    st = eng.state()
    assert st["resumable"] and st["done"] == ["vault", "config"] and "secrets" in st["pending"]
    eng.selection = {"preset": "ogrenci", "modules": E.preset_modules("ogrenci"), "fields": {"vault": str(vault), "name": "x"}}
    eng.apply(resume=True, wait=True)
    assert eng.error == ""
    assert not (vault / "_system" / "config" / "profile.yaml").exists()      # config adımı yeniden koşmadı
    assert eng.state()["done"][-1] == "shortcuts" and not eng.state()["resumable"]
    assert eng.progress()["percent"] == 100


def test_failed_step_is_resumable(env, monkeypatch):
    eng, kr, cmds, vault = env
    (vault / "_system" / "pyproject.toml").unlink()
    eng.apply(sel(vault), wait=True)
    assert "pyproject" in eng.error and eng.state()["done"] == ["vault", "config", "secrets"]
    assert eng.state()["resumable"]


# -- geri alma / kaldırma
def test_disable_module_keeps_files(env):
    eng, kr, cmds, vault = env
    eng.apply(sel(vault), wait=True)
    before = sorted(p.name for p in (vault / "_system" / "config").iterdir())
    r = eng.disable_modules(["courses"])
    assert r["disabled"] == ["courses"]
    assert "courses: false" in (vault / "_system" / "config" / "features.yaml").read_text(encoding="utf-8")
    assert sorted(p.name for p in (vault / "_system" / "config").iterdir()) == before
    with pytest.raises(ValueError):
        eng.disable_modules(["yok"])


def test_uninstall_plan_then_confirm_never_touches_notes(env, monkeypatch):
    eng, kr, cmds, vault = env
    eng.vault = vault
    trashed = []
    monkeypatch.setattr(E, "_trash", lambda: trashed.append)
    r = eng.uninstall(False)
    assert r["applied"] is False and any(a["id"] == "code" for a in r["plan"]) and not trashed
    r = eng.uninstall(True)
    assert r["applied"] and trashed == [str(vault / "_system")]
    assert (vault / "20-Projeler" / "not.md").read_text() == "benim notum"
    monkeypatch.setattr(E, "_trash", lambda: None)               # send2trash yok → yalnız listele
    plan = eng.uninstall(True)
    assert "code" not in plan["done"] and (vault / "_system").exists()


# -- bağlantı testleri, sağlık, güncelleme, profil
def test_connection_tests(env, monkeypatch):
    eng, kr, cmds, vault = env
    calls = []

    def fake_http(url, headers=None, timeout=5):
        calls.append((url, headers))
        return (200, "") if "openai" in url or "11434" in url else (401, "")
    monkeypatch.setattr(E, "_http", fake_http)
    assert eng.test("ollama")["ok"]
    assert eng.test("openai", {"openai_key": SECRET})["ok"]
    assert not eng.test("anthropic", {"anthropic_key": "x" * 10})["ok"]
    assert eng.test("gemini")["message"] == "Anahtar girilmedi"
    monkeypatch.setattr(E, "_imap_login", lambda h, u, p: (True, "ok"))
    assert eng.test("imap", {"imap_host": "h", "imap_email": "e", "imap_password": "p"})["ok"]
    assert not eng.test("bilinmeyen")["ok"]
    assert SECRET not in json.dumps(eng.test("openai", {"openai_key": SECRET}))
    assert any(h and h.get("Authorization") == f"Bearer {SECRET}" for _, h in calls)
    (vault / ".obsidian").mkdir()
    assert eng.test("obsidian")["ok"]


def test_health_update_profile(env, monkeypatch):
    eng, kr, cmds, vault = env
    h = eng.health()
    assert [r["status"] for r in h["rows"]] == ["ok", "warn"] and h["rows"][1]["hint"] == "kur" and h["ok"] and "0.9.0" in h["summary"]
    assert E.latest_tag("a\trefs/tags/v0.9.0\nb\trefs/tags/v0.10.1\nc\trefs/tags/junk") == "0.10.1"
    (vault / "_system" / "VERSION").write_text("0.8.1")
    assert eng.version_info()["current"] == "0.8.1"
    eng.set_selection(sel(vault))
    p = eng.export_profile()
    assert "imap_password" not in p["fields"] and "openai_key" not in p["fields"] and p["fields"]["name"] == "Ayşe"
    eng2 = E.Engine(data=eng.data)
    eng2.import_profile({"preset": "ajans", "fields": {"name": "Z", "openai_key": SECRET}, "modules": {"whatsapp": False}})
    assert eng2.selection["modules"]["imap"] and not eng2.selection["modules"]["whatsapp"] and "openai_key" not in eng2.selection["fields"]
    with pytest.raises(ValueError):
        eng2.import_profile({"modules": {"yok": True}})


def test_sha256_verify(tmp_path):
    f = tmp_path / "k.zip"
    f.write_bytes(b"merhaba")
    h = E.sha256_file(f)
    assert E.verify_file(f, h.upper()) and not E.verify_file(f, "0" * 64)
    assert E.main(["--verify", str(f), h]) == 0 and E.main(["--verify", str(f), "0" * 64]) == 2


def test_silent_cli_needs_yes():
    assert E.main(["--preset", "minimal"]) == 1


# -- sunucu
@pytest.fixture
def srv(env):
    eng, kr, cmds, vault = env
    s = S.make_server(eng).start()
    yield s, eng, vault
    s.stop()


def call(srv, method, path, body=None, token=True, headers=None):
    s = srv
    h = {"Content-Type": "application/json", **(headers or {})}
    if token:
        h["X-Setup-Token"] = s.token
    req = urllib.request.Request(f"http://127.0.0.1:{s.server_address[1]}{path}", method=method, headers=h,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def test_server_token_required(srv):
    s, eng, vault = srv
    for method, path in (("GET", "/api/presets"), ("POST", "/api/apply"), ("GET", "/api/profile"), ("POST", "/api/shutdown"),
                         ("GET", "/api/progress")):
        assert call(s, method, path, {} if method == "POST" else None, token=False)[0] == 403
    assert call(s, "GET", "/api/presets", headers={"X-Setup-Token": "yanlis"}, token=False)[0] == 403
    assert call(s, "GET", "/api/presets")[0] == 200
    assert call(s, "GET", f"/api/presets?t={s.token}", token=False)[0] == 403         # API'de jeton URL'den kabul edilmez
    assert call(s, "GET", "/api/presets", headers={"Host": "evil.com"})[0] == 403
    assert call(s, "GET", "/api/presets", headers={"Origin": "http://evil.com"})[0] == 403
    assert s.url.startswith("http://127.0.0.1:") and s.url.endswith(s.token)


def test_server_static_open_api_needs_token_and_blocks_traversal(srv):
    s, eng, vault = srv
    ui = S.UI
    ui.mkdir(exist_ok=True)
    made = not (ui / "index.html").exists()
    if made:
        (ui / "index.html").write_text("<html></html>")
    try:
        base = f"http://127.0.0.1:{s.server_address[1]}"
        assert urllib.request.urlopen(base + "/").status == 200                    # arayüz dosyaları jetonsuz (sır yok)
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(base + f"/api/state?t={s.token}")              # API: jeton yalnız başlıktan
        assert e.value.code == 403
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(base + f"/ui/..%2Fengine.py?t={s.token}")
        assert e.value.code == 404
    finally:
        if made:
            (ui / "index.html").unlink()


def test_server_flow(srv):
    s, eng, vault = srv
    code, j = call(s, "GET", "/api/presets")
    assert set(j["presets"]) == {"tam", "bulut", "minimal", "ogrenci", "ajans"} and "gmail" in j["modules"]
    code, j = call(s, "GET", "/api/fields?preset=ajans")
    assert any(f["key"] == "imap_password" and f["secret"] for f in j["fields"])
    assert call(s, "GET", "/api/hardware")[1]["recommend"]["profile"] in E.PROFILES
    code, j = call(s, "POST", "/api/apply", sel(vault))
    assert code == 202
    eng._thread.join(10)
    code, j = call(s, "GET", "/api/progress")
    assert j["percent"] == 100 and not j["running"] and j["error"] == "" and len(j["log"]) <= 200
    assert SECRET not in json.dumps(j) and "hunter2" not in json.dumps(j)
    code, j = call(s, "GET", "/api/profile")
    assert "hunter2" not in json.dumps(j) and SECRET not in json.dumps(j)
    assert call(s, "POST", "/api/profile", j)[1]["ok"]
    assert call(s, "POST", "/api/test", {"kind": "yok"})[1]["ok"] is False
    assert call(s, "GET", "/api/health")[1]["rows"]
    assert call(s, "GET", "/api/state")[1]["done"][-1] == "shortcuts"
    code, j = call(s, "POST", "/api/uninstall", {})
    assert j["applied"] is False
    assert call(s, "POST", "/api/modules/disable", {"keys": ["yok"]})[0] == 400
    assert call(s, "POST", "/api/apply", {"preset": "yok"})[0] == 400
    assert call(s, "GET", "/api/bilinmeyen")[0] == 404
    assert (vault / "20-Projeler" / "not.md").read_text() == "benim notum"


def test_server_busy_returns_409(srv):
    s, eng, vault = srv
    eng.running = True
    assert call(s, "POST", "/api/apply", sel(vault))[0] == 409
    eng.running = False
