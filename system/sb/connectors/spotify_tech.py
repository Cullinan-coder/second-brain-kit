"""Spotify "Technical Log Information" paketi (my_spotify_data.zip) → müzik zevki kayıtları + özet notu.

Paket çoğunlukla cihaz/ağ/önbellek günlüğüdür; bunlar ALINMAZ (cihaz modeli, IP, oturum kimliği yok).
Alınanlar (source=spotify):
  search    SearchViewResponse      → arama sorguları
  save      AddedToCollection       → beğenilenlere eklenen şarkılar
  repeat    OnRepeatContents        → "Tekrar tekrar" listesi anlık görüntüleri
  daylist   DaylistGenerated        → günlük liste başlığı (ruh hâli/tür etiketi)
  lyrics    MinimumLyricsCharactersSeen → sözüne bakılan şarkılar
  dj / radar DJTrackServed, ReleaseRadarServedRecs → önerilen şarkılar (yalnız özette, kayıt değil)
Şarkı/sanatçı kimlikleri Spotify bağlıysa Web API ile ada çevrilir (önbellek: <data>/spotify_names.json).
"""
from __future__ import annotations

import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ._common import clean, ingest_items, sid

FILES = ("SearchViewResponse", "AddedToCollection", "OnRepeatContents", "DaylistGenerated",
         "MinimumLyricsCharactersSeen", "DJTrackServed", "ReleaseRadarServedRecs")
_TAG = re.compile(r"<[^>]+>")


def is_tech_pack(path) -> bool:
    p = Path(path)
    try:
        if p.is_dir():
            return any(p.rglob("ReadMeFirst_TechnicalLogInformation.pdf")) or any(p.rglob("OnRepeatContents.json"))
        with zipfile.ZipFile(p) as z:
            return any(n.endswith(("ReadMeFirst_TechnicalLogInformation.pdf", "OnRepeatContents.json")) for n in z.namelist())
    except (OSError, zipfile.BadZipFile):
        return False


def _load(path) -> dict[str, list]:
    out: dict[str, list] = {}
    p = Path(path)
    if p.is_dir():
        for name in FILES:
            for f in p.rglob(f"{name}.json"):
                out.setdefault(name, []).extend(json.loads(f.read_text(encoding="utf-8-sig")))
        return out
    with zipfile.ZipFile(p) as z:
        for info in z.infolist():
            stem = Path(info.filename).stem
            if stem in FILES and info.file_size < 200 * 1024 * 1024:
                out.setdefault(stem, []).extend(json.loads(z.read(info).decode("utf-8-sig")))
    return out


def _ms(e: dict) -> int | None:
    t = e.get("context_time") or e.get("message_timestamp")
    return int(t) if isinstance(t, (int, float)) else None


def _tid(uri: str | None) -> str | None:
    return uri.rsplit(":", 1)[-1] if isinstance(uri, str) and uri.startswith("spotify:track:") else None


def final_searches(events: list[dict], gap_ms: int = 90_000) -> list[tuple[str, int | None]]:
    """Yazarken her harfte bir olay düşer ("Kib", "Kibri", "Kibrit"); her dizinin yalnız son hâli tutulur.
    Dizi: art arda, aralarında ≤ gap_ms olan ve biri ötekinin önekini paylaşan sorgular."""
    qs = sorted(((e.get("message_query") or "").strip(), _ms(e) or 0) for e in events)
    qs = sorted((x for x in qs if x[0]), key=lambda x: x[1])
    out: list[tuple[str, int]] = []
    for q, ms in qs:
        if out:
            pq, pms = out[-1]
            a, b = pq.lower(), q.lower()
            if ms - pms <= gap_ms and (b.startswith(a) or a.startswith(b) or a[:3] == b[:3]):
                out[-1] = (q if len(b) >= len(a) else pq, ms)
                continue
        out.append((q, ms))
    return [(q, ms or None) for q, ms in out if len(q) >= 3]


def parse(path) -> tuple[list[dict], dict]:
    """(kayıtlar, özet verisi) döner. Kayıtlarda yalnız müzik bilgisi; cihaz/ağ alanları atılır."""
    d = _load(path)
    rows: list[dict] = []
    stats = {"searches": Counter(), "saved": [], "repeat": Counter(), "daylists": [], "lyrics": Counter(),
             "dj": Counter(), "radar": Counter(), "search_list": [], "first_ms": None, "last_ms": None}

    def add(kind, ms, title, body, meta, *key):
        rows.append({"source": "spotify", "id": sid("tech", kind, *key), "date_ms": ms, "kind": kind,
                     "title": clean(title)[:200], "url": meta.get("url"), "body": clean(body)[:2000], "meta": meta})
        if ms:
            stats["first_ms"] = min(ms, stats["first_ms"] or ms)
            stats["last_ms"] = max(ms, stats["last_ms"] or ms)

    for q, ms in final_searches(d.get("SearchViewResponse", [])):
        stats["searches"][q.lower()] += 1
        stats["search_list"].append((q, ms))
        add("search", ms, f"Spotify araması: {q}", q, {"query": q}, q.lower(), ms)
    for e in d.get("AddedToCollection", []):
        t = _tid(e.get("message_item_uri"))
        if t and t not in {x for x, _ in stats["saved"]}:
            stats["saved"].append((t, _ms(e)))
            add("save", _ms(e), "Beğenilenlere eklendi", t, {"track_id": t, "url": f"https://open.spotify.com/track/{t}"}, t, _ms(e))
    for e in d.get("OnRepeatContents", []):
        ids = [x for x in (_tid(u) for u in e.get("message_contents") or []) if x]
        for t in ids:
            stats["repeat"][t] += 1
        if ids:
            add("repeat", _ms(e), "Tekrar tekrar listesi", " ".join(ids), {"track_ids": ids}, _ms(e))
    for e in d.get("DaylistGenerated", []):
        title = e.get("message_playlist_title") or ""
        desc = _TAG.sub("", e.get("message_playlist_description") or "")
        if title:
            stats["daylists"].append((title, _ms(e)))
            add("daylist", _ms(e), f"Günlük liste: {title}", f"{title}. {desc}", {"title": title}, title, _ms(e))
    for e in d.get("MinimumLyricsCharactersSeen", []):
        t = _tid(e.get("message_track_uri"))
        if t:
            stats["lyrics"][t] += 1
    for t, n in stats["lyrics"].items():
        add("lyrics", None, "Sözlerine bakıldı", t, {"track_id": t, "count": n,
                                                     "url": f"https://open.spotify.com/track/{t}"}, t)
    for e in d.get("DJTrackServed", []):
        t = _tid(e.get("message_track_uri"))
        if t:
            stats["dj"][t] += 1
    for e in d.get("ReleaseRadarServedRecs", []):
        for t in (_tid(u) for u in e.get("message_track_uris") or []):
            if t:
                stats["radar"][t] += 1
    return rows, stats


# --- ad çözümleme (isteğe bağlı, Spotify bağlıysa) ---

def _cache_path() -> Path:
    from ..config import DATA
    return Path(DATA) / "spotify_names.json"


def _local_names(con, ids: list[str]) -> dict[str, dict]:
    """Daha önce içe aktarılmış tam dinleme geçmişinden (kind=play, url .../track/<id>) ad bul — ağsız."""
    out: dict[str, dict] = {}
    if con is None:
        return out
    for t in ids:
        row = con.execute("SELECT title, meta FROM items WHERE source='spotify' AND kind='play' AND url = ? LIMIT 1",
                          (f"https://open.spotify.com/track/{t}",)).fetchone()
        if row:
            try:
                artist = (json.loads(row[1] or "{}") or {}).get("artist") or ""
            except ValueError:
                artist = ""
            out[t] = {"name": row[0], "artist": artist}
    return out


def resolve_names(ids: list[str], con=None, max_api: int = 150) -> dict[str, dict]:
    """track_id → {name, artist}: önbellek → yerel dinleme geçmişi → Spotify Web API (tek tek; toplu /tracks
    yeni uygulamalara 403). Bağlı değilse ya da hata olursa elde olanla döner."""
    cache_file = _cache_path()
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    todo = [i for i in dict.fromkeys(ids) if i not in cache]
    cache.update(_local_names(con, todo))
    todo = [i for i in todo if i not in cache][:max_api]
    if todo:
        try:
            from .. import spotify_api
            if spotify_api.ready():
                for t in todo:
                    tr = spotify_api._api("GET", f"/tracks/{t}")
                    if tr and tr.get("id"):
                        cache[t] = {"name": tr.get("name"),
                                    "artist": ", ".join(a.get("name", "") for a in tr.get("artists") or [])}
        except Exception as e:                                  # ağ/kimlik/kota hatası: ad olmadan devam
            print(f"  Spotify adlarının bir kısmı alınamadı: {type(e).__name__}")
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return cache


def _label(t: str, names: dict) -> str:
    n = names.get(t)
    return f"{n['name']} — {n['artist']}" if n and n.get("name") else f"spotify:track:{t}"


def _day(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d") if ms else "?"


def summary_note(stats: dict, names: dict, today: str) -> str:
    lines = ["---", "type: kaynak", "status: aktif", "tags: [spotify, muzik]", "source: spotify",
             "source_id: spotify:technical-log", f"created: {today}", f"updated: {today}", "due: null", "---",
             "# Spotify müzik zevki (teknik günlük paketi)", "",
             f"Kaynak: Spotify \"Technical Log Information\" paketi · kapsam {_day(stats['first_ms'])} → {_day(stats['last_ms'])}.",
             "Cihaz, ağ ve önbellek günlükleri alınmadı; yalnız müzik bilgisi. Tam dinleme geçmişi için bkz. [[Dinleme geçmişi]].", ""]

    def section(title, items):
        if items:
            lines.extend([f"## {title}", "", *items, ""])

    section("Son dönemde tekrar tekrar dinlenenler",
            [f"{i}. {_label(t, names)} ({n} listede)" for i, (t, n) in enumerate(stats["repeat"].most_common(25), 1)])
    section("Beğenilenlere eklenenler",
            [f"- {_day(ms)} · {_label(t, names)}" for t, ms in sorted(stats["saved"], key=lambda x: x[1] or 0, reverse=True)])
    section("Sözlerine en çok bakılanlar",
            [f"{i}. {_label(t, names)} ({n} kez)" for i, (t, n) in enumerate(stats["lyrics"].most_common(15), 1)])
    rep = [f"{i}. {q} ({n} kez)" for i, (q, n) in enumerate(stats["searches"].most_common(15), 1) if n > 1]
    section("En çok aranan", rep)
    section("Son aramalar", [f"- {_day(ms)} · {q}" for q, ms in sorted(stats["search_list"], key=lambda x: x[1] or 0, reverse=True)[:40]])
    section("Spotify'ın senin için ürettiği günlük listeler (ruh hâli/tür)",
            [f"- {_day(ms)} · {t}" for t, ms in sorted(stats["daylists"], key=lambda x: x[1] or 0, reverse=True)])
    section("DJ'in en çok çaldığı (öneri)",
            [f"{i}. {_label(t, names)}" for i, (t, _) in enumerate(stats["dj"].most_common(10), 1)])
    return "\n".join(lines).rstrip() + "\n"


def run(path, con, dry_run: bool = False, vault: Path | None = None, **_) -> dict:
    rows, stats = parse(path)
    ids = [t for t, _ in stats["repeat"].most_common(25)] + [t for t, _ in stats["saved"]] + \
          [t for t, _ in stats["lyrics"].most_common(15)] + [t for t, _ in stats["dj"].most_common(10)]
    names = {} if dry_run else resolve_names(ids, con)
    for r in rows:                                               # başlıklara şarkı adını yaz (aranabilir olsun)
        t = (r.get("meta") or {}).get("track_id")
        if t and names.get(t):
            r["title"] = clean(f"{r['title']}: {_label(t, names)}")[:200]
            r["body"] = clean(f"{_label(t, names)} {r['body']}")
    res = ingest_items("spotify", rows, con, dry_run, refresh=True)
    if not dry_run:
        from ..config import VAULT
        v = Path(vault or VAULT)
        note = v / "40-Kaynaklar" / "Spotify" / "Müzik zevki.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(summary_note(stats, names, datetime.now().strftime("%Y-%m-%d")), encoding="utf-8")
        res["not"] = str(note)
    res["adlandirilan"] = sum(1 for t in set(ids) if names.get(t))
    return res
