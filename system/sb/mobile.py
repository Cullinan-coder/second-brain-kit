"""Paket M: telefon — paylaş→beyne at, web push, dış erişim tüneli planı (Faz 5).

Ağ/keyring/push dış dünyaya yalnız `_kr_get/_kr_set`, `_sender`, `_capture`, `_capture_file`, `shutil.which` üzerinden gider (testte taklit edilir).
- VAPID özel anahtarı yalnız keyring'de; abonelikler `config.DATA/push_subs.json` (kasaya yazılmaz).
- Tünel kendiliğinden başlamaz; Cloudflare Access politikası onaylanmadan `ready: False`.
"""
from __future__ import annotations

import base64
import html
import importlib.util
import json
import os
import re
import shutil
import threading
from email.parser import BytesParser
from email.policy import default as _policy
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import capture, config
from .redact import redact

_lock = threading.Lock()
MAX_TEXT = 8000
VAPID_KEY = "push-vapid-private"


# ---------------- paylaş -> beyne at
def parse_form(raw: bytes, ctype: str) -> tuple[dict, list[tuple[str, bytes]]]:
    """multipart/form-data, JSON ya da urlencoded gövde -> (alanlar, [(dosya adı, bayt)])."""
    ct = (ctype or "").lower()
    if ct.startswith("application/json"):
        d = json.loads(raw.decode("utf-8") or "{}")
        return (d if isinstance(d, dict) else {}), []
    if ct.startswith("multipart/form-data"):
        msg = BytesParser(policy=_policy).parsebytes(b"Content-Type: " + ctype.encode("latin-1", "replace") + b"\r\n\r\n" + raw)
        fields: dict = {}
        files: list[tuple[str, bytes]] = []
        for part in msg.iter_parts() if msg.is_multipart() else []:
            name, fn = part.get_param("name", header="content-disposition"), part.get_filename()
            payload = part.get_payload(decode=True) or b""
            if fn:
                files.append((fn, payload))
            elif name:
                fields[str(name)] = payload.decode("utf-8", "replace")
        return fields, files
    return {k: v[0] for k, v in parse_qs(raw.decode("utf-8", "replace")).items()}, []


def compose(title: str = "", text: str = "", url: str = "") -> str:
    title, text, url = (str(x or "").strip() for x in (title, text, url))
    parts = [p for p in (title if title and title not in text else "", text) if p]
    if url and url not in text:
        parts.append(url)
    return redact("\n".join(parts))[:MAX_TEXT]


def _capture(text: str) -> str:
    return capture.capture(text)


def _capture_file(path: str) -> str:
    return capture.capture_file(path)


def share(title: str = "", text: str = "", url: str = "", files: list[tuple[str, bytes]] | None = None) -> dict:
    """Paylaşılanı mevcut yakalama yoluna verir. Metin `redact`'lıdır. {ok, results[]}."""
    results: list[str] = []
    body = compose(title, text, url)
    if body:
        results.append(_capture(body))
    for fn, data in (files or [])[:5]:
        name = re.sub(r"[^\w .()-]", "_", Path(str(fn)).name).strip(" .")[:80] or "paylasim"
        if Path(name).suffix.lower() not in capture.FILE_EXT:
            results.append(f"Desteklenmeyen dosya türü: {name}")
            continue
        tmp = config.DATA / "share-tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        p = tmp / name
        try:
            p.write_bytes(data)
            results.append(_capture_file(str(p)))
        finally:
            p.unlink(missing_ok=True)
    if not results:
        return {"ok": False, "error": "paylaşılacak bir şey yok"}
    return {"ok": True, "results": results}


def share_page(title: str = "", text: str = "", url: str = "") -> str:
    """iOS Kestirme / Android dışı yedek: `/share?text=` sayfası (Opus kökten sunar). Önizler, düğmeyle gönderir."""
    t = compose(title, text, url)
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Beyne at</title><link rel="manifest" href="/manifest.webmanifest">
<style>body{{font:16px system-ui;margin:16px;max-width:640px}}textarea{{width:100%;min-height:40vh;font:inherit;padding:8px}}button{{font:inherit;padding:10px 18px;margin-top:8px}}</style></head>
<body><h1>Beyne at</h1><textarea id="t" aria-label="Metin">{html.escape(t)}</textarea><div><button id="b" type="button">Beyne at</button> <span id="m" role="status"></span></div>
<script>document.getElementById('b').onclick=async()=>{{const m=document.getElementById('m');m.textContent='Gönderiliyor…';
try{{const r=await fetch('/api/v2/share',{{method:'POST',headers:{{'X-SB':'1','Content-Type':'application/json'}},body:JSON.stringify({{text:document.getElementById('t').value}})}});
const j=await r.json();m.textContent=r.ok?(j.results||['Tamam']).join(' '):(j.error||'Hata');}}catch(e){{m.textContent='Ulaşılamadı; sonra yeniden dene';}}}};</script></body></html>"""


# ---------------- Web Push
def _kr_get(name: str) -> str | None:
    import keyring
    return keyring.get_password(config.KEYRING_SERVICE, name)


def _kr_set(name: str, value: str) -> None:
    import keyring
    keyring.set_password(config.KEYRING_SERVICE, name, value)


def push_available() -> bool:
    return importlib.util.find_spec("pywebpush") is not None and importlib.util.find_spec("cryptography") is not None


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def vapid_public_key(create: bool = True) -> str:
    """Uygulama sunucu anahtarı (base64url, sıkıştırılmamış P-256 noktası). Özel anahtar yalnız keyring'e yazılır."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    raw = _kr_get(VAPID_KEY)
    if raw:
        key = ec.derive_private_key(int.from_bytes(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)), "big"), ec.SECP256R1())
    elif create:
        key = ec.generate_private_key(ec.SECP256R1())
        _kr_set(VAPID_KEY, _b64u(key.private_numbers().private_value.to_bytes(32, "big")))
    else:
        return ""
    return _b64u(key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))


def _subs_path() -> Path:
    return config.DATA / "push_subs.json"


def subscriptions() -> list[dict]:
    try:
        d = json.loads(_subs_path().read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _save_subs(rows: list[dict]) -> None:
    config.DATA.mkdir(parents=True, exist_ok=True)
    _subs_path().write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def valid_subscription(sub) -> dict | None:
    if not isinstance(sub, dict):
        return None
    ep, keys = str(sub.get("endpoint") or ""), sub.get("keys") or {}
    if urlparse(ep).scheme != "https" or len(ep) > 1000 or not isinstance(keys, dict):
        return None
    p256, auth = str(keys.get("p256dh") or ""), str(keys.get("auth") or "")
    if not re.fullmatch(r"[\w-]{20,200}={0,2}", p256) or not re.fullmatch(r"[\w-]{8,100}={0,2}", auth):
        return None
    return {"endpoint": ep, "keys": {"p256dh": p256, "auth": auth}}


def subscribe(sub) -> bool:
    s = valid_subscription(sub)
    if not s:
        return False
    with _lock:
        rows = [r for r in subscriptions() if r.get("endpoint") != s["endpoint"]] + [s]
        _save_subs(rows[-20:])
    return True


def unsubscribe(endpoint: str) -> int:
    with _lock:
        rows = subscriptions()
        keep = [r for r in rows if r.get("endpoint") != endpoint]
        if len(keep) != len(rows):
            _save_subs(keep)
    return len(rows) - len(keep)


def _sender(sub: dict, payload: str) -> None:
    from pywebpush import Vapid, webpush
    raw = _kr_get(VAPID_KEY)
    if not raw:
        raise RuntimeError("VAPID anahtarı yok")
    webpush(subscription_info=sub, data=payload, vapid_private_key=Vapid.from_string(raw),
            vapid_claims={"sub": os.environ.get("SB_VAPID_SUB") or "mailto:second-brain@localhost.invalid"}, ttl=3600, timeout=10)


def push_send(title: str, body: str = "", link: str = "") -> dict:
    """Tüm abonelere gönderir. pywebpush yoksa {available: False}. Ölü abonelik (404/410) silinir."""
    if not push_available():
        return {"available": False, "sent": 0}
    payload = json.dumps({"title": str(title)[:100], "body": redact(str(body))[:200], "link": str(link)[:300]}, ensure_ascii=False)
    sent = 0
    for s in subscriptions():
        try:
            _sender(s, payload)
            sent += 1
        except Exception as e:                                   # noqa: BLE001
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in (404, 410):
                unsubscribe(s.get("endpoint", ""))
    return {"available": True, "sent": sent}


def on_notify(row: dict) -> None:
    """`convstore.notify` kancası (Opus bağlar). Arka planda, hata yutar; abonelik yoksa hiçbir şey yapmaz."""
    try:
        if not subscriptions() or not push_available():
            return
        threading.Thread(target=push_send, args=(row.get("title", ""), row.get("body", ""), row.get("link", "")), daemon=True).start()
    except Exception:                                            # noqa: BLE001
        pass


def push_status() -> dict:
    avail = push_available()
    pub = ""
    if avail:
        try:
            pub = vapid_public_key()
        except Exception:                                        # noqa: BLE001 — keyring yoksa bildirim kapalı
            avail = False
    return {"available": avail, "public_key": pub, "subscriptions": len(subscriptions())}


# ---------------- dış erişim tüneli (kendiliğinden başlamaz)
def _tunnel_cfg() -> dict:
    try:
        d = json.loads((config.DATA / "tunnel.json").read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def tunnel_status() -> dict:
    """tunnel.json: {hostname, tunnel, access_policy: true, port}. `access_policy` Access'te e-posta politikası kurulduktan sonra elle onaylanır."""
    cfg = _tunnel_cfg()
    have = bool(shutil.which("cloudflared"))
    missing = []
    if not have:
        missing.append("cloudflared kurulu değil")
    if not cfg.get("hostname"):
        missing.append("hostname (tunnel.json) yok")
    if cfg.get("access_policy") is not True:
        missing.append("Cloudflare Access (e-posta doğrulaması) politikası onaylanmadı")
    return {"ready": not missing, "missing": missing, "hostname": cfg.get("hostname", ""),
            "access_policy": cfg.get("access_policy") is True, "cloudflared": have}


def tunnel_plan() -> dict:
    """Komutları üretir, çalıştırmaz. Hazır değilse `commands` boş; yalnız kurulum adımları."""
    st, cfg = tunnel_status(), _tunnel_cfg()
    name, host = cfg.get("tunnel") or "second-brain", cfg.get("hostname") or "<alt.alan.adin.com>"
    try:
        port = int(cfg.get("port") or 8765)
    except (TypeError, ValueError):
        port = 8765
    steps = ["cloudflared tunnel login", f"cloudflared tunnel create {name}", f"cloudflared tunnel route dns {name} {host}",
             "Zero Trust > Access > Applications: self-hosted uygulama ekle, politika = yalnız kendi e-postan (One-time PIN)",
             "Politikayı kurunca tunnel.json içine \"access_policy\": true yaz"]
    run = [f"cloudflared tunnel run --url http://127.0.0.1:{port} {name}"] if st["ready"] else []
    return {"ready": st["ready"], "missing": st["missing"], "steps": steps, "commands": run,
            "note": "Access politikası olmadan tünel açılmaz; bu işlev komut çalıştırmaz."}
