"""Faz 4a Paket P: kişisel iş uçları (harcama, abonelik, garanti, sağlık, liste, yemek, bakım, hediye, ruh hali, seyahat)."""
from __future__ import annotations

from . import chat, personal
from .convstore import valid_sid
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


@route("GET", "/api/v2/spending")
def _spending(ctx: Ctx) -> dict:
    return _bad(personal.spending, _s(ctx, "month"))


@route("GET", "/api/v2/subscriptions")
def _subs(ctx: Ctx) -> list:
    return personal.subscriptions()


@route("GET", "/api/v2/warranties")
def _warranties(ctx: Ctx) -> list:
    return personal.warranties()


@route("GET", "/api/v2/health/meds", local_only=True)
def _meds(ctx: Ctx) -> dict:
    return personal.health()


@route("POST", "/api/v2/health/remind", local_only=True)
def _remind(ctx: Ctx) -> dict:
    """Takvime EKLEMEZ; onay kartı üretir (Onayla'ya basılınca tek [HATIRLATMA] etkinliği eklenir)."""
    sid = str(ctx.arg("sid") or ctx.sid or "")
    if not valid_sid(sid) or ctx.session is None:
        raise ApiError(400, "geçersiz sohbet kimliği")
    ev = _bad(personal.health_event, _s(ctx, "kind") or "med", _s(ctx, "name"))
    from .gcal_api import Calendar, NewEvent

    def run():
        e = NewEvent("HATIRLATMA", ev["title"], ev["day"], ev["at"], ev["minutes"], description="Sağlık hatırlatması (sb)",
                     reminders=ev["reminders"])
        cal = ctx.calendar or Calendar("main")
        return str(cal.add(e, dry_run=False)[0])
    chat.add_proposal(ctx.session, "takvim", f"Hatırlatma: {ev['title']}", f"{ev['day']} {ev['at']:%H:%M}", run)
    return {"ok": True, "proposals": chat.pending(ctx.session)}


@route("GET", "/api/v2/reading-list")
def _reading(ctx: Ctx) -> dict:
    return personal.reading_list()


@route("POST", "/api/v2/reading-list")
def _reading_add(ctx: Ctx) -> dict:
    return _bad(personal.add_reading, _s(ctx, "title"), _s(ctx, "kind") or "okunacak")


@route("POST", "/api/v2/meal-plan", model=True, local_only=True)
def _meal(ctx: Ctx) -> dict:
    return _bad(personal.meal_plan, ctx.arg("days", 7))


@route("GET", "/api/v2/maintenance")
def _maint(ctx: Ctx) -> list:
    return personal.maintenance()


@route("POST", "/api/v2/gift")
def _gift(ctx: Ctx) -> dict:
    return _bad(personal.add_gift, _s(ctx, "person"), _s(ctx, "idea"))


@route("GET", "/api/v2/gifts")
def _gifts(ctx: Ctx) -> list:
    return personal.gifts(_s(ctx, "person"))


@route("POST", "/api/v2/mood")
def _mood_add(ctx: Ctx) -> dict:
    return _bad(personal.add_mood, ctx.arg("level"), _s(ctx, "note"))


@route("GET", "/api/v2/mood")
def _mood(ctx: Ctx) -> dict:
    return _bad(personal.mood, ctx.arg("days", 30))


@route("POST", "/api/v2/trip", model=True, local_only=True)
def _trip(ctx: Ctx) -> dict:
    return _bad(personal.trip, _s(ctx, "destination"), _s(ctx, "start"), _s(ctx, "end"))
