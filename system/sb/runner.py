"""Günlük/haftalık otomatik çalıştırma: adımlar ayrı süreçte (biri çökerse diğerleri sürer), kilit, günlük, özet.

Windows Görev Zamanlayıcı bu modülü çağırır (`sb daily`, `sb weekly`). Tek makine (PC) olduğu için
çift çalışma kilit dosyasıyla engellenir; kilit 6 saatten eskiyse bayat sayılır.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from .config import DATA, SYSTEM, VAULT, accounts

LOCK = DATA / "run.lock"
LOGS = DATA / "logs"
STALE_HOURS = 6

# (ad, sb argümanları, zaman aşımı sn). Sıra önemli: veri çek → kategorile → tarih → kasa notları → bağlantılar.
def mail_steps() -> list[tuple[str, list[str], int]]:
    """accounts.yaml'daki her Gmail (gmail kapsamlı) ve IMAP hesabı için bir 'mail' adımı."""
    try:
        acc = accounts()
    except OSError:
        return []
    steps = [(f"mail {a}", ["mail-fetch", a], 3600) for a, c in (acc.get("google") or {}).items() if "gmail" in (c.get("scopes") or [])]
    steps += [(f"mail {a}@", ["mail-fetch", a], 1800) for a in (acc.get("imap") or {})]
    return steps


DAILY_REST = [
    ("sms/arama", ["sms-sync"], 1800),
    ("mail kategori", ["mail-categorize"], 600),
    ("tarih çıkarma", ["extract-dates", "--days", "14", "--apply"], 3600),
    ("onayladıkların → takvim", ["approve", "--apply"], 600),     # onay-bekleyenler.md'de [x] işaretlediklerin
    ("takvim → kasa", ["sync-gcal"], 900),
    ("arşivleme", ["housekeep", "--apply"], 300),                # süresi geçen/biten işler 90-Arşiv'e
    ("not kutusu", ["inbox-process", "--apply"], 1800),            # 00-Inbox/Dump → ilgili notlar (yerel model)
    ("rehber", ["contacts-sync"], 900),
    ("drive", ["drive-sync"], 5400),
    ("drive notları", ["drive-index"], 900),
    ("bilgisayar dosyaları", ["local-files"], 5400),
    ("belge içerikleri", ["content-sync"], 7200),
    ("projeler", ["projects-sync"], 3600),
    ("proje derleme", ["project-deep", "--all"], 10800),
    ("ders dosyaları", ["course-files"], 900),
    ("ders derleme", ["course-deep", "--all"], 7200),
    ("oturum günlükleri", ["sessions-sync"], 7200),
    ("obs", ["obs-import"], 300),
    ("bağlantılar", ["links"], 900),
    ("mail notları", ["mail-index"], 900),
    ("rehber (SMS bağlantısı)", ["contacts-sync"], 900),
    ("araçlar notu", ["arsenal"], 300),                         # Araçlar ve erişimler.md (doctor + kaynak sayımı)
]


@contextmanager
def lock():
    DATA.mkdir(parents=True, exist_ok=True)
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime > STALE_HOURS * 3600:
        LOCK.unlink()                      # bayat kilit (çöken önceki çalışma)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit(f"Başka bir çalışma sürüyor ({LOCK}); bu çalışma atlandı.")
    with os.fdopen(fd, "w") as f:
        f.write(f"{os.getpid()} {datetime.now():%F %T}")
    try:
        yield
    finally:
        LOCK.unlink(missing_ok=True)


def run_step(name: str, args: list[str], timeout: int, log) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "-X", "utf8", "-m", "sb", *args], cwd=SYSTEM, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        out, rc = (p.stdout or "") + (p.stderr or ""), p.returncode
    except subprocess.TimeoutExpired:
        out, rc = f"zaman aşımı ({timeout} sn)", 124
    dur = time.time() - t0
    lines = [l for l in out.strip().splitlines() if l.strip()]
    tail = " | ".join(lines[-2:]) if lines else ""
    log(f"[{'OK' if rc == 0 else 'HATA'}] {name} ({dur:.0f} sn) rc={rc}\n" + "\n".join("    " + l for l in lines[-12:]))
    return {"name": name, "rc": rc, "tail": tail, "seconds": dur}


def _logger(kind: str):
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / f"{kind}-{datetime.now():%Y%m%d-%H%M}.log"

    def log(msg: str) -> None:
        print(msg, flush=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%H:%M:%S} {msg}\n")
    return log


def git_sync(log) -> str:
    """Kasa değişikliklerini commit + push eder (Obsidian Git ile çakışırsa bir kez daha dener)."""
    def git(*a):
        return subprocess.run(["git", "-C", str(VAULT), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for attempt in range(2):
        git("add", "-A")
        if not git("status", "--porcelain").stdout.strip():
            return "git: değişiklik yok"
        c = git("commit", "-q", "-m", f"otomatik güncelleme {datetime.now():%Y-%m-%d %H:%M}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
        p = git("push", "-q")
        if p.returncode == 0:
            return "git: gönderildi"
        log(f"git push hatası (deneme {attempt + 1}): {(p.stderr or c.stderr).strip()[:200]}")
        git("pull", "--rebase", "-q")
    return "git: gönderilemedi"


def lint_errors() -> int:
    p = subprocess.run([sys.executable, "-X", "utf8", str(SYSTEM / "tools" / "lint.py")], cwd=SYSTEM, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    last = (p.stdout.strip().splitlines() or ["0 hata"])[-1]
    return int(last.split(",")[-1].strip().split()[0]) if "hata" in last else 0


def _deliver(text: str, log) -> None:
    """Özeti mail (varsayılan, şirket SMTP → sadece kullanıcının adresi) ve Telegram bağlıysa Telegram ile gönderir."""
    from . import mailer, telegram
    subject = text.splitlines()[0][:120] if text else "Second Brain"
    try:
        log(f"Mail gönderildi ({mailer.send(subject, text)}) → {', '.join(mailer.settings()['to'])}")
    except BaseException as e:      # SystemExit dahil: teslimat hatası çalışmayı düşürmemeli
        log(f"Mail gönderilemedi: {e}")
    if telegram.chat_id():
        try:
            log(f"Telegram: {telegram.send(text)} mesaj gönderildi")
        except Exception as e:
            log(f"Telegram gönderilemedi: {e}")


def _write_note(title: str, source_id: str, text: str) -> None:
    from .notes import NoteSpec, Vault
    Vault(VAULT).upsert(NoteSpec(
        folder="50-Günlük", title=title,
        frontmatter={"type": "gunluk", "status": "acik", "tags": ["gunluk", "ozet"], "source": "obs", "source_id": source_id,
                     "due": None},
        owned=(), body=f"# {title}\n\n<!-- sb:auto:ozet:start -->\n<!-- sb:auto:ozet:end -->\n", auto={"ozet": text}), date.today())


def fetch_events() -> list[tuple[str, str]] | None:
    """Bugün ve yarının takvim etkinlikleri; okunamazsa None."""
    try:
        from datetime import timedelta
        from .gcal_api import Calendar
        now = datetime.now().astimezone()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        out = []
        for ev in Calendar("main").list_events(start, start + timedelta(days=2)):
            s = ev["start"]
            if "dateTime" in s:
                d = datetime.fromisoformat(s["dateTime"]).astimezone()
                when = f"{'bugün' if d.date() == now.date() else 'yarın'} {d:%H:%M}"
            else:
                when = f"{'bugün' if s['date'] == now.date().isoformat() else 'yarın'} (tüm gün)"
            out.append((when, ev.get("summary", "(başlıksız)")))
        return out
    except Exception:
        return None


MARKER = DATA / "last_daily.txt"


def daily(skip: set[str] | None = None, force: bool = False) -> int:
    from . import digest, maildb, telegram
    log = _logger("daily")
    # Oturum açılışı ve 13:00 tetikleyicileri aynı gün iki kez çalıştırmasın.
    if not force and MARKER.exists() and MARKER.read_text().strip() == date.today().isoformat():
        log("Bugün zaten çalıştı; atlandı (zorlamak için: sb daily --force).")
        return 0
    with lock():
        log(f"günlük çalışma başladı {datetime.now():%F %T}")
        steps = [run_step(n, a, t, log) for n, a, t in mail_steps() + DAILY_REST if not skip or n not in skip]
        try:
            con = maildb.connect(DATA / "mail.db")
            if telegram.chat_id():
                try:
                    n = telegram.pull(con)
                    log(f"Telegram'dan {n} yeni not alındı")
                except Exception as e:
                    log(f"Telegram çekme hatası: {e}")
            text = digest.build_daily(con, VAULT, date.today(), fetch_events(), steps)
        except Exception as e:
            text = f"⚠ Sabah özeti üretilemedi: {e}"
        log(git_sync(log))
        _write_note(f"{date.today():%Y-%m-%d} Özet", f"ozet:{date.today():%Y-%m-%d}", text)
        _deliver(text, log)
        MARKER.write_text(date.today().isoformat())
    return 0 if all(s["rc"] == 0 for s in steps) else 1


def weekly() -> int:
    from . import digest, maildb
    log = _logger("weekly")
    with lock():
        log(f"haftalık çalışma başladı {datetime.now():%F %T}")
        con = maildb.connect(DATA / "mail.db")
        text = digest.build_weekly(con, VAULT, date.today(), lint_errors())
        iso = date.today().isocalendar()
        _write_note(f"{iso[0]}-W{iso[1]:02d} Haftalık", f"hafta:{iso[0]}-W{iso[1]:02d}", text)
        log(git_sync(log))
        _deliver(text, log)
    return 0
