"""Paket M: paylaş, push, tünel, statik dosyalar (gerçek ağ/keyring/push yok)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from sb import api_mobile, chat, config, mobile, webroutes  # noqa: F401 — MODULES kaydı Opus'ta; burada doğrudan yükle
from sb.webroutes import Ctx

WEB = Path(mobile.__file__).parent / "web"
SUB = {"endpoint": "https://fcm.googleapis.com/fcm/send/abc", "keys": {"p256dh": "B" * 40, "auth": "a" * 16}}


def call(method, path, data=None, raw=b"", ctype="", query=None):
    r = webroutes.find(method, path)
    assert r is not None, path
    ctx = Ctx(method, path, data or {}, query or {}, raw, ctype, "s1", False, chat.Session(), None, None, "local")
    code, body, _, _ = webroutes.call(r, ctx)
    return code, json.loads(body)


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    store = {}
    monkeypatch.setattr(mobile, "_kr_get", lambda n: store.get(n))
    monkeypatch.setattr(mobile, "_kr_set", lambda n, v: store.__setitem__(n, v))
    monkeypatch.setattr(mobile.shutil, "which", lambda n: None)
    return store


def test_routes_registered():
    for m, p in [("POST", "/api/v2/share"), ("POST", "/api/v2/push/subscribe"), ("GET", "/api/v2/push/status"), ("GET", "/api/v2/tunnel")]:
        assert webroutes.find(m, p) is not None


def test_share_redacts_and_captures(monkeypatch):
    seen = []
    monkeypatch.setattr(mobile, "_capture", lambda t: seen.append(t) or "ok")
    code, out = call("POST", "/api/v2/share", {"title": "Başlık", "text": "mail ali@example.com iban TR330006100519786457841326", "url": "https://x.org/a"},
                     raw=json.dumps({"title": "Başlık", "text": "mail ali@example.com iban TR330006100519786457841326", "url": "https://x.org/a"}).encode(),
                     ctype="application/json")
    assert code == 200 and out["ok"]
    assert "TR330006100519786457841326" not in seen[0] and "Başlık" in seen[0] and "https://x.org/a" in seen[0]


def test_share_multipart_file(monkeypatch):
    got = {}
    monkeypatch.setattr(mobile, "_capture", lambda t: "m")
    def cf(p):
        got["name"], got["data"] = Path(p).name, Path(p).read_bytes()
        return "dosya"
    monkeypatch.setattr(mobile, "_capture_file", cf)
    b = "XBOUND"
    raw = (f"--{b}\r\nContent-Disposition: form-data; name=\"text\"\r\n\r\nmerhaba\r\n"
           f"--{b}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"../x.txt\"\r\nContent-Type: text/plain\r\n\r\nicerik\r\n--{b}--\r\n").encode()
    code, out = call("POST", "/api/v2/share", raw=raw, ctype=f"multipart/form-data; boundary={b}")
    assert code == 200 and out["results"] == ["m", "dosya"]
    assert got["name"] == "x.txt" and got["data"] == b"icerik"
    assert not (config.DATA / "share-tmp" / "x.txt").exists()


def test_share_rejects_empty_and_bad_ext(monkeypatch):
    monkeypatch.setattr(mobile, "_capture_file", lambda p: pytest.fail("çağrılmamalı"))
    code, _ = call("POST", "/api/v2/share", raw=b"{}", ctype="application/json")
    assert code == 400
    assert "Desteklenmeyen" in mobile.share(files=[("a.exe", b"x")])["results"][0]


def test_share_page_escapes():
    assert "<script>alert" not in mobile.share_page(text="<script>alert(1)</script>").split("<script>")[0]
    assert "&lt;script&gt;" in mobile.share_page(text="<script>x</script>")


def test_push_unavailable(monkeypatch):
    monkeypatch.setattr(mobile, "push_available", lambda: False)
    assert mobile.push_send("a")["available"] is False
    code, out = call("POST", "/api/v2/push/subscribe", {"subscription": SUB})
    assert code == 200 and out["available"] is False and mobile.subscriptions() == []
    assert call("GET", "/api/v2/push/status")[1]["available"] is False


def test_push_subscribe_and_send(monkeypatch, env):
    monkeypatch.setattr(mobile, "push_available", lambda: True)
    sent = []
    monkeypatch.setattr(mobile, "_sender", lambda s, p: sent.append((s, json.loads(p))))
    assert call("POST", "/api/v2/push/subscribe", {"subscription": SUB})[1]["ok"]
    assert call("POST", "/api/v2/push/subscribe", {"subscription": {"endpoint": "http://x", "keys": {}}})[0] == 400
    assert mobile.push_send("Başlık", "gövde TR330006100519786457841326")["sent"] == 1
    assert sent[0][1]["title"] == "Başlık" and "TR330006100519786457841326" not in sent[0][1]["body"]
    # abonelik yalnız config.DATA'da, vault'ta değil
    assert (config.DATA / "push_subs.json").exists()
    assert call("POST", "/api/v2/push/unsubscribe", {"endpoint": SUB["endpoint"]})[1]["removed"] == 1


def test_push_dead_subscription_removed(monkeypatch):
    monkeypatch.setattr(mobile, "push_available", lambda: True)
    class E(Exception):
        response = type("R", (), {"status_code": 410})()
    def boom(s, p):
        raise E()
    monkeypatch.setattr(mobile, "_sender", boom)
    mobile.subscribe(SUB, "local")
    assert mobile.push_send("x")["sent"] == 0 and mobile.subscriptions() == []


def test_vapid_private_only_in_keyring(env):
    pytest.importorskip("cryptography")
    pub = mobile.vapid_public_key()
    assert len(pub) >= 80 and mobile.VAPID_KEY in env
    assert mobile.vapid_public_key() == pub                     # kalıcı
    priv = env[mobile.VAPID_KEY]
    for f in config.DATA.rglob("*") if config.DATA.exists() else []:
        if f.is_file():
            assert priv not in f.read_text(encoding="utf-8", errors="ignore")


def test_on_notify_no_subs_noop(monkeypatch):
    monkeypatch.setattr(mobile.threading, "Thread", lambda *a, **k: pytest.fail("iş parçacığı açılmamalı"))
    mobile.on_notify({"title": "x"})


def test_tunnel_not_ready_without_access(monkeypatch):
    monkeypatch.setattr(mobile.shutil, "which", lambda n: "/bin/cloudflared")
    config.DATA.mkdir(parents=True, exist_ok=True)
    (config.DATA / "tunnel.json").write_text(json.dumps({"hostname": "b.example.com"}), encoding="utf-8")
    st = mobile.tunnel_status()
    assert st["ready"] is False and any("Access" in m for m in st["missing"])
    assert mobile.tunnel_plan()["commands"] == []
    (config.DATA / "tunnel.json").write_text(json.dumps({"hostname": "b.example.com", "access_policy": True}), encoding="utf-8")
    assert mobile.tunnel_status()["ready"] is True and mobile.tunnel_plan()["commands"]
    assert call("GET", "/api/v2/tunnel")[1]["status"]["ready"] is True


def test_tunnel_default_not_ready():
    assert mobile.tunnel_status()["ready"] is False


def test_manifest_and_static():
    m = json.loads((WEB / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert m["display"] == "standalone" and m["share_target"]["action"] == "/share" and m["icons"]
    assert chat.static_file("manifest.webmanifest")[1].startswith("application/manifest+json")
    assert chat.static_file("sw.js") and chat.static_file("icon.svg") and chat.static_file("mobile.js")


@pytest.mark.skipif(not shutil.which("node"), reason="node yok")
@pytest.mark.parametrize("f", ["sw.js", "mobile.js"])
def test_node_check(f):
    r = subprocess.run(["node", "--check", str(WEB / f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
