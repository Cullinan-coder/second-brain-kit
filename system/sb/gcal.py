"""Google Takvim etkinliklerini kasa notlarına dönüştürür.

Girdi: Calendar API `events.list` (singleEvents=true) biçiminde bir JSON ({"events": [...]}).
Faz 2'de bu JSON takvim bağlayıcısından alınan anlık görüntüdür; Faz 3'te API'den çekilecek.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from .notes import NoteSpec

TAG_RE = re.compile(r"^\[(SINAV|SUNUM|ÖDEV|BAŞVURU|GÖRÜŞME|YOLCULUK|RANDEVU|HATIRLATMA|AKADEMİK|TATİL)\]\s*(.+)$")
COURSE_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<code>[A-Z]{2,4}\d{3})\)\s*$")
CODE_IN_TEXT_RE = re.compile(r"\b([A-Z]{2,4}\d{3})\b")
WEEKDAYS = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
KIND = {"SINAV": "sinav", "SUNUM": "sunum", "ÖDEV": "odev"}
SEMESTER = "2026-Guz"
DERS_ROOT = "10-Dersler"


@dataclass
class Event:
    id: str
    series: str            # tekrarlayan etkinlikte seri kimliği, değilse kendi kimliği
    title: str
    start: datetime
    end: datetime
    all_day: bool
    description: str
    link: str

    @classmethod
    def parse(cls, raw: dict) -> "Event":
        s, e = raw["start"], raw["end"]
        if "date" in s:
            start, end, all_day = datetime.fromisoformat(s["date"]), datetime.fromisoformat(e["date"]), True
        else:
            start, end = datetime.fromisoformat(s["dateTime"]), datetime.fromisoformat(e["dateTime"])
            # Bağlayıcı tüm gün etkinlikleri UTC gece yarısı olarak döndürüyor.
            all_day = start.utcoffset() == timedelta(0) and start.time() == end.time() == datetime.min.time()
        return cls(
            id=raw["id"],
            series=raw.get("recurringEventId") or raw["id"],
            title=raw.get("summary", "").strip(),
            start=start,
            end=end,
            all_day=all_day,
            description=(raw.get("description") or "").strip(),
            link=raw.get("htmlLink", ""),
        )


def course_label(code: str, name: str) -> str:
    return f"{code} {name}"


def build_specs(raw_events: list[dict], today: date) -> list[NoteSpec]:
    events = [Event.parse(r) for r in raw_events if r.get("status") != "cancelled"]
    courses: dict[str, str] = {}                      # kod -> ad
    slots: dict[str, set[str]] = defaultdict(set)     # kod -> {"Pzt 13:00–15:50"}
    series_ids: dict[str, set[str]] = defaultdict(set)
    tagged: dict[str, list[Event]] = defaultdict(list)

    for ev in events:
        m = COURSE_RE.match(ev.title)
        if m and ev.series != ev.id:
            code, name = m["code"], m["name"].strip()
            courses[code] = name
            slots[code].add(f"{WEEKDAYS[ev.start.weekday()]} {ev.start:%H:%M}–{ev.end:%H:%M}")
            series_ids[code].add(ev.series)
        elif TAG_RE.match(ev.title):
            tagged[ev.series].append(ev)

    name_to_code = {name: code for code, name in courses.items()}
    specs = [_course_spec(code, name, slots[code], series_ids[code]) for code, name in sorted(courses.items())]

    academic: list[Event] = []
    for series, evs in tagged.items():
        evs.sort(key=lambda e: e.start.replace(tzinfo=None))     # tüm gün (naive) ve saatli (aware) etkinlikler birlikte sıralanır
        tag, rest = TAG_RE.match(evs[0].title).groups()
        code = _find_code(evs[0], name_to_code)
        if tag in KIND and code:
            specs.append(_teslim_spec(tag, rest, code, courses[code], series, evs, today))
        elif tag in ("BAŞVURU", "GÖRÜŞME"):
            specs.append(_career_spec(tag, rest, series, evs, today))
        elif tag in ("YOLCULUK", "RANDEVU", "HATIRLATMA"):
            continue                                              # sadece takvimde durur, kasada not açılmaz
        else:
            academic.extend(evs)
    if academic:
        specs.append(_academic_spec(academic, today))
    return specs


def _find_code(ev: Event, name_to_code: dict[str, str]) -> str | None:
    for name, code in name_to_code.items():
        if name in ev.title:
            return code
    m = CODE_IN_TEXT_RE.search(ev.description)
    return m.group(1) if m and m.group(1) in name_to_code.values() else None


def _course_spec(code: str, name: str, slots: set[str], series: set[str]) -> NoteSpec:
    label = course_label(code, name)
    order = {d: i for i, d in enumerate(WEEKDAYS)}
    schedule = sorted(slots, key=lambda s: (order[s.split()[0]], s))
    body = (
        f"# {label}\n\n"
        "## Teslimler ve sınavlar\n"
        "```base\nfilters:\n  and:\n    - 'type == \"teslim\"'\n    - file.hasLink(this.file)\n"
        "views:\n  - type: table\n    name: Teslimler\n    order: [file.name, kind, due, due_time, status]\n"
        "    sort:\n      - property: due\n        direction: ASC\n```\n\n"
        "## Haftalık program\n<!-- sb:auto:program:start -->\n<!-- sb:auto:program:end -->\n\n"
        "## Notlar\n"
    )
    return NoteSpec(
        folder=f"{DERS_ROOT}/{label}",
        title=label,
        frontmatter={
            "type": "ders", "status": "aktif", "tags": ["ders"],
            "source": "gcal", "source_id": f"ders:{code}",
            "due": None, "code": code, "semester": SEMESTER,
            "instructor": None, "schedule": schedule,
            "calendar_series": sorted(series),
        },
        owned=("schedule", "calendar_series"),
        body=body,
        auto={"program": "\n".join(f"- {s}" for s in schedule) + "\n\nKaynak: Google Takvim (açık mavi, tekrarlayan)."},
    )


def _teslim_spec(tag: str, rest: str, code: str, name: str, series: str, evs: list[Event], today: date) -> NoteSpec:
    # "Yapay Sinir Ağları – Proje Sunumu" -> "Proje Sunumu"; "(23:59)" eki saat alanına gider.
    what = re.sub(r"\s*\(\d{2}:\d{2}\)\s*$", "", rest.split("–", 1)[-1]).strip()
    recurring = len(evs) > 1
    upcoming = [e for e in evs if e.start.date() >= today] or evs[-1:]
    nxt = upcoming[0]
    label = course_label(code, name)
    lines = [
        f"- Takvim başlığı: `{nxt.title}`",
        f"- Sıradaki: {nxt.start:%Y-%m-%d %H:%M}" + (f" (toplam {len(evs)} tekrar, son: {evs[-1].start:%Y-%m-%d})" if recurring else ""),
        f"- [Takvimde aç]({nxt.link})" if nxt.link else "",
        "",
        nxt.description,
    ]
    return NoteSpec(
        folder=f"{DERS_ROOT}/{label}",
        title=f"{code} {what}",
        frontmatter={
            "type": "teslim", "kind": KIND[tag],
            "status": "acik", "tags": ["teslim"] + (["tekrarlayan"] if recurring else []),
            "source": "gcal", "source_id": series,
            "due": nxt.start.date(), "due_time": f"{nxt.start:%H:%M}",
            "course": f"[[{label}]]", "calendar_event_id": nxt.id,
        },
        owned=("due", "due_time", "calendar_event_id"),
        body=f"# {code} {what}\n\n## Takvim\n<!-- sb:auto:takvim:start -->\n<!-- sb:auto:takvim:end -->\n\n## Notlar\n\n## Yapılacaklar\n- [ ] \n",
        auto={"takvim": "\n".join(l for l in lines if l is not None).strip()},
        reset_on_change={"due": {"status": "acik"}} if recurring else {},
    )


def _career_spec(tag: str, rest: str, series: str, evs: list[Event], today: date) -> NoteSpec:
    """[BAŞVURU] ve [GÖRÜŞME] etkinlikleri 30-Kariyer altında kendi notunu alır."""
    upcoming = [e for e in evs if e.start.date() >= today] or evs[-1:]
    nxt = upcoming[0]
    is_app = tag == "BAŞVURU"
    title = re.sub(r"\s*\(\d{2}:\d{2}\)\s*$", "", rest).strip()
    return NoteSpec(
        folder="30-Kariyer/Başvurular" if is_app else "30-Kariyer/Görüşmeler", title=title,
        frontmatter={
            "type": "basvuru" if is_app else "gorusme", "status": "planlandi", "tags": ["basvuru" if is_app else "gorusme"],
            "source": "gcal", "source_id": series, "due": nxt.start.date(),
            "due_time": None if nxt.all_day else f"{nxt.start:%H:%M}", "calendar_event_id": nxt.id,
        },
        owned=("due", "due_time", "calendar_event_id"),
        body=f"# {title}\n\n## Takvim\n<!-- sb:auto:takvim:start -->\n<!-- sb:auto:takvim:end -->\n\n## Notlar\n\n## İlerleme\n- [ ] \n",
        auto={"takvim": f"- Takvim başlığı: `{nxt.title}`\n- Tarih: {nxt.start:%Y-%m-%d %H:%M}\n"
                        + (f"- [Takvimde aç]({nxt.link})\n" if nxt.link else "") + (f"\n{nxt.description}" if nxt.description else "")},
    )


def _academic_spec(evs: list[Event], today: date) -> NoteSpec:
    rows = ["| Başlangıç | Bitiş | Etkinlik |", "|---|---|---|"]
    for ev in sorted(evs, key=lambda e: e.start.replace(tzinfo=None)):
        last = ev.end - timedelta(days=1) if ev.all_day else ev.end
        end = "" if last.date() == ev.start.date() else f"{last:%Y-%m-%d}"
        mark = "~~" if last.date() < today else ""
        rows.append(f"| {mark}{ev.start:%Y-%m-%d}{mark} | {end} | {mark}{ev.title}{mark} |")
    return NoteSpec(
        folder=DERS_ROOT,
        title="ÜNİ 2026-2027 Akademik Takvim",
        frontmatter={
            "type": "akademik", "status": "aktif", "tags": ["akademik", "okul"],
            "source": "gcal", "source_id": "akademik:2026-2027",
            "due": None, "semester": "2026-2027",
        },
        owned=(),
        body="# ÜNİ 2026-2027 Akademik Takvim\n\nGeçmiş tarihler üstü çizili görünür. Kaynak: Google Takvim ([AKADEMİK], [TATİL], dönem [SINAV] etkinlikleri).\n\n"
             "<!-- sb:auto:takvim:start -->\n<!-- sb:auto:takvim:end -->\n\n## Notlar\n",
        auto={"takvim": "\n".join(rows)},
    )
