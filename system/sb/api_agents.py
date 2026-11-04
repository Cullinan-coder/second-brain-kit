"""Faz 4b Paket J: ajan uçları."""
from __future__ import annotations

from . import agents
from .webroutes import ApiError, Ctx, route


def _bad(fn, *a, **k):
    try:
        return fn(*a, **k)
    except KeyError as e:
        raise ApiError(404, f"bulunamadı: {e.args[0] if e.args else ''}")
    except PermissionError as e:
        raise ApiError(403, str(e))
    except ValueError as e:
        raise ApiError(400, str(e))


def _s(ctx: Ctx, name: str) -> str:
    return str(ctx.arg(name, "") or "").strip()


@route("GET", "/api/v2/agents")
def _list(ctx: Ctx) -> list:
    return agents.catalog()


@route("POST", "/api/v2/agents/run", model=True, local_only=True)
def _run(ctx: Ctx) -> dict:
    return _bad(agents.run, _s(ctx, "id"), _s(ctx, "input"), bool(ctx.data.get("web")))


@route("POST", "/api/v2/agents/code", local_only=True)      # telefon çerezi gece işi ekleyemez (D-05)
def _code(ctx: Ctx) -> dict:
    return _bad(agents.code_bridge, _s(ctx, "task"), _s(ctx, "where"))


@route("GET", "/api/v2/agent-runs")
def _runs(ctx: Ctx) -> list:
    return agents.runs()


@route("POST", "/api/v2/flows/run", model=True, local_only=True)
def _flow(ctx: Ctx) -> dict:
    return _bad(agents.run_flow, ctx.data.get("template"), _s(ctx, "input"))


@route("GET", "/api/v2/night-report")
def _night(ctx: Ctx) -> dict:
    return agents.night_report()
