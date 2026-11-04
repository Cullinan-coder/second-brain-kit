"""Faz 2 API katmanı: kayıt, dağıtım, yerel-yalnız, yükleme sınırı, statik dosya güvenliği."""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from sb import chat, webroutes


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setattr(chat, "retrieve", lambda text: ("", ""))

    @webroutes.route("GET", "/api/v2/_t/echo")
    def _echo(ctx):
        return {"q": ctx.query, "sid": ctx.sid, "remote": ctx.remote}

    @webroutes.route("POST", "/api/v2/_t/chat", model=True)
    def _chat(ctx):
        return ctx.respond(ctx.arg("text", ""))

    @webroutes.route("POST", "/api/v2/_t/up", upload=True)
    def _up(ctx):
        return {"n": len(ctx.raw), "name": ctx.arg("name")}

    @webroutes.route("POST", "/api/v2/_t/local", local_only=True)
    def _local(ctx):
        return {"ok": True}

    @webroutes.route("GET", "/api/v2/_t/err")
    def _err(ctx):
        raise webroutes.ApiError(409, "çakışma")

    srv = ThreadingHTTPServer(("127.0.0.1", 0), chat.make_handler(chat_fn=lambda m, c: {"content": "selam Ayşe"}))
    port = srv.server_address[1]
    monkeypatch.setattr(chat, "ALLOWED_HOSTS", {f"127.0.0.1:{port}"})
    monkeypatch.setattr(chat, "ALLOWED_ORIGINS", {f"http://127.0.0.1:{port}"})
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()
    for k in [k for k in webroutes.ROUTES if "/_t/" in k[1]]:
        del webroutes.ROUTES[k]


def _post(url, body, ctype="application/json", headers=None):
    data = body if isinstance(body, bytes) else json.dumps(body).encode()
    from sb import localauth
    h = {"Content-Type": ctype, "X-SB": "1", "X-SB-Token": localauth.token(), **(headers or {})}
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h))


def test_v2_get_post_upload_and_errors(server):
    r = json.loads(urllib.request.urlopen(server + "/api/v2/_t/echo?a=1&sid=k").read())
    assert r == {"q": {"a": "1", "sid": "k"}, "sid": "k", "remote": False}
    assert json.loads(_post(server + "/api/v2/_t/chat", {"sid": "s", "text": "merhaba"}).read())["reply"] == "selam Ayşe"
    assert json.loads(_post(server + "/api/v2/_t/up?name=a.wav", b"\x00" * 1000, "audio/wav").read()) == {"n": 1000, "name": "a.wav"}
    assert json.loads(_post(server + "/api/v2/_t/local", {}).read()) == {"ok": True}
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(server + "/api/v2/_t/err")
    assert e.value.code == 409 and json.loads(e.value.read())["error"] == "çakışma"
    with pytest.raises(urllib.error.HTTPError) as e:
        _post(server + "/api/v2/_t/chat", {"text": "x"}, headers={"X-SB": ""})          # CSRF başlığı yok
    assert e.value.code == 403
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(server + "/api/v2/yok")
    assert e.value.code == 404


def test_static_file_rejects_traversal_and_unknown_types(tmp_path, monkeypatch):
    monkeypatch.setattr(chat, "WEB", tmp_path)
    (tmp_path / "app.js").write_text("x", encoding="utf-8")
    (tmp_path / "gizli.py").write_text("x", encoding="utf-8")
    assert chat.static_file("app.js") == (b"x", "text/javascript; charset=utf-8")
    for bad in ("../chat.py", "gizli.py", ".env", "a/b.js", "..", ""):
        assert chat.static_file(bad) is None


def test_routes_listing_reports_registered():
    out = webroutes.call(webroutes.find("GET", "/api/v2/routes"), webroutes.Ctx("GET", "/api/v2/routes"))
    assert out[0] == 200 and "GET /api/v2/routes" in json.loads(out[1])["routes"]


def test_extension_origin_only_when_allowlisted(tmp_path, monkeypatch):
    from sb import config
    monkeypatch.setattr(config, "SYSTEM", tmp_path)
    assert chat.extension_origins() == set()                                   # dosya yok: hiçbir eklenti
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "eklentiler.yaml").write_text("chrome: [abcdefghijklmnopabcdefghijklmnop, '../kotu']\n", encoding="utf-8")
    assert chat.extension_origins() == {"chrome-extension://abcdefghijklmnopabcdefghijklmnop"}


def test_spotify_callback_escapes_reflected_error(server, monkeypatch):
    from sb import spotify_api
    monkeypatch.setattr(spotify_api, "client_id", lambda: "x")
    r = urllib.request.urlopen(server + "/spotify/callback?error=%3Cscript%3Ealert(1)%3C/script%3E")
    body = r.read().decode("utf-8")
    assert "<script>" not in body and "&lt;script&gt;" in body
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]
