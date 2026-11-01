"""Faz 3b Paket C uçları: iletişim (mail taslağı/özeti, bekleyenler, takip, ilişki, tarihler, bülten, toplantı). Mail salt okunur."""
from __future__ import annotations

from datetime import datetime, timedelta

from . import chat, comms
from .webroutes import ApiError, Ctx, route


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except ValueError as e:
        raise ApiError(400, str(e))
    except LookupError as e:
        raise ApiError(404, str(e.args[0] if e.args else "bulunamadı"))
    except RuntimeError as e:
        raise ApiError(502, str(e)[:200])


def _int(v, default, lo=0, hi=3650):
    try:
        return max(lo, min(int(v), hi))
    except (TypeError, ValueError):
        return default


@route("POST", "/api/v2/draft", model=True)
def draft(ctx: Ctx) -> dict:
    return _guard(comms.draft, str(ctx.arg("to") or ""), str(ctx.arg("subject") or ""), str(ctx.arg("context") or ""),
                  str(ctx.arg("tone") or ""), str(ctx.arg("lang") or "tr"))


@route("GET", "/api/v2/thread-summary", model=True)
def thread_summary(ctx: Ctx) -> dict:
    return _guard(comms.thread_summary, str(ctx.arg("thread_id") or ""))


@route("GET", "/api/v2/awaiting")
def awaiting(ctx: Ctx) -> dict:
    items = comms.awaiting(_int(ctx.arg("days"), 3, 1, 365))
    return {"count": len(items), "items": items[:100]}


@route("POST", "/api/v2/followup")
def followup(ctx: Ctx) -> dict:
    return _guard(comms.followup, str(ctx.arg("id") or ""), ctx.arg("days", 3))


@route("GET", "/api/v2/dates")
def dates(ctx: Ctx) -> dict:
    items = comms.upcoming_dates(_int(ctx.arg("days"), 30, 1, 366))
    return {"count": len(items), "items": items}


@route("GET", "/api/v2/relationships")
def relationships(ctx: Ctx) -> dict:
    items = comms.relationships(_int(ctx.arg("days"), 90, 7, 1000), limit=100000)
    return {"count": len(items), "items": items[:100]}


@route("POST", "/api/v2/bulk-draft")
def bulk_draft(ctx: Ctx) -> dict:
    channel = str(ctx.arg("channel") or "mail")
    wa = None
    if channel == "whatsapp":
        if ctx.session is None:
            raise ApiError(400, "geçersiz sohbet kimliği")
        # mevcut akış: her kişi için ayrı onay kartı; yeni gönderim yolu yok
        wa = lambda contact, text: chat._whatsapp(ctx.session, {"contact": contact, "text": text})
    res = _guard(comms.bulk_draft, ctx.arg("names"), str(ctx.arg("template") or ""), channel, wa)
    return {"items": res, "proposals": chat.pending(ctx.session) if ctx.session is not None else []}


@route("GET", "/api/v2/newsletters")
def newsletters(ctx: Ctx) -> dict:
    items = comms.newsletters()
    return {"count": len(items), "items": items, "note": "Yalnız öneri; abonelikten çıkma yapılmaz."}


@route("GET", "/api/v2/calls/recent")
def calls_recent(ctx: Ctx) -> dict:
    items = comms.recent_calls()
    return {"count": len(items), "items": items}


@route("POST", "/api/v2/translate", model=True)
def translate(ctx: Ctx) -> dict:
    return _guard(comms.translate, str(ctx.arg("text") or ""), str(ctx.arg("to") or "tr"))


@route("POST", "/api/v2/mail-to-task")
def mail_to_task(ctx: Ctx) -> dict:
    return _guard(comms.mail_to_task, str(ctx.arg("message_id") or ""))


@route("POST", "/api/v2/meeting-prep", model=True)
def meeting_prep(ctx: Ctx) -> dict:
    event, title = None, str(ctx.arg("title") or "")
    eid = str(ctx.arg("event_id") or "")
    if eid and ctx.calendar is not None:
        now = datetime.now().astimezone()
        try:
            event = next((e for e in ctx.calendar.list_events(now - timedelta(days=1), now + timedelta(days=30)) if e.get("id") == eid), None)
        except Exception:
            event = None
        if event is None and not title:
            raise ApiError(404, "etkinlik bulunamadı")
    names = ctx.arg("people") or []
    if not isinstance(names, list):
        raise ApiError(400, "people liste olmalı")
    return _guard(comms.meeting_prep, title, names, event)


@route("POST", "/api/v2/meeting-after", model=True)
def meeting_after(ctx: Ctx) -> dict:
    return _guard(comms.meeting_after, str(ctx.arg("text") or ""), str(ctx.arg("title") or ""))
