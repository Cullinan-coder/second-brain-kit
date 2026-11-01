"""Faz 3a Paket V uçları: görev panosu, günlük plan, zaman bloklama, pomodoro, alışkanlık, hedef, haftalık gözden geçirme."""
from __future__ import annotations

from datetime import datetime, timedelta

from . import chat, productivity as pr
from .convstore import valid_sid
from .webroutes import ApiError, Ctx, route


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except ValueError as e:
        raise ApiError(400, str(e))
    except LookupError as e:
        raise ApiError(404, str(e.args[0] if e.args else "bulunamadı"))
    except PermissionError as e:
        raise ApiError(409, str(e))


@route("GET", "/api/v2/tasks/board")
def tasks_board(ctx: Ctx) -> dict:
    return pr.board()


@route("POST", "/api/v2/tasks/move")
def tasks_move(ctx: Ctx) -> dict:
    return _guard(pr.move_task, str(ctx.arg("id") or ""), str(ctx.arg("to") or ""))


@route("POST", "/api/v2/tasks/add")
def tasks_add(ctx: Ctx) -> dict:
    card = _guard(pr.add_task, ctx.arg("text"), str(ctx.arg("due") or ""), str(ctx.arg("project") or ""), ctx.arg("priority"),
                  str(ctx.arg("repeat") or ""), str(ctx.arg("after") or ""))
    return {"ok": True, "card": card}


@route("GET", "/api/v2/plan/today")
def plan_today(ctx: Ctx) -> dict:
    return pr.plan_today(ctx.calendar)


@route("POST", "/api/v2/plan/block")
def plan_block(ctx: Ctx) -> dict:
    """Takvime EKLEMEZ; onay kartı üretir (Onayla'ya basılınca eklenir)."""
    sid = str(ctx.arg("sid") or ctx.sid or "")
    if not valid_sid(sid) or ctx.session is None:
        raise ApiError(400, "geçersiz sohbet kimliği")
    title = " ".join(str(ctx.arg("title") or "").split())[:100]
    try:
        start, end = datetime.fromisoformat(str(ctx.arg("start"))), datetime.fromisoformat(str(ctx.arg("end")))
    except ValueError:
        raise ApiError(400, "start/end ISO biçiminde olmalı (YYYY-AA-GGTSS:DD)")
    if not title:
        raise ApiError(400, "başlık boş")
    if not timedelta(0) < end - start <= timedelta(hours=8):
        raise ApiError(400, "süre 0-8 saat arası olmalı")
    from .gcal_api import Calendar, NewEvent

    def run():
        ev = NewEvent("HATIRLATMA", f"Odak: {title}", start.date(), start.time(), int((end - start).total_seconds() // 60),
                      description="Zaman bloğu (sb plan)")
        cal = ctx.calendar or Calendar("main")
        return str(cal.add(ev, dry_run=False)[0])
    chat.add_proposal(ctx.session, "takvim", f"Zaman bloğu: {title}", f"{start:%Y-%m-%d %H:%M} – {end:%H:%M}", run)
    return {"ok": True, "proposals": chat.pending(ctx.session)}


@route("POST", "/api/v2/plan/pomodoro")
def plan_pomodoro(ctx: Ctx) -> dict:
    return _guard(pr.pomodoro, str(ctx.arg("task_id") or ""), ctx.arg("minutes", 25))


@route("POST", "/api/v2/plan/mood")
def plan_mood(ctx: Ctx) -> dict:
    return _guard(pr.set_mood, ctx.arg("level"))


@route("GET", "/api/v2/habits")
def habits_list(ctx: Ctx) -> dict:
    return {"habits": pr.habits()}


@route("POST", "/api/v2/habits")
def habits_post(ctx: Ctx) -> dict:
    if ctx.arg("id"):
        return {"habits": _guard(pr.habit_mark, str(ctx.arg("id")), ctx.arg("done", True) is not False)}
    return {"habits": _guard(pr.habit_add, ctx.arg("name"))}


@route("GET", "/api/v2/goals")
def goals_list(ctx: Ctx) -> dict:
    return {"goals": pr.goals()}


@route("GET", "/api/v2/review/week")
def review_get(ctx: Ctx) -> dict:
    return pr.review_week()


@route("POST", "/api/v2/review/week")
def review_post(ctx: Ctx) -> dict:
    return _guard(pr.review_save, ctx.arg("answers"))
