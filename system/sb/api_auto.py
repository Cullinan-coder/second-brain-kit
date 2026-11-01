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


@route("GET", "/api/v2/approvals")
def approvals(ctx: Ctx) -> dict:
    return {"approvals": au.approvals()}


@route("POST", "/api/v2/approvals/decide", local_only=True)
def approvals_decide(ctx: Ctx) -> dict:
    return _guard(au.decide, str(ctx.arg("id") or ""), ctx.arg("ok") is True, ctx.calendar)
