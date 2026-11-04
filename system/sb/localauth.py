"""Yerel asistan sunucusu (127.0.0.1:8765) için oturum jetonu (denetim D-04, D-19).

Sorun: yerel istekler kimliksizdi; tarayıcıdaki herhangi bir sayfa ya da aynı makinedeki bir süreç `X-SB: 1` başlığını kendisi koyup
durum değiştirebiliyordu. Çözüm: rastgele bir jeton (`~/.secondbrain/chat.token`, yalnız kullanıcıya açık) üretilir;
- arayüz (index.html, bubble.html, klasik sayfa) jetonu sunucudan YÜKLENİRKEN gömülü alır ve `sbtoken.js` bütün aynı-köken
  `fetch` isteklerine `X-SB-Token` başlığını ekler,
- masaüstü uygulaması, tepsi, Obsidian eklentisi ve komut satırı araçları jetonu aynı dosyadan okur,
- tarayıcı eklentisi jeton yerine kullanıcının izin verdiği `chrome-extension://<kimlik>` Origin'iyle tanınır (yalnız paylaş ucu).
Telefon (uzak) yolu eşleme çerezini kullanmaya devam eder; jeton gerekmez.
"""
from __future__ import annotations

import hmac
import os
import secrets
import sys
from pathlib import Path

HEADER = "X-SB-Token"
FILE_NAME = "chat.token"


def token_path() -> Path:
    from . import config
    return Path(config.DATA) / FILE_NAME


def _restrict(path: Path) -> None:
    """Dosyayı yalnız kullanıcıya aç (Windows: ACL mirası kapatılır; diğerleri: 0600). En iyi çaba."""
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    if sys.platform == "win32" and "PYTEST_CURRENT_TEST" not in os.environ and not os.environ.get("SB_NO_ACL"):
        try:
            import subprocess
            user = os.environ.get("USERNAME", "")
            if user:
                subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:F"], capture_output=True, timeout=10,
                               creationflags=0x08000000)
        except Exception:                                      # noqa: BLE001 — ACL ayarlanamazsa jeton yine de çalışır
            pass


def token() -> str:
    """Kalıcı rastgele jeton (ilk çağrıda üretilir). Dosya bozuk/kısaysa yenilenir."""
    p = token_path()
    try:
        t = p.read_text(encoding="utf-8").strip()
        if len(t) >= 32:
            return t
    except OSError:
        pass
    t = secrets.token_urlsafe(32)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t, encoding="utf-8")
    _restrict(p)
    return t


def valid(candidate: str | None) -> bool:
    if not candidate:
        return False
    return hmac.compare_digest(str(candidate).strip().encode("utf-8", "replace"), token().encode("utf-8"))


def headers() -> dict[str, str]:
    """Python istemcileri (masaüstü uygulaması, tepsi, e2e) için başlıklar."""
    return {"X-SB": "1", HEADER: token()}
