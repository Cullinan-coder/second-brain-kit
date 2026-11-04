"""Arayüz belirteçleri: sb/web/tokens.css tek kaynaktır; kurulum sihirbazı birebir aynasını kullanır."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB, UI = ROOT / "sb" / "web", ROOT / "setup" / "ui"


def test_tokens_ayna_esit():
    assert (WEB / "tokens.css").read_bytes() == (UI / "tokens.css").read_bytes(), "setup/ui/tokens.css, sb/web/tokens.css'in kopyası olmalı"


def test_tokens_baglantili():
    assert 'href="/static/tokens.css"' in (WEB / "index.html").read_text(encoding="utf-8")
    assert 'href="tokens.css"' in (UI / "index.html").read_text(encoding="utf-8")
    assert "/static/tokens.css" in (WEB / "sw.js").read_text(encoding="utf-8")


def test_renk_kopyasi_yok():
    """design.css/setup.css kendi renk belirteçlerini tanımlamaz (tokens.css'e bağlıdır)."""
    for f in (WEB / "design.css", UI / "setup.css"):
        css = f.read_text(encoding="utf-8")
        assert "--bg:#" not in css and "--surface:#" not in css and "--fg:#" not in css, f.name


def test_hareket_ve_kontrast_destegi():
    for f in (WEB / "design.css", UI / "setup.css"):
        css = f.read_text(encoding="utf-8")
        assert "prefers-reduced-motion" in css and "forced-colors" in css and "prefers-contrast" in css, f.name
