"""Bugün ve Kaynaklar görünümleri (sb/web/today.js): dosya bağlantıları, sw önbelleği, güvenli DOM kullanımı, 14:00 → 840 düzeltmesi."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from sb import chat, today

WEB = Path(chat.__file__).parent / "web"


def _t(name):
    return (WEB / name).read_text(encoding="utf-8")


def test_today_js_served_and_linked():
    html = _t("index.html")
    assert '<script defer src="/static/today.js"></script>' in html
    assert html.index("/static/app.js") < html.index("/static/today.js")      # SB önce yüklenir
    assert 'id="btn-sources"' in html and 'id="src-badge" class="bell-badge"' in html
    got = chat.static_file("today.js")
    assert got and got[1].startswith(("application/javascript", "text/javascript"))


def test_today_js_contract():
    js = _t("today.js")
    for needle in ("registerView('today'", "registerView('sources'", "/api/v2/today", "/api/v2/freshness", "60000", "Yalnız sorunlu",
                   "SB.openView('today')", "refreshBadge"):
        assert needle in js, needle
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "eval(" not in js
    assert "fetch(" not in js                                   # X-SB belirteci SB.api sarmalayıcısından


def test_today_styles_and_reduced_motion():
    css = _t("views.css")
    assert ".today-grid" in css and ".today-skel" in css
    assert re.search(r"prefers-reduced-motion:reduce\)\{\.today-skel\{animation:none\}", css)
    assert re.search(r"max-width:640px\)\{\s*\.today-grid\{grid-template-columns:1fr\}", css)


def test_sw_cache_bumped_and_lists_today():
    sw = _t("sw.js")
    assert "sb-shell-v4" in sw and "/static/today.js" in sw


def test_startup_goes_to_today_when_done():
    js = _t("startup.js")
    assert "SB.openView('today')" in js and "watching" in js


@pytest.mark.skipif(not shutil.which("node"), reason="node yok")
@pytest.mark.parametrize("f", ["today.js", "startup.js", "sw.js"])
def test_node_check(f):
    r = subprocess.run(["node", "--check", str(WEB / f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_due_time_sexagesimal_is_formatted(tmp_path):
    d = tmp_path / "10-Dersler" / "X"
    d.mkdir(parents=True)
    from datetime import date
    day = date(2026, 11, 5)
    (d / "Sınav.md").write_text(f"---\ntype: teslim\nstatus: acik\ndue: {day}\ndue_time: 14:00\n---\n# Sınav\n", encoding="utf-8")
    rows = today.deadlines(tmp_path, day, 7)
    assert rows and rows[0]["time"] == "14:00"
