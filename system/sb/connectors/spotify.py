"""Spotify 'Extended streaming history' ve kısa 'StreamingHistory' (.json ya da klasör) → items (source=spotify)."""
from __future__ import annotations

import json
from pathlib import Path

from ._common import clean, ingest_items, parse_iso, sid

MIN_MS = 30_000


def _files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(p for p in path.glob("*.json") if "streaminghistory" in p.name.lower().replace("_", ""))
    return [path]


def parse(path) -> list[dict]:
    rows = []
    for f in _files(Path(path)):
        for e in json.loads(f.read_text(encoding="utf-8-sig")):
            if "master_metadata_track_name" in e:
                track, artist = e.get("master_metadata_track_name"), e.get("master_metadata_album_artist_name")
                album, played = e.get("master_metadata_album_album_name"), e.get("ms_played") or 0
                when, uri = e.get("ts", ""), e.get("spotify_track_uri") or ""
            else:
                track, artist, album = e.get("trackName"), e.get("artistName"), None
                played, when, uri = e.get("msPlayed") or 0, e.get("endTime", ""), ""
            if not track or played < MIN_MS:
                continue
            ms = parse_iso(when.replace(" ", "T"))
            url = f"https://open.spotify.com/track/{uri.rsplit(':', 1)[-1]}" if uri.startswith("spotify:track:") else None
            rows.append({"source": "spotify", "id": sid(when, uri or artist, track, played), "date_ms": ms,
                         "kind": "play", "title": clean(track), "url": url,
                         "body": clean(f"{track} {artist or ''} {album or ''}"),
                         "meta": {"artist": artist, "album": album, "ms": played}})
    return rows


def run(path, con, dry_run: bool = False, **_) -> dict:
    return ingest_items("spotify", parse(path), con, dry_run)
