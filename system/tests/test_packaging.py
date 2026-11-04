"""Paketleme (1.0 Paket 5): PyInstaller spec/giriş noktaları, kısayol ve başlatıcı komutları, release.yml, kurulum betikleri.
Gerçek derleme yok (CI'da sınanır); gerçek komut/kısayol yok (taklitli)."""
import importlib.util
import json
import plistlib
import sys
from pathlib import Path

import pytest

SYSTEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SYSTEM))
from setup import autostart as AS  # noqa: E402
from setup import engine as E  # noqa: E402


def _first(*cands):
    for c in cands:
        if c.exists():
            return c
    pytest.skip("dosya yok: " + str(cands[0]))


# kaynak (_system/packaging, _system/kit/*) ve kit (packaging/, kök, .github/workflows) yerleşimleri
PKG = _first(SYSTEM / "packaging", SYSTEM.parent / "packaging") if ((SYSTEM / "packaging").exists() or (SYSTEM.parent / "packaging").exists()) else SYSTEM / "packaging"


def _pkg(name) -> Path:
    """packaging/ yalnız kaynakta ve kitte var; kurulmuş kasada yoksa test atlanır."""
    if not (PKG / name).exists():
        pytest.skip("paketleme dosyaları bu kopyada yok")
    return PKG / name


def _kitfile(name):
    return _first(SYSTEM / "kit" / name, SYSTEM.parent / name)


def _load(path: Path, name: str):
    if not path.exists():                                     # kurulmuş kasada packaging/ yok (yalnız derlemede gerekir)
        pytest.skip("paketleme dosyaları bu kopyada yok")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def setup_entry():
    return _load(_pkg("setup_entry.py"), "sb_setup_entry")


@pytest.fixture(scope="module")
def app_entry():
    return _load(_pkg("app_entry.py"), "sb_app_entry")


# ------------------------------------------------------------------ spec / build
@pytest.mark.parametrize("name", ["setup.spec", "app.spec", "build.py", "setup_entry.py", "app_entry.py"])
def test_packaging_files_parse(name):
    src = _pkg(name).read_text(encoding="utf-8")
    compile(src, name, "exec")


def test_spec_contents():
    s = _pkg("setup.spec").read_text(encoding="utf-8")
    assert "setup_entry.py" in s and "Second Brain Setup" in s and "BUNDLE" in s and "console=False" in s
    assert "kit/system" in s and "kit/vault" in s and "setup/ui" in s and "SB_UV_BIN" in s and "launcher" in s
    assert "webview" in s and "icon.ico" in s and "icon.icns" in s
    a = _pkg("app.spec").read_text(encoding="utf-8")
    assert "app_entry.py" in a and 'NAME = "Second Brain"' in a and "BUNDLE" in a and "console=False" in a
    for icon in ("icon.ico", "icon.icns"):
        assert _pkg(icon).stat().st_size > 1000


def test_build_names_have_no_spaces():
    b = _load(_pkg("build.py"), "sb_build")
    assert " " not in b.RELEASE_WIN["setup"] and " " not in b.RELEASE_MAC["setup"]
    assert b.RELEASE_WIN["setup"].startswith("Second-Brain-Setup") and b.RELEASE_MAC["setup"].endswith(".zip")


# ------------------------------------------------------------------ setup_entry
def test_setup_entry_uv_env(setup_entry, tmp_path):
    (tmp_path / "uv").mkdir()
    (tmp_path / "uv" / "uv.exe").write_text("x")
    env = {}
    assert setup_entry.configure_environment(env, tmp_path, "win32") == {"SB_UV": str(tmp_path / "uv" / "uv.exe")}
    assert env["SB_UV"].endswith("uv.exe")
    assert setup_entry.configure_environment({"SB_UV": "elle"}, tmp_path, "win32") == {}       # verilmiş değer ezilmez
    assert setup_entry.configure_environment({}, None, "win32") == {}
    assert setup_entry.find_bundled_uv(tmp_path, "darwin") is None                             # macOS adı `uv`


def test_engine_kit_dir_meipass(tmp_path, monkeypatch):
    kit = tmp_path / "kit"
    (kit / "system" / "sb").mkdir(parents=True)
    (kit / "vault").mkdir()
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert E.kit_dir() == kit and E.code_dir() == kit / "system"
    monkeypatch.delattr(sys, "_MEIPASS")
    assert E.kit_dir() is None or (E.ROOT / "system" / "sb").exists()


def test_engine_uv_bin(tmp_path, monkeypatch):
    uv = tmp_path / "uv.exe"
    uv.write_text("x")
    monkeypatch.setenv("SB_UV", str(uv))
    monkeypatch.setattr(E.shutil, "which", lambda n: None)
    assert E.uv_bin() == str(uv)
    monkeypatch.setattr(E.shutil, "which", lambda n: "/usr/bin/uv")                             # PATH'te varsa o kullanılır
    assert E.uv_bin() == "uv"
    monkeypatch.setattr(E.shutil, "which", lambda n: None)
    data = tmp_path / "data"
    kept = E.install_uv(data)                                                                   # geçici klasörden kalıcı kopya
    assert Path(kept) == data / "bin" / "uv.exe" and Path(kept).is_file() and E.uv_bin() == kept


# ------------------------------------------------------------------ kısayol ve başlatıcı komutları
def _eng(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "_system" / "sb").mkdir(parents=True)
    monkeypatch.setattr(E, "kit_dir", lambda: None)
    monkeypatch.setenv("SB_APPS_DIR", str(tmp_path / "Apps"))
    return E.Engine(vault, data=tmp_path / "data")


def test_shortcut_script_targets_launcher():
    ps = E.shortcut_script(r"C:\Users\a b\.secondbrain\bin\Second Brain.exe", [], r"C:\v\_system")
    assert "GetFolderPath('Desktop')" in ps and "GetFolderPath('Programs')" in ps and "Second Brain.lnk" in ps
    assert r"'C:\Users\a b\.secondbrain\bin\Second Brain.exe'" in ps and ".Save()" in ps.replace("$s.Save()", ".Save()")
    assert "O''Brien" in E.shortcut_script("O'Brien.exe", [], "x")                              # tek tırnak kaçışı


def test_shortcuts_step_windows_packaged(tmp_path, monkeypatch):
    eng = _eng(tmp_path, monkeypatch)
    bundle = tmp_path / "bundle"
    (bundle / "launcher").mkdir(parents=True)
    (bundle / "launcher" / "Second Brain.exe").write_text("exe")
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    calls = []
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (calls.append(cmd), (0, ""))[1])
    assert eng._step_shortcuts() is None
    exe = tmp_path / "data" / "bin" / "Second Brain.exe"
    assert exe.read_text() == "exe"                                                              # başlatıcı kalıcı yere kopyalandı
    assert calls[0][:3] == ["powershell", "-NoProfile", "-Command"] and str(exe) in calls[0][3]
    # otomatik başlatma da aynı paketli exe'yi kullanır
    prog, args, _ = AS.launch_command(eng, True, "win32")
    assert prog == str(exe) and args == ["--minimized"]


def test_shortcuts_step_windows_unpackaged_uses_pythonw(tmp_path, monkeypatch):
    eng = _eng(tmp_path, monkeypatch)
    py = eng.vault / "_system" / ".venv" / "Scripts"
    py.mkdir(parents=True)
    (py / "pythonw.exe").write_text("x")
    monkeypatch.setattr(sys, "platform", "win32")
    calls = []
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (calls.append(cmd), (0, ""))[1])
    eng._step_shortcuts()
    assert "pythonw.exe" in calls[0][3] and "-m app.desktop" in calls[0][3]


def test_shortcuts_step_failure_is_reported(tmp_path, monkeypatch):
    eng = _eng(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(E, "_run_capture", lambda cmd, timeout=15, cwd=None: (1, "erişim engellendi"))
    with pytest.raises(RuntimeError, match="kısayol"):
        eng._step_shortcuts()


def test_shortcuts_step_macos_stub_and_bundle(tmp_path, monkeypatch):
    eng = _eng(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(E, "_run_capture", lambda *a, **k: (_ for _ in ()).throw(AssertionError("macOS'ta komut yok")))
    eng._step_shortcuts()                                                                        # paketsiz: iskelet .app
    app = tmp_path / "Apps" / "Second Brain.app"
    pl = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
    sh = (app / "Contents" / "MacOS" / "Second Brain").read_text()
    assert pl["CFBundleExecutable"] == "Second Brain" and "-m app.desktop" in sh and ".venv/bin/python" in sh
    # paketli: gömülü .app kopyalanır
    bundle = tmp_path / "bundle"
    (bundle / "launcher" / "Second Brain.app" / "Contents" / "MacOS").mkdir(parents=True)
    (bundle / "launcher" / "Second Brain.app" / "Contents" / "MacOS" / "Second Brain").write_text("bin")
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    eng._step_shortcuts()
    assert (app / "Contents" / "MacOS" / "Second Brain").read_text() == "bin"
    assert AS.launch_command(eng, False, "darwin")[0] == str(app / "Contents" / "MacOS" / "Second Brain")


def test_shortcuts_step_is_last():
    assert E.STEPS[-1][0] == "shortcuts"


# ------------------------------------------------------------------ app_entry
def _installed(tmp_path, plat="win32"):
    vault = tmp_path / "vault"
    system = vault / "_system"
    (system / "app").mkdir(parents=True)
    (system / "app" / "desktop.py").write_text("x")
    sub = ".venv/Scripts" if plat == "win32" else ".venv/bin"
    (system / sub).mkdir(parents=True)
    (system / sub / ("pythonw.exe" if plat == "win32" else "python")).write_text("x")
    (system / sub / "python.exe").write_text("x") if plat == "win32" else None
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    (data / "kit.json").write_text(json.dumps({"vault": str(vault)}))
    return system, data


def test_app_entry_launch_command(app_entry, tmp_path, monkeypatch):
    monkeypatch.delenv("SB_VAULT", raising=False)
    system, data = _installed(tmp_path)
    assert app_entry.find_system(data) == system
    launched = []
    rc = app_entry.main(["--minimized"], popen=lambda cmd, **kw: launched.append((cmd, kw)), plat="win32", data=data)
    cmd, kw = launched[0]
    assert rc == 0 and cmd == [str(system / ".venv" / "Scripts" / "pythonw.exe"), "-m", "app.desktop", "--minimized"]
    assert kw["cwd"] == str(system) and kw["creationflags"] & 0x08000000                         # konsol penceresi yok
    sysm, datam = _installed(tmp_path / "mac", "darwin")
    assert app_entry.build_command(sysm, [], "darwin") == [str(sysm / ".venv" / "bin" / "python"), "-m", "app.desktop"]
    assert app_entry.popen_kwargs(sysm, "darwin")["start_new_session"] is True


def test_app_entry_without_install_offers_setup(app_entry, tmp_path, monkeypatch):
    monkeypatch.delenv("SB_VAULT", raising=False)
    home = tmp_path / "home"
    (home / "Desktop").mkdir(parents=True)
    (home / "Desktop" / "Second Brain Setup.exe").write_text("x")
    asked, opened = [], []
    rc = app_entry.main([], popen=lambda *a, **k: pytest.fail("kurulum yokken başlatılmamalı"), plat="win32", data=tmp_path / "yok",
                        ask_fn=lambda m: (asked.append(m), True)[1], open_fn=opened.append, tell_fn=lambda m: None, home=home)
    assert rc == 2 and asked and opened == [home / "Desktop" / "Second Brain Setup.exe"]
    told = []                                                                                    # Setup yoksa indirme adresi söylenir
    app_entry.main([], plat="win32", data=tmp_path / "yok", ask_fn=lambda m: True, open_fn=opened.append, tell_fn=told.append, home=tmp_path / "bos")
    assert "releases" in told[0]


def test_app_entry_broken_venv(app_entry, tmp_path, monkeypatch):
    monkeypatch.delenv("SB_VAULT", raising=False)
    system, data = _installed(tmp_path)
    for f in (system / ".venv" / "Scripts").iterdir():
        f.unlink()
    told = []
    rc = app_entry.main([], popen=lambda *a, **k: pytest.fail("başlatılmamalı"), plat="win32", data=data, tell_fn=told.append)
    assert rc == 3 and "Python ortamı" in told[0]


# ------------------------------------------------------------------ CI ve betikler
def test_release_workflow():
    yaml = pytest.importorskip("yaml")
    cands = [SYSTEM / "kit" / "release.yml", SYSTEM.parent / ".github" / "workflows" / "release.yml"]
    path = next((c for c in cands if c.exists()), None)
    if path is None:
        pytest.skip("yayın akışı dosyası bu kopyada yok (kurulmuş kasada bulunmaz)")
    wf = yaml.safe_load(path.read_text(encoding="utf-8"))
    on = wf.get("on", wf.get(True))                                                              # PyYAML `on` anahtarını True okur
    assert "v*" in on["push"]["tags"]
    job = wf["jobs"]["build"]
    assert set(job["strategy"]["matrix"]["os"]) == {"windows-latest", "macos-latest"}
    assert wf["permissions"]["contents"] == "write"
    text = json.dumps(wf)
    assert "packaging/build.py" in text and "softprops/action-gh-release" in text and "GITHUB_TOKEN" in text and "pyinstaller" in text


def test_install_scripts_download_to_desktop():
    ps = _kitfile("install.ps1").read_text(encoding="utf-8")
    assert "GetFolderPath(\"Desktop\")" in ps and "Second Brain Setup.exe" in ps
    assert "gh release download" in ps and "--repo" in ps and "second-brain-kit" in ps
    assert "SB_GH_TOKEN" in ps and "GITHUB_TOKEN" in ps and "api.github.com" in ps and "releases/latest" in ps
    assert "--cli" in ps and "setup\\app.py" in ps and "winget install GitHub.cli" in ps            # eski yol + yönerge
    sh = _kitfile("install.sh").read_text(encoding="utf-8")
    assert "$HOME/Desktop" in sh and "Second Brain Setup.app" in sh and "gh release download" in sh
    assert "SB_GH_TOKEN" in sh and "GITHUB_TOKEN" in sh and "api.github.com" in sh and "--cli" in sh and "setup/app.py" in sh
    assert "Second-Brain-Setup-macOS.zip" in sh


def test_build_kit_ships_packaging_and_release_yml():
    bk = SYSTEM / "tools" / "build_kit.py"
    if not bk.exists():
        pytest.skip("kitte build_kit yok")
    src = bk.read_text(encoding="utf-8")
    assert "release.yml" in src and "build_packaging" in src and '"app"' in src
