"""Sabah özeti ve haftalık denetim metinleri (yapay zekasız, deterministik ve ucuz).

`build_daily` saf bir fonksiyondur: veritabanı, kasa yolu ve (isteğe bağlı) takvim etkinlikleri verilir, metin döner.
"""
from __future__ import annotations

import sqlite3
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from .notes import SKIP_DIRS, split_note
from .redact import redact
from .config import IMPORTANT_CATEGORIES, USER

IMPORTANT = IMPORTANT_CATEGORIES
DONE = ("tamamlandi", "iptal", "arsiv", "kabul", "red", "vazgecildi", "yapildi")
DAYS_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
MONTHS_TR = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


def _notes(vault: Path, folder: str):
    base = vault / folder
    if not base.is_dir():
        return
    for p in sorted(base.rglob("*.md")):
        if not any(part in SKIP_DIRS for part in p.relative_to(vault).parts[:-1]):
            yield p, split_note(p.read_text(encoding="utf-8"))[0]


def upcoming(vault: Path, today: date, days: int = 7) -> list[str]:
    end, rows = today + timedelta(days=days), []
    for folder in ("10-Dersler", "30-Kariyer", "20-Projeler"):
        for p, fm in _notes(vault, folder):
            due = fm.get("due")
            if isinstance(due, date) and today <= due <= end and fm.get("status") not in DONE:
                rows.append((due, f"• {due:%d.%m} {fm.get('due_time') or ''} {p.stem} ({fm.get('type')})".replace("  ", " ")))
    return [r[1] for r in sorted(rows)]


def pending(vault: Path) -> list[str]:
    p = vault / "00-Inbox" / "onay-bekleyenler.md"
    return [l[6:].strip() for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("- [ ]")] if p.exists() else []


def project_activity(vault: Path, since: date) -> list[str]:
    out = []
    for p, fm in _notes(vault, "20-Projeler"):
        la = fm.get("last_activity")
        if isinstance(la, date) and la >= since:
            out.append(f"• {p.stem} (son etkinlik {la:%d.%m})")
    return out


def assistant_report(hours: int = 26) -> list[str]:
    """Asistanın (Qwen) ve günlük kuralların kasada yaptığı değişiklikler — 'dün ne yaptım'."""
    from . import vault_ops
    entries = [e for e in vault_ops.recent(hours) if e["actor"] != "claude"]
    if not entries:
        return ["🤖 Asistan: dün kasada değişiklik yapmadı"]
    who = {"asistan": "asistan", "kural": "otomatik", "kullanici": "sen", "onay": "senin onayınla", "inbox": "not kutusu"}
    lines = [f"🤖 Asistan dün {len(entries)} değişiklik yaptı (geri almak için asistana 'geri al' de)"]
    for e in entries[-10:]:
        name = e["path"].rsplit("/", 1)[-1].removesuffix(".md") or "—"
        lines.append(f"• [{who.get(e['actor'], e['actor'])}] {e['action']}: {name} — {e['detail'][:90]}")
    return lines


def build_daily(con: sqlite3.Connection, vault: Path, today: date, events: list[tuple[str, str]] | None,
                steps: list[dict] | None = None, now: datetime | None = None) -> str:
    now = now or datetime.now()
    since_ms = int((now - timedelta(hours=26)).timestamp() * 1000)
    head = f"☀️ Günaydın {USER} — {DAYS_TR[today.weekday()]}, {today.day} {MONTHS_TR[today.month]}"
    out = [head, ""]

    out.append("📅 Takvim (bugün ve yarın)")
    if events is None:
        out.append("• takvim okunamadı")
    else:
        out += [f"• {when} {title}" for when, title in events] or ["• etkinlik yok"]

    up = upcoming(vault, today, 7)
    out += ["", "⏰ 7 gün içindeki teslim/sınav/başvuru"] + (up[:12] or ["• yok"])

    pend = pending(vault)
    if pend:
        out += ["", f"❓ Onayını bekleyen {len(pend)} takvim adayı (00-Inbox/onay-bekleyenler.md)"] + [f"• {x[:110]}" for x in pend[:4]]

    out += ["", *assistant_report()]

    rows = con.execute(
        "SELECT category, subject, from_name, from_addr FROM messages WHERE date_ms >= ? AND account != 'sms' "
        "AND category NOT IN ('gonderilen') ORDER BY date_ms DESC", (since_ms,)).fetchall()
    cats = Counter(r[0] for r in rows)
    out += ["", f"✉️ Yeni mail: {len(rows)}" + (" (" + ", ".join(f"{k} {v}" for k, v in sorted(cats.items(), key=lambda kv: (-kv[1], kv[0]))[:5]) + ")" if rows else "")]
    for cat, subj, name, addr in [r for r in rows if r[0] in IMPORTANT][:6]:
        out.append(f"• [{cat}] {(subj or '(konusuz)')[:70]} — {(name or addr or '?')[:25]}")

    n_sms = con.execute("SELECT COUNT(*) FROM messages WHERE account = 'sms' AND date_ms >= ?", (since_ms,)).fetchone()[0]
    missed = con.execute("SELECT COUNT(*) FROM calls WHERE type = 3 AND date_ms >= ?", (since_ms,)).fetchone()[0]
    out += ["", f"📱 Yeni SMS: {n_sms} · cevapsız arama: {missed}"]

    act = project_activity(vault, today - timedelta(days=1))
    if act:
        out += ["", "🛠 Projelerde hareket"] + act[:8]

    if steps is not None:
        bad = [s for s in steps if s["rc"] != 0]
        out += ["", f"⚙️ Güncelleme: {len(steps) - len(bad)}/{len(steps)} adım tamam"]
        for s in bad:
            out.append(f"⚠ {s['name']}: {s['tail'][:140]}")
            if "invalid_grant" in s["tail"] or "RefreshError" in s["tail"]:
                out.append("   → Google girişi düşmüş: uv run --directory ...\\_system python -m sb login main|side")
    return redact("\n".join(out))


def build_weekly(con: sqlite3.Connection, vault: Path, today: date, lint_errors: int, steps_note: str = "") -> str:
    out = [f"📋 Haftalık özet — {today:%d.%m.%Y}", ""]
    week_ms = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
    n_mail = con.execute("SELECT COUNT(*) FROM messages WHERE date_ms >= ? AND account != 'sms'", (week_ms,)).fetchone()[0]
    n_sms = con.execute("SELECT COUNT(*) FROM messages WHERE date_ms >= ? AND account = 'sms'", (week_ms,)).fetchone()[0]
    out.append(f"Bu hafta: {n_mail} mail, {n_sms} SMS.")
    act = project_activity(vault, today - timedelta(days=7))
    out += ["", f"🛠 Bu hafta hareket gören proje: {len(act)}"] + act[:12]
    stale = []
    for p, fm in _notes(vault, "20-Projeler"):
        la = fm.get("last_activity")
        if fm.get("status") == "aktif" and isinstance(la, date) and (today - la).days > 30:
            stale.append(f"• {p.stem}: {(today - la).days} gündür dokunulmadı ama 'aktif'")
    if stale:
        out += ["", "🕸 Eskimiş 'aktif' projeler (durumu güncelle ya da beklemeye al)"] + stale
    up = upcoming(vault, today, 14)
    out += ["", "📆 Önümüzdeki 14 gün"] + (up[:15] or ["• yok"])
    pend = pending(vault)
    out += ["", f"❓ Onay bekleyen: {len(pend)}"]
    out += ["", f"🧹 Kasa denetimi: {'temiz' if lint_errors == 0 else f'{lint_errors} hata (lint çalıştır)'}"]
    if steps_note:
        out += ["", steps_note]
    return redact("\n".join(out))
