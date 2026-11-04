"""Faz 4b Paket A uçları: otomasyon kuralları, kuru çalıştırma, webhook, bekleyen onaylar."""
from __future__ import annotations

from . import automation as au
from .webroutes import ApiError, Ctx, route


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except ValueError as e:
        raise ApiError(400, str(e))
    except LookupError as e:
        raise ApiError(404, str(e.args[0] if e.args else "bulunamadı"))
    except PermissionError as e:
        raise ApiError(403, str(e))


@route("GET", "/api/v2/automations")
def auto_list(ctx: Ctx) -> dict:
    return {"rules": au.load_rules(), "triggers": list(au.TRIGGERS), "actions": list(au.ACTIONS), "external": list(au.EXTERNAL)}


@route("POST", "/api/v2/automations")
def auto_post(ctx: Ctx) -> dict:
    if ctx.arg("id") and ctx.arg("acik") is not None and not ctx.arg("tetik"):
        return {"rule": _guard(au.set_enabled, str(ctx.arg("id")), ctx.arg("acik") is not False)}
    return {"rule": _guard(au.add_rule, {k: ctx.data.get(k) for k in ("id", "ad", "tetik", "kosul", "eylem", "acik")})}


@route("POST", "/api/v2/automations/test")
def auto_test(ctx: Ctx) -> dict:
    data = ctx.arg("data")
    return _guard(au.test_run, str(ctx.arg("id") or ""), data if isinstance(data, dict) else None)


@route("POST", "/api/v2/hook", local_only=False)
def hook(ctx: Ctx) -> dict:
    """Zapier/n8n/Make: {name, token, data}. Token keyring'de (`sb set-secret hook-<ad>`); yoksa/yanlışsa 403."""
    res = _guard(au.fire_webhook, str(ctx.arg("name") or ""), str(ctx.arg("token") or ""), ctx.arg("data"))
    return {"ok": True, "ran": len(res)}


# ---- TEK onay görünümü (D-30): sohbet kartları, otomasyon ve tarih adayları aynı depoda (sb/approvals.py)
def _viewer(ctx: Ctx) -> str:
    from . import approvals as ap
    return ap.PHONE if ctx.remote else ap.LOCAL


@route("GET", "/api/v2/approvals")
def approvals(ctx: Ctx) -> dict:
    """Bekleyen onaylar (?status=all: son kararlar da). Telefon yalnız kendi kartlarını ve tarih adaylarını görür."""
    from . import approvals as ap
    viewer = _viewer(ctx)
    status = None if str(ctx.arg("status") or "") == "all" else ap.PENDING
    rows = [ap.public(r, viewer) for r in ap.records(status=status, viewer=viewer)]
    return {"approvals": rows[::-1], "count": ap.count(viewer)}


@route("POST", "/api/v2/approvals/decide")
def approvals_decide(ctx: Ctx) -> dict:
    """Tek karar ucu. Telefondan: yalnız kendi kartı; komut/WhatsApp/gece/silme/otomasyon/tarih bilgisayardan (D-05)."""
    from . import approvals as ap, chat
    try:
        out = chat.decide_card(str(ctx.arg("id") or ""), ctx.arg("ok") is True, remote=ctx.remote, calendar=ctx.calendar)
    except ap.NotFound as e:
        raise ApiError(404, str(e))
    except ap.ApprovalError as e:                            # zaten sonuçlandı / süresi doldu / telefondan onaylanamaz
        raise ApiError(403, str(e))
    st = out["status"]
    return {"ok": out["ok"], "id": out["id"], "status": st, "durum": st, "message": out["message"], "sonuc": out["message"],
            "proposals": chat.pending(ctx.session) if ctx.session is not None else [], "count": ap.count(_viewer(ctx))}
