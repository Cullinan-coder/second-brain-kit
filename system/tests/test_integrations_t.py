import importlib.util
import json
import re
from pathlib import Path

import pytest

D = Path(__file__).resolve().parent.parent / "integrations"


def test_manifest_narrow():
    m = json.loads((D / "browser-extension" / "manifest.json").read_text(encoding="utf-8"))
    assert m["manifest_version"] == 3
    assert set(m["permissions"]) <= {"activeTab", "contextMenus", "storage"}
    assert m["host_permissions"] == ["http://127.0.0.1:8765/*"]


def test_js_only_local_urls_no_innerhtml():
    for f in ("background.js", "popup.js", "popup.html"):
        t = (D / "browser-extension" / f).read_text(encoding="utf-8")
        for u in re.findall(r"https?://[^\s\"'`)]+", t):
            assert u.startswith("http://127.0.0.1:8765"), (f, u)
        assert "innerHTML" not in t


def test_tray_importable():
    pytest.importorskip("pystray")
    spec = importlib.util.spec_from_file_location("tray", D / "tray" / "tray.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.main)
