"""Bugün ve kaynak tazeliği uçları (salt okunur; telefon da görebilir, hassas alanlar kırpılır).

GET /api/v2/today      → `sb/today.py:build` (teslimler, bekleyen onaylar, önemli okunmamış mailler, eskiyen kaynaklar, son başarısız adım)
GET /api/v2/freshness  → `sb/freshness.py:status` (etkin kaynakların tazeliği)
Telefon (ctx.remote): mail konusu/gönderen, onay ayrıntısı, dosya adı ve adım çıktısı çıkarılır.
"""
from __future__ import annotations

from . import freshness, today
from .webroutes import Ctx, route


@route("GET", "/api/v2/today")
def _today(ctx: Ctx) -> dict:
    return today.build(remote=ctx.remote)


@route("GET", "/api/v2/freshness")
def _freshness(ctx: Ctx) -> dict:
    st = freshness.status()
    if ctx.remote:
        for s in st["sources"]:
            s.pop("file", None)
            s.pop("last_fail", None)
    return st
