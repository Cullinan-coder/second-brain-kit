"""Faz 4a Paket G uçları: gizlilik paneli, önizleme, denetim, izin profilleri, yedekler, dışa aktarma.

Hiçbir uç kendiliğinden şifrelemez/siler/geri yükler. Şifreleme ve geri yükleme yalnız CLI'dadır.
"""
from __future__ import annotations

from . import chat, privacy as pv, vault_ops
from .convstore import valid_sid
from .webroutes import ApiError, Ctx, route


@route("GET", "/api/v2/privacy")
def privacy_overview(ctx: Ctx) -> dict:
    return pv.overview()


@route("GET", "/api/v2/privacy/preview")
def privacy_preview(ctx: Ctx) -> dict:
    text = str(ctx.arg("text") or "")[:20000]
    masked, n = pv.cloud_filter(text, mask_contacts=True if str(ctx.arg("contacts") or "") in ("1", "true") else None)
    return {"text": masked, "masked": n, "mask_contacts": pv.mask_contacts_enabled()}


@route("GET", "/api/v2/audit")
def audit(ctx: Ctx) -> dict:
    try:
        limit = int(ctx.arg("limit") or 100)
    except ValueError:
        raise ApiError(400, "limit sayı olmalı")
    return {"entries": pv.audit(str(ctx.arg("actor") or ""), str(ctx.arg("q") or ""), limit)}


@route("GET", "/api/v2/permissions")
def permissions_get(ctx: Ctx) -> dict:
    return pv.permissions()


@route("POST", "/api/v2/permissions")
def permissions_set(ctx: Ctx) -> dict:
    try:
        return pv.set_profile(str(ctx.arg("profile") or ""))
    except ValueError as e:
        raise ApiError(400, str(e))


@route("GET", "/api/v2/backups")
def backups_list(ctx: Ctx) -> dict:
    return pv.backups()


@route("POST", "/api/v2/backups/create")
def backups_create(ctx: Ctx) -> dict:
    return pv.create_backup()


@route("POST", "/api/v2/export")
def export_post(ctx: Ctx) -> dict:
    try:
        z = pv.export(str(ctx.arg("scope") or "vault"))
    except ValueError as e:
        raise ApiError(400, str(e))
    return {"ok": True, "file": str(z), "name": z.name, "bytes": z.stat().st_size}


@route("POST", "/api/v2/export/archive")
def export_archive(ctx: Ctx) -> dict:
    """'Silme' = klasörü arşive taşıma ÖNERİSİ: yalnız onay kartı üretir; kalıcı silme yok."""
    sid = str(ctx.arg("sid") or ctx.sid or "")
    if not valid_sid(sid) or ctx.session is None:
        raise ApiError(400, "geçersiz sohbet kimliği")
    folder = str(ctx.arg("folder") or "")
    try:
        files = pv.archive_candidates(folder)
    except ValueError as e:
        raise ApiError(400, str(e))
    if not files:
        raise ApiError(404, "klasörde not yok")

    def run():
        done = [vault_ops.archive(f, "gizlilik: arşive taşıma", actor="onay") for f in files]
        return f"{len(done)} not arşive taşındı (geri alınabilir)"
    chat.add_proposal(ctx.session, "kasa", f"Arşive taşı: {folder}", f"{len(files)} not 90-Arşiv'e taşınır (silinmez)", run)
    return {"ok": True, "files": len(files), "proposals": chat.pending(ctx.session)}
