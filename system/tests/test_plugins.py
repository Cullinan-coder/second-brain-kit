"""Eklenti tanımları (plugins/): şema, katalog kapsaması, modül/kaynak eşleşmesi, hazır seçimler."""
import pytest

from sb import features, plugins


def test_every_manifest_is_valid():
    assert plugins.validate() == []


def test_counts():
    assert len(plugins.all("module")) >= len(features.MODULES)
    assert len(plugins.all("source")) >= 30
    assert len(plugins.all("mcp")) >= 16
    assert {m["id"] for m in plugins.all("sector")} >= {"tekstil", "kisisel"}


def test_all_250_catalog_items_linked_to_a_module():
    cat = {i["id"] for i in features.catalog()}
    assert len(cat) == 250
    linked: dict[int, list[str]] = {}
    for m in plugins.all("module"):
        for i in m["catalog_ids"]:
            linked.setdefault(i, []).append(m["id"])
    assert cat - set(linked) == set(), "boşta madde var"
    assert set(linked) - cat == set(), "katalogda olmayan madde bağlanmış"
    assert not {i: v for i, v in linked.items() if len(v) > 1}, "madde birden çok modüle bağlı"
    assert plugins.tree_item_count() == 250


def test_every_modules_key_has_manifest():
    for key in features.MODULES:
        m = plugins.get(key)
        assert m and m["type"] == "module" and m["module"] == key
        assert m["default_on"] == bool(features.MODULES[key][3])


def test_every_registry_source_has_manifest():
    reg = plugins.registry_names()
    assert "whatsapp" in reg and "spotify" in reg
    by_connector = {m["import"]["connector"] for m in plugins.all("source") if m["import"]["connector"]}
    assert reg <= by_connector, reg - by_connector
    for extra in ("takeout", "history-import", "whatsapp", "linkedin", "sms"):
        assert plugins.get(extra, "source")


def test_registry_matches_real_module():
    from sb.connectors import REGISTRY
    assert set(REGISTRY) == plugins.registry_names()


def test_how_to_is_detailed_and_bilingual():
    for m in plugins.all("source"):
        for lang in ("tr", "en"):
            txt = m["import"]["how_to"][lang]
            assert len(txt) > 200 and "1. " in txt and "2. " in txt, m["id"]
    wa = plugins.get("whatsapp", "source")["import"]["how_to"]["tr"]
    assert "Sohbeti dışa aktar" in wa and "Medyasız" in wa
    assert "takeout.google.com" in plugins.get("takeout", "source")["import"]["how_to"]["tr"]
    assert "Veri kontrolleri" in plugins.get("history-import", "source")["import"]["how_to"]["tr"]


def test_secrets_are_flagged():
    for m in plugins.all():
        r = m["requires"]
        for f in r["fields"]:
            assert f["secret"] == (f["kind"] == "secret"), (m["id"], f["key"])
            if f["key"].endswith(("password", "token", "_key", "_pat")):
                assert f["secret"], (m["id"], f["key"])
        assert set(r["secrets"]) == {f["key"] for f in r["fields"] if f["secret"]}


def test_secret_validation_catches_mistakes():
    bad = {"id": "x", "type": "mcp", "name": {"tr": "a", "en": "a"}, "desc": {"tr": "a", "en": "a"}, "category": "setup",
           "requires": {"accounts": [], "secrets": [], "apps": [],
                        "fields": [{"key": "api_token", "label": {"tr": "a", "en": "a"}, "kind": "text", "secret": False, "required": True}]},
           "health": {"cli": "sb doctor"}, "mcp": {"command": "x", "args": [], "env": {}, "install": None, "docs_url": "https://x"}}
    assert any("sır gibi" in e for e in plugins.validate_manifest(bad))


def test_mcp_catalog():
    ids = {m["id"] for m in plugins.all("mcp")}
    assert {"second-brain", "github", "notion", "slack", "filesystem", "fetch", "gdrive", "postgres", "sqlite", "puppeteer", "playwright",
            "brave-search", "memory", "sequential-thinking", "linear", "atlassian", "figma", "sentry"} <= ids
    for m in plugins.all("mcp"):
        mc = m["mcp"]
        assert mc["install"] is not None or mc["docs_url"], m["id"]
    assert plugins.get("linear", "mcp")["mcp"]["install"] is None


def test_presets_four_axes():
    ax = plugins.presets()["axes"]
    assert set(ax["meslek"]) == {"ogrenci", "ajans", "yazilimci", "akademisyen", "girisimci", "satis", "icerik", "arastirmaci"}
    assert set(ax["donanim"]) == {"guclu_gpu", "orta", "zayif_bulut", "mac_apple"}
    assert set(ax["gizlilik"]) == {"tam_yerel", "karma", "bulut"}
    assert set(ax["yogunluk"]) == {"minimal", "gunluk", "guc"}
    mods = set(features.MODULES) | {m["id"] for m in plugins.all("module")}
    for a in ("meslek", "yogunluk"):
        for name, d in ax[a].items():
            assert set(d.get("add") or d["modules"]) <= mods, (a, name)


def test_combine_order_and_constraints():
    r = plugins.combine("ogrenci", "guclu_gpu", "karma", "minimal")
    assert r["modules"]["assistant"] and r["modules"]["courses"] and r["modules"]["cards"]    # meslek minimal tabana ekler
    assert not r["modules"]["whatsapp"]
    assert r["models"]["profile"] == "full" and r["privacy_profile"]["mode"] == "karma"
    # gizlilik meslek eklerini kısıtlar: içerik üreticisi image_gen ister, tam yerel kapatır
    r = plugins.combine("icerik", "guclu_gpu", "tam_yerel", "guc")
    assert r["modules"]["image_gen"] is False and r["models"]["cloud"] is False
    assert r["privacy_profile"]["permission_profile"] == "sıkı"
    assert any("image_gen" in w for w in r["warnings"])
    # donanım kısıtı: zayıf donanım ses/görüntü modüllerini kapatır, bağımlılar da kapanır
    r = plugins.combine("arastirmaci", "zayif_bulut", "bulut", "guc")
    assert not r["modules"]["vision"] and not r["modules"]["voice"] and not r["modules"]["wake_word"]
    assert r["models"]["profile"] == "cloud" and r["models"]["local_model"] is False
    # tam yerel + zayıf donanım: çakışma uyarısı, küçük yerel model
    r = plugins.combine(None, "zayif_bulut", "tam_yerel", "gunluk")
    assert r["models"]["profile"] == "small" and r["models"]["local_model"] and r["warnings"]
    # mac: RAM'e göre profil
    assert plugins.combine(None, "mac_apple", "karma", "gunluk", ram_gb=16)["models"]["profile"] == "medium"
    assert plugins.combine(None, "mac_apple", "karma", "gunluk", ram_gb=64)["models"]["profile"] == "full"
    # modules anahtarları tam MODULES kümesi
    assert set(r["modules"]) == set(features.MODULES)
    with pytest.raises(ValueError):
        plugins.combine("yok")


def test_yogunluk_ordering():
    n = {y: sum(plugins.combine(None, "guclu_gpu", "karma", y)["modules"].values()) for y in ("minimal", "gunluk", "guc")}
    assert n["minimal"] < n["gunluk"] < n["guc"]
    assert not plugins.combine(None, "guclu_gpu", "karma", "guc")["modules"]["wake_word"]


def test_for_preset_and_tree():
    on = {m["id"] for m in plugins.for_preset(meslek="ogrenci", yogunluk="minimal")}
    assert "courses" in on and "assistant" in on and "whatsapp" not in on
    tree = plugins.features_tree()
    assert all(c["modules"] for c in tree)
    mod = next(m for c in tree for m in c["modules"] if m["id"] == "whatsapp")
    assert {i["id"] for i in mod["items"]} == {87, 184}


def test_requirements():
    r = plugins.requirements({"modules": {"gmail": True, "imap": True, "voice": False}, "sources": ["spotify", "whatsapp"], "mcp": ["github"]})
    assert "google" in r["accounts"] and "imap" in r["accounts"] and "github" in r["accounts"]
    keys = {f["key"] for f in r["fields"]}
    assert {"gmail", "imap_password", "github_pat", "me"} <= keys
    assert "imap_password" in r["secrets"] and "github_pat" in r["secrets"] and "gmail" not in r["secrets"]
    assert {i["id"] for i in r["imports"]} == {"spotify", "whatsapp"}
    assert plugins.get("whatsapp")["type"] == "module" and plugins.get("source:whatsapp")["type"] == "source"
    assert r["mcps"][0]["id"] == "github" and "Docker" in r["apps"]
    assert r["unknown"] == []
    assert plugins.requirements({"modules": ["yok"]})["unknown"] == ["yok"]


def test_sector_packs():
    t = plugins.get("tekstil")
    assert {r["id"] for r in t["roles"]} == {"patron", "muhasebe", "satis", "uretim"}
    assert {"satis_raporu", "gelir_gider", "mail_ozeti"} <= {r["id"] for r in t["reports"]}
    assert t["coming_soon"] and t["coming_soon"][0]["status"] == "yakinda"
    k = plugins.get("kisisel")
    assert k["default"] is True and [s["id"] for s in plugins.all("sector") if s.get("default")] == ["kisisel"]


def test_engine_presets_modules_known():
    """Mevcut kurulum motoru hazır seçimlerindeki modüllerin hepsinin manifesti var."""
    from setup import engine
    for p in engine.PRESETS.values():
        for k in p["modules"]:
            assert plugins.get(k), k
