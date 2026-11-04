"""“Çalışmaya başla” ve uygulama ayarları uçları (Paket 4)."""
from __future__ import annotations

import sys
import threading

from . import startup
from .config import SYSTEM
from .webroutes import Ctx, route

_setup_srv = None
_setup_lock = threading.Lock()


def _make_setup_server():
    if str(SYSTEM) not in sys.path:
        sys.path.insert(0, str(SYSTEM))
    from setup import server                                     # setup/server.py
    return server.make_server().start()


def settings_url() -> str:
    """Setup sunucusunu (uygulama ömrü boyunca tek örnek) jetonla başlatır; ayarlar kipi adresini döndürür."""
    global _setup_srv
    with _setup_lock:
        if _setup_srv is None:
            _setup_srv = _make_setup_server()
        return _setup_srv.url + "&mode=settings"


@route("POST", "/api/v2/startup/run", local_only=True)
def run(ctx: Ctx) -> dict:
    # ctx.arg("auto_update") yok sayılır: güncelleme yalnız kullanıcı ayarıyla (config/uygulama.yaml) uygulanır.
    started = startup.start()
    return {"started": started, "status": startup.status()}


@route("GET", "/api/v2/startup/status", local_only=True)
def status(ctx: Ctx) -> dict:
    return startup.status()


@route("GET", "/api/v2/startup/settings-url", local_only=True, sensitive=True)    # kurulum jetonunu verir: jetonsuz GET'e verilmez (D-04)
def settings(ctx: Ctx) -> dict:
    return {"url": settings_url()}
