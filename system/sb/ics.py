"""Mail ekindeki .ics (takvim) dosyalarını tarih çıkarmaya uygun kısa metne çevirir."""
from __future__ import annotations

import re
from datetime import datetime

MARK = "[Takvim eki]"
FIELDS = ("SUMMARY", "DTSTART", "DTEND", "LOCATION", "DESCRIPTION")


def _unfold(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _fmt_dt(value: str, params: str) -> str:
    v = value.strip()
    for fmt, out in (("%Y%m%dT%H%M%SZ", "%Y-%m-%d %H:%M UTC"), ("%Y%m%dT%H%M%S", "%Y-%m-%d %H:%M"), ("%Y%m%d", "%Y-%m-%d")):
        try:
            s = datetime.strptime(v, fmt).strftime(out)
            tz = re.search(r"TZID=([^;:]+)", params)
            return f"{s} ({tz.group(1)})" if tz and not s.endswith("UTC") else s
        except ValueError:
            continue
    return v


def summarize(text: str, max_len: int = 1500) -> str:
    events, cur = [], None
    for line in _unfold(text):
        if line.startswith("BEGIN:VEVENT"):
            cur = {}
        elif line.startswith("END:VEVENT") and cur is not None:
            events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            head, value = line.split(":", 1)
            name, _, params = head.partition(";")
            if name in FIELDS and name not in cur:
                value = value.replace("\\n", " ").replace("\\,", ",").replace("\\;", ";")
                cur[name] = _fmt_dt(value, params) if name.startswith("DT") else value.strip()
    parts = []
    for ev in events:
        parts.append(" | ".join(f"{k}: {ev[k]}" for k in FIELDS if ev.get(k)))
    return (f"{MARK}\n" + "\n".join(parts))[:max_len] if parts else ""
