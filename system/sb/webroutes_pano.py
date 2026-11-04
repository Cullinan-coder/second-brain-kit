"""Pano web uçları (/api/v2/pano/*). Hepsi yalnız yerel (telefondan çağrılamaz); veri buluta/modele gitmez."""
from __future__ import annotations

import functools

from . import pano
from .webroutes import ApiError, Ctx, Raw
from .webroutes import route as _route

OFF_MSG = "Kopya geçmişi modülü kapalı (Uygulama ayarları → Özellikler ya da `sb features --on pano`)"


def route(method: str, path: str, **kw):
    """Özellik anahtarı kapalıyken uç hiçbir şey yapmaz (403); yalnız durum ucu `module:false` döner."""
    def deco(fn):
        @functools.wraps(fn)
        def guarded(ctx: Ctx):
            if not pano.module_on():
                if path.endswith("/status"):
                    return {"module": False, "enabled": False, "running": False}
                raise ApiError(403, OFF_MSG)
            return fn(ctx)
        _route(method, path, **kw)(guarded)
        return fn
    return deco


def _id(ctx: Ctx) -> int:
    try:
        return int(ctx.arg("id"))
    except (TypeError, ValueError):
        raise ApiError(400, "id gerekli") from None


def _flag(v):
    if v in (None, "", "any"):
        return None
    return str(v).lower() in ("1", "true", "yes", "evet")


def _int(v, d: int) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


def _kind(ctx: Ctx) -> str:
    k = str(ctx.arg("kind", "") or "")
    if k and k not in pano.KINDS:
        raise ApiError(400, "kind image|text|link olmalı")
    return k


def _wrap(fn):
    try:
        return fn()
    except KeyError as e:
        raise ApiError(404, str(e.args[0]) if e.args else "kayıt yok") from None
    except ValueError as e:
        raise ApiError(400, str(e)) from None


@route("GET", "/api/v2/pano/status", local_only=True)
def status(ctx: Ctx) -> dict:
    pano.ensure_running()                                   # arayüz açıldıysa ve izin varsa izleyici başlar
    pano.purge()
    return pano.status()


@route("GET", "/api/v2/pano/list", local_only=True)
def list_(ctx: Ctx) -> dict:
    res = pano.list_items(_kind(ctx), _int(ctx.arg("page"), 1), _int(ctx.arg("per"), 30), _flag(ctx.arg("pinned")))
    if ctx.arg("folder") or ctx.arg("tag"):
        k = _kind(ctx)
        res = pano.search("", [k] if k else None, _flag(ctx.arg("pinned")), str(ctx.arg("tag", "")), str(ctx.arg("folder", "")),
                          limit=_int(ctx.arg("per"), 30), offset=(max(1, _int(ctx.arg("page"), 1)) - 1) * _int(ctx.arg("per"), 30))
    res["folders"] = pano.folders()
    return res


@route("GET", "/api/v2/pano/trash", local_only=True)
def trash(ctx: Ctx) -> dict:
    return pano.search("", None, trash=True)


@route("GET", "/api/v2/pano/search", local_only=True)
def search(ctx: Ctx) -> dict:
    k = _kind(ctx)
    return pano.search(str(ctx.arg("q", "")), [k] if k else None, _flag(ctx.arg("pinned")), str(ctx.arg("tag", "")),
                       str(ctx.arg("folder", "")), limit=_int(ctx.arg("per"), 100))


@route("GET", "/api/v2/pano/item", local_only=True)
def item(ctx: Ctx) -> dict:
    return _wrap(lambda: pano.get(_id(ctx)))


@route("GET", "/api/v2/pano/image", local_only=True)
def image(ctx: Ctx) -> Raw:
    i = _id(ctx)
    return _wrap(lambda: Raw(pano.image_bytes(i, thumb=bool(_flag(ctx.arg("thumb")))), "image/png"))


@route("POST", "/api/v2/pano/pin", local_only=True)
def pin(ctx: Ctx) -> dict:
    return _wrap(lambda: pano.set_pinned(_id(ctx), _flag(ctx.arg("value"))))


@route("POST", "/api/v2/pano/tag", local_only=True)
def tag(ctx: Ctx) -> dict:
    """Etiketleri (tags: liste) ve/veya adı (name) ayarlar."""
    tags = ctx.data.get("tags")
    if tags is not None and not isinstance(tags, list):
        raise ApiError(400, "tags liste olmalı")
    return _wrap(lambda: pano.set_meta(_id(ctx), tags=tags, name=ctx.data.get("name")))


@route("POST", "/api/v2/pano/folder", local_only=True)
def folder(ctx: Ctx) -> dict:
    return _wrap(lambda: pano.set_meta(_id(ctx), folder=str(ctx.data.get("folder", ""))))


@route("POST", "/api/v2/pano/remove", local_only=True)
def remove(ctx: Ctx) -> dict:
    """Çöp kutusuna taşır (geri alınabilir). Kalıcı silme bu uçta yoktur."""
    return _wrap(lambda: pano.remove(_id(ctx)))


@route("POST", "/api/v2/pano/restore", local_only=True)
def restore(ctx: Ctx) -> dict:
    """id verilirse onu, verilmezse son kaldırılanı geri getirir."""
    if ctx.arg("id") in (None, ""):
        it = pano.undo_remove()
        if not it:
            raise ApiError(404, "geri alınacak kayıt yok")
        return it
    return _wrap(lambda: pano.restore(_id(ctx)))


@route("POST", "/api/v2/pano/copy", local_only=True)
def copy(ctx: Ctx) -> dict:
    i = _id(ctx)
    try:
        return _wrap(lambda: pano.copy_back(i))
    except RuntimeError as e:
        raise ApiError(409, str(e)) from None


@route("GET", "/api/v2/pano/settings", local_only=True)
def settings_get(ctx: Ctx) -> dict:
    return {"settings": pano.settings(), "retention_choices": list(pano.RETENTION_CHOICES)}


@route("POST", "/api/v2/pano/settings", local_only=True)
def settings_set(ctx: Ctx) -> dict:
    patch = {k: v for k, v in ctx.data.items() if k != "sid"}
    s = _wrap(lambda: pano.set_settings(patch))
    pano.ensure_running()
    return {"settings": s, "status": pano.status()}
