"""Hazır uygulamalar (ClipBoardLine, Nashi) uçları: durum kartı, Aç, Şimdi senkronla. Kurulum yalnız kurulum sihirbazından/`sb apps install`."""
from __future__ import annotations

from . import apps
from .webroutes import ApiError, Ctx, route


def _id(ctx: Ctx) -> str:
    i = str(ctx.arg("id") or "")
    if i not in apps.ids():
        raise ApiError(404, "bilinmeyen uygulama")
    return i


@route("GET", "/api/v2/apps/status", local_only=True)
def status(ctx: Ctx) -> dict:
    out = []
    for c in apps.catalog():
        st = apps.status(c["id"])
        st["title"] = c["name"].get("tr") if isinstance(c["name"], dict) else c["name"]
        st["about"] = (c["app"].get("about") or {}).get("tr", "")
        out.append(st)
    return {"apps": out}


@route("POST", "/api/v2/apps/start", local_only=True)
def start(ctx: Ctx) -> dict:
    try:
        return apps.start(_id(ctx))
    except apps.AppsError as e:
        raise ApiError(400, str(e))


@route("POST", "/api/v2/apps/sync", local_only=True)
def sync(ctx: Ctx) -> dict:
    try:
        r = apps.sync(_id(ctx))
    except apps.AppsError as e:
        raise ApiError(400, str(e))
    return {"result": r, "text": apps.format_sync(r), "status": apps.status(r["kaynak"])}


@route("POST", "/api/v2/apps/update", local_only=True)
def update(ctx: Ctx) -> dict:
    """Yeni sürüm var mı: yalnız BİLDİRİR (sürüm, değişiklik notu bağlantısı, yeni SHA-256). Kurmaz, sabitlemez."""
    try:
        return {"update": apps.update_available(_id(ctx))}
    except apps.AppsError as e:
        raise ApiError(400, str(e))


@route("POST", "/api/v2/apps/accept", local_only=True)
def accept(ctx: Ctx) -> dict:
    """Kullanıcının açık onayı (arayüzdeki onay düğmesi): bildirilen sürüm + özet kullanıcı tarafında sabitlenir. Kurulum ayrı: `sb apps install <id> --force`."""
    version = str(ctx.arg("version") or "").strip()
    if not version:
        raise ApiError(400, "sürüm gerekli")
    try:
        return apps.accept_update(_id(ctx), version)
    except apps.AppsError as e:
        raise ApiError(400, str(e))
