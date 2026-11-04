"""Pano testleri: gerçek panoya hiç dokunulmaz (sahte arabirim); veri tmp_path altındaki config.DATA'dadır."""
import io
import time

import pytest

from sb import features, pano, webroutes

DAY = 86400


class FakeClip(pano.Backend):
    name, available = "fake", True

    def __init__(self):
        self.s = pano.Snapshot()
        self.seq = 0
        self.written = []

    def put(self, text="", png=b"", excluded=False, app=""):
        self.seq += 1
        self.s = pano.Snapshot(text=text, image_png=png, excluded=excluded, app=app, seq=self.seq)

    def snapshot(self, max_text, max_image):
        return self.s

    def write_text(self, text):
        self.written.append(("text", text))

    def write_image(self, png):
        self.written.append(("image", png))


@pytest.fixture(autouse=True)
def module_on(monkeypatch):
    """Özellik anahtarı varsayılan KAPALI; testler modülü açar (kapalı davranış ayrı testte)."""
    monkeypatch.setattr(features, "_choices", lambda: {"pano": True})


@pytest.fixture
def clip():
    fake = FakeClip()
    pano.set_backend(fake)
    pano.OCR = lambda path: ""
    yield fake
    pano.set_backend(None)
    pano.OCR = pano._ocr


@pytest.fixture
def on(clip):
    pano.set_settings({"enabled": True, "collect_images": True})
    return clip


def png(color=(255, 0, 0), size=(8, 8)) -> bytes:
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", size, color).save(b, "PNG")
    return b.getvalue()


def test_default_off_nothing_stored(clip):
    assert pano.settings()["enabled"] is False
    assert pano.capture_text("merhaba dünya") == "off"
    clip.put("merhaba")
    assert pano.Watcher(clip).poll_once() == "off"
    assert pano.search()["total"] == 0


def test_text_and_images_toggle_separately(on):
    pano.set_settings({"collect_text": False})
    assert pano.capture_text("bir metin") == "skipped:text-off"
    assert pano.capture_image(png()) == "saved"
    pano.set_settings({"collect_text": True, "collect_images": False})
    assert pano.capture_text("bir metin") == "saved"
    assert pano.capture_image(png((0, 1, 2))) == "skipped:images-off"


def test_dedupe_refreshes_time(on):
    assert pano.capture_text("aynı metin", now=1000.0) == "saved"
    assert pano.capture_text("  aynı metin \n", now=2000.0) == "refreshed"
    r = pano.search()
    assert r["total"] == 1 and r["items"][0]["updated"] == 2000.0 and r["items"][0]["created"] == 1000.0
    assert pano.capture_image(png()) == "saved"
    assert pano.capture_image(png()) == "refreshed"
    assert pano.search(kinds=["image"])["total"] == 1


def test_link_vs_text(on):
    assert pano.classify("https://example.com/a?b=1") == "link"
    assert pano.classify("  https://example.com  ") == "link"
    assert pano.classify("bak şuna https://example.com güzel") == "text"
    assert pano.classify("https://a.com\nhttps://b.com") == "text"
    pano.capture_text("https://example.com/x")
    pano.capture_text("paragraf https://example.com/x içinde")
    assert pano.search(kinds=["link"])["total"] == 1 and pano.search(kinds=["text"])["total"] == 1


@pytest.mark.parametrize("secret", [
    "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456",
    "sk-ant-abcdefghijklmnopqrstuvwxyz123456",
    "ghp_" + "a1B2c3D4e5" * 4,
    "TR33 0006 1005 1978 6457 8413 26",
    "GB82 WEST 1234 5698 7654 32",
    "4111 1111 1111 1111",
    "şifre: hunter2hunter",
    "password = Tr0ub4dor&3",
    "Zq7#kP9$mX2!vL5w",
    "-----BEGIN RSA PRIVATE KEY-----\nabc",
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXk",
    "doğrulama kodu 482913",
])
def test_secrets_never_stored(on, secret):
    assert pano.capture_text(secret) == "skipped:secret"
    assert pano.search()["total"] == 0


def test_normal_text_not_flagged(on):
    for t in ("toplantı yarın saat 10:00'da", "https://example.com/a/b?q=1", "C:\\Users\\ayse\\Belgeler\\rapor.docx", "Merhaba, nasılsın?"):
        assert pano.capture_text(t) == "saved", t


def test_password_manager_flag_and_blacklist(on):
    on.put("gizli ama normal görünen metin", excluded=True)
    w = pano.Watcher(on)
    assert w.poll_once() == "skipped:excluded"
    on.put("keepass'ten gelen", app="KeePassXC.exe")
    assert w.poll_once() == "skipped:app"
    pano.set_settings({"blacklist": ["notepad"]})
    on.put("not defteri", app="notepad.exe")
    assert w.poll_once() == "skipped:app"
    on.put("kalem", app="word.exe")
    assert w.poll_once() == "saved"
    assert w.poll_once() == "same"                      # panoda değişiklik yok
    assert pano.search()["total"] == 1


def test_watcher_text_and_image(on):
    w = pano.Watcher(on)
    on.put(png=png((1, 2, 3)))
    assert w.poll_once() == "saved"
    on.put("https://example.com")
    assert w.poll_once() == "saved"
    assert {i["kind"] for i in pano.search()["items"]} == {"image", "link"}


def test_size_limits(on):
    pano.set_settings({"max_text_kb": 1})
    assert pano.capture_text("a" * 2000) == "skipped:too-big"
    pano.set_settings({"max_image_mb": 1})
    big = png((9, 9, 9), (1800, 1800))
    import random
    random.seed(1)
    from PIL import Image
    im = Image.frombytes("RGB", (900, 900), random.randbytes(900 * 900 * 3))
    b = io.BytesIO(); im.save(b, "PNG")
    assert len(b.getvalue()) > 1024 * 1024
    assert pano.capture_image(b.getvalue()) == "skipped:too-big"
    assert big  # küçük ama çözülebilir
    pano.set_settings({"max_img_dir_mb": 50})
    pano._img_total  # sınır işlevi var
    assert pano.capture_image(png((5, 5, 5))) == "saved"


def test_retention_and_pin_exception(on):
    old = time.time() - 40 * DAY
    pano.capture_text("eski sıradan", now=old)
    pano.capture_text("eski sabit", now=old)
    pano.capture_text("eski klasörlü", now=old)
    pano.capture_text("eski etiketli", now=old)
    ids = {i["text"]: i["id"] for i in pano.search()["items"]}
    pano.set_pinned(ids["eski sabit"], True)
    pano.set_meta(ids["eski klasörlü"], folder="iş/proje")
    pano.set_meta(ids["eski etiketli"], tags=["x"])
    pano.capture_text("yeni", now=time.time())              # yakalama süresi dolanları da temizler
    pano.purge()
    texts = {i["text"] for i in pano.search()["items"]}
    assert texts == {"eski sabit", "eski klasörlü", "eski etiketli", "yeni"}
    assert "eski sıradan" in {i["text"] for i in pano.search(trash=True)["items"]}


def test_retention_per_kind(on):
    pano.set_settings({"retention": {"link": 3}})
    t = time.time() - 5 * DAY
    pano.capture_text("https://example.com/eski", now=t)
    pano.capture_text("beş günlük metin", now=t)
    pano.purge()
    assert [i["kind"] for i in pano.search()["items"]] == ["text"]
    with pytest.raises(ValueError):
        pano.set_settings({"retention": {"text": 5}})


def test_search_fields_and_filters(on):
    pano.capture_text("alışveriş listesi: süt, ekmek")
    pano.capture_text("https://example.com/yemek-tarifi")
    pano.capture_image(png())
    ids = {i["kind"]: i["id"] for i in pano.search()["items"]}
    pano.set_meta(ids["text"], tags=["Market"], name="Cuma listesi", folder="ev/alışveriş")
    assert pano.search("ekmek")["total"] == 1
    assert pano.search("CUMA")["total"] == 1                # ad
    assert pano.search("market")["total"] == 1              # etiket
    assert pano.search(tag="#market")["total"] == 1
    assert pano.search(folder="ev")["total"] == 1           # iç içe klasör
    assert pano.search(folder="ev/alışveriş")["total"] == 1
    assert pano.search(folder="ev/başka")["total"] == 0
    assert pano.search("tarifi", kinds=["link"])["total"] == 1
    assert pano.search("tarifi", kinds=["text"])["total"] == 0
    pano.set_pinned(ids["link"], True)
    assert [i["kind"] for i in pano.search(pinned=True)["items"]] == ["link"]
    assert pano.search()["items"][0]["kind"] == "link"      # sabitler önde
    assert {f["path"] for f in pano.folders()} == {"ev", "ev/alışveriş"}


def test_ocr_search(on):
    pano.OCR = lambda path: "FATURA toplam 120 TL"
    assert pano.capture_image(png((3, 3, 3))) == "saved"
    assert pano.search("fatura")["total"] == 1
    pano.OCR = lambda path: "password: abc12345"
    pano.capture_image(png((4, 4, 4)))
    assert pano.search("abc12345")["total"] == 0           # sır içeren OCR metni dizine alınmaz


def test_ocr_skipped_when_unavailable(on, monkeypatch):
    pano.OCR = pano._ocr
    monkeypatch.setattr(pano.shutil, "which", lambda n: None)
    assert pano.capture_image(png((7, 7, 7))) == "saved"
    assert pano.search(kinds=["image"])["items"][0]["has_ocr"] is False


def test_trash_restore_undo(on):
    pano.capture_text("bir")
    pano.capture_text("iki")
    a, b = [i["id"] for i in pano.search()["items"]]
    pano.remove(a)
    time.sleep(0.01)
    pano.remove(b)
    assert pano.search()["total"] == 0 and pano.search(trash=True)["total"] == 2
    assert pano.undo_remove()["id"] == b
    assert pano.restore(a)["id"] == a
    assert pano.search()["total"] == 2
    pano.remove(b)
    assert pano.capture_text("bir") == "refreshed"       # çöpteki aynı içerik geri gelir
    assert pano.search()["total"] == 2
    assert pano.undo_remove() is None
    pano.remove(a, hard=True)
    with pytest.raises(KeyError):
        pano.get(a)


def test_trash_expiry_deletes_files(on):
    pano.capture_image(png((8, 8, 8)))
    i = pano.search()["items"][0]["id"]
    path = next(pano._img_dir().glob("*.png"))
    pano.remove(i)
    pano.purge(now=time.time() + 31 * DAY)
    assert not path.exists() and pano.search(trash=True)["total"] == 0


def test_clear_keeps_protected(on):
    pano.capture_text("sıradan")
    pano.capture_text("sabit olan")
    sid = [i["id"] for i in pano.search()["items"] if i["text"] == "sabit olan"][0]
    pano.set_pinned(sid, True)
    assert pano.clear() == 1
    assert [i["text"] for i in pano.search()["items"]] == ["sabit olan"]


def test_copy_back_uses_fake_clipboard(on):
    pano.capture_text("geri yaz")
    pano.capture_image(png((6, 6, 6)))
    for it in pano.search()["items"]:
        assert pano.copy_back(it["id"])["ok"]
    assert ("text", "geri yaz") in on.written and any(k == "image" for k, _ in on.written)


def test_image_bytes_and_thumb(on):
    pano.capture_image(png((1, 1, 1), (800, 600)))
    i = pano.search()["items"][0]["id"]
    from PIL import Image
    assert Image.open(io.BytesIO(pano.image_bytes(i))).size == (800, 600)
    assert max(Image.open(io.BytesIO(pano.image_bytes(i, thumb=True))).size) <= 360


def test_routes_local_only_and_flow(on):
    rs = webroutes.load()
    pano_routes = [r for (m, p), r in rs.items() if p.startswith("/api/v2/pano/")]
    assert len(pano_routes) >= 13 and all(r.local_only for r in pano_routes)

    def call(m, p, data=None, query=None):
        r = webroutes.find(m, p)
        code, body, ct, _ = webroutes.call(r, webroutes.Ctx(m, p, data or {}, query or {}))
        import json
        return code, (json.loads(body) if "json" in ct else body)

    pano.capture_text("rota denemesi")
    code, res = call("GET", "/api/v2/pano/list", query={"kind": "text"})
    assert code == 200 and res["total"] == 1
    i = res["items"][0]["id"]
    assert call("POST", "/api/v2/pano/pin", {"id": i})[1]["pinned"] is True
    assert call("POST", "/api/v2/pano/tag", {"id": i, "tags": ["a"], "name": "ad"})[1]["tags"] == ["a"]
    assert call("POST", "/api/v2/pano/folder", {"id": i, "folder": "x/y"})[1]["folder"] == "x/y"
    assert call("GET", "/api/v2/pano/search", query={"q": "rota"})[1]["total"] == 1
    assert call("POST", "/api/v2/pano/copy", {"id": i})[0] == 200
    assert call("POST", "/api/v2/pano/remove", {"id": i})[0] == 200
    assert call("GET", "/api/v2/pano/trash")[1]["total"] == 1
    assert call("POST", "/api/v2/pano/restore", {})[1]["id"] == i
    assert call("GET", "/api/v2/pano/item", query={"id": "999"})[0] == 404
    assert call("POST", "/api/v2/pano/settings", {"retention": {"text": 7}})[1]["settings"]["retention"]["text"] == 7
    assert call("POST", "/api/v2/pano/settings", {"retention": {"text": 8}})[0] == 400
    pano.watcher().stop()


def test_api_settings_off_stops_and_status(clip):
    st = pano.status()
    assert st["enabled"] is False and st["running"] is False and st["counts"] == {"image": 0, "text": 0, "link": 0}


def test_module_off_blocks_capture_watcher_and_routes(clip, monkeypatch):
    monkeypatch.setattr(features, "_choices", lambda: {})
    assert features.MODULES["pano"][3] is False and not pano.module_on()
    pano.set_settings({"enabled": True})                       # kullanıcı ayarı açık olsa da modül kapalıyken çalışmaz
    assert pano.capture_text("merhaba dünya") == "off"
    clip.put("merhaba")
    assert pano.Watcher(clip).poll_once() == "off"
    assert pano.ensure_running() is False and not pano.watcher().running
    assert pano.status()["enabled"] is False and pano.status()["module"] is False
    routes = webroutes.load()
    fn = routes[("GET", "/api/v2/pano/list")].fn
    with pytest.raises(webroutes.ApiError) as e:
        fn(None)
    assert e.value.code == 403
    st = routes[("GET", "/api/v2/pano/status")].fn(None)
    assert st["module"] is False and st["enabled"] is False
