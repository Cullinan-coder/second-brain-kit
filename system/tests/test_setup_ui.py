"""Kurulum paneli arayüzü (Faz 5 · Paket P): i18n tamlığı, dış kaynak yokluğu, ham innerHTML yokluğu, js sözdizimi, pencere mantığı."""
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

SETUP = Path(__file__).resolve().parent.parent / "setup"
UI = SETUP / "ui"


def _i18n():
    return json.loads((UI / "i18n.json").read_text(encoding="utf-8"))


def test_i18n_iki_dilde_tam():
    d = _i18n()
    assert set(d) == {"tr", "en"}
    assert set(d["tr"]) == set(d["en"])
    assert all(v.strip() for lang in d.values() for v in lang.values())


JS_FILES = ["setup.js", "wizard.js", "settings.js"]
STEP_IDS = "welcome presets features profile accounts keys models mcp data phone startup summary".split()


def _js():
    return chr(10).join((UI / f).read_text(encoding="utf-8") for f in JS_FILES)


def test_kullanilan_anahtarlar_tanimli():
    html = (UI / "index.html").read_text(encoding="utf-8")
    keys = set(re.findall(r"t\('([\w.]+)'", _js())) | set(re.findall(r'data-i18n(?:-title)?="([\w.]+)"', html))
    tr = _i18n()["tr"]
    assert not [k for k in keys if not k.endswith(".") and k not in tr]
    # dinamik anahtarlar
    dyn = [f"tab.{x}" for x in "features accounts keys models mcp data phone startup update health uninstall log".split()]
    dyn += [f"step.{s}.{p}" for s in STEP_IDS for p in "td"]
    dyn += [f"axis.{a}{x}" for a in "meslek donanim gizlilik yogunluk".split() for x in ("", ".d")]
    dyn += [f"st.{s}" for s in "bekliyor calisiyor tamam hata".split()]
    dyn += [f"sum.{s}" for s in "done skipped todo".split()]
    dyn += [f"req.{s}" for s in "acct key gpu other".split()]
    dyn += [f"scope.{s}" for s in "gmail calendar contacts drive".split()]
    dyn += [f"imap.{s}" for s in "gmail outlook icloud yandex custom host port user password".split()]
    dyn += [f"profile.{s}" for s in "name full_name vault timezone org role".split()]
    dyn += [f"welcome.p.{i}" for i in range(1, 5)] + [f"tour.{i}.{p}" for i in range(1, 6) for p in "tx"]
    dyn += [f"g.{i}.{p}" for i in range(1, 8) for p in "tx"]
    dyn += ["svc.spotify.id", "svc.spotify.secret", "svc.telegram.token", "svc.github.pat"]
    for wiz, n in {"spotify": 4, "telegram": 4, "tailscale": 4, "github": 3}.items():
        dyn += [f"wiz.{wiz}.name"] + [f"wiz.{wiz}.{i}" for i in range(1, n + 1)]
    assert not [k for k in dyn if k not in tr]


def test_adim_bilesenleri_ve_ayarlar_kipi():
    js = _js()
    for s in STEP_IDS:
        assert f"R.{s} =" in js, s
    assert "mode" in js and "'settings'" in js
    ui = (UI / "index.html").read_text(encoding="utf-8")
    for f in JS_FILES:
        assert f'src="{f}"' in ui


@pytest.mark.parametrize("name", ["index.html", "setup.css", "setup.js", "wizard.js", "settings.js"])
def test_dis_kaynak_yok(name):
    src = (UI / name).read_text(encoding="utf-8")
    assert not re.search(r"https?://|(?<![\w:])//cdn|@import\s+url", src), name
    if name == "index.html":
        for attr in re.findall(r'(?:src|href)="([^"]+)"', src):
            assert not re.match(r"^(https?:)?//", attr), attr


def test_ham_innerhtml_yok():
    assert not re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(", _js())


def test_sifre_alani_ve_jeton():
    js = _js()
    assert "X-Setup-Token" in js and "'password'" in js and "wipeSecrets" in js
    stored = re.findall(r"localStorage\.setItem\(([^)]*)\)", js)
    assert stored and not any("password" in s or "fields" in s for s in stored)


def test_api_sozlesmesi_uclari_kullaniliyor():
    js = _js()
    for ep in ("/api/catalog", "/api/presets", "/api/combine", "/api/requirements", "/api/wizard", "/api/profile/basic", "/api/account/google",
               "/api/account/imap", "/api/accounts", "/api/secret", "/api/secrets", "/api/ollama", "/api/models/pull", "/api/voice/setup", "/api/mcp",
               "/api/mcp/install", "/api/mcp/custom", "/api/import/upload", "/api/import/preview", "/api/import/run", "/api/imports", "/api/phone",
               "/api/autostart", "/api/apply", "/api/progress", "/api/summary", "/api/path/check", "/api/account/school"):
        assert ep in js, ep


@pytest.mark.skipif(not shutil.which("node"), reason="node yok")
@pytest.mark.parametrize("name", JS_FILES)
def test_js_sozdizimi(name):
    r = subprocess.run(["node", "--check", str(UI / name)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def _load_app():
    spec = importlib.util.spec_from_file_location("setup_app_under_test", SETUP / "app.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pencere_pywebview_varsa():
    app = _load_app()
    calls, stopped = [], []
    wv = types.SimpleNamespace(create_window=lambda *a, **k: calls.append((a, k)), start=lambda: calls.append("start"))
    assert app.run_window("http://127.0.0.1:1/?t=x", lambda: stopped.append(1), wv) == "window"
    assert calls[0][0][0] == "Second Brain Kurulum" and {k: v for k, v in calls[0][1].items() if k != "js_api"} == {"width": 1100, "height": 760} and hasattr(calls[0][1]["js_api"], "pick_folder")
    assert calls[-1] == "start" and stopped == [1]


def test_pencere_yoksa_tarayici():
    app = _load_app()
    opened, stopped = [], []

    class B:
        def open(self, u):
            opened.append(u)

    def sleep(_):
        raise KeyboardInterrupt

    assert app.run_window("http://127.0.0.1:1/?t=x", lambda: stopped.append(1), None, B(), sleep) == "browser"
    assert opened == ["http://127.0.0.1:1/?t=x"] and stopped == [1]


def test_main_sunucuyu_baslatir(monkeypatch):
    app = _load_app()
    seen = {}
    srv = types.SimpleNamespace(url="http://127.0.0.1:1/?t=x", stop=lambda: seen.setdefault("stop", True))
    srv.start = lambda: srv
    fake = types.SimpleNamespace(make_server=lambda port=0: srv)
    monkeypatch.setattr(app, "_load_server", lambda: fake)
    monkeypatch.setattr(app, "run_window", lambda url, stop, wv=None: stop())
    monkeypatch.setitem(sys.modules, "webview", None)
    assert app.main([]) == 0
    assert seen.get("stop") is True


def test_kurulum_betikleri_paneli_cagirir():
    # kaynak kasada _system/kit/, kurulmuş kitte kökte (system/ ya da _system/'ın üstü)
    kit = next((d for d in (SETUP.parent / "kit", SETUP.parent.parent) if (d / "install.ps1").exists()), None)
    if kit is None:
        pytest.skip("kurulum betikleri bu kopyada yok")
    ps, sh = (kit / "install.ps1").read_text(encoding="utf-8"), (kit / "install.sh").read_text(encoding="utf-8")
    for s in (ps, sh):
        assert "setup/app.py" in s and "install.py" in s and "--cli" in s and "astral.sh/uv" in s


# ------------------------------------------------------------------ canlı deneme bulguları (2026-11-04): arayüz davranışları
def test_bulgular_arayuz_parcalari_var():
    js = _js()
    tr = _i18n()["tr"]
    assert "Önceki ekran" == tr["g.prev"] and "Sonraki ekran" == tr["g.next"]        # madde 5: alt Geri/İleri ile karışmaz
    assert "t('g.prev')" in js and "t('g.next')" in js and "t('wiz.prev'), () => { i--" not in js
    assert "function paintTop" in js and "top.install" in js and "Kurulum %{p}" == tr["top.install"]     # madde 6
    assert "data.imported" in js and "state.read" in js                                                  # madde 7
    assert "mcp.rec" in js and "'second-brain'" in js and "S.mcpFb" in js and "mcp.done" in js            # madde 8-9
    assert "keys.optional" in js and "isLocal()" in js and "tam_yerel" in js                              # madde 10
    assert "accountNotes" in js and "schoolBox" in js and "/api/account/school" in js                      # madde 11
    assert "SERVICE_KEYS" in js                                                                           # madde 12
    assert "oll.have" in js                                                                               # madde 14
    assert "catName(" in js                                                                               # madde 19
    assert "errorCard" in js and "err.retry" in js and "resume: !!resume" in js and "error_info" in js    # madde 21
    assert "/api/summary" in js and "sum.empty" in tr and "stepState" in js                               # madde 16
    assert "/api/path/check" in js and "profile.vault.short" in js                                        # madde 4
    for k in ("g.cs.ok",):                                                                                # madde 15: "yüklendi ✓" bir kez
        assert js.count("t('g.cs.ok')") == 1


def test_madde18_dar_pencere_duzeni():
    css = (UI / "setup.css").read_text(encoding="utf-8")
    assert "max-width:900px" in css and "minmax(0,1fr)" in css and "overflow-x:hidden" in css
    assert ".sandbox-bar{overflow-wrap:anywhere}" in css
