"""Dışa aktarılmış ekran süresi CSV'si (ManicTime/RescueTime vb.: uygulama, süre, tarih) → items (kind=ekran)."""
from __future__ import annotations

import re

from ._common import clean, ingest_items, sid
from .bank import date_ms, num, pick, read_rows

APP = ("application", "app", "uygulama", "name", "activity", "program", "tag")
DUR = ("duration", "süre", "sure", "time spent (seconds)", "time spent", "seconds", "time", "total time")
DATE = ("date", "tarih", "day", "start", "start time", "başlangıç")


def seconds(s: str) -> int | None:
    s = (s or "").strip().lower()
    m = re.fullmatch(r"(\d+):(\d{2})(?::(\d{2}))?(?:\.\d+)?", s)
    if m:
        a, b, c = int(m.group(1)), int(m.group(2)), m.group(3)
        return a * 3600 + b * 60 + int(c) if c is not None else a * 60 + b
    parts = re.findall(r"(\d+(?:[.,]\d+)?)\s*(saat|sa|h|dakika|dk|min|m|saniye|sn|s)\b", s)
    if parts:
        mult = {"saat": 3600, "sa": 3600, "h": 3600, "dakika": 60, "dk": 60, "min": 60, "m": 60}
        return int(sum(float(n.replace(",", ".")) * mult.get(u, 1) for n, u in parts))
    v = num(s)
    return int(v) if v is not None else None


def parse(path) -> list[dict]:
    rows, seen = [], {}
    for r in read_rows(path):
        app, sec = pick(r, APP), seconds(pick(r, DUR))
        if not app or not sec or sec <= 0:
            continue
        raw = pick(r, DATE)
        ms = date_ms(raw[:19].replace("T", " ")) or date_ms(raw[:10])
        key = (ms, app.lower(), pick(r, ("title", "başlık", "document")))
        seen[key] = seen.get(key, 0) + 1
        rows.append({"source": "screentime", "id": sid("ekran", *key, seen[key]), "date_ms": ms, "kind": "ekran",
                     "title": clean(app), "url": None, "body": clean(f"{app} {key[2]} {sec // 60} dk"),
                     "meta": {"seconds": sec, "app": app}})
    return rows


def run(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("screentime", parse(path), con, dry_run, refresh=True)
