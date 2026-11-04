"""Dışa aktarım dosyalarından içe aktaran bağlayıcılar (WhatsApp, Telegram, Kindle, YouTube, Spotify, tarayıcı, RSS, akademik).

Her modül: parse(path) -> list[dict] (saf) ve run(path, con, dry_run=False, **seçenek) -> {"kaynak", "okunan", "yeni", ...}.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from . import academic, browser, kindle, rss, spotify, telegram, whatsapp, youtube
from . import clipboardline, nashi, spotify_tech
from . import bank, discord, learning, notes, notion, places, reading, screentime, slack, social, tasks_import

REGISTRY = {
    # Faz 4c (kaynak adı açıkça verilir: sb import <kaynak> <dosya|klasör>)
    "discord": discord.run, "slack": slack.run, "notion": notion.run,
    "keep": notes.run_keep, "apple-notlar": notes.run_apple, "onenote": notes.run_onenote, "evernote": notes.run_evernote,
    "instagram": social.run_instagram, "x": social.run_x,
    "todoist": tasks_import.run, "ticktick": tasks_import.run, "mstodo": tasks_import.run, "trello": tasks_import.run,
    "jira": tasks_import.run, "linear": tasks_import.run,
    "pocket": reading.run_pocket, "raindrop": reading.run_raindrop,
    "gphotos": places.run_photos, "gmaps": places.run_maps, "bank": bank.run,
    "coursera": learning.run_coursera, "udemy": learning.run_udemy, "screentime": screentime.run,
    "whatsapp": whatsapp.run,
    "clipboardline": clipboardline.run, "nashi": nashi.run,       # sb 0.11: hazır uygulamalar (yol = uygulamanın veri klasörü; sb apps sync)
    "telegram": telegram.run,
    "kindle": kindle.run,
    "youtube": youtube.run,
    "spotify": spotify.run,
    "spotify-teknik": spotify_tech.run,                       # my_spotify_data.zip (Technical Log Information)
    "browser": browser.run,
    "rss": rss.run,
    "arxiv": academic.run_arxiv,
    "zotero": academic.run,
    "bibtex": academic.run,
}
NO_PATH = {"rss", "arxiv"}
_WA_LINE = re.compile(r"^\[?\d{1,2}[./]\d{1,2}[./]\d{2,4},?\s+\d{1,2}:\d{2}", re.M)


def _head(path: Path, n: int = 20000) -> str:
    with path.open("rb") as f:
        return f.read(n).decode("utf-8-sig", "replace")


def detect(path) -> str | None:
    """Dosya adı ve içeriğe göre kaynak tahmini; bilinmiyorsa None."""
    p = Path(path)
    name = p.name.lower()
    if p.is_dir():
        if spotify_tech.is_tech_pack(p):
            return "spotify-teknik"
        return "spotify" if any("streaminghistory" in x.name.lower().replace("_", "") for x in p.glob("*.json")) else None
    if not p.exists():
        return None
    ext = p.suffix.lower()
    if ext == ".zip":
        if spotify_tech.is_tech_pack(p):
            return "spotify-teknik"
        try:
            with zipfile.ZipFile(p) as z:
                return "whatsapp" if any(n.lower().endswith(".txt") for n in z.namelist()) else None
        except zipfile.BadZipFile:
            return None
    if "clippings" in name:
        return "kindle"
    if "watch-history" in name or "subscriptions" in name and ext == ".csv":
        return "youtube"
    if "streaminghistory" in name.replace("_", ""):
        return "spotify"
    if name in ("history", "bookmarks") or name == "places.sqlite":
        return "browser"
    if name == "zotero.sqlite":
        return "zotero"
    if ext == ".bib":
        return "bibtex"
    if ext == ".txt":
        h = _head(p)
        if "==========" in h:
            return "kindle"
        return "whatsapp" if _WA_LINE.search(h.replace("‎", "")) else None
    if ext == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
        except ValueError:
            return None
        if isinstance(data, dict):
            if "roots" in data:
                return "browser"
            if "chats" in data or "messages" in data:
                return "telegram"
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            if "titleUrl" in data[0] or "header" in data[0]:
                return "youtube"
            if {"ts", "endTime"} & data[0].keys():
                return "spotify"
    if ext in (".html", ".htm") and "youtube" in _head(p).lower():
        return "youtube"
    if ext in (".sqlite", ".db", "") and p.is_file() and _head(p, 16).startswith("SQLite format"):
        return "browser"
    return None


def format_result(r: dict, dry_run: bool) -> str:
    if r.get("not"):
        return f"{r['kaynak']}: {r['not']}"
    s = f"{r['kaynak']}: okunan {r['okunan']}, " + (f"yeni olacak {r['yeni']}" if dry_run else f"yeni {r['yeni']}")
    if r.get("tarih_min"):
        s += f"\n  tarih aralığı: {r['tarih_min']} … {r['tarih_max']}"
    if r.get("ornek"):
        s += "\n  örnek başlıklar: " + " | ".join(r["ornek"])
    return s + ("\n  (dry-run: hiçbir şey yazılmadı)" if dry_run else "")


def cli(args) -> int:
    from .. import maildb
    from ..config import MAIL_DB
    if args.source == "browser" and args.discover:
        found = browser.discover()
        for d in found:
            print(f"{d['tarayici']:8} {d['profil']:12} {d['tur']:15} {d['boyut'] // 1024:>8} KB  {d['yol']}")
        print(f"{len(found)} dosya bulundu" if found else "tarayıcı profili bulunamadı")
        return 0
    name = args.source
    if name == "auto":
        if not args.path:
            print("auto için yol gerekli")
            return 1
        name = detect(args.path)
        if not name:
            print(f"kaynak anlaşılamadı: {args.path}")
            return 1
        print(f"algılanan kaynak: {name}")
    if name not in REGISTRY:
        print(f"bilinmeyen kaynak: {name} (seçenekler: auto, {', '.join(REGISTRY)})")
        return 1
    if name not in NO_PATH and not args.path:
        print(f"{name} için yol gerekli")
        return 1
    if args.path and not Path(args.path).exists():
        print(f"bulunamadı: {args.path}")
        return 1
    con = maildb.connect(MAIL_DB if not args.dry_run or MAIL_DB.exists() else Path(":memory:"))
    try:
        r = REGISTRY[name](args.path, con, dry_run=args.dry_run, me=args.me, days=args.days)
    except (ValueError, OSError) as e:
        print(f"{name}: okunamadı — {e}")
        return 1
    finally:
        con.close()
    print(format_result(r, args.dry_run))
    return 0
