"""`sb today`: tek ekranlık "bugün" özeti ve `GET /api/v2/today` / `GET /api/v2/freshness` JSON'u.

Bölümler: bugünün ve 7 günün teslim/sınav/etkinlikleri (kasa notlarındaki `due`; `brain_today` ile aynı klasörler ve bitmiş durumlar),
bekleyen onaylar (sayı + en eski 3), önemli okunmamış mailler (profildeki önem kategorileri), eskiyen/bayat kaynaklar (en çok 5, ipucuyla),
son başarısız günlük adım. Salt okunur: hiçbir şey yazmaz, ağa çıkmaz (takvim API'si çağrılmaz; takvim etkinlikleri `sync-gcal` ile
kasaya düşmüş notlardan okunur).

`remote=True` (telefon): mail konuları/göndericiler, onay ayrıntıları, dosya adları ve adım çıktıları ÇIKARILIR; yalnız sayılar,
başlıklar ve ipuçları kalır.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from . import approvals, config, freshness
from .notes import SKIP_DIRS, split_note
from .redact import redact

FOLDERS = ("10-Dersler", "30-Kariyer", "20-Projeler")
DONE = ("tamamlandi", "iptal", "arsiv", "kabul", "red", "vazgecildi", "yapildi")     # digest.DONE ile aynı
MAX_STALE = 5
MAX_MAIL = 5
MAX_APPROVALS = 3


def deadlines(vault: Path, today: date, days: int = 7) -> list[dict]:
    """Önümüzdeki `days` günde (bugün dahil) açık notların `due` tarihleri, tarihe göre sıralı."""
    end, rows = today + timedelta(days=days), []
    for folder in FOLDERS:
        base = Path(vault) / folder
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if any(part in SKIP_DIRS for part in p.relative_to(vault).parts[:-1]):
                continue
            try:
                fm = split_note(p.read_text(encoding="utf-8"))[0]
            except (OSError, ValueError):
                continue
            due = fm.get("due")
            t = fm.get("due_time")
            if isinstance(t, int) and not isinstance(t, bool):          # YAML 1.1: 14:00 → 840 (60'lık sayı sistemi)
                t = f"{t // 60:02d}:{t % 60:02d}"
            if isinstance(due, date) and not isinstance(due, datetime) and today <= due <= end and fm.get("status") not in DONE:
                rows.append({"date": due.isoformat(), "time": str(t or ""), "title": p.stem,
                             "type": fm.get("type"), "kind": fm.get("kind"), "status": fm.get("status"),
                             "days_left": (due - today).days})
    rows.sort(key=lambda r: (r["date"], r["time"], r["title"]))
    return rows


def unread_mail(con: sqlite3.Connection, now: datetime, days: int = 7, limit: int = MAX_MAIL) -> dict:
    """Önemli kategorilerdeki okunmamış (Gmail UNREAD etiketli) mailler: sayı + en yeni `limit` tanesi."""
    cats = tuple(config.IMPORTANT_CATEGORIES)
    since = int((now - timedelta(days=days)).timestamp() * 1000)
    q = ("FROM messages WHERE account != 'sms' AND category IN (%s) AND date_ms >= ? AND labels LIKE '%%UNREAD%%' "
         "AND (labels IS NULL OR labels NOT LIKE '%%SENT%%')" % ",".join("?" * len(cats)))
    try:
        total = con.execute("SELECT COUNT(*) " + q, (*cats, since)).fetchone()[0]
        rows = con.execute("SELECT category, subject, from_name, from_addr, date_ms " + q + " ORDER BY date_ms DESC LIMIT ?",
                           (*cats, since, limit)).fetchall()
    except sqlite3.Error:
        return {"count": 0, "items": []}
    by_cat: dict[str, int] = {}
    try:
        for c, n in con.execute("SELECT category, COUNT(*) " + q + " GROUP BY category", (*cats, since)):
            by_cat[c] = n
    except sqlite3.Error:
        pass
    return {"count": total, "by_category": by_cat,
            "items": [{"category": c, "subject": redact(s or "(konusuz)")[:90], "from": redact(n or a or "?")[:40],
                       "date": datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M")} for c, s, n, a, ms in rows]}


def pending_approvals(remote: bool = False) -> dict:
    viewer = approvals.PHONE if remote else None
    recs = sorted(approvals.records(viewer=viewer), key=lambda r: r.get("created", ""))
    oldest = [{"id": r["id"], "kind": r.get("kind"), "title": redact(r.get("title", ""))[:100], "created": r.get("created"),
               **({} if remote else {"detail": redact(r.get("detail", ""))[:140]})} for r in recs[:MAX_APPROVALS]]
    return {"count": len(recs), "oldest": oldest}


def _open_db() -> sqlite3.Connection | None:
    p = Path(config.DATA) / "mail.db"
    if not p.exists():
        return None
    try:
        return sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True, timeout=10)
    except sqlite3.Error:
        return None


def build(now: datetime | None = None, remote: bool = False, vault: Path | None = None) -> dict:
    """`/api/v2/today` gövdesi (aynı zamanda `sb today --json`)."""
    now = now or datetime.now()
    today = now.date()
    rows = deadlines(Path(vault or config.VAULT), today, 7)
    todays = [r for r in rows if r["date"] == today.isoformat()]
    con = _open_db()
    try:
        mail = unread_mail(con, now) if con else {"count": 0, "items": []}
    finally:
        if con:
            con.close()
    if remote:
        mail = {"count": mail["count"], "by_category": mail.get("by_category", {}), "items": []}
    fr = freshness.status(now.astimezone())
    stale = [{k: s[k] for k in ("source", "name", "state", "age_days", "threshold_days", "hint", "mode")}
             for s in fr["sources"] if s["state"] in ("bayat", "eskiyor")]
    failed = freshness.last_failed_step()
    if failed and remote:
        failed = {"name": failed["name"], "ts": failed["ts"], "rc": failed["rc"]}
    return {"generated": now.astimezone().isoformat(timespec="seconds"), "date": today.isoformat(), "remote": remote,
            "deadlines": {"today": todays, "week": rows},
            "approvals": pending_approvals(remote),
            "mail": mail,
            "stale_sources": {"total": len(stale), "items": stale[:MAX_STALE]},
            "last_failed_step": failed}


def render(t: dict) -> str:
    """Tek ekranlık metin."""
    d = t["deadlines"]
    out = [f"BUGÜN — {t['date']}", ""]
    out.append(f"Teslim / sınav / etkinlik: bugün {len(d['today'])}, 7 gün {len(d['week'])}")
    for r in d["week"][:10]:
        mark = "BUGÜN" if r["days_left"] == 0 else f"{r['days_left']} gün"
        out.append(f"  • {r['date'][5:]} {r['time']:5} {r['title']} ({r['type']}) — {mark}")
    if len(d["week"]) > 10:
        out.append(f"  … ve {len(d['week']) - 10} tane daha")
    if not d["week"]:
        out.append("  • yok")
    a = t["approvals"]
    out += ["", f"Bekleyen onay: {a['count']}"]
    for r in a["oldest"]:
        out.append(f"  • [{r['kind']}] {r['title']} ({str(r.get('created', ''))[:10]})")
    m = t["mail"]
    out += ["", f"Önemli okunmamış mail (7 gün): {m['count']}"]
    for r in m["items"]:
        out.append(f"  • [{r['category']}] {r['subject']} — {r['from']}")
    s = t["stale_sources"]
    out += ["", f"Eskiyen kaynak: {s['total']}" + (f" (ilk {len(s['items'])} gösteriliyor)" if s["total"] > len(s["items"]) else "")]
    for r in s["items"]:
        out.append(f"  • {r['name']['tr']}: {r['age_days']:g} gün ({r['state']}, eşik {r['threshold_days']}) → {r['hint']['tr']}")
    f = t["last_failed_step"]
    out += ["", "Son başarısız günlük adım: " + (f"{f['name']} ({str(f['ts'])[:16].replace('T', ' ')})" + (f" — {f['tail'][:100]}" if f.get("tail") else "") if f else "yok")]
    return "\n".join(out)


def cli(args) -> int:
    t = build()
    print(json.dumps(t, ensure_ascii=False, indent=1) if args.json else render(t))
    return 0
