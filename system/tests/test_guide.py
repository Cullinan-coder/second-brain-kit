"""Kullanıcı rehberi üreticisi (tools/build_guide.py): üretim, 258 madde, kaynak/MCP sayfaları, bağlantılar, sır taraması, --check."""
import importlib.util
import re
from pathlib import Path

import pytest

from sb import features, plugins

CODE = Path(__file__).resolve().parent.parent
TOOL = CODE / "tools" / "build_guide.py"
SRC = CODE / "docs" / "rehber-src"

pytestmark = pytest.mark.skipif(not TOOL.exists() or not SRC.exists(), reason="rehber üreticisi/kaynağı bu kopyada yok")


def _load():
    spec = importlib.util.spec_from_file_location("build_guide", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def bg():
    return _load()


@pytest.fixture(scope="module")
def built(bg, tmp_path_factory):
    out = tmp_path_factory.mktemp("rehber")
    stats = bg.build(out)
    return out, stats


def test_build_runs_and_counts(built):
    out, stats = built
    assert stats["modules"] == len(plugins.all("module")) == 51
    assert stats["sources"] == len(plugins.all("source")) == 39
    assert stats["mcps"] == len(plugins.all("mcp")) == 18
    assert stats["items"] == 258
    assert (out / "README.md").exists()
    assert len(list(out.rglob("*.md"))) == len(stats["files"])


def test_hand_written_pages_copied_and_detailed(bg, built):
    out, _ = built
    for h in bg.HAND_PAGES:
        src = SRC / f"{h}.md"
        assert src.exists(), h
        want = bg._drop_missing_images(src.read_text(encoding="utf-8").replace("\r\n", "\n"))     # dosyası olmayan görüntüler atlanır
        assert (out / f"{h}.md").read_text(encoding="utf-8").strip() == want.strip()
        assert len(src.read_text(encoding="utf-8")) > 1500, f"{h} çok kısa"
    assert src.name  # son sayfa


def test_all_258_items_present_in_module_pages(built):
    out, _ = built
    text = {p.stem: p.read_text(encoding="utf-8") for p in (out / "moduller").glob("*.md")}
    owner = {}
    for m in plugins.all("module"):
        for i in m["catalog_ids"]:
            owner[i] = m["id"]
    for it in features.catalog():
        mid = owner[it["id"]]
        assert f'<a id="madde-{it["id"]}"></a>' in text[mid], it["id"]
        assert re.search(rf"^### {it['id']}\. {re.escape(it['ad'])}$", text[mid], re.M), it["id"]
    catalog = (out / "17-ozellik-katalogu.md").read_text(encoding="utf-8")
    for it in features.catalog():
        assert f"#madde-{it['id']})" in catalog


def test_module_pages_have_required_sections(built):
    out, _ = built
    for m in plugins.all("module"):
        t = (out / "moduller" / f"{m['id']}.md").read_text(encoding="utf-8")
        for sec in ("## Ne işe yarar", "## Nasıl açılır", "## Hangi hesap, veri ya da anahtar ister", "## Nasıl kullanılır", "## Hazır seçimlerde"):
            assert sec in t, (m["id"], sec)


def test_source_and_mcp_pages_exist(built):
    out, _ = built
    for s in plugins.all("source"):
        t = (out / "kaynaklar" / f"{s['id']}.md").read_text(encoding="utf-8")
        assert "## Dışa aktarma adımları" in t and "## Sihirbazda yükleme" in t and "## Sorun giderme" in t
        assert re.search(r"^1\. ", t, re.M) and re.search(r"^2\. ", t, re.M)
    for m in plugins.all("mcp"):
        t = (out / "mcp" / f"{m['id']}.md").read_text(encoding="utf-8")
        assert "## Sihirbazda kurulum" in t and "## Sorun giderme" in t
        assert m["mcp"]["docs_url"] in t


def test_presets_page_lists_all_axes(built):
    out, _ = built
    t = (out / "15-hazir-secimler.md").read_text(encoding="utf-8")
    for axis in plugins.presets()["axes"].values():
        for v in axis.values():
            assert v["name"]["tr"] in t
    assert (out / "20-sektor-paketleri.md").read_text(encoding="utf-8").count("## ") >= 2


def test_internal_links_resolve(bg, built):
    out, _ = built
    errs = [e for e in bg.validate(out) if "bağlantı" in e]
    assert errs == []


def test_validate_clean(bg, built):
    out, _ = built
    assert bg.validate(out) == []


def test_no_secret_or_personal_data(bg, built):
    out, _ = built
    for p in out.rglob("*.md"):
        found = bg.secret_findings(p.read_text(encoding="utf-8"))
        assert found == [], (p.name, found)


def test_secret_scanner_detects_samples(bg):
    assert bg.secret_findings("yaz: kisi@gmail.com")
    assert bg.secret_findings("ghp_" + "a" * 36)
    assert bg.secret_findings("+90 532 123 45 67")
    assert bg.secret_findings("AIza" + "b" * 35)
    assert not bg.secret_findings("ornek@gmail.com ve Ayşe Yılmaz")


def test_build_is_deterministic(bg, tmp_path):
    a = bg.build(tmp_path / "a")["files"]
    b = bg.build(tmp_path / "b")["files"]
    assert a == b


def test_check_flags_missing_page_and_stale(bg, tmp_path, monkeypatch):
    out = tmp_path / "rehber"
    bg.build(out)
    (out / "moduller" / "gmail.md").unlink()
    errs = bg.validate(out)
    assert any("gmail" in e for e in errs)
    # bozuk bağlantı
    out2 = tmp_path / "r2"
    bg.build(out2)
    p = out2 / "00-baslangic.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n[kırık](yok-boyle-sayfa.md)\n", encoding="utf-8")
    assert any("yok-boyle-sayfa" in e for e in bg.validate(out2))


def test_check_command_clean_on_committed_output(bg):
    out = CODE / "docs" / "rehber"
    if not out.exists():
        pytest.skip("docs/rehber üretilmemiş")
    assert bg.check() == []


def test_image_placeholders_use_img_folder(bg, built):
    out, _ = built
    # rehberde kırık görüntü olmaz: bağlantı verilen her görüntünün dosyası docs/rehber/img/ altında var
    missing = []
    for p in out.rglob("*.md"):
        for name in re.findall(r"(?<!`)!\[[^\]]*\]\((?:\.\./)?img/([^)\s]+)\)", p.read_text(encoding="utf-8")):
            if not (bg.OUT / "img" / name).is_file():
                missing.append((p.name, name))
    assert not missing, missing[:5]
