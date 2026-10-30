"""Spotify Web API (Premium): şarkıyı doğrudan çalma. Yetkilendirme PKCE ile — istemci sırrı YOK, yalnız Client ID.

Akış: kullanıcı bir kez http://127.0.0.1:8765/spotify/login açar → Spotify onay sayfası → /spotify/callback.
Yenileme jetonu keyring'de (service second-brain, ad spotify-refresh); kasaya ya da git'e gitmez.
İzinler yalnız çalma durumu/kontrolü: user-read-playback-state, user-modify-playback-state.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import urllib.parse
import urllib.request

import keyring
import yaml

from .config import KEYRING_SERVICE, SYSTEM

REDIRECT = "http://127.0.0.1:8765/spotify/callback"
SCOPES = "user-read-playback-state user-modify-playback-state"
KEY = "spotify-refresh"
_pending: dict[str, str] = {}            # state → code_verifier (yalnız bellekte, 10 dk)
_token: dict = {"access": "", "exp": 0.0}


def client_id() -> str:
    try:
        cfg = yaml.safe_load((SYSTEM / "config" / "spotify.yaml").read_text(encoding="utf-8")) or {}
    except OSError:
        return ""
    return str(cfg.get("client_id") or "").strip()


def ready() -> bool:
    return bool(client_id()) and bool(keyring.get_password(KEYRING_SERVICE, KEY))


def login_url() -> str:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    _pending.clear()
    _pending[state] = verifier
    return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": client_id(), "response_type": "code", "redirect_uri": REDIRECT, "scope": SCOPES,
        "code_challenge_method": "S256", "code_challenge": challenge, "state": state})


def _post_token(data: dict) -> dict:
    req = urllib.request.Request("https://accounts.spotify.com/api/token", urllib.parse.urlencode(data).encode(),
                                 {"Content-Type": "application/x-www-form-urlencoded"})
    return json.load(urllib.request.urlopen(req, timeout=20))


def callback(code: str, state: str) -> str:
    verifier = _pending.pop(state, None)
    if not verifier:
        return "Geçersiz ya da süresi geçmiş istek; /spotify/login'i yeniden aç."
    tok = _post_token({"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
                       "client_id": client_id(), "code_verifier": verifier})
    keyring.set_password(KEYRING_SERVICE, KEY, tok["refresh_token"])
    _token.update(access=tok["access_token"], exp=time.time() + tok.get("expires_in", 3600) - 60)
    return "Spotify bağlandı. Bu sekmeyi kapatabilirsin."


def _access() -> str:
    if _token["access"] and time.time() < _token["exp"]:
        return _token["access"]
    refresh = keyring.get_password(KEYRING_SERVICE, KEY)
    if not refresh:
        raise RuntimeError("Spotify bağlı değil")
    tok = _post_token({"grant_type": "refresh_token", "refresh_token": refresh, "client_id": client_id()})
    if tok.get("refresh_token"):                       # Spotify yenileme jetonunu döndürebilir
        keyring.set_password(KEYRING_SERVICE, KEY, tok["refresh_token"])
    _token.update(access=tok["access_token"], exp=time.time() + tok.get("expires_in", 3600) - 60)
    return _token["access"]


def _api(method: str, path: str, body: dict | None = None, query: dict | None = None):
    url = "https://api.spotify.com/v1" + path + ("?" + urllib.parse.urlencode(query) if query else "")
    req = urllib.request.Request(url, json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Authorization": f"Bearer {_access()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def _spotify_running() -> bool:
    import subprocess
    import sys
    if sys.platform != "win32":
        return subprocess.run(["pgrep", "-x", "Spotify"], capture_output=True).returncode == 0
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Spotify.exe", "/NH"], capture_output=True, text=True,
                       timeout=10, creationflags=0x08000000)
    return "Spotify.exe" in (r.stdout or "")


def _device(wait: int = 25) -> str | None:
    """HER ZAMAN bu bilgisayar: Spotify kapalıysa açılır, bilgisayar cihaz listesine düşene kadar beklenir.
    (Etkin cihaza çalınca şarkı telefondaki Spotify'a gidiyordu.)"""
    import socket
    me = socket.gethostname().lower()
    if not _spotify_running():
        os.startfile("spotify:")
    for _ in range(wait):
        devs = _api("GET", "/me/player/devices").get("devices", [])
        pc = [d for d in devs if d.get("type") == "Computer" and d.get("name", "").lower() == me] or \
             [d for d in devs if d.get("type") == "Computer"]
        if pc:
            return pc[0]["id"]
        time.sleep(1)
    return None


def play(query: str) -> str:
    res = _api("GET", "/search", query={"q": query, "type": "track", "limit": 1, "market": "TR"})   # from_token ülke izni ister → 403
    items = res.get("tracks", {}).get("items", [])
    if not items:
        return f"Spotify'da '{query}' için şarkı bulunamadı."
    t = items[0]
    name = f"{t['name']} — {', '.join(a['name'] for a in t['artists'])}"
    dev = _device()
    if not dev:
        return f"Bilgisayardaki Spotify açılamadı ya da bağlanmadı; Spotify'ı açıp tekrar dene. (Bulunan: {name})"
    # Yeni açılan Spotify ilk komutu sessizce kaçırabiliyor: çalıyor mu diye bak, değilse tekrar dene (en fazla 3 kez).
    # Doğrudan {"uris": [...]} komutu masaüstü Spotify'da sessizce boş kalıyordu (item=None). Çalışan yol:
    # önce çalmayı bu bilgisayara AKTAR, sonra şarkıyı albümünün içinden başlat (context_uri + offset).
    try:
        _api("PUT", "/me/player", {"device_ids": [dev], "play": False})
        time.sleep(2)
    except urllib.error.HTTPError:
        pass                                               # aktarım başarısızsa yine de çalmayı dene
    body = {"context_uri": t["album"]["uri"], "offset": {"uri": t["uri"]}} if t.get("album", {}).get("uri") else {"uris": [t["uri"]]}
    for attempt in range(3):
        try:
            _api("PUT", "/me/player/play", body, {"device_id": dev})
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return "Spotify çalmaya izin vermedi: doğrudan çalma yalnız Premium hesapta çalışır."
            if e.code != 404:                              # 404: cihaz henüz hazır değil → bekle, tekrar dene
                raise
        for _ in range(6):
            time.sleep(1)
            st = _api("GET", "/me/player") or {}
            if st.get("is_playing") and (st.get("device") or {}).get("id") == dev and \
                    (st.get("item") or {}).get("uri") == t["uri"]:
                return f"Çalıyor (bu bilgisayarda): {name}"
        time.sleep(2 * (attempt + 1))
    return f"Spotify açıldı ama çalma başlamadı; Spotify penceresinde ▶'ye basman gerekebilir. (Şarkı: {name})"
