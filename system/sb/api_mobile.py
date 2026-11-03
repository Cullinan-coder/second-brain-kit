"""Paket M uçları: paylaş, push aboneliği, tünel durumu."""
from __future__ import annotations

from . import mobile
from .webroutes import ApiError, Ctx, route


@route("POST", "/api/v2/share", upload=True)
def share(ctx: Ctx) -> dict:
    try:
        fields, files = mobile.parse_form(ctx.raw, ctx.ctype)
    except Exception:                                            # noqa: BLE001
        raise ApiError(400, "geçersiz paylaşım gövdesi")
    out = mobile.share(fields.get("title", ""), fields.get("text", ""), fields.get("url", ""), files)
    if not out.get("ok"):
        raise ApiError(400, out.get("error", "paylaşılamadı"))
    return out


@route("GET", "/api/v2/push/status")
def push_status(ctx: Ctx) -> dict:
    return mobile.push_status()


@route("POST", "/api/v2/push/subscribe")
def push_subscribe(ctx: Ctx) -> dict:
    if not mobile.push_available():
        return {"available": False, "ok": False}
    if not mobile.subscribe(ctx.arg("subscription")):
        raise ApiError(400, "geçersiz abonelik")
    return {"available": True, "ok": True, "subscriptions": len(mobile.subscriptions())}


@route("POST", "/api/v2/push/unsubscribe")
def push_unsubscribe(ctx: Ctx) -> dict:
    return {"removed": mobile.unsubscribe(str(ctx.arg("endpoint") or ""))}


@route("GET", "/api/v2/tunnel", local_only=True)
def tunnel(ctx: Ctx) -> dict:
    return {"status": mobile.tunnel_status(), "plan": mobile.tunnel_plan()}
