"""Asistan sohbet modu uçları: bulut ↔ yerel model (sb/chat_mode.py)."""
from __future__ import annotations

from . import chat_mode
from .webroutes import ApiError, Ctx, route


@route("GET", "/api/v2/chat/mode")
def mode_get(ctx: Ctx) -> dict:
    return chat_mode.status()


@route("POST", "/api/v2/chat/mode")          # telefondan da değişir; eşleme/Origin/jeton denetimi sunucuda (chat.py) yapılır
def mode_set(ctx: Ctx) -> dict:
    try:
        chat_mode.set_mode(str(ctx.arg("mode") or ""))
    except ValueError as e:
        raise ApiError(400, str(e))
    return chat_mode.status()
