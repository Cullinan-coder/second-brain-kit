"""Google Fotoğraflar yan dosyaları (gphotos) ve Haritalar zaman çizelgesi (gmaps) → items. Fotoğraf dosyası okunmaz."""
from __future__ import annotations

import json
import re
from pathlib import Path

from ._common import clean, ingest_items, parse_iso, sid


def _json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError):
        return None


def _files(path) -> list[Path]:
    p = Path(path)
    return sorted(p.rglob("*.json")) if p.is_dir() else [p]


def _e7(v) -> float | None:
    return round(v / 1e7, 6) if isinstance(v, (int, float)) else None


def _latlng(s: str) -> tuple[float | None, float | None]:
    m = re.findall(r"-?\d+(?:\.\d+)?", s or "")
    return (float(m[0]), float(m[1])) if len(m) >= 2 else (None, None)


# ---- Google Fotoğraflar
def parse_photos(path) -> list[dict]:
    rows = []
    for f in _files(path):
        d = _json(f)
        if not isinstance(d, dict) or "photoTakenTime" not in d:
            continue
        ts = d["photoTakenTime"].get("timestamp")
        ms = int(ts) * 1000 if ts and str(ts).isdigit() else None
        g = d.get("geoData") or {}
        lat, lng = g.get("latitude"), g.get("longitude")
        has_geo = bool(lat or lng)
        title = d.get("title") or f.stem
        rows.append({"source": "gphotos", "id": sid("foto", title, ts), "date_ms": ms, "kind": "foto",
                     "title": clean(title), "url": None, "body": clean(f"{title} {d.get('description', '')}"),
                     "meta": {"lat": lat if has_geo else None, "lng": lng if has_geo else None}})
    return rows


# ---- Google Haritalar
def _visit(o: dict) -> dict | None:
    pv = o.get("placeVisit")
    if not pv:
        return None
    loc, dur = pv.get("location") or {}, pv.get("duration") or {}
    a, b = parse_iso(dur.get("startTimestamp", "")), parse_iso(dur.get("endTimestamp", ""))
    name = loc.get("name") or loc.get("address") or "Bilinmeyen yer"
    return _place(a, b, name, _e7(loc.get("latitudeE7")), _e7(loc.get("longitudeE7")), loc.get("address"))


def _segment(o: dict) -> dict | None:
    seg = o.get("activitySegment")
    if not seg:
        return None
    dur = seg.get("duration") or {}
    a, b = parse_iso(dur.get("startTimestamp", "")), parse_iso(dur.get("endTimestamp", ""))
    return _move(a, b, seg.get("activityType") or "HAREKET", seg.get("distance"))


def _place(a, b, name, lat, lng, addr=None) -> dict:
    mins = round((b - a) / 60000) if a and b and b >= a else None
    return {"source": "gmaps", "id": sid("ziyaret", a, name), "date_ms": a, "kind": "ziyaret", "title": clean(name),
            "url": None, "body": clean(f"{name} {addr or ''} {mins or ''} dk"),
            "meta": {"lat": lat, "lng": lng, "minutes": mins}}


def _move(a, b, kind, dist) -> dict:
    mins = round((b - a) / 60000) if a and b and b >= a else None
    return {"source": "gmaps", "id": sid("hareket", a, kind, dist), "date_ms": a, "kind": "hareket", "title": clean(kind.lower()),
            "url": None, "body": clean(f"{kind.lower()} {dist or ''} m {mins or ''} dk"),
            "meta": {"meters": dist, "minutes": mins}}


def _timeline(d: dict) -> list[dict]:
    rows = []
    for s in d.get("semanticSegments", []):
        a, b = parse_iso(s.get("startTime", "")), parse_iso(s.get("endTime", ""))
        if "visit" in s:
            top = s["visit"].get("topCandidate") or {}
            lat, lng = _latlng((top.get("placeLocation") or {}).get("latLng", ""))
            rows.append(_place(a, b, top.get("semanticType") or top.get("placeId") or "Ziyaret", lat, lng))
        elif "activity" in s:
            act = s["activity"]
            rows.append(_move(a, b, (act.get("topCandidate") or {}).get("type") or "HAREKET", act.get("distanceMeters")))
    return rows


def _records(d: dict) -> list[dict]:
    """Ham nokta kayıtları (Records.json): gün başına tek özet satırı."""
    days: dict[str, list] = {}
    for loc in d.get("locations", []):
        t = loc.get("timestamp") or ""
        if t:
            days.setdefault(t[:10], []).append(loc)
    rows = []
    for day, pts in sorted(days.items()):
        ms = parse_iso(day + "T00:00:00Z")
        first = pts[0]
        rows.append({"source": "gmaps", "id": sid("gun", day), "date_ms": ms, "kind": "gun-ozeti", "title": f"Konum kayıtları {day}",
                     "url": None, "body": f"{len(pts)} konum noktası {day}",
                     "meta": {"points": len(pts), "lat": _e7(first.get("latitudeE7")), "lng": _e7(first.get("longitudeE7"))}})
    return rows


def parse_maps(path) -> list[dict]:
    rows = []
    for f in _files(path):
        d = _json(f)
        if not isinstance(d, dict):
            continue
        for o in d.get("timelineObjects", []):
            r = _visit(o) or _segment(o)
            if r:
                rows.append(r)
        rows += _timeline(d)
        rows += _records(d)
    return rows


def run_photos(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("gphotos", parse_photos(path), con, dry_run)


def run_maps(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("gmaps", parse_maps(path), con, dry_run)
