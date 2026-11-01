"""Coursera/Udemy ilerleme CSV/JSON (kurs, ilerleme %, tamamlanma tarihi) → items (kind=kurs)."""
from __future__ import annotations

import json
from pathlib import Path

from ._common import clean, ingest_items, parse_iso, sid, text_date
from .bank import date_ms, num, pick, read_rows

COURSE = ("course", "course name", "course_name", "title", "kurs", "kurs adı")
PROG = ("progress", "progress %", "percent_complete", "completion_percentage", "ilerleme", "ilerleme %")
DONE = ("completed", "completion date", "completion_date", "completed_at", "completed on", "tamamlanma tarihi", "tamamlanma")


def _when(s: str) -> int | None:
    return parse_iso(s) or date_ms(s) or text_date(s)


def _records(path: Path) -> list[dict]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), [])
        return [{str(k).lower(): "" if v is None else str(v) for k, v in e.items()} for e in data if isinstance(e, dict)]
    return read_rows(path)


def parse(path, source: str = "coursera") -> list[dict]:
    rows = []
    for r in _records(Path(path)):
        name = pick(r, COURSE)
        if not name:
            continue
        pct = num(pick(r, PROG))
        done_raw = pick(r, DONE)
        flag = done_raw.lower() in ("true", "yes", "evet")
        ms = _when(done_raw) if done_raw and not flag and done_raw.lower() not in ("false", "no", "hayır") else None
        if pct is None and (flag or ms):
            pct = 100.0
        pct = round(pct, 1) if pct is not None else None
        rows.append({"source": source, "id": sid(source, name.lower()), "date_ms": ms, "kind": "kurs",
                     "title": clean(name), "url": pick(r, ("url", "course_url")) or None,
                     "body": clean(f"{name} {'%' + str(pct) if pct is not None else ''}"),
                     "meta": {"progress": pct, "completed": bool(ms) or flag or pct == 100.0}})
    return rows


def run_coursera(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("coursera", parse(path, "coursera"), con, dry_run, refresh=True)


def run_udemy(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("udemy", parse(path, "udemy"), con, dry_run, refresh=True)
