"""Paket O: Obsidian eklentisi + mini balon (statik denetimler)."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent / "integrations"
PLUGIN = ROOT / "obsidian-plugin"
BUBBLE = ROOT / "bubble" / "bubble.html"


def test_manifest():
    m = json.loads((PLUGIN / "manifest.json").read_text(encoding="utf-8"))
    assert m["id"] == "second-brain-assistant"
    assert m["minAppVersion"] == "1.5.0"
    assert m["isDesktopOnly"] is True
    for k in ("name", "version", "description", "author"):
        assert m.get(k)


def test_plugin_files_exist():
    for n in ("main.js", "styles.css", "README.md"):
        assert (PLUGIN / n).is_file()


@pytest.mark.skipif(not shutil.which("node"), reason="node yok")
def test_main_js_syntax():
    r = subprocess.run(["node", "--check", str(PLUGIN / "main.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_plugin_safe():
    js = (PLUGIN / "main.js").read_text(encoding="utf-8")
    assert "innerHTML" not in js and "eval(" not in js
    for u in re.findall(r"https?://[^\s'\"`)]+", js):
        assert u.startswith("http://127.0.0.1"), u


def test_bubble_local_only():
    html = BUBBLE.read_text(encoding="utf-8")
    assert "innerHTML" not in html
    urls = re.findall(r"https?://[^\s'\"`)<>]+", html)
    assert urls and all(u.startswith("http://127.0.0.1") for u in urls), urls
    assert not re.search(r"(src|href)\s*=\s*[\"']\s*(https?:)?//", html)
    assert "/api/v2/chat" in html and "/api/v2/stt" in html and "MediaRecorder" in html
