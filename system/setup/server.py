"""Kurulum paneli yerel sunucusu (stdlib http; yalnız 127.0.0.1; rastgele port; oturum jetonu).

API SÖZLEŞMESİ (Paket P arayüzü buna göre yazar)
------------------------------------------------
Güvenlik: sunucu yalnız 127.0.0.1'e bağlanır. Her /api/* isteği `X-Setup-Token: <jeton>` başlığı taşımalıdır, yoksa/yanlışsa 403.
Statik arayüz: `GET /?t=<jeton>` index.html'i, `GET /ui/<dosya>?t=<jeton>` ya da `GET /<dosya>?t=<jeton>` setup/ui/ dosyalarını verir
(jetonsuz 403). Sayfa jetonu `location.search`'ten alıp sonraki tüm fetch'lerde `X-Setup-Token` başlığına koyar. Host başlığı
127.0.0.1/localhost değilse ya da Origin başka kökense 403 (DNS rebinding koruması). Gövdeler JSON (en çok 1 MB); yanıtlar JSON, UTF-8.
Hata: {"error": "mesaj"} + 400/403/404/409.

GET  /api/presets    -> {presets: {id: {label, desc, local_model, modules: {anahtar: bool}}},
                         modules: {anahtar: {name, desc, requires, default, category}}, categories: {kategori: [anahtar]}}
GET  /api/fields?preset=ogrenci[&modules=a,b]  -> {fields: [{key,label,kind:"text|path|email|secret",secret,required?,default?}], preset, local_model}
GET  /api/hardware   -> {hardware: {os,ram_gb,cpu_cores,gpu,vram_gb,disk_free_gb,note}, recommend: {profile,model,vision_model,download_gb,why}}
POST /api/apply      {preset, modules?: {anahtar: bool}, fields: {alan: değer}, resume?: bool} -> 202 {started:true} | 409 {error} (iş sürüyor)
                     Sır alanları (imap_password, openai_key, anthropic_key, gemini_key, telegram_token) sunucuya BİR KEZ gider,
                     keyring'e yazılır, bellekten silinir; dosyaya/günlüğe/profile girmez.
GET  /api/progress   -> {running, job: "apply|update|", percent, steps: [{id,title,status: pending|running|done|skipped|error}],
                         log: [son 200 satır], error}
GET  /api/state      -> {resumable, done: [adım], pending: [adım], selection, updated}   (kaldığın yerden devam: apply {resume:true})
POST /api/test       {kind: ollama|google|imap|openai|anthropic|gemini|tailscale|obsidian, fields?: {...}} -> {ok, message}
GET  /api/profile    -> {format, version, preset, modules, fields (sırsız), local_model}      (indirilecek profil dosyası)
POST /api/profile    {profil JSON} -> {ok, selection}   (içe aktarma; sır alanları yok sayılır)
GET  /api/health     -> {ok, rows: [{status: ok|warn|fail, name, hint}], summary, returncode?, message?}   (`sb doctor`)
GET  /api/update     -> {current, latest, source, update_available}
POST /api/update     {} -> 202 {started:true} | 409   (`sb update` çalışır; /api/progress ile izle, job:"update")
GET  /api/uninstall  -> {applied:false, plan: [{id,desc,auto}]}
POST /api/uninstall  {confirm: true} -> {applied, plan, done}   (confirm yoksa yalnız plan; kasa notlarına dokunulmaz)
POST /api/modules/disable {keys: [anahtar]} -> {disabled, note}   (bir özelliği geri al; dosya silinmez)
POST /api/shutdown   {} -> {ok:true}   (sunucu kapanır; app.py pencere kapanınca çağırır)
"""
from __future__ import annotations

import hmac
import json
import mimetypes
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from . import engine as E
except ImportError:                                           # python setup/server.py gibi doğrudan çalıştırma
    import engine as E  # type: ignore

UI = Path(__file__).resolve().parent / "ui"
MAX_BODY = 1 << 20
STATIC_EXT = {".html", ".css", ".js", ".json", ".svg", ".png", ".ico", ".woff2", ".txt"}


class Handler(BaseHTTPRequestHandler):
    server_version = "SetupPanel"
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):                                # konsola istek günlüğü yazma (URL'de jeton var)
        pass

    @property
    def eng(self) -> E.Engine:
        return self.server.engine                             # type: ignore[attr-defined]

    # -- yardımcılar
    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        if host not in ("127.0.0.1", "localhost"):
            return False
        origin = self.headers.get("Origin")
        if origin:
            o = urlparse(origin)
            return o.hostname in ("127.0.0.1", "localhost") and o.port == self.server.server_address[1]
        return True

    def _token_ok(self, query: dict) -> bool:
        tok = self.headers.get("X-Setup-Token") or (query.get("t") or [""])[0]
        return bool(tok) and hmac.compare_digest(tok, self.server.token)   # type: ignore[attr-defined]

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            raise ValueError("istek çok büyük")
        raw = self.rfile.read(n) if n else b""
        data = json.loads(raw.decode("utf-8")) if raw.strip() else {}
        if not isinstance(data, dict):
            raise ValueError("JSON nesnesi bekleniyor")
        return data

    # -- yönlendirme
    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if not self._host_ok():
            return self._json(403, {"error": "yasak"})
        api = u.path.startswith("/api/")
        if api and not self.headers.get("X-Setup-Token"):     # API'de jeton yalnız başlıktan (URL'ye sızmasın)
            return self._json(403, {"error": "jeton gerekli"})
        if api and not self._token_ok(q):                      # arayüz dosyaları (html/css/js) sır içermez; jeton yalnız API'de
            return self._json(403, {"error": "jeton gerekli"})
        try:
            if api:
                return self._api(method, u.path, q)
            if method != "GET":
                return self._json(404, {"error": "bulunamadı"})
            return self._static(u.path)
        except ValueError as e:
            return self._json(400, {"error": str(e)})
        except json.JSONDecodeError:
            return self._json(400, {"error": "geçersiz JSON"})
        except Exception as e:
            return self._json(500, {"error": E.redact(f"{type(e).__name__}: {e}", self.eng._secrets)})

    def _static(self, path: str) -> None:
        rel = "index.html" if path in ("/", "") else path.removeprefix("/ui/").lstrip("/")
        p = (UI / rel).resolve()
        if UI.resolve() not in p.parents or p.suffix.lower() not in STATIC_EXT or not p.is_file():
            return self._json(404, {"error": "bulunamadı"})
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        if p.suffix == ".js":
            ctype = "text/javascript"
        self._send(200, p.read_bytes(), ctype + ("; charset=utf-8" if ctype.startswith("text/") else ""))

    def _api(self, method: str, path: str, q: dict) -> None:
        e = self.eng
        route = (method, path)
        if route == ("GET", "/api/presets"):
            return self._json(200, {"presets": E.PRESETS, "modules": E.modules_meta(), "categories": E.CATEGORIES})
        if route == ("GET", "/api/fields"):
            preset = (q.get("preset") or [e.selection.get("preset") or "tam"])[0]
            mods = E.preset_modules(preset)
            if q.get("modules"):
                on = {m for m in q["modules"][0].split(",") if m}
                mods = {k: k in on for k in mods}
            lm = E.PRESETS[preset]["local_model"]
            return self._json(200, {"fields": E.fields_for(mods, lm), "preset": preset, "local_model": lm})
        if route == ("GET", "/api/hardware"):
            hw = E.hardware()
            return self._json(200, {"hardware": hw, "recommend": E.recommend(hw)})
        if route == ("POST", "/api/apply"):
            b = self._body()
            if not e.apply({"preset": b.get("preset"), "modules": b.get("modules"), "fields": b.get("fields")}, resume=bool(b.get("resume"))):
                return self._json(409, {"error": "başka bir iş sürüyor"})
            return self._json(202, {"started": True})
        if route == ("GET", "/api/progress"):
            return self._json(200, e.progress())
        if route == ("GET", "/api/state"):
            return self._json(200, e.state())
        if route == ("POST", "/api/test"):
            b = self._body()
            return self._json(200, e.test(str(b.get("kind") or ""), b.get("fields") if isinstance(b.get("fields"), dict) else None))
        if route == ("GET", "/api/profile"):
            return self._json(200, e.export_profile())
        if route == ("POST", "/api/profile"):
            return self._json(200, {"ok": True, "selection": e.import_profile(self._body())})
        if route == ("GET", "/api/health"):
            return self._json(200, e.health())
        if route == ("GET", "/api/update"):
            return self._json(200, e.version_info())
        if route == ("POST", "/api/update"):
            if not e.run_update():
                return self._json(409, {"error": "başka bir iş sürüyor"})
            return self._json(202, {"started": True})
        if route == ("GET", "/api/uninstall"):
            return self._json(200, e.uninstall(False))
        if route == ("POST", "/api/uninstall"):
            return self._json(200, e.uninstall(self._body().get("confirm") is True))
        if route == ("POST", "/api/modules/disable"):
            keys = self._body().get("keys")
            if not isinstance(keys, list):
                raise ValueError("keys listesi gerekli")
            return self._json(200, e.disable_modules([str(k) for k in keys]))
        if route == ("POST", "/api/shutdown"):
            self._json(200, {"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return None
        return self._json(404, {"error": "bulunamadı"})


class SetupServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, engine: E.Engine | None = None, port: int = 0):
        super().__init__(("127.0.0.1", port), Handler)
        self.engine = engine or E.Engine()
        self.token = secrets.token_urlsafe(24)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}/?t={self.token}"

    def start(self) -> "SetupServer":
        threading.Thread(target=self.serve_forever, daemon=True).start()
        return self

    def stop(self) -> None:
        self.shutdown()
        self.server_close()


def make_server(engine: E.Engine | None = None, port: int = 0) -> SetupServer:
    return SetupServer(engine, port)


if __name__ == "__main__":
    srv = make_server()
    print(srv.url, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
