"""Kurulum motoru 1.0 genişlemesi (Paket 2): katalog, hesaplar, sırlar, modeller, MCP, veri yükleme, otomatik başlatma.
Gerçek komut/ağ/keyring/OAuth/Başlangıç klasörü/claude/ollama YOK: hepsi taklit; ağ ve sızıntı yolları ayrıca engelli."""
import http.client
import io
import json
import sys
from pathlib import Path

import pytest

SYSTEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SYSTEM))

from setup import accounts as A  # noqa: E402
from setup import autostart as AS  # noqa: E402
from setup import engine as E  # noqa: E402
from setup import imports as IM  # noqa: E402
from setup import mcp as M  # noqa: E402
from setup import server as S  # noqa: E402

_REAL_IMAP_LOGIN = E._imap_login                               # env fixture'ı değiştirmeden önceki gerçek işlev
SECRET = "sk-TESTSECRET1234567890abcdef"
PW = "hunter2-gizli-parola"


class FakeKeyring:
    def __init__(self):
        self.store = {}

    def set_password(self, svc, name, val):
        self.store[(svc, name)] = val

    def get_password(self, svc, name):
        return self.store.get((svc, name))

    def delete_password(self, svc, name):
        self.store.pop((svc, name), None)


@pytest.fixture
def env(tmp_path, monkeypatch):
    kr = FakeKeyring()
    calls = {"capture": [], "stream": []}

    def no_net(*a, **k):
        raise RuntimeError("testte gerçek ağ yok")
    monkeypatch.setattr("urllib.request.urlopen", no_net)
    monkeypatch.setattr(E, "_http", lambda *a, **k: (200, "{}"))
    monkeypatch.setattr(E, "_imap_login", lambda host, user, pw, port=993: (True, "IMAP girişi başarılı"))
    monkeypatch.setattr(A, "_post_json", no_net)
    monkeypatch.setattr(E, "_keyring", lambda: kr)
    monkeypatch.setattr(E, "kit_dir", lambda: None)
    monkeypatch.setenv("SB_APPS_DIR", str(tmp_path / "Apps"))          # gerçek ~/Applications / Masaüstü / Başlat yollarına bakma
    monkeypatch.setattr(E, "_trash", lambda: None)
    monkeypatch.setattr(E.shutil, "which", lambda n: None)

    def cap(cmd, timeout=15, cwd=None):
        calls["capture"].append(cmd)
        return 127, "yok"

    def stream(cmd, log, cwd=None):
        calls["stream"].append(cmd)
        log("$ " + " ".join(cmd))
        return 0
    monkeypatch.setattr(E, "_run_capture", cap)
    monkeypatch.setattr(E, "_run_stream", stream)
    # gerçek Başlangıç klasörü / LaunchAgents / Claude Desktop yapılandırması asla
    monkeypatch.setattr(AS, "startup_dir", lambda: tmp_path / "startup")
    monkeypatch.setattr(AS, "launch_agents_dir", lambda: tmp_path / "LaunchAgents")
    monkeypatch.setattr(M, "desktop_config_path", lambda: tmp_path / "desktop" / "claude_desktop_config.json")
    vault = tmp_path / "vault"
    (vault / "_system" / "config").mkdir(parents=True)
    (vault / "_system" / "pyproject.toml").write_text("[project]\nname='x'\n")
    (vault / "_system" / "sb").mkdir()
    eng = E.Engine(vault, data=tmp_path / "data")
    return eng, kr, calls, vault, tmp_path


@pytest.fixture
def srv(env):
    eng = env[0]
    s = S.make_server(eng).start()
    tok = s.token
    port = s.server_address[1]

    def call(method, path, body=None, raw=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        h = {"X-Setup-Token": tok, **(headers or {})}
        data = raw
        if body is not None:
            data, h["Content-Type"] = json.dumps(body).encode(), "application/json"
        c.request(method, path, body=data, headers=h)
        r = c.getresponse()
        txt = r.read().decode("utf-8")
        c.close()
        return r.status, json.loads(txt) if txt else {}
    yield call, eng
    s.stop()


# ------------------------------------------------------------------ katalog / hazır seçim / gereksinim
def test_catalog_contract(srv):
    call, _ = srv
    st, c = call("GET", "/api/catalog")
    assert st == 200 and set(c) >= {"categories", "modules", "sources", "mcps", "sectors"}
    assert sum(len(m["items"]) for m in c["modules"]) == 258
    m = c["modules"][0]
    assert set(m) >= {"id", "name", "desc", "category", "default_on", "requires", "items"}
    assert all({"id", "name", "cat"} <= set(i) for i in m["items"])
    s = c["sources"][0]
    assert set(s) >= {"id", "name", "desc", "formats", "how_to", "connector"}
    assert set(c["mcps"][0]) >= {"id", "name", "desc", "install", "docs_url", "env", "note"}
    assert any(x["install"] is None for x in c["mcps"])
    _, en = call("GET", "/api/catalog?lang=en")
    assert en["modules"][0]["name"] != "" and en["categories"] != c["categories"]


def test_presets_combine_requirements(srv, monkeypatch):
    call, _ = srv
    monkeypatch.setattr(E, "donanim_recommendation", lambda: "orta")
    st, p = call("GET", "/api/presets")
    assert st == 200 and set(p["axes"]) == {"meslek", "donanim", "gizlilik", "yogunluk"} and p["recommended"] == {"donanim": "orta"}
    assert "presets" in p                                      # eski sözleşme bozulmadı
    st, r = call("POST", "/api/combine", {"meslek": "ogrenci", "donanim": "zayif_bulut", "gizlilik": "karma", "yogunluk": "gunluk"})
    assert st == 200 and r["modules"]["courses"] is True and r["modules"]["voice"] is False
    assert set(r) >= {"modules", "items", "models", "privacy_profile", "warnings"} and len(r["items"]) == 258
    st, bad = call("POST", "/api/combine", {"meslek": "yok"})
    assert st == 400
    st, q = call("POST", "/api/requirements", {"modules": {"gmail": True, "imap": True}, "items": {}})
    assert st == 200 and "google" in q["accounts"] and isinstance(q["secrets"], list) and isinstance(q["imports"], list)


# ------------------------------------------------------------------ sihirbaz durumu ve kimlik
def test_wizard_never_stores_secrets(srv, env):
    call, eng = srv
    st, _ = call("POST", "/api/wizard", {"step": 6, "data": {"name": "Ayşe", "imap_password": PW, "openai_key": SECRET,
                                                              "note": f"anahtarım {SECRET}", "nested": {"api_key": "x", "ok": 1}}})
    assert st == 200
    raw = eng.wizard_file.read_text(encoding="utf-8")
    assert PW not in raw and SECRET not in raw and "imap_password" not in raw and "api_key" not in raw
    _, w = call("GET", "/api/wizard")
    assert w["step"] == 6 and w["data"]["name"] == "Ayşe" and w["data"]["nested"] == {"ok": 1}


def test_profile_basic(srv, env):
    call, eng = srv
    v = env[4] / "yeni-kasa"
    st, r = call("POST", "/api/profile/basic", {"name": "Ayşe", "full_name": "Ayşe Y", "vault": str(v), "timezone": "Europe/Istanbul", "org": "X"})
    assert st == 200 and eng.vault == v.resolve() and eng.selection["fields"]["org"] == "X"
    assert call("POST", "/api/profile/basic", {"name": "A", "vault": str(v), "timezone": "Mars/Olympus"})[0] == 400
    assert call("POST", "/api/profile/basic", {"name": "", "vault": str(v)})[0] == 400


# ------------------------------------------------------------------ hesaplar
def test_imap_account_saved_without_secret_in_files(srv, env):
    call, eng = srv
    _, kr, _, vault, _ = env
    st, r = call("POST", "/api/account/imap", {"alias": "is", "preset": "outlook", "user": "a@b.com", "password": PW})
    assert st == 200 and r["ok"] is True
    assert kr.store[("second-brain", "imap-is")] == PW
    y = (vault / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")
    assert PW not in y and "outlook.office365.com" in y and "preset: outlook" in y
    _, acc = call("GET", "/api/accounts")
    assert acc["imap"][0]["alias"] == "is" and acc["imap"][0]["has_password"] is True and PW not in json.dumps(acc)
    # hazır sunucu seçeneği: preset sb'de olmayanlar için host/port yazılır, preset anahtarı yazılmaz
    call("POST", "/api/account/imap", {"alias": "g", "preset": "gmail", "user": "a@gmail.com", "password": PW})
    assert "imap.gmail.com" in (vault / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")
    assert "preset: gmail" not in (vault / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")
    st, rm = call("POST", "/api/account/remove", {"alias": "is"})
    assert st == 200 and ("second-brain", "imap-is") not in kr.store
    assert [a["alias"] for a in call("GET", "/api/accounts")[1]["imap"]] == ["g"]
    assert call("POST", "/api/account/remove", {"alias": "yok"})[0] == 400


def test_imap_failure_saves_nothing(srv, env, monkeypatch):
    call, _ = srv
    _, kr, _, vault, _ = env
    monkeypatch.setattr(E, "_imap_login", lambda *a, **k: (False, "IMAP girişi başarısız: error"))
    st, r = call("POST", "/api/account/imap", {"alias": "is", "host": "mail.b.com", "user": "a@b.com", "password": PW})
    assert r["ok"] is False and not kr.store and PW not in json.dumps(r)
    assert not (vault / "_system" / "config" / "accounts.yaml").exists()
    assert call("POST", "/api/account/imap", {"alias": "../x", "host": "h.com", "user": "u", "password": "p"})[0] == 400
    assert call("POST", "/api/account/imap", {"alias": "is", "host": "a b;c", "user": "u", "password": "p"})[0] == 400


def test_google_oauth_flow_mocked(srv, env, monkeypatch):
    call, eng = srv
    _, kr, calls, vault, tmp = env
    body = {"alias": "main", "scopes": ["gmail", "calendar"], "email": "a@gmail.com"}
    assert call("POST", "/api/account/google", {**body, "scopes": ["gmail", "root"]})[0] == 400
    st, r = call("POST", "/api/account/google", body)                    # istemci dosyası yok
    assert r["ok"] is False and "client_secret" in r["message"]
    cs = tmp / "cs.json"
    cs.write_text(json.dumps({"installed": {"client_id": "x"}}))

    def fake_login(cmd, timeout=15, cwd=None):
        calls["capture"].append(cmd)
        kr.set_password("second-brain", "google:main", json.dumps({"refresh_token": "r", "scopes": []}))
        return 0, "tamam"
    monkeypatch.setattr(E, "_run_capture", fake_login)
    st, r = call("POST", "/api/account/google", {**body, "client_secret": str(cs)})
    assert r == {"ok": True, "email": "a@gmail.com", "message": "Google hesabı bağlandı"}
    assert "login" in calls["capture"][-1] and "main" in calls["capture"][-1]
    y = (vault / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")
    assert "a@gmail.com" in y and "refresh_token" not in y
    assert call("GET", "/api/accounts")[1]["google"][0]["authorized"] is True
    # başarısız giriş: kayıt geri alınır
    monkeypatch.setattr(E, "_run_capture", lambda *a, **k: (1, "kullanıcı iptal etti"))
    kr.store.clear()
    r = call("POST", "/api/account/google", {**body, "alias": "yan"})[1]
    assert r["ok"] is False and "yan" not in (vault / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")


# ------------------------------------------------------------------ sırlar
def test_secret_goes_to_keyring_only(srv, env, monkeypatch):
    call, eng = srv
    _, kr, _, vault, _ = env
    seen = []
    monkeypatch.setattr(E, "_http", lambda url, headers=None, timeout=5: (seen.append(url), (200, "{}"))[1])
    st, r = call("POST", "/api/secret", {"key": "api-openai", "value": SECRET, "test": True})
    assert st == 200 and r["ok"] and r["tested"] and r["ok"] is True and SECRET not in json.dumps(r)
    assert kr.store[("second-brain", "api-openai")] == SECRET and seen and "openai" in seen[0]
    st, lst = call("GET", "/api/secrets")
    d = {x["key"]: x["set"] for x in lst["secrets"]}
    assert d["api-openai"] is True and d["api-anthropic"] is False and SECRET not in json.dumps(lst)
    for bad in ("vault-key", "google:main", "../x", "api-"):
        assert call("POST", "/api/secret", {"key": bad, "value": "v"})[0] == 400
    eng.log(f"deneme {SECRET}")                                           # günlük maskeler
    assert SECRET not in "\n".join(eng.progress()["log"])
    for p in (eng.data, vault):
        for f in p.rglob("*"):
            if f.is_file():
                assert SECRET not in f.read_text(encoding="utf-8", errors="ignore")


# ------------------------------------------------------------------ modeller
def test_ollama_info_and_pull(srv, env, monkeypatch):
    call, eng = srv
    assert call("GET", "/api/ollama")[1]["installed"] is False

    def cap(cmd, timeout=15, cwd=None):
        if cmd[:2] == ["ollama", "--version"]:
            return 0, "ollama version is 0.6.5"
        return 0, "NAME ID SIZE MODIFIED\nqwen3:8b abc123 5.2 GB 2 days ago\nsmall:1b abc 700 MB 1 day ago"
    monkeypatch.setattr(E, "_run_capture", cap)
    o = call("GET", "/api/ollama")[1]
    assert o["installed"] and o["version"] == "0.6.5" and [m["name"] for m in o["models"]] == ["qwen3:8b", "small:1b"]

    def stream(cmd, log, cwd=None):
        log("pulling manifest")
        log("pulling abc... 45% ▕██▏")
        return 0
    monkeypatch.setattr(E, "_run_stream", stream)
    assert A.pull_model(eng, "qwen3:8b", wait=True) is True
    pr = eng.progress()
    assert pr["job"] == "pull:qwen3:8b" and pr["percent"] == 100 and pr["steps"][0]["status"] == "done"
    assert any("45%" in ln for ln in pr["log"]) and not pr["error"]
    assert call("POST", "/api/models/pull", {"name": "x; rm -rf /"})[0] == 400
    monkeypatch.setattr(E, "_run_stream", lambda cmd, log, cwd=None: 1)
    A.pull_model(eng, "qwen3:8b", wait=True)
    assert eng.progress()["error"] and eng.progress()["steps"][0]["status"] == "error"


def test_job_lock_and_voice_install(srv, env, monkeypatch):
    call, eng = srv
    _, _, calls, _, _ = env
    assert A.voice_setup(eng, True, wait=True)
    cmds = [" ".join(c) for c in calls["stream"]]
    assert any("--extra voice-gpu" in c for c in cmds) and any("voice --setup" in c for c in cmds)
    eng.running = True
    assert call("POST", "/api/voice/setup", {"gpu": False})[0] == 409
    eng.running = False
    monkeypatch.setattr(A, "_install_cmds", lambda: [["ollama-kurucu"]])
    monkeypatch.setattr(A, "ollama_info", lambda: {"installed": True})
    assert A.ollama_install(eng, wait=True) and calls["stream"][-1] == ["ollama-kurucu"]


# ------------------------------------------------------------------ MCP
def test_mcp_install_custom_remove(srv, env, monkeypatch):
    call, eng = srv
    _, kr, calls, _, tmp = env
    monkeypatch.setattr(E.shutil, "which", lambda n: "/usr/bin/claude" if n == "claude" else None)
    monkeypatch.setattr(E, "WIN", False)
    st, ov = call("GET", "/api/mcp")
    assert st == 200 and ov["catalog"] and ov["claude_cli"] is True
    # belge-yalnız
    r = call("POST", "/api/mcp/install", {"id": "atlassian"})[1]
    assert r["ok"] is False and r["docs_url"]
    # sır gerekli alan
    assert call("POST", "/api/mcp/install", {"id": "github", "env": {}})[0] == 400
    r = call("POST", "/api/mcp/install", {"id": "github", "env": {"github_pat": SECRET}})[1]
    assert r["ok"] is True and SECRET not in json.dumps(r) and SECRET not in "\n".join(eng.progress()["log"])
    assert kr.store[("second-brain", "mcp-github-github-pat")] == SECRET
    add = [c for c in calls["stream"] if c[:3] == ["claude", "mcp", "add"]][-1]
    assert f"GITHUB_PERSONAL_ACCESS_TOKEN={SECRET}" in add and add[3] == "github" and "docker" in add
    assert ["docker", "pull", "ghcr.io/github/github-mcp-server"] in calls["stream"]          # ön koşul
    # kendi MCP'm
    r = call("POST", "/api/mcp/custom", {"name": "benim", "command": "node", "args": ["s.js"], "env": {"TOK": "abc-gizli"}})[1]
    assert r["ok"] and "abc-gizli" not in json.dumps(r)
    assert call("POST", "/api/mcp/custom", {"name": "kötü ad", "command": "node"})[0] == 400
    assert call("POST", "/api/mcp/custom", {"name": "x", "command": "node", "env": {"1BAD": "v"}})[0] == 400
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (calls["capture"].append(cmd), (0, ""))[1])
    assert call("POST", "/api/mcp/remove", {"name": "benim"})[1]['ok'] is True
    assert calls["capture"][-1] == ["claude", "mcp", "remove", "benim", "-s", "user"]
    assert call("POST", "/api/mcp/remove", {"name": "a;b"})[0] == 400
    # kurulu liste: Claude Desktop yapılandırması (değerler dönmez)
    cfg = M.desktop_config_path()
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"mcpServers": {"abc": {"command": "npx", "args": ["-y", "x"], "env": {"K": SECRET}}}}))
    inst = M.installed()
    assert {"name": "abc", "source": "claude-desktop", "command": "npx -y x", "status": ""} in inst and SECRET not in json.dumps(inst)


def test_mcp_without_claude(srv):
    call, _ = srv
    r = call("POST", "/api/mcp/install", {"id": "memory"})[1]
    assert r["ok"] is False and "claude" in r["message"]


# ------------------------------------------------------------------ veri yükleme
def up(call, source, name, data: bytes):
    from urllib.parse import quote
    return call("POST", f"/api/import/upload?source={source}&name={quote(name)}", raw=data)


def test_upload_sanitises_and_limits(srv, env, monkeypatch):
    call, eng = srv
    st, r = up(call, "kindle", "../../evil/..\\Clippings.txt", b"hello")
    assert st == 200 and r["file"] == "Clippings.txt"
    f = eng.data / "import_staging" / "kindle" / "Clippings.txt"
    assert f.read_bytes() == b"hello"
    assert not list((eng.data).rglob("evil*"))
    assert up(call, "yok-kaynak", "a.txt", b"x")[0] == 400
    assert up(call, "../x", "a.txt", b"x")[0] == 400
    assert up(call, "kindle", "..", b"x")[0] == 400
    assert call("POST", "/api/import/upload?source=kindle&name=a.txt", raw=b"")[0] == 400
    monkeypatch.setattr(IM, "MAX_UPLOAD", 10)
    st, r = up(call, "kindle", "big.txt", b"x" * 11)
    assert st == 413 and not (eng.data / "import_staging" / "kindle" / "big.txt").exists()
    assert not list((eng.data / "import_staging").rglob("*.part"))


def test_import_preview_and_run(srv, env, monkeypatch):
    call, eng = srv
    _, _, calls, _, _ = env
    up(call, "kindle", "Clippings.txt", b"x")
    assert call("POST", "/api/import/preview", {"source": "kindle", "file": "yok.txt"})[0] == 400
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (calls["capture"].append(cmd), (0, f"kindle: okunan 12, yeni olacak 12 {SECRET}"))[1])
    st, p = call("POST", "/api/import/preview", {"source": "kindle", "file": "Clippings.txt"})
    assert st == 200 and p["ok"] and p["read"] == 12 and SECRET not in json.dumps(p)
    cmd = calls["capture"][-1]
    assert "import" in cmd and "kindle" in cmd and "--dry-run" in cmd
    assert call("POST", "/api/import/run", {"source": "kindle", "file": "Clippings.txt"})[0] == 202
    eng._thread.join()
    cmd = calls["stream"][-1]
    assert "import" in cmd and "--dry-run" not in cmd
    h = call("GET", "/api/imports")[1]["imports"]
    assert h and h[-1]["source"] == "kindle" and h[-1]["ok"] is True
    # bağlayıcısı olmayan kaynak
    up(call, "linkedin", "arsiv.zip", b"x")
    r = call("POST", "/api/import/preview", {"source": "linkedin", "file": "arsiv.zip"})[1]
    assert r["ok"] is False and r["supported"] is False
    assert call("POST", "/api/import/run", {"source": "linkedin", "file": "arsiv.zip"})[0] == 400


# ------------------------------------------------------------------ telefon
def test_phone(srv, env, monkeypatch):
    call, _ = srv
    r = call("GET", "/api/phone")[1]
    assert r["installed"] is False and r["connected"] is False
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (0, "100.101.102.103\n"))
    monkeypatch.setattr(A, "_post_json", lambda url, obj, timeout=4: {"pin": "123456", "devices": 2})
    r = call("GET", "/api/phone")[1]
    assert r["connected"] and r["address"] == "http://100.101.102.103:8765" and r["pairing_code"] == "123456" and r["devices"] == 2
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (0, "8.8.8.8\n"))     # Tailscale aralığı dışı
    assert call("GET", "/api/phone")[1]["connected"] is False


# ------------------------------------------------------------------ otomatik başlatma
def test_autostart_only_when_on(srv, env, monkeypatch):
    call, eng = srv
    _, _, calls, _, tmp = env
    monkeypatch.setattr(AS.sys, "platform", "win32")
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (calls["capture"].append(cmd), (0, ""))[1])
    r = call("POST", "/api/autostart", {"on": False})[1]
    assert r["ok"] and not (tmp / "startup").exists() and calls["capture"] == []          # kapalıyken hiçbir şey yazılmaz
    assert call("POST", "/api/autostart", {})[0] == 400                                   # on belirtilmedi
    assert not (tmp / "startup").exists()
    # PowerShell taklidi kısayolu oluşturur
    def fake_ps(cmd, timeout=15, cwd=None):
        calls["capture"].append(cmd)
        (tmp / "startup").mkdir(parents=True, exist_ok=True)
        (tmp / "startup" / AS.LNK).write_text("lnk")
        return 0, ""
    monkeypatch.setattr(E, "_run_capture", fake_ps)
    r = call("POST", "/api/autostart", {"on": True, "minimized": True})[1]
    assert r["ok"] and r["on"] is True and r["command"][-2:] == ["app.desktop", "--minimized"] and r["command"][0].endswith("pythonw.exe")
    ps = calls["capture"][-1]
    assert ps[0] == "powershell" and "WScript.Shell" in ps[-1] and "--minimized" in ps[-1] and "-m app.desktop" in ps[-1]
    assert call("GET", "/api/autostart")[1]["on"] is True
    call("POST", "/api/autostart", {"on": False})
    assert not (tmp / "startup" / AS.LNK).exists() and call("GET", "/api/autostart")[1]["on"] is False


def test_autostart_exe_and_macos(env, monkeypatch):
    eng, _, _, vault, tmp = env
    exe = vault / "_system" / "Second Brain.exe"
    exe.write_text("x")
    prog, args, _ = AS.launch_command(eng, True, "win32")
    assert prog == str(exe) and args == ["--minimized"]
    exe.unlink()
    monkeypatch.setattr(E, "launcher_exe", lambda data, plat=None: None)     # kurulu uygulama araması taklit (CI'da gerçek .app olabilir)
    r = AS.apply(eng, True, False, plat="darwin")
    import plistlib
    pl = plistlib.loads((tmp / "LaunchAgents" / AS.PLIST).read_bytes())
    assert r["ok"] and pl["RunAtLoad"] and pl["ProgramArguments"][-2:] == ["-m", "app.desktop"] and ".venv/bin/python" in pl["ProgramArguments"][0].replace("\\", "/")
    assert AS.apply(eng, False, plat="darwin")["on"] is False and not (tmp / "LaunchAgents" / AS.PLIST).exists()
    assert AS.apply(eng, True, plat="linux")["supported"] is False


# ------------------------------------------------------------------ apply: seçim → features.yaml + plugins.yaml
def test_apply_writes_plugin_selection(srv, env):
    call, eng = srv
    _, _, _, vault, _ = env
    st, r = call("POST", "/api/apply", {"preset": "minimal", "fields": {"name": "Ayşe", "vault": str(vault), "openai_key": SECRET},
                                        "selection": {"modules": {"gmail": True, "courses": False, "imports_life": True},
                                                      "items": {"1": True, "2": False}}})
    assert st == 202
    eng._thread.join()
    import yaml
    cfg = vault / "_system" / "config"
    feats = yaml.safe_load((cfg / "features.yaml").read_text(encoding="utf-8"))["modules"]
    assert feats["gmail"] is True and feats["courses"] is False and "imports_life" not in feats
    pl = yaml.safe_load((cfg / "plugins.yaml").read_text(encoding="utf-8"))
    assert pl["modules"]["imports_life"] is True and pl["items"] == {"1": True, "2": False}
    # kurulum sonrası ilerleme adımları normal ve sır sızmadı
    assert [s["id"] for s in eng.progress()["steps"]][0] == "vault"
    for f in list(eng.data.rglob("*")) + list(vault.rglob("*")):
        if f.is_file():
            assert SECRET not in f.read_text(encoding="utf-8", errors="ignore")
    assert SECRET not in "\n".join(eng.progress()["log"])


def test_requires_token(srv, env):
    call, eng = srv
    s = S.make_server(eng).start()
    try:
        c = http.client.HTTPConnection("127.0.0.1", s.server_address[1])
        c.request("POST", "/api/secret", body=b"{}")
        assert c.getresponse().status == 403
    finally:
        s.stop()


# ------------------------------------------------------------------ canlı deneme bulguları (2026-11-04)
def test_madde13_imap_hatalari_anlasilir_turkce(monkeypatch):
    import imaplib
    import socket
    import ssl
    msg = E.imap_error_message
    m = msg(ConnectionRefusedError(), "imap.x.com", 993)
    assert "ConnectionRefused" not in m and "Bağlanılamadı" in m and "imap.x.com:993" in m
    assert "Sunucu bulunamadı" in msg(socket.gaierror(11001, "x"), "yok.example", 993)
    assert "zaman aşımı" in msg(socket.timeout(), "h", 993)
    assert "port 993" in msg(ssl.SSLError("x"), "h", 143)
    a = msg(imaplib.IMAP4.error("[AUTHENTICATIONFAILED] Invalid credentials"), "h", 993)
    assert "UYGULAMA ŞİFRESİ" in a and "Kimlik reddedildi" in a
    # gerçek _imap_login: istisna adı kullanıcıya sızmaz
    class Boom:
        def __init__(self, *a, **k):
            raise ConnectionRefusedError()
    monkeypatch.setattr(imaplib, "IMAP4_SSL", Boom)
    ok, text = _REAL_IMAP_LOGIN("imap.x.com", "u", "p", 993)
    assert ok is False and "ConnectionRefusedError" not in text and "Bağlanılamadı" in text


def test_madde11_okul_hesabi_sir_yazmaz(srv, env):
    call, eng = srv
    _, kr, _, vault, _ = env
    st, r = call("POST", "/api/account/school", {"url": "https://obs.okul.edu.tr", "user": "2021001"})
    assert st == 200 and r["ok"] is True
    assert call("POST", "/api/secret", {"key": "svc-school-password", "value": PW})[0] == 200
    assert kr.store[("second-brain", "svc-school-password")] == PW
    y = (vault / "_system" / "config" / "accounts.yaml").read_text(encoding="utf-8")
    assert "obs.okul.edu.tr" in y and "2021001" in y and PW not in y
    assert call("GET", "/api/accounts")[1]["school"]["has_password"] is True
    assert call("POST", "/api/account/school", {"url": "bad host!", "user": "x"})[0] == 400


def test_madde12_madde20_ozet_ve_sir_adlari(srv, env):
    call, eng = srv
    _, kr, _, vault, _ = env
    call("POST", "/api/secret", {"key": "telegram-bot", "value": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"})
    st, sm = call("GET", "/api/summary")
    assert st == 200 and sm["secrets"] == ["telegram-bot"] and "ABC-DEF" not in json.dumps(sm)
    assert eng.stored_secret_names() == ["telegram-bot"]


def test_madde9_kendi_mcp_belgesi_kullanici_belgesi():
    m = E.plugins_mod().get("second-brain", "mcp")
    doc = m["mcp"]["docs_url"]
    assert doc == "docs/mcp-second-brain.md" and "v1-plan" not in doc
    assert (SYSTEM / doc).is_file() and not E.internal_doc(Path(doc).name)
    first = [x for x in E.catalog("tr")["mcps"] if x["id"] == "second-brain"][0]
    assert first["docs_url"] == doc


def test_madde1_code_root_kasa_secilince_hedef_kasa(tmp_path, monkeypatch):
    """Gerçek kipte de: kurulumdan önce çalışan kurulumun değil, HEDEF kasanın _system'i; kod yoksa kit'ten kopyalanır."""
    kit = tmp_path / "kit"
    (kit / "system" / "sb").mkdir(parents=True)
    (kit / "system" / "sb" / "__init__.py").write_text("", encoding="utf-8")
    (kit / "system" / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (kit / "system" / "config").mkdir()
    (kit / "system" / "config" / "profile.example.yaml").write_text("name: x\n", encoding="utf-8")
    (kit / "system" / "config" / "profile.yaml").write_text("bio: kisisel\n", encoding="utf-8")
    monkeypatch.setattr(E, "kit_dir", lambda: kit)
    eng = E.Engine(tmp_path / "hedef", data=tmp_path / "data")
    root = eng.code_root()
    assert root == (tmp_path / "hedef" / "_system") and (root / "sb" / "__init__.py").is_file()
    assert not (root / "config" / "profile.yaml").exists() and (root / "config" / "profile.example.yaml").is_file()
    cmd = eng.sb_cmd("import", "x")
    assert str(kit) not in " ".join(cmd) and str(root) in cmd
    with pytest.raises(RuntimeError):                          # kasa kitin içinde olamaz
        E.Engine(kit / "system" / "v", data=tmp_path / "d2").prepare_code()


def test_madde_ice_aktarma_sayisi_kaydedilir(srv, env, monkeypatch):
    call, eng = srv
    assert IM.parse_count(["  42 mesaj yazıldı"]) == 42
    IM._record(eng, "whatsapp", "a.txt", True, "ok", 42)
    assert call("GET", "/api/imports")[1]["imports"][-1]["count"] == 42
