"""Faz 3b Paket R: kariyer + kalan okul uçları (CRM, teklif, saat, pano, CV, mülakat, portfolyo, pazar, sözleşme, finans, çalışma araçları)."""
from __future__ import annotations

from . import career
from .webroutes import ApiError, Ctx, route


def _bad(fn, *a, **k):
    try:
        return fn(*a, **k)
    except KeyError as e:
        raise ApiError(404, f"bulunamadı: {e.args[0] if e.args else ''}")
    except ValueError as e:
        raise ApiError(400, str(e))


def _s(ctx: Ctx, name: str) -> str:
    return str(ctx.arg(name, "") or "").strip()


@route("GET", "/api/v2/crm")
def _crm(ctx: Ctx) -> list:
    return career.crm()


@route("POST", "/api/v2/quote")
def _quote(ctx: Ctx) -> dict:
    return _bad(career.write_quote, _s(ctx, "client"), ctx.data.get("items"), _s(ctx, "currency") or "TRY")


@route("POST", "/api/v2/time")
def _time(ctx: Ctx) -> dict:
    return _bad(career.log_time, _s(ctx, "project"), ctx.data.get("minutes"), _s(ctx, "note"))


@route("GET", "/api/v2/time/report")
def _time_report(ctx: Ctx) -> dict:
    return _bad(career.time_report, _s(ctx, "project"), _s(ctx, "month"))


@route("GET", "/api/v2/applications/board")
def _board(ctx: Ctx) -> dict:
    return career.board()


@route("POST", "/api/v2/cv", model=True, local_only=True)
def _cv(ctx: Ctx) -> dict:
    return _bad(career.make_cv, _s(ctx, "target"), _s(ctx, "lang") or "tr")


@route("POST", "/api/v2/interview", model=True, local_only=True)
def _interview(ctx: Ctx) -> dict:
    return _bad(career.make_interview, _s(ctx, "role"), _s(ctx, "company"))


@route("POST", "/api/v2/portfolio")
def _portfolio(ctx: Ctx) -> dict:
    return career.portfolio()


@route("POST", "/api/v2/linkedin-post", model=True, local_only=True)
def _post(ctx: Ctx) -> dict:
    return _bad(career.linkedin_post, _s(ctx, "topic"))


@route("GET", "/api/v2/market")
def _market(ctx: Ctx) -> dict:
    return career.market()


@route("POST", "/api/v2/market/sync")
def _market_sync(ctx: Ctx) -> dict:
    return career.market_sync()


@route("GET", "/api/v2/contracts")
def _contracts(ctx: Ctx) -> list:
    return career.contracts()


@route("GET", "/api/v2/finance")
def _finance(ctx: Ctx) -> dict:
    return career.finance()


@route("POST", "/api/v2/course-notes", model=True)
def _course_notes(ctx: Ctx) -> dict:
    return _bad(career.course_notes, _s(ctx, "code"), _s(ctx, "source_path"))


@route("POST", "/api/v2/tutor", model=True)
def _tutor(ctx: Ctx) -> dict:
    return _bad(career.tutor, _s(ctx, "code"), _s(ctx, "question"))


@route("POST", "/api/v2/bib")
def _bib(ctx: Ctx) -> dict:
    try:
        return _bad(career.bib, _s(ctx, "text"), _s(ctx, "doi"), _s(ctx, "url"), _s(ctx, "style") or "apa")
    except ApiError:
        raise
    except Exception as e:                                       # noqa: BLE001 — ağ/DOI hatası
        raise ApiError(502, f"kaynak alınamadı: {str(e)[:120]}")


@route("POST", "/api/v2/writing", model=True)
def _writing(ctx: Ctx) -> dict:
    return _bad(career.writing, _s(ctx, "path"), _s(ctx, "task"))


@route("GET", "/api/v2/group")
def _group(ctx: Ctx) -> dict:
    return _bad(career.group, _s(ctx, "project"))
