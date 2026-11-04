"""Sihirbaz yardımcıları: hesaplar (Google/IMAP), sırlar, modeller (ollama/ses), telefon (Tailscale).

Gerçek komut/şifre kasası yalnız `engine._run_capture/_run_stream/_keyring` kapılarından geçer (testte taklit/engelli).
Sırlar yalnız keyring'e yazılır; accounts.yaml, durum dosyası ve günlüğe girmez.
"""
from __future__ import annotations
import os

import ipaddress
import json
import re
import shutil
import urllib.request
from pathlib import Path

try:
    from . import engine as E
except ImportError:                                           # pragma: no cover
    import engine as E  # type: ignore

GOOGLE_SCOPES = ("gmail", "calendar", "contacts", "drive")
ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,29}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HOST_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
IMAP_PRESETS = {
    "gmail": {"host": "imap.gmail.com", "port": 993, "hint": "Gmail'de IMAP açık ve uygulama şifresi gerekir (2 adımlı doğrulama)."},
    "outlook": {"host": "outlook.office365.com", "port": 993, "hint": "Kişisel Outlook: IMAP açık + uygulama şifresi."},
    "icloud": {"host": "imap.mail.me.com", "port": 993, "hint": "iCloud: appleid.apple.com'dan uygulamaya özel şifre."},
    "yandex": {"host": "imap.yandex.com", "port": 993, "hint": "Yandex: ayarlarda IMAP'i aç, uygulama şifresi üret."},
}
SB_PRESETS = {"outlook", "icloud"}                             # sb.imap.resolve yalnız bunları tanır
SECRET_NAME_RE = re.compile(r"^(api-[a-z0-9_-]{1,40}|imap-[a-z0-9_-]{1,30}|mcp-[a-z0-9_-]{1,80}|svc-[a-z0-9_-]{1,60}|telegram-bot)$")
KNOWN_SECRETS = ["svc-school-password", "api-openai", "api-anthropic", "api-gemini", "api-openrouter", "api-groq", "api-deepseek", "api-mistral", "telegram-bot",
                 "svc-spotify-client-id", "svc-spotify-client-secret", "svc-github-pat"]
KEY_TESTS = {
    "openai": ("https://api.openai.com/v1/models", "bearer"), "openrouter": ("https://openrouter.ai/api/v1/models", "bearer"),
    "groq": ("https://api.groq.com/openai/v1/models", "bearer"), "deepseek": ("https://api.deepseek.com/v1/models", "bearer"),
    "mistral": ("https://api.mistral.ai/v1/models", "bearer"),
    "anthropic": ("https://api.anthropic.com/v1/models", "anthropic"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/models", "gemini"),
}
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,80}$")

def _uv() -> str:
    """PATH'te uv yoksa paketli Setup'ın gömülü/kalıcı uv'si (SB_UV) — engine.uv_bin ile aynı kural."""
    p = os.environ.get("SB_UV")
    return p if p and Path(p).is_file() and not shutil.which("uv") else "uv"



# ------------------------------------------------------------------ ortak
def _config(eng) -> Path:
    c = eng.ensure_vault() / "_system" / "config"            # kasa seçilmediyse varsayılan konum
    c.mkdir(parents=True, exist_ok=True)
    return c


def _read_accounts(eng) -> dict:
    p = _config(eng) / "accounts.yaml"
    d = (E._yaml().safe_load(p.read_text(encoding="utf-8")) if p.exists() else None) or {}
    d["google"] = d.get("google") or {}
    d["imap"] = d.get("imap") or {}
    return d


def _write_accounts(eng, acc: dict) -> None:
    p = _config(eng) / "accounts.yaml"
    if p.exists():
        shutil.copy2(p, p.with_suffix(".yaml.bak"))
    tmp = p.with_suffix(".yaml.tmp")
    tmp.write_text("# Hesaplar (gizli bilgi YOK; şifreler işletim sistemi şifre kasasında)\n"
                   + E._yaml().safe_dump(acc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    tmp.replace(p)


def _alias(v) -> str:
    a = str(v or "").strip().lower()
    if not ALIAS_RE.match(a):
        raise ValueError("takma ad: 1-30 karakter, küçük harf/rakam/-/_")
    return a


def _kr():
    kr = E._keyring()
    if not kr:
        raise ValueError("şifre kasası (keyring) yok")
    return kr


def _remember(eng, *vals) -> None:
    eng._secrets += [str(v) for v in vals if v]


# ------------------------------------------------------------------ hesaplar
def add_google(eng, b: dict) -> dict:
    alias = _alias(b.get("alias"))
    scopes = b.get("scopes")
    if not isinstance(scopes, list) or not scopes or any(s not in GOOGLE_SCOPES for s in scopes):
        raise ValueError(f"scopes: {', '.join(GOOGLE_SCOPES)} içinden en az biri")
    email = str(b.get("email") or (eng.selection.get("fields") or {}).get("gmail") or "").strip()
    if not EMAIL_RE.match(email):
        raise ValueError("Google e-posta adresi gerekli (email alanı ya da kimlik adımındaki Gmail)")
    secrets_dir = eng.data / "secrets"
    cs = secrets_dir / "client_secret.json"
    if b.get("client_secret") and isinstance(b["client_secret"], str):
        src = Path(str(b["client_secret"])).expanduser()
        if src.is_file() and not cs.exists():
            try:
                ok = bool({"installed", "web"} & set(json.loads(src.read_text(encoding="utf-8"))))
            except Exception:                                 # noqa: BLE001
                ok = False
            if not ok:
                return {"ok": False, "message": "Dosya geçerli bir OAuth istemcisi (client_secret.json) değil"}
            secrets_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, cs)
    if not cs.is_file():
        return {"ok": False, "message": "client_secret.json yok (Google Cloud kurulum rehberi)"}
    acc = _read_accounts(eng)
    prev = acc["google"].get(alias)
    acc["google"][alias] = {"email": email, "scopes": list(scopes), "source": f"gmail-{alias}"}
    _write_accounts(eng, acc)
    if getattr(eng, "sandbox", None):                         # deneme kipi: OAuth akışı başlatılmaz
        _kr().set_password(E.KEYRING_SERVICE, f"google:{alias}", "deneme-jetonu")
        eng.log(f"[deneme] atlandı: Google OAuth ({alias}, {email})")
        return {"ok": True, "email": email, "sandbox": True, "message": "deneme: bağlandı (Google girişi başlatılmadı)"}
    rc, out = E._run_capture(eng.sb_cmd("login", alias), 300)                 # tarayıcı açılır, kullanıcı izin verir
    token = None
    try:
        token = _kr().get_password(E.KEYRING_SERVICE, f"google:{alias}")
    except Exception:                                         # noqa: BLE001
        pass
    if rc != 0 or not token:
        acc = _read_accounts(eng)
        if prev is None:
            acc["google"].pop(alias, None)
        else:
            acc["google"][alias] = prev
        _write_accounts(eng, acc)
        last = out.strip().splitlines()[-1] if out.strip() else f"kod {rc}"
        return {"ok": False, "message": "Google girişi tamamlanmadı: " + E.redact(last, eng._secrets)[:300]}
    return {"ok": True, "email": email, "message": "Google hesabı bağlandı"}


def add_imap(eng, b: dict) -> dict:
    alias = _alias(b.get("alias"))
    preset = str(b.get("preset") or "custom")
    if preset != "custom" and preset not in IMAP_PRESETS:
        raise ValueError(f"preset: {', '.join(IMAP_PRESETS)} ya da custom")
    p = IMAP_PRESETS.get(preset, {})
    host = str(b.get("host") or p.get("host") or "").strip()
    try:
        port = int(b.get("port") or p.get("port") or 993)
    except (TypeError, ValueError):
        raise ValueError("port sayı olmalı")
    user, pw = str(b.get("user") or "").strip(), str(b.get("password") or "")
    _remember(eng, pw)
    if not HOST_RE.match(host) or not 1 <= port <= 65535:
        raise ValueError("sunucu ya da port geçersiz")
    if not user or not pw:
        raise ValueError("kullanıcı ve şifre gerekli")
    ok, msg = E._imap_login(host, user, pw, port)
    if not ok:
        return {"ok": False, "message": E.redact(msg, eng._secrets) + (" · " + p["hint"] if p.get("hint") else "")}
    _kr().set_password(E.KEYRING_SERVICE, f"imap-{alias}", pw)
    acc = _read_accounts(eng)
    ent = {"email": user if EMAIL_RE.match(user) else str(b.get("email") or user), "host": host, "port": port, "source": f"imap-{alias}"}
    if preset in SB_PRESETS:
        ent["preset"] = preset
    acc["imap"][alias] = ent
    _write_accounts(eng, acc)
    return {"ok": True, "message": msg}


def _has(name: str) -> bool:
    kr = E._keyring()
    try:
        return bool(kr and kr.get_password(E.KEYRING_SERVICE, name))
    except Exception:                                         # noqa: BLE001
        return False


def client_secret_path(eng) -> Path:
    return eng.data / "secrets" / "client_secret.json"


def save_client_secret(eng, raw: bytes) -> dict:
    """Google Cloud'dan inen client_secret.json: geçerli OAuth istemcisi (installed/web) ise DATA/secrets/ altına yazılır."""
    try:
        d = json.loads(raw.decode("utf-8-sig"))
    except Exception:                                         # noqa: BLE001
        raise ValueError("Dosya geçerli bir JSON değil")
    if not isinstance(d, dict) or not ({"installed", "web"} & set(d)):
        raise ValueError("Bu dosya bir OAuth istemcisi (client_secret.json) değil: 'installed' ya da 'web' anahtarı yok")
    p = client_secret_path(eng)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_bytes(raw)
    tmp.replace(p)
    return {"ok": True, "uploaded": True, "message": "client_secret.json yüklendi"}


def set_school(eng, b: dict) -> dict:
    """Okul (ÖBS/LMS) girişi: adres + kullanıcı adı accounts.yaml `school`a, şifre `svc-school-password` olarak keyring'e (POST /api/secret).
    Her ikisi de boşsa kayıt kaldırılır."""
    url, user = str(b.get("url") or "").strip(), str(b.get("user") or "").strip()
    if url and not re.match(r"^(https?://)?[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?(:\d{1,5})?(/\S*)?$", url):
        raise ValueError("okul adresi geçersiz (örn. obs.okul.edu.tr)")
    if len(user) > 120 or "\n" in user:
        raise ValueError("kullanıcı adı geçersiz")
    acc = _read_accounts(eng)
    if url or user:
        acc["school"] = {"url": url, "user": user}
    else:
        acc.pop("school", None)
    _write_accounts(eng, acc)
    return {"ok": True, "message": "Okul bilgileri kaydedildi (şifre ayrı, şifre kasasına)" if (url or user) else "Okul bilgileri kaldırıldı",
            "has_password": _has("svc-school-password")}


def list_accounts(eng) -> dict:
    acc = _read_accounts(eng)
    sch = acc.get("school") if isinstance(acc.get("school"), dict) else None
    return {"client_secret": client_secret_path(eng).is_file(),
            "school": ({"url": sch.get("url", ""), "user": sch.get("user", ""), "has_password": _has("svc-school-password")} if sch else None),
            **{"google": [{"alias": a, "email": v.get("email"), "scopes": v.get("scopes") or [], "authorized": _has(f"google:{a}")}
                       for a, v in acc["google"].items()],
            "imap": [{"alias": a, "email": v.get("email"), "host": v.get("host"), "port": v.get("port", 993), "has_password": _has(f"imap-{a}")}
                     for a, v in acc["imap"].items()]}}


def remove_account(eng, b: dict) -> dict:
    alias = _alias(b.get("alias"))
    acc = _read_accounts(eng)
    removed = []
    kr = E._keyring()
    for kind, key in (("google", f"google:{alias}"), ("imap", f"imap-{alias}")):
        if alias in acc[kind]:
            acc[kind].pop(alias)
            removed.append(kind)
            try:
                if kr:
                    kr.delete_password(E.KEYRING_SERVICE, key)
            except Exception:                                 # noqa: BLE001
                pass
    if not removed:
        raise ValueError(f"hesap yok: {alias}")
    _write_accounts(eng, acc)                                 # önceki sürüm accounts.yaml.bak; arşivlenmiş mail silinmez
    return {"ok": True, "removed": removed}


# ------------------------------------------------------------------ sırlar
def test_key(provider: str, key: str) -> dict:
    if provider not in KEY_TESTS:
        return {"tested": False}
    url, style = KEY_TESTS[provider]
    hdr = {"bearer": {"Authorization": f"Bearer {key}"}, "anthropic": {"x-api-key": key, "anthropic-version": "2023-06-01"},
           "gemini": {"x-goog-api-key": key}}[style]
    code, _ = E._http(url, hdr, timeout=6)
    return {"tested": True, "ok": code == 200, "message": "Anahtar geçerli" if code == 200 else f"Reddedildi ya da ulaşılamadı (kod {code})"}


def set_secret(eng, b: dict) -> dict:
    key, val = str(b.get("key") or ""), b.get("value")
    if not SECRET_NAME_RE.match(key):
        raise ValueError("geçersiz anahtar adı (api-*, imap-*, mcp-*, telegram-bot)")
    if not isinstance(val, str) or not val.strip():
        raise ValueError("değer boş")
    val = val.strip()
    _remember(eng, val)
    _kr().set_password(E.KEYRING_SERVICE, key, val)
    out = {"ok": True, "key": key, "set": True}
    if b.get("test") and key.startswith("api-"):
        out.update(test_key(key[4:], val))
    return out


def list_secrets(eng) -> dict:
    names = list(KNOWN_SECRETS)
    try:
        if eng.vault:
            names += [f"imap-{a}" for a in _read_accounts(eng)["imap"]]
    except Exception:                                         # noqa: BLE001
        pass
    return {"secrets": [{"key": n, "set": _has(n)} for n in dict.fromkeys(names)], "keyring": bool(E._keyring())}


# ------------------------------------------------------------------ modeller
def _parse_ollama_list(out: str) -> list[dict]:
    rows = []
    for ln in out.splitlines()[1:]:
        m = re.match(r"^(\S+)\s+\S+\s+([\d.]+)\s*(GB|MB|KB)", ln)
        if m:
            sz = float(m.group(2)) / {"GB": 1, "MB": 1024, "KB": 1024 ** 2}[m.group(3)]
            rows.append({"name": m.group(1), "size_gb": round(sz, 2)})
    return rows


def ollama_info() -> dict:
    rc, out = E._run_capture(["ollama", "--version"], 8)
    if rc != 0:
        return {"installed": False, "running": False, "models": [], "version": ""}
    ver = re.search(r"\d+\.\d+\.\d+", out)
    rc2, lst = E._run_capture(["ollama", "list"], 10)
    return {"installed": True, "running": rc2 == 0, "models": _parse_ollama_list(lst) if rc2 == 0 else [],
            "version": ver.group(0) if ver else ""}


def _install_cmds() -> list[list[str]]:
    if E.WIN:
        ps = ("$f=Join-Path $env:TEMP 'OllamaSetup.exe'; Invoke-WebRequest -UseBasicParsing https://ollama.com/download/OllamaSetup.exe "
              "-OutFile $f; Start-Process -FilePath $f -ArgumentList '/SILENT' -Wait")
        return [["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps]]
    if E.MAC:
        return [["sh", "-c", "curl -fsSL https://ollama.com/download/Ollama-darwin.zip -o /tmp/Ollama.zip && "
                             "unzip -qo /tmp/Ollama.zip -d /Applications && open -a Ollama"]]
    return [["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"]]


def ollama_install(eng, wait: bool = False) -> bool:
    def work(pct):
        if getattr(eng, "sandbox", None):
            eng.log("[deneme] atlandı: Ollama kurulumu")
            return
        for cmd in _install_cmds():
            if E._run_stream(cmd, eng.log):
                raise RuntimeError("Ollama kurulumu başarısız (ollama.com'dan elle kurabilirsin)")
        if not ollama_info()["installed"]:
            raise RuntimeError("Kurulum bitti ama ollama bulunamadı; uygulamayı yeniden başlat")
    return eng.run_job("ollama_install", "Ollama kurulumu", work, wait)


def pull_model(eng, name: str, wait: bool = False) -> bool:
    if not MODEL_RE.match(name or ""):
        raise ValueError("geçersiz model adı")

    def work(pct):
        def log(line):
            eng.log(line)
            m = re.findall(r"(\d{1,3})%", line)
            if m:
                pct(int(m[-1]))
        if E._run_stream(["ollama", "pull", name], log):
            raise RuntimeError(f"{name} indirilemedi (Ollama çalışıyor mu?)")
    return eng.run_job("pull:" + name, f"Model indiriliyor: {name}", work, wait)


def voice_setup(eng, gpu: bool, wait: bool = False) -> bool:
    def work(pct):
        cmd = [_uv(), "sync", "--directory", str(eng.code_root()), "--extra", "voice"] + (["--extra", "voice-gpu"] if gpu else [])
        if E._run_stream(cmd, eng.log):
            raise RuntimeError("ses kütüphaneleri kurulamadı")
        pct(70)
        E._run_stream(eng.sb_cmd("voice", "--setup"), eng.log)
    return eng.run_job("voice", "Ses (faster-whisper) kurulumu", work, wait)


# ------------------------------------------------------------------ telefon
def _post_json(url: str, obj: dict, timeout: int = 4) -> dict:
    req = urllib.request.Request(url, data=json.dumps(obj).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "X-SB": "1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read(100000))


def _tailscale_ip() -> tuple[bool, str]:
    cands = ["tailscale"] + ([r"C:\Program Files\Tailscale\tailscale.exe"] if E.WIN else [])
    for exe in cands:
        rc, out = E._run_capture([exe, "ip", "-4"], 8)
        if rc == 127:
            continue
        ip = (out.split() or [""])[0] if rc == 0 else ""
        try:
            if ip and ipaddress.ip_address(ip) in ipaddress.ip_network("100.64.0.0/10"):
                return True, ip
        except ValueError:
            pass
        return True, ""
    return False, ""


def phone_info(port: int = 8765) -> dict:
    installed, ip = _tailscale_ip()
    out = {"installed": installed, "connected": bool(ip), "ip": ip, "address": f"http://{ip}:{port}" if ip else "",
           "pairing_code": "", "devices": 0, "assistant_running": False}
    try:
        info = _post_json(f"http://127.0.0.1:{port}/api/remote", {})
        out.update(assistant_running=True, pairing_code=str(info.get("pin") or ""), devices=int(info.get("devices") or 0))
    except Exception:                                         # noqa: BLE001 — asistan sunucusu kapalı
        pass
    return out
