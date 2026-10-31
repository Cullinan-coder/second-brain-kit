"""Asistan web API kayıt defteri (Faz 2). Her modül kendi uçlarını `@route` ile kaydeder; chat.py yalnız dağıtır.

Sözleşme:
- Uç işlevi `fn(ctx: Ctx) -> dict | list | Raw` döner. dict/list JSON olarak gönderilir; `Raw` dosya/ses gibi ham gövdedir.
- Hata için `ApiError(kod, mesaj)` fırlat; diğer istisnalar 500 + kısa mesaj olur (sunucu düşmez).
- `local_only=True`: telefondan (Tailscale) çağrılamaz. `model=True`: model kilidi altında çalışır (aynı anda tek model çağrısı).
- `upload=True`: gövde JSON değil ham bayt (ses, görsel, dosya; en çok MAX_UPLOAD), `ctx.raw` + `ctx.ctype`; ek alanlar sorgu dizisinde.
- Yollar `/api/v2/` ile başlar. GET uçları yan etkisiz olmalı (yalnız okuma).
"""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable

MAX_UPLOAD = 30 * 1024 * 1024
MODULES = ("api_conv", "api_views", "api_memory", "voice", "vision")   # yoksa ya da hata verirse atlanır


class ApiError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


@dataclass
class Raw:
    body: bytes
    ctype: str = "application/octet-stream"
    filename: str = ""


@dataclass
class Ctx:
    method: str
    path: str
    data: dict = field(default_factory=dict)        # JSON gövdesi (POST) — GET'te boş
    query: dict = field(default_factory=dict)       # ?a=1 → {"a": "1"} (tek değer)
    raw: bytes = b""
    ctype: str = ""
    sid: str = ""                                   # istemcinin sohbet kimliği (gövde 'sid' ya da ?sid=)
    remote: bool = False                            # telefondan mı
    session: Any = None                             # chat.Session
    respond: Callable[[str], dict] | None = None    # respond(text) → {reply, trace, proposals}; model kilidi çağırana ait
    calendar: Any = None

    def arg(self, name: str, default: Any = None) -> Any:
        return self.data.get(name, self.query.get(name, default))


@dataclass
class Route:
    method: str
    path: str
    fn: Callable[[Ctx], Any]
    local_only: bool = False
    model: bool = False
    upload: bool = False


ROUTES: dict[tuple[str, str], Route] = {}
LOAD_ERRORS: dict[str, str] = {}


def route(method: str, path: str, *, local_only: bool = False, model: bool = False, upload: bool = False):
    assert path.startswith("/api/v2/"), path

    def deco(fn):
        ROUTES[(method.upper(), path)] = Route(method.upper(), path, fn, local_only, model, upload)
        return fn
    return deco


_loaded = False


def load() -> dict[tuple[str, str], Route]:
    """Uç modüllerini bir kez içe aktarır; birinin hatası diğerlerini engellemez (hata LOAD_ERRORS'ta)."""
    global _loaded
    if not _loaded:
        _loaded = True
        for m in MODULES:
            try:
                importlib.import_module(f"sb.{m}")
            except ModuleNotFoundError as e:
                if e.name != f"sb.{m}":
                    LOAD_ERRORS[m] = f"{type(e).__name__}: {e}"
            except Exception as e:                               # noqa: BLE001 — bir modül diğerlerini düşürmesin
                LOAD_ERRORS[m] = f"{type(e).__name__}: {e}"
    return ROUTES


def find(method: str, path: str) -> Route | None:
    return load().get((method.upper(), path.split("?")[0]))


def call(r: Route, ctx: Ctx) -> tuple[int, bytes, str, str]:
    """(kod, gövde, içerik türü, dosya adı)."""
    try:
        out = r.fn(ctx)
    except ApiError as e:
        return e.code, json.dumps({"error": e.message}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", ""
    except Exception as e:                                       # noqa: BLE001
        msg = f"{type(e).__name__}: {str(e)[:200]}"
        return 500, json.dumps({"error": msg}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", ""
    if isinstance(out, Raw):
        return 200, out.body, out.ctype, out.filename
    return 200, json.dumps(out, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8", ""


@route("GET", "/api/v2/routes")
def _routes(ctx: Ctx) -> dict:
    """Arayüzün hangi özelliklerin açık olduğunu öğrenmesi için (kapalı modülün düğmesi gizlenir)."""
    return {"routes": sorted(f"{m} {p}" for m, p in load()), "errors": LOAD_ERRORS}
