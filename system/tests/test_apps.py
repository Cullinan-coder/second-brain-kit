"""sb/apps.py: hazır uygulamalar (ClipBoardLine, Nashi) — ağsız (sahte indirme), gerçek kayıt defteri/süreç/kurucu YOK."""
import hashlib
import io
import json
import zipfile
from argparse import Namespace

import pytest

from sb import apps

NASHI_REL = "https://github.com/orkunisitmak/nashi-app/releases/download/v0.7.14-45/"
CBL_REL = "https://github.com/orkunisitmak/clipboardline/releases/download/windows-1.7.8-build71/"


class Resp(io.BytesIO):
    def __init__(self, data: bytes, status: int = 200, headers: dict | None = None):
        super().__init__(data)
        self.status = status
        self.headers = headers if headers is not None else {"Content-Length": str(len(data))}


def make_zip(files: dict[str, bytes], top: str = "") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(top + name, data)
    return buf.getvalue()


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Windows ortamı taklidi: ortam değişkenleri tmp altında, kayıt defteri/süreç/kurucu sahte."""
    monkeypatch.delenv("SB_SETUP_SANDBOX", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setattr(apps, "plat", lambda: "win")
    reg: dict[str, str] = {}
    monkeypatch.setattr(apps, "_reg_set", lambda n, v: reg.__setitem__(n, v))
    monkeypatch.setattr(apps, "_reg_get", lambda n: reg.get(n))
    monkeypatch.setattr(apps, "_reg_del", lambda n: reg.pop(n, None))
    procs: set[str] = set()
    monkeypatch.setattr(apps, "_proc_running", lambda name: name in procs)
    spawned: list = []
    monkeypatch.setattr(apps, "_spawn", lambda cmd, cwd=None: spawned.append((cmd, cwd)))
    served: dict[str, bytes] = {}
    opened: list[str] = []

    def fake_open(url, headers=None, timeout=60):
        apps.check_url(url)
        opened.append(url)
        if url not in served:
            raise OSError("404")
        return Resp(served[url])
    monkeypatch.setattr(apps, "_open", fake_open)
    monkeypatch.setattr(apps, "NSIS_WAIT", 0)
    shortcuts: list = []
    monkeypatch.setattr(apps, "start_menu_shortcut", lambda name, exe: shortcuts.append((name, exe)) or None)
    return type("Env", (), {"reg": reg, "procs": procs, "spawned": spawned, "served": served, "opened": opened,
                            "tmp": tmp_path, "shortcuts": shortcuts})


def serve_nashi(env, payload: bytes | None = None, sha: str | None = None):
    payload = payload or make_zip({"Nashi.exe": b"MZ-nashi", "lib/x.dll": b"dll"})
    env.served[NASHI_REL + "Nashi-Windows-x64.zip"] = payload
    env.served[NASHI_REL + "SHA256SUMS.txt"] = f"{sha or hashlib.sha256(payload).hexdigest()}  Nashi-Windows-x64.zip\n".encode()
    return payload


# ------------------------------------------------------------------ katalog ve durum
def test_catalog_from_manifests():
    assert apps.ids() == ["clipboardline", "nashi"]
    s = apps.spec("nashi", "win")
    assert s["asset"] == "Nashi-Windows-x64.zip" and s["method"] == "zip-extract" and s["background_args"] == ["--background"]
    assert apps.spec("clipboardline", "win")["method"] == "nsis-silent"
    with pytest.raises(apps.AppsError):
        apps.get("yok")


def test_status_not_installed_then_installed(env):
    st = apps.status("nashi")
    assert st["supported"] and not st["installed"] and not st["running"] and st["autostart"] == "login"
    exe = apps.exe_path("nashi")
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"x")
    env.procs.add("Nashi.exe")
    st = apps.status("nashi")
    assert st["installed"] and st["running"] and "Nashi" in apps.format_status(st)


def test_unsupported_platform_status(monkeypatch):
    monkeypatch.setattr(apps, "plat", lambda: None)
    st = apps.status("nashi")
    assert not st["supported"]
    with pytest.raises(apps.AppsError):
        apps.install("nashi")


# ------------------------------------------------------------------ indirme güvenliği
@pytest.mark.parametrize("url", [
    "http://github.com/orkunisitmak/nashi-app/x", "https://evil.example.com/a.zip", "https://github.com/someoneelse/repo/releases/x",
    "https://github.com.evil.com/orkunisitmak/x", "ftp://objects.githubusercontent.com/x"])
def test_check_url_rejects(url):
    with pytest.raises(apps.AppsError):
        apps.check_url(url)


@pytest.mark.parametrize("url", [NASHI_REL + "a.zip", "https://objects.githubusercontent.com/x", "https://release-assets.githubusercontent.com/y",
                                  "https://api.github.com/repos/orkunisitmak/nashi-app/releases"])
def test_check_url_accepts(url):
    assert apps.check_url(url) == url


def test_parse_sums_variants():
    h1, h2 = "a" * 64, "b" * 64
    d = apps.parse_sums(f"{h1}  ClipBoardLine-Setup-1.7.8-x64.exe\n{h2} *Other.zip\nçöp satır\n")
    assert apps.expected_sha(d, "ClipBoardLine-Setup-1.7.8-x64.exe") == h1 and apps.expected_sha(d, "other.ZIP") == h2
    assert apps.expected_sha(d, "yok") is None


def test_download_size_limit_stops_and_deletes(env, tmp_path, monkeypatch):
    monkeypatch.setattr(apps, "_open", lambda url, headers=None, timeout=60: Resp(b"x" * 5000, headers={}))
    with pytest.raises(apps.AppsError, match="sınır"):
        apps.download(NASHI_REL + "a.zip", tmp_path / "d" / "a.zip", 1000)
    assert not (tmp_path / "d" / "a.zip").exists() and not (tmp_path / "d" / "a.zip.part").exists()


def test_download_declared_size_too_big(env, tmp_path, monkeypatch):
    monkeypatch.setattr(apps, "_open", lambda url, headers=None, timeout=60: Resp(b"x", headers={"Content-Length": str(10**12)}))
    with pytest.raises(apps.AppsError, match="büyük"):
        apps.download(NASHI_REL + "a.zip", tmp_path / "a.zip", 1000)


# ------------------------------------------------------------------ zip-slip
@pytest.mark.parametrize("name", ["../evil.txt", "a/../../evil.txt", "/abs/evil.txt", "C:/evil.txt", "..\\evil.txt"])
def test_zip_slip_rejected(tmp_path, name):
    z = tmp_path / "bad.zip"
    z.write_bytes(make_zip({"ok.txt": b"1", name: b"2"}))
    dest = tmp_path / "out"
    with pytest.raises(apps.AppsError):
        apps.safe_extract(z, dest)
    assert not dest.exists() or not any(dest.iterdir())          # hiçbir şey açılmadı
    assert not (tmp_path / "evil.txt").exists()


def test_zip_symlink_and_bomb_rejected(tmp_path, monkeypatch):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        zi = zipfile.ZipInfo("link")
        zi.external_attr = 0o120777 << 16
        z.writestr(zi, "target")
    (tmp_path / "s.zip").write_bytes(buf.getvalue())
    with pytest.raises(apps.AppsError, match="sembolik"):
        apps.safe_extract(tmp_path / "s.zip", tmp_path / "o1")
    (tmp_path / "b.zip").write_bytes(make_zip({"a": b"1", "b": b"2"}))
    monkeypatch.setattr(apps, "MAX_ZIP_FILES", 1)
    with pytest.raises(apps.AppsError, match="aşırı"):
        apps.safe_extract(tmp_path / "b.zip", tmp_path / "o2")


# ------------------------------------------------------------------ kurulum (zip-extract)
def test_install_nashi_flattens_verifies_and_writes_run_key(env):
    payload = make_zip({"Nashi.exe": b"MZ", "res/a.txt": b"a"}, top="Nashi-Windows-x64/")
    serve_nashi(env, payload)
    seen = []
    r = apps.install("nashi", lambda p, m: seen.append(p))
    assert r["ok"] and r["installed"]
    exe = apps.exe_path("nashi")
    assert exe.read_bytes() == b"MZ" and (exe.parent / "res" / "a.txt").exists()          # üst klasör düzleştirildi
    assert seen[-1] == 100 and seen == sorted(seen)
    assert apps.load_state()["nashi"]["version"] == "0.7.14"
    assert env.reg["SecondBrain-Nashi"] == f'"{exe}" --background'                       # varsayılan kip: bilgisayar açılınca
    assert env.shortcuts == [("Nashi", exe)]                                              # taşınabilir zip: Başlat menüsü kısayolu
    assert not (apps.downloads_dir() / "Nashi-Windows-x64.zip").exists()                  # indirilen paket silindi
    assert all(u.startswith(("https://github.com/orkunisitmak/", "https://api.github.com/")) for u in env.opened)
    assert apps.install("nashi")["message"].startswith("Nashi zaten kurulu")             # ikinci kez: indirme yok
    n = len(env.opened)
    apps.install("nashi")
    assert len(env.opened) == n


def test_install_sha_mismatch_stops_and_deletes(env):
    serve_nashi(env, sha="0" * 64)
    with pytest.raises(apps.AppsError, match="SHA-256 uyuşmuyor"):
        apps.install("nashi")
    assert not apps.exe_path("nashi").exists()
    assert not (apps.downloads_dir() / "Nashi-Windows-x64.zip").exists()
    assert env.reg == {} and "nashi" not in apps.load_state()


def test_install_without_sums_entry_refuses(env):
    payload = serve_nashi(env)
    env.served[NASHI_REL + "SHA256SUMS.txt"] = f"{hashlib.sha256(payload).hexdigest()}  baska.zip\n".encode()
    with pytest.raises(apps.AppsError, match="doğrulanamadığı"):
        apps.install("nashi")
    assert not apps.exe_path("nashi").exists()


def test_install_refuses_when_running(env):
    serve_nashi(env)
    apps.install("nashi")
    env.procs.add("Nashi.exe")
    with pytest.raises(apps.AppsError, match="çalışıyor"):
        apps.install("nashi", force=True)


def test_install_zip_without_exe(env):
    serve_nashi(env, make_zip({"readme.txt": b"x"}))
    with pytest.raises(apps.AppsError, match="bulunamadı"):
        apps.install("nashi")
    assert not apps.exe_path("nashi").parent.exists()


def test_api_resolution_used_when_available(env):
    payload = serve_nashi(env)
    api = "https://api.github.com/repos/orkunisitmak/nashi-app/releases/tags/v0.7.14-45"
    other = "https://objects.githubusercontent.com/zip"
    env.served[api] = json.dumps({"assets": [{"name": "Nashi-Windows-x64.zip", "browser_download_url": other, "size": len(payload)},
                                              {"name": "SHA256SUMS.txt", "browser_download_url": NASHI_REL + "SHA256SUMS.txt", "size": 10}]}).encode()
    env.served[other] = payload
    apps.install("nashi")
    assert other in env.opened and apps.exe_path("nashi").exists()


# ------------------------------------------------------------------ kurulum (NSIS)
def test_install_clipboardline_nsis_silent(env, monkeypatch):
    payload = b"MZ-installer" * 100
    env.served[CBL_REL + "ClipBoardLine-Setup-1.7.8-x64.exe"] = payload
    env.served[CBL_REL + "SHA256SUMS"] = f"{hashlib.sha256(payload).hexdigest()}  ClipBoardLine-Setup-1.7.8-x64.exe\n".encode()
    calls = []

    def fake_run(cmd, timeout=600):
        calls.append(cmd)
        exe = apps.exe_path("clipboardline")
        exe.parent.mkdir(parents=True, exist_ok=True)
        exe.write_bytes(b"app")
        return 0, ""
    monkeypatch.setattr(apps, "_run", fake_run)
    r = apps.install("clipboardline")
    assert r["ok"] and calls[0][1] == "/S" and calls[0][0].endswith("ClipBoardLine-Setup-1.7.8-x64.exe")
    assert env.reg["SecondBrain-ClipBoardLine"] == f'"{apps.exe_path("clipboardline")}"'
    assert apps.load_state()["clipboardline"]["version"] == "1.7.8"


def test_install_clipboardline_silent_fails_opens_normal_installer(env, monkeypatch):
    payload = b"MZ" * 50
    env.served[CBL_REL + "ClipBoardLine-Setup-1.7.8-x64.exe"] = payload
    env.served[CBL_REL + "SHA256SUMS"] = f"{hashlib.sha256(payload).hexdigest()}  ClipBoardLine-Setup-1.7.8-x64.exe\n".encode()
    monkeypatch.setattr(apps, "_run", lambda cmd, timeout=600: (1, "hata"))
    r = apps.install("clipboardline")
    assert r["ok"] is False and r["manual"] and not r["installed"]
    assert env.spawned and env.spawned[0][0][0].endswith("ClipBoardLine-Setup-1.7.8-x64.exe") and len(env.spawned[0][0]) == 1
    assert env.reg == {}


# ------------------------------------------------------------------ deneme kipi
def test_sandbox_skips_everything(env, monkeypatch, tmp_path):
    monkeypatch.setenv("SB_SETUP_SANDBOX", str(tmp_path / "sbx"))
    r = apps.install("nashi")
    assert r["skipped"] and r["message"].startswith("[deneme] atlandı") and env.opened == []
    a = apps.set_autostart("nashi", "login")
    assert a["skipped"] and env.reg == {}
    assert apps.start("nashi")["skipped"] and env.spawned == []
    assert (tmp_path / "sbx" / "data" / "apps.json").exists()                   # seçim yalnız deneme klasörüne yazıldı
    assert not (tmp_path / "data" / "apps.json").exists()


# ------------------------------------------------------------------ başlangıç
def _fake_installed(env, app_id):
    exe = apps.exe_path(app_id)
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_bytes(b"x")
    return exe


def test_autostart_modes(env):
    exe = _fake_installed(env, "nashi")
    apps.set_autostart("nashi", "login")
    assert env.reg == {"SecondBrain-Nashi": f'"{exe}" --background'}
    assert apps.status("nashi")["autostart_active"] is True
    apps.set_autostart("nashi", "startup")
    assert env.reg == {} and apps.autostart_mode("nashi") == "startup"
    apps.set_autostart("nashi", "login")
    apps.set_autostart("nashi", "off")
    assert env.reg == {} and apps.autostart_mode("nashi") == "off"
    with pytest.raises(apps.AppsError):
        apps.set_autostart("nashi", "bazen")


def test_autostart_login_not_written_when_not_installed(env):
    apps.set_autostart("nashi", "login")
    assert env.reg == {} and apps.autostart_mode("nashi") == "login"           # seçim saklandı, kurulunca yazılır


def test_real_registry_never_touched_by_default_tests():
    """Bu testler _reg_* taklidi olmadan çalışsaydı gerçek HKCU'ya yazardı: işlevler winreg'i yalnız çağrılınca içe aktarır."""
    import inspect
    src = inspect.getsource(apps)
    assert "import winreg" in src and src.count("import winreg") == 3 and "\nimport winreg" not in src


def test_start_and_background(env):
    exe = _fake_installed(env, "nashi")
    r = apps.start("nashi")
    assert r["started"] and env.spawned[-1] == ([str(exe)], str(exe.parent))
    r = apps.start("nashi", background=True)
    assert env.spawned[-1][0] == [str(exe), "--background"]
    env.procs.add("Nashi.exe")
    n = len(env.spawned)
    assert apps.start("nashi")["started"] is False and len(env.spawned) == n
    with pytest.raises(apps.AppsError, match="kurulu değil"):
        apps.start("clipboardline")


def test_start_startup_apps_only_startup_mode(env):
    _fake_installed(env, "nashi")
    _fake_installed(env, "clipboardline")
    apps.set_autostart("nashi", "startup")
    apps.set_autostart("clipboardline", "login")
    out = apps.start_startup_apps(log=lambda *_: None)
    assert [o["id"] for o in out] == ["nashi"] and env.spawned[-1][0][-1] == "--background"


# ------------------------------------------------------------------ sürüm denetimi
def test_update_available(env):
    rels = [{"tag_name": "v0.7.15-46", "draft": False, "prerelease": False}, {"tag_name": "v0.7.14-45", "draft": False, "prerelease": False},
            {"tag_name": "v0.8.0-1", "draft": False, "prerelease": True}, {"tag_name": "ilgisiz", "draft": False, "prerelease": False}]
    env.served["https://api.github.com/repos/orkunisitmak/nashi-app/releases?per_page=30"] = json.dumps(rels).encode()
    u = apps.update_available("nashi")
    assert u["available"] and u["latest"] == "0.7.15" and u["tag"] == "v0.7.15-46" and u["current"] == "0.7.14"
    rels[0]["draft"] = True
    env.served["https://api.github.com/repos/orkunisitmak/nashi-app/releases?per_page=30"] = json.dumps(rels).encode()
    assert apps.update_available("nashi")["available"] is False
    assert apps.update_available("clipboardline")["available"] is False and "error" in apps.update_available("clipboardline")


# ------------------------------------------------------------------ macOS dalı (taklit komutlarla)
def test_mac_zip_uses_ditto_and_checks_paths(env, monkeypatch, tmp_path):
    monkeypatch.setattr(apps, "plat", lambda: "mac")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.setattr(apps.Path, "home", classmethod(lambda cls: tmp_path / "home"))
    z = tmp_path / "n.zip"
    z.write_bytes(make_zip({"Nashi.app/Contents/x": b"1"}))
    cmds = []

    def fake_run(cmd, timeout=600):
        cmds.append(cmd)
        (tmp_path / "home" / "Applications" / "Nashi.app").mkdir(parents=True)
        return 0, ""
    monkeypatch.setattr(apps, "_run", fake_run)
    r = apps._install_method("nashi", apps.spec("nashi", "mac"), z, "mac")
    assert r["installed"] and cmds[0][:3] == ["ditto", "-x", "-k"]
    z.write_bytes(make_zip({"../evil": b"1"}))
    with pytest.raises(apps.AppsError):
        apps._install_method("nashi", apps.spec("nashi", "mac"), z, "mac")


# ------------------------------------------------------------------ CLI
def test_cli_list_status_autostart(env, capsys):
    ns = lambda **k: Namespace(**{"action": "list", "id": "", "mode": "", "force": False, "background": False, "dry_run": False, **k})  # noqa: E731
    assert apps.cli(ns()) == 0 and "ClipBoardLine" in capsys.readouterr().out
    assert apps.cli(ns(action="status")) == 0 and "Nashi: kurulu değil" in capsys.readouterr().out
    assert apps.cli(ns(action="autostart", id="nashi")) == 0 and "login" in capsys.readouterr().out
    assert apps.cli(ns(action="autostart", id="nashi", mode="off")) == 0
    assert apps.cli(ns(action="start", id="nashi")) == 1 and "kurulu değil" in capsys.readouterr().out
    assert apps.cli(ns(action="install", id="")) == 1


def test_cli_registered_in_main(capsys):
    from sb.__main__ import main
    with pytest.raises(SystemExit) as e:
        main(["apps", "--help"])
    assert e.value.code == 0 and "autostart" in capsys.readouterr().out


# ------------------------------------------------------------------ asistan uçları, döngü, manifest doğrulama
def test_assistant_routes(env):
    from sb import chat, webroutes
    from sb.webroutes import Ctx

    def call(path, data=None, method="GET"):
        r = webroutes.find(method, path)
        assert r is not None, path
        code, body, _, _ = webroutes.call(r, Ctx(method, path, data or {}, {}, session=chat.Session()))
        return code, json.loads(body)
    code, out = call("/api/v2/apps/status")
    assert code == 200 and [a["id"] for a in out["apps"]] == ["clipboardline", "nashi"] and out["apps"][0]["title"].startswith("ClipBoardLine")
    assert call("/api/v2/apps/start", {"id": "yok"}, "POST")[0] == 404
    code, out = call("/api/v2/apps/start", {"id": "nashi"}, "POST")
    assert code == 400 and "kurulu değil" in out["error"]
    _fake_installed(env, "nashi")
    code, out = call("/api/v2/apps/start", {"id": "nashi"}, "POST")
    assert code == 200 and out["started"]


def test_apps_loop_syncs_only_when_installed(env):
    import threading
    from sb import chat

    class Stop(threading.Event):
        def __init__(self, turns):
            super().__init__()
            self.left = turns

        def wait(self, t=None):                                                  # 20 sn bekleme ve aralık atlanır; turns tur sonra durur
            self.left -= 1
            if self.left <= 0:
                self.set()
            return self.is_set()
    n = []
    chat.apps_loop(Stop(4), 1, sync=lambda: n.append(1))
    assert n == []                                                              # hiçbir uygulama kurulu değil → senkron yok
    _fake_installed(env, "nashi")
    m = []
    chat.apps_loop(Stop(4), 1, sync=lambda: m.append(1))
    assert len(m) == 3


def test_sync_respects_module_switch_and_missing_data(env, monkeypatch):
    from sb import features
    r = apps.sync("nashi")
    assert "veri klasörü yok" in r["not"] and apps.load_state()["nashi"]["last_sync"]
    monkeypatch.setattr(features, "enabled", lambda k: False)
    assert apps.sync("nashi", require_enabled=True)["not"] == "modül kapalı"
    assert [x["not"] for x in apps.sync_all()] == ["modül kapalı", "modül kapalı"]


def test_manifest_validation_catches_bad_app_section():
    from sb import plugins
    m = dict(plugins.get("nashi", "module"))
    assert plugins.validate_manifest(m) == []
    bad = json.loads(json.dumps({k: v for k, v in m.items() if k != "_file"}))
    bad["app"]["win"]["method"] = "powershell"
    bad["app"]["repo"] = "yanlis"
    del bad["app"]["win"]["sums"]
    errs = plugins.validate_manifest(bad)
    assert any("method" in e for e in errs) and any("repo" in e for e in errs) and any("sums" in e for e in errs)


def test_detect_version_for_manually_installed_app(env, monkeypatch):
    assert apps.detect_version("clipboardline") is None                         # kurulu değil
    _fake_installed(env, "clipboardline")
    monkeypatch.setattr(apps, "_run", lambda cmd, timeout=600: (0, "1.7.8.0\r\n"))
    assert apps.detect_version("clipboardline") == "1.7.8" and apps.load_state()["clipboardline"]["version"] == "1.7.8"
    monkeypatch.setattr(apps, "_run", lambda cmd, timeout=600: (1, "hata"))
    assert apps.detect_version("clipboardline") is None


def test_clipboardline_install_dir_matches_electron_builder_package_name():
    s = apps.spec("clipboardline", "win")
    assert s["exe"].endswith(r"Programs\clipboardline-desktop\ClipBoardLine.exe") and s["install_dir"].endswith("clipboardline-desktop")


def test_start_menu_shortcut_writes_lnk_under_appdata(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setattr(apps.sys, "platform", "win32")
    calls = []

    def fake_run(cmd, timeout=600):
        calls.append(cmd)
        (tmp_path / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Nashi.lnk").write_bytes(b"L")
        return 0, ""
    monkeypatch.setattr(apps, "_run", fake_run)
    exe = tmp_path / "Programs" / "Nashi" / "Nashi.exe"
    lnk = apps.start_menu_shortcut("Nashi", exe)
    assert lnk == tmp_path / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Nashi.lnk"
    assert calls and "WScript.Shell" in calls[0][-1] and str(exe) in calls[0][-1]
    monkeypatch.setattr(apps, "_run", lambda cmd, timeout=600: (1, "hata"))
    (tmp_path / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Nashi.lnk").unlink()
    assert apps.start_menu_shortcut("Nashi", exe) is None                                # başarısızlık kurulumu bozmaz
    monkeypatch.setattr(apps.sys, "platform", "darwin")
    assert apps.start_menu_shortcut("Nashi", exe) is None
