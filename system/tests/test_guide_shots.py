"""Rehber ekran görüntüsü araçları: demo kasası uydurma veri içerir (kişisel ad yok), katalog rehber-src ile tutarlı.
Tarayıcı/ağ gerektiren kısım (tools/guide_shots.py main) testte çalıştırılmaz."""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parent.parent
TOOLS = CODE / "tools"
FORBIDDEN = ("sa" "met", "ko" "ca", "ko" "caeli", "all" "craft", "cull" "inan", "ko" "ca" "sa" "met")
# Çekilemeyen / kart başına görüntüler (bilerek katalog dışı)
SKIPPED = re.compile(r"^(google-\d.*|kurulum-.*|kaynak-.*|yukleme-.*|mcp-(?!katalog$).*|modeller-indirme)$")

pytestmark = pytest.mark.skipif(not (TOOLS / "guide_shots.py").exists(), reason="araç bu kopyada yok")


def _load(name):
    sys.path.insert(0, str(TOOLS))
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def dv():
    return _load("demo_vault")


@pytest.fixture(scope="module")
def gs():
    return _load("guide_shots")


def test_demo_vault_has_no_personal_names(dv, tmp_path):
    root = dv.build(tmp_path / "sb-demo")
    files = [p for p in root.rglob("*") if p.is_file()]
    assert len(list((root / "SecondBrain").rglob("*.md"))) >= 15
    assert (root / "data" / "mail.db").is_file()
    assert list((root / "data" / "convs").glob("*.json"))
    for p in files:
        data = p.read_bytes()
        if p.suffix == ".db":                                   # SQLite: metin sütunları
            import sqlite3
            con = sqlite3.connect(p)
            data = "\n".join(" ".join(str(c) for c in row) for t in ("messages",) for row in con.execute(f"select * from {t}")).encode()
            con.close()
        low = (p.name + "\n" + data.decode("utf-8", errors="ignore")).lower()
        for w in FORBIDDEN:
            assert w not in low, f"{p.name}: yasak sözcük {w!r}"
        assert "kullanici" not in low


def test_demo_vault_notes_pass_lint_schema(dv):
    for rel, text in dv.notes().items():
        if rel == "Dashboard.md":
            continue
        assert text.startswith("---\n") and "\ntype: " in text and "\nstatus: " in text, rel
    # yaklaşan tarihler: en az iki teslim/sınav bugünden sonra
    due = [re.search(r"\ndue: (\S+)", t).group(1) for t in dv.notes().values() if re.search(r"\ndue: \S+", t)]
    assert len(due) >= 3 and all(d >= dv._d(0) for d in due)


def test_demo_forbidden_list_matches_task(dv):
    assert set(dv.FORBIDDEN) >= set(("sa" "met", "ko" "ca", "ko" "caeli", "all" "craft", "cull" "inan", "ko" "ca" "sa" "met"))


def test_demo_refuses_real_assistant_port(dv):
    with pytest.raises(SystemExit):
        dv.main(["serve", "--port", "8765"])


def test_catalog_names_exist_in_guide_and_cover_obtainable(gs):
    guide = gs.guide_image_names()
    assert guide, "rehber-src içinde görüntü yok"
    cat = set(gs.CATALOG)
    assert cat <= guide, f"rehberde olmayan görüntü adı: {sorted(cat - guide)}"
    uncovered = {n for n in guide if n not in cat and not SKIPPED.match(n)}
    assert not uncovered, f"katalogda olmayan ama çekilebilir görüntüler: {sorted(uncovered)}"


def test_catalog_shape_and_targets(gs):
    for name, (target, steps) in gs.CATALOG.items():
        assert target in ("wizard", "settings", "chat", "chat_scripted"), name
        assert steps and all(isinstance(s, tuple) and s[0] in ("step", "js", "wait", "tab", "click", "view", "open_conv", "send", "wait_reply", "wait_gone") for s in steps), name
    order = gs.catalog_names()
    assert sorted(order) == sorted(gs.CATALOG) and order[-1] in gs.LAST
    # sihirbaz adım görüntüleri 1..12 hepsi var
    assert {n for n in gs.CATALOG if re.match(r"sihirbaz-\d+-", n)} >= {n for n in gs.guide_image_names() if re.match(r"sihirbaz-\d+-", n)}


def test_demo_vault_path_is_fake(gs):
    p = gs.DEMO_VAULT_PATH.lower()
    assert "ayse" in p and not any(w in p for w in FORBIDDEN)


def test_websocket_frame_roundtrip(gs):
    """Maskeli çerçeve kodlama: sunucu tarafı açılımıyla aynı yük çıkar (ağsız)."""
    import socket
    a, b = socket.socketpair()
    ws = gs.WS.__new__(gs.WS)
    ws.s, ws.rest, ws.id = a, b"", 0
    ws.send("merhaba " * 40)
    raw = b.recv(65536)
    assert raw[0] == 0x81 and raw[1] & 0x80
    n = raw[1] & 0x7F
    off = 2
    if n == 126:
        n = int.from_bytes(raw[2:4], "big"); off = 4
    mask = raw[off:off + 4]
    body = bytes(c ^ mask[i % 4] for i, c in enumerate(raw[off + 4:off + 4 + n]))
    assert body.decode() == "merhaba " * 40
    a.close(); b.close()


def test_setup_server_phone_info_is_fake(dv):
    """Demo kurulum paneli gerçek asistana (8765) ve Tailscale'e bakmaz: telefon durumu uydurma."""
    info = dv.fake_phone_info()
    assert info["ip"].startswith("100.64.") and ":8765" not in info["address"] and info["pairing_code"] == "123456"
