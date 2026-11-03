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


def test_kullanilan_anahtarlar_tanimli():
    js = (UI / "setup.js").read_text(encoding="utf-8")
    html = (UI / "index.html").read_text(encoding="utf-8")
    keys = set(re.findall(r"\bt\('([\w.]+)'", js)) | set(re.findall(r'data-i18n(?:-title)?="([\w.]+)"', html))
    tr = _i18n()["tr"]
    assert not [k for k in keys if not k.endswith(".") and k not in tr]
    # dinamik anahtarlar
    dyn = [f"tab.{x}" for x in "kur hesaplar model sihirbaz guncelle saglik kaldir gunluk".split()]
    dyn += [f"cat.{c}" for c in "mail google data ai assist other".split()]
    dyn += [f"st.{s}" for s in "bekliyor calisiyor tamam hata".split()]
    dyn += [f"tour.{i}.{p}" for i in range(1, 6) for p in "tx"]
    for wiz, n in {"google": 7, "spotify": 4, "telegram": 4, "tailscale": 4}.items():
        dyn += [f"wiz.{wiz}.name"] + [f"wiz.{wiz}.{i}" for i in range(1, n + 1)]
    assert not [k for k in dyn if k not in tr]


@pytest.mark.parametrize("name", ["index.html", "setup.css", "setup.js"])
def test_dis_kaynak_yok(name):
    src = (UI / name).read_text(encoding="utf-8")
    assert not re.search(r"https?://|(?<![\w:])//cdn|@import\s+url", src), name
    if name == "index.html":
        for attr in re.findall(r'(?:src|href)="([^"]+)"', src):
            assert not re.match(r"^(https?:)?//", attr), attr


def test_ham_innerhtml_yok():
    js = (UI / "setup.js").read_text(encoding="utf-8")
    assert not re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(", js)


def test_sifre_alani_ve_jeton():
    js = (UI / "setup.js").read_text(encoding="utf-8")
    assert "X-Setup-Token" in js and "'password'" in js and "wipeSecrets" in js
    stored = re.findall(r"localStorage\.setItem\(([^)]*)\)", js)
    assert stored and not any("password" in s or "fields" in s for s in stored)


@pytest.mark.skipif(not shutil.which("node"), reason="node yok")
def test_js_sozdizimi():
    r = subprocess.run(["node", "--check", str(UI / "setup.js")], capture_output=True, text=True)
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
    assert calls[0][0][0] == "Second Brain Kurulum" and calls[0][1] == {"width": 1100, "height": 760}
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
