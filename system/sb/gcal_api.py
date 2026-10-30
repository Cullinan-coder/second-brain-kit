"""Google Takvim: okuma (kasa aktarımı için) ve kurallı etkinlik ekleme.

Kurallar CLAUDE.md'deki tabloyla aynıdır. Eklenen her etkinlik
`extendedProperties.private.sb_source_id` taşır; ekleme öncesi hem bu kimlik hem
aynı gün + aynı başlık aranır, varsa eklenmez. Bu modül etkinlik SİLMEZ.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .config import TIMEZONE
from .google_auth import service

TZ = ZoneInfo(TIMEZONE)
DAY, HOUR = 1440, 60


@dataclass(frozen=True)
class Rule:
    color: str
    reminders: tuple[int, ...]          # dakika
    timed_extra: tuple[int, ...] = ()   # saatli etkinlikte ek hatırlatmalar
    free: bool = False                  # takvimde "müsait"
    all_day_only: bool = False


RULES = {
    "SINAV": Rule("11", (7 * DAY, 3 * DAY, DAY), timed_extra=(2 * HOUR,)),
    "SUNUM": Rule("11", (7 * DAY, 3 * DAY, DAY), timed_extra=(2 * HOUR,)),
    "ÖDEV": Rule("6", (3 * DAY, DAY, 3 * HOUR), free=True),
    "BAŞVURU": Rule("3", (14 * DAY, 7 * DAY, 2 * DAY), free=True),
    "GÖRÜŞME": Rule("10", (DAY, 2 * HOUR, 30)),
    "YOLCULUK": Rule("9", (DAY, 3 * HOUR)),
    "RANDEVU": Rule("4", (DAY, 2 * HOUR)),
    "HATIRLATMA": Rule("5", (10,)),
    "AKADEMİK": Rule("8", (), free=True, all_day_only=True),
    "TATİL": Rule("8", (), free=True, all_day_only=True),
}


def _fold(t: str) -> str:
    return t.translate(str.maketrans("İIıÖöÜüŞşÇçĞğ", "iiiooUussccgg")).lower()


def match_tag(s: str) -> str | None:
    """'gorusme', 'Görüşme', 'GÖRÜŞME' → 'GÖRÜŞME'; bilinmeyen etiket → None."""
    return next((t for t in RULES if _fold(t) == _fold(s)), None)


@dataclass
class NewEvent:
    tag: str                 # RULES anahtarı
    title: str               # etiketsiz başlık, ör. "Yapay Sinir Ağları – Final"
    day: date
    at: time | None = None   # None → tüm gün
    minutes: int = 60
    description: str = ""
    source_id: str = ""      # "gmail-main:<msgid>" gibi
    reminders: tuple[int, ...] | None = None   # dakika önce; verilirse etiketin varsayılan hatırlatmalarının yerine geçer

    @property
    def summary(self) -> str:
        if self.tag == "ÖDEV" and self.at == time(23, 59) and "(23:59)" not in self.title:
            return f"[ÖDEV] {self.title} (23:59)"
        return f"[{self.tag}] {self.title}"


FALLBACK_REMINDER = 3 * HOUR
DEADLINE_TAGS = ("ÖDEV", "BAŞVURU")


def build_body(ev: NewEvent, now: datetime | None = None) -> dict:
    rule = RULES[ev.tag]
    at = None if rule.all_day_only else ev.at
    reminders = list(ev.reminders) if ev.reminders is not None else list(rule.reminders) + (list(rule.timed_extra) if at else [])
    if reminders:
        # Geçmişte kalacak hatırlatmaları at; hiçbiri kalmazsa yakın bir yedek koy (ör. yarınki son başvuru).
        start_at = datetime.combine(ev.day, at or time.min, TZ)
        now = now or datetime.now(TZ)
        future = [m for m in reminders if start_at - timedelta(minutes=m) > now]
        if not future and start_at - timedelta(minutes=FALLBACK_REMINDER) > now:
            future = [FALLBACK_REMINDER]
        reminders = future
    body = {
        "summary": ev.summary,
        "description": (ev.description + "\n\n" if ev.description else "") + "Second Brain tarafından eklendi.",
        "colorId": rule.color,
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": m} for m in reminders]},
        "extendedProperties": {"private": {"sb_source_id": ev.source_id, "sb_created_by": "second-brain"}},
    }
    if rule.free:
        body["transparency"] = "transparent"
    if at is None:
        body["start"] = {"date": ev.day.isoformat()}
        body["end"] = {"date": (ev.day + timedelta(days=1)).isoformat()}
    else:
        start = datetime.combine(ev.day, at)
        dur = timedelta(minutes=1) if ev.tag in DEADLINE_TAGS and at == time(23, 59) else timedelta(minutes=ev.minutes)
        body["start"] = {"dateTime": start.isoformat(), "timeZone": TIMEZONE}
        body["end"] = {"dateTime": (start + dur).isoformat(), "timeZone": TIMEZONE}
    return body


class Calendar:
    def __init__(self, alias: str = "main", calendar_id: str = "primary"):
        self.api = service(alias, "calendar", "v3").events()
        self.cal = calendar_id

    def list_events(self, start: datetime, end: datetime) -> list[dict]:
        out, token = [], None
        while True:
            resp = self.api.list(
                calendarId=self.cal, timeMin=start.astimezone(TZ).isoformat(), timeMax=end.astimezone(TZ).isoformat(),
                singleEvents=True, orderBy="startTime", maxResults=2500, pageToken=token,
            ).execute()
            out += resp.get("items", [])
            token = resp.get("nextPageToken")
            if not token:
                return out

    def find_duplicate(self, ev: NewEvent) -> dict | None:
        if ev.source_id:
            resp = self.api.list(calendarId=self.cal, privateExtendedProperty=f"sb_source_id={ev.source_id}",
                                 singleEvents=True, maxResults=5).execute()
            if resp.get("items"):
                return resp["items"][0]
        day_start = datetime.combine(ev.day, time.min, TZ)
        for item in self.list_events(day_start, day_start + timedelta(days=1)):
            if item.get("summary", "").strip().casefold() == ev.summary.strip().casefold():
                return item
        return None

    def add(self, ev: NewEvent, dry_run: bool = True) -> tuple[str, dict]:
        """('exists' | 'dry-run' | 'created', etkinlik) döndürür."""
        dup = self.find_duplicate(ev)
        if dup:
            return "exists", dup
        body = build_body(ev)
        if dry_run:
            return "dry-run", body
        return "created", self.api.insert(calendarId=self.cal, body=body).execute()
