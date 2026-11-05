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
    from . import features
    steps = [(f"mail {a}", ["mail-fetch", a], 3600) for a, c in (acc.get("google") or {}).items()
             if "gmail" in (c.get("scopes") or []) and features.enabled("gmail")]
    steps += [(f"mail {a}@", ["mail-fetch", a], 1800) for a in (acc.get("imap") or {}) if features.enabled("imap")]
    return steps


DAILY_REST = [
    ("sms/arama", ["sms-sync"], 1800),
    ("içe aktarma klasörü", ["import-inbox"], 3600),          # 00-Inbox/İçe aktar: yeni dışa aktarma dosyaları (asistan açıkken 10 dk'da bir de bakar)
    ("mail kategori", ["mail-categorize"], 600),
    ("tarih çıkarma", ["extract-dates", "--days", "14", "--apply"], 3600),
    ("onayladıkların → takvim", ["approve", "--apply"], 600),     # onay-bekleyenler.md'de [x] işaretlediklerin
    ("takvim → kasa", ["sync-gcal"], 900),
    ("arşivleme", ["housekeep", "--apply"], 300),                # süresi geçen/biten işler 90-Arşiv'e
    ("not kutusu", ["inbox-process", "--apply"], 1800),            # 00-Inbox/Dump → ilgili notlar (yerel model)
    ("rehber", ["contacts-sync"], 900),
    ("drive", ["drive-sync"], 5400),
    ("drive notları", ["drive-index"], 900),
    ("e-destek", ["moodle-sync", "--apply"], 1800),              # okul Moodle'ı → ders notları, dosyalar (lms.moodle_url boşsa atlanır)
    ("bilgisayar dosyaları", ["local-files"], 5400),
    ("belge içerikleri", ["content-sync"], 7200),
    ("hazır uygulamalar (ClipBoardLine, Nashi)", ["apps", "sync", "all"], 900),
    ("projeler", ["projects-sync"], 3600),
    ("proje derleme", ["project-deep", "--all"], 10800),
    ("UZEM / Moodle dersleri", ["uzem", "sync", "--daily"], 900),            # haftalık konular, duyurular, ödevler, ders dosyaları (40-Kaynaklar/UZEM)
    ("ders dosyaları", ["course-files"], 900),
    ("ders derleme", ["course-deep", "--all"], 7200),
    ("oturum günlükleri", ["sessions-sync"], 7200),
    ("obs", ["obs-import"], 300),
    ("bağlantılar", ["links"], 900),
    ("mail notları", ["mail-index"], 900),
    ("rehber (SMS bağlantısı)", ["contacts-sync"], 900),
    ("fatura/kargo", ["derive", "--days", "30"], 600),
    ("github derin", ["github-deep", "--days", "14"], 900),
    ("beyin dizini", ["index"], 7200),                            # yeni/değişen belgeler parçalanır ve gömülür
    ("kişi bağlantıları", ["mentions"], 1800),
    ("sohbet bağlantıları", ["chat-links"], 600),
    ("kişi birleştirme (otomatik)", ["merge-people", "--auto"], 900),
    ("kayıtlı aramalar", ["search2", "--saved"], 600),
    ("günlük yansıma", ["persona", "--reflect"], 900),
    ("otomasyonlar", ["automation-tick"], 900),                  # config/otomasyon.yaml kuralları; takvim/WhatsApp onaya düşer           # dünün makbuz/takvim/görevlerinden 5 satır (yerel model)
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
    from . import telemetry
    telemetry.record("daily_step", name, dur * 1000, rc == 0)
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


def git_push_enabled() -> bool:
    """`config/gizlilik.yaml` → `git_push` (varsayılan true). false: günlük çalışma kasayı yalnız yerelde commit'ler, GitHub'a göndermez."""
    try:
        from . import privacy
        return bool(privacy._yaml(privacy.GIZLILIK_CFG).get("git_push", True))
    except Exception:                                                # noqa: BLE001
        return True


def git_sync(log) -> str:
    """Kasa değişikliklerini commit + push eder (Obsidian Git ile çakışırsa bir kez daha dener)."""
    def git(*a):
        return subprocess.run(["git", "-C", str(VAULT), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for attempt in range(2):
        git("add", "-A")
        if not git("status", "--porcelain").stdout.strip():
            return "git: değişiklik yok"
        c = git("commit", "-q", "-m", f"otomatik güncelleme {datetime.now():%Y-%m-%d %H:%M}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
        if not git_push_enabled():                                   # kişisel notlar GitHub'a gitmesin: yalnız yerel commit (geri alma için)
            return "git: yerelde commit'lendi (GitHub'a gönderim kapalı: config/gizlilik.yaml → git_push: false)"
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


DELIVERY_WARN = DATA / "delivery_warning.txt"     # gelen kutusuna ulaşmayan özet → bir sonraki özetin başına uyarı


def _deliver(text: str, log) -> None:
    """Özeti mail (varsayılan, şirket SMTP → sadece kullanıcının adresi) ve Telegram bağlıysa Telegram ile gönderir.

    Gönderdikten sonra mailin gelen kutusuna gerçekten düştüğü Gmail'den (salt okunur) kontrol edilir; düşmediyse
    masaüstü bildirimi + bir sonraki özete uyarı. "Gönderildi" sunucunun kabul ettiği anlamına gelir, teslim değil.
    """
    from . import actions, mailer, telegram
    subject = text.splitlines()[0][:120] if text else "Second Brain"
    problem = None
    try:
        msgid = mailer.new_id()
        log(f"Mail gönderildi ({mailer.send(subject, text, msgid=msgid)}) → {', '.join(mailer.settings()['to'])}")
        where = mailer.delivery(msgid)
        log(f"Teslim kontrolü: {where}")
        if where != "gelen kutusu" and not where.startswith("kontrol edilemedi"):
            problem = f"'{subject}' maili gelen kutusuna değil, {where} klasörüne düştü."
    except BaseException as e:      # SystemExit dahil: teslimat hatası çalışmayı düşürmemeli
        log(f"Mail gönderilemedi: {e}")
        problem = f"'{subject}' maili gönderilemedi: {e}"
    if problem:
        DELIVERY_WARN.write_text(f"{datetime.now():%Y-%m-%d %H:%M} {problem}", encoding="utf-8")
        try:
            actions.toast("Second Brain: özet maili ulaşmadı", problem + " Özet kasada da duruyor (50-Günlük).")
        except Exception as e:
            log(f"Bildirim gösterilemedi: {e}")
    else:
        DELIVERY_WARN.unlink(missing_ok=True)
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
        from . import features, freshness
        try:
            seeded = freshness.seed()["added"]                # ilk çalışmada mail.db geçmişinden tazelik tohumu
            if seeded:
                log(f"kaynak tazeliği tohumlandı: {len(seeded)} kaynak")
        except Exception as e:                                 # noqa: BLE001
            log(f"tazelik tohumu atlandı: {e}")
        steps = [run_step(n, a, t, log) for n, a, t in mail_steps() + DAILY_REST
                 if (not skip or n not in skip) and features.step_enabled(a)]
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
        if DELIVERY_WARN.exists():
            lines = text.splitlines() or [""]
            text = "\n".join([lines[0], "", f"⚠ Önceki özet: {DELIVERY_WARN.read_text(encoding='utf-8').strip()}", *lines[1:]])
        log(git_sync(log))
        _write_note(f"{date.today():%Y-%m-%d} Özet", f"ozet:{date.today():%Y-%m-%d}", text)
        _deliver(text, log)
        MARKER.write_text(date.today().isoformat())
    return 0 if all(s["rc"] == 0 for s in steps) else 1


def weekly_backup(log) -> str:
    """Haftalık şifreli kasa yedeği (kasa anahtarıyla `.zip.enc`); son `backup_keep` (varsayılan 8) tutulur. Hata haftalığı düşürmez
    ama rapora yazılır: anahtar okunamıyor / şifreleme kurulu değilse DÜZ yedek alınmaz."""
    try:
        from . import privacy
        r = privacy.create_backup(scheduled=True)
        if r.get("ok"):
            msg = f"💾 Şifreli yedek alındı: {r['created'][0]}" + (f" (eski {len(r['removed'])} yedek silindi)" if r.get("removed") else "")
        else:
            msg = f"⚠ Yedek alınamadı: {r.get('message', '?')}"
    except Exception as e:                                       # noqa: BLE001
        msg = f"⚠ Yedek alınamadı: {type(e).__name__}: {str(e)[:150]}"
    log(msg)
    return msg


def weekly() -> int:
    from . import digest, maildb
    log = _logger("weekly")
    with lock():
        log(f"haftalık çalışma başladı {datetime.now():%F %T}")
        con = maildb.connect(DATA / "mail.db")
        text = digest.build_weekly(con, VAULT, date.today(), lint_errors())
        from . import features
        if features.enabled("brain"):
            for name, args, to in (("konu kümeleri", ["clusters"], 3600), ("belge kümeleri", ["clusters", "--docs"], 3600),
                                   ("bağlantı önerileri", ["suggest-links"], 1800), ("bağlantılar (otomatik)", ["suggest-links", "--auto"], 900),
                                   ("graf renkleri", ["graph-style"], 300), ("analizler", ["analyze", "all"], 3600)):
                run_step(name, args, to, log)
        if features.enabled("memory_ui"):
            for name, args, to in (("beni tanı", ["persona", "--weekly"], 1800), ("tercih adayları", ["persona", "--prefs"], 1800)):
                run_step(name, args, to, log)
        try:
            from . import hygiene, memory
            text += "\n\n🧾 Bu hafta (makbuzlar)\n" + memory.recap(7)
            text += "\n\n🧹 Hafıza hijyeni\n" + hygiene.render(hygiene.report(limit=8))
        except Exception as e:                                   # rapor eki haftalık özeti düşürmesin
            log(f"hijyen/recap eklenemedi: {e}")
        iso = date.today().isocalendar()
        _write_note(f"{iso[0]}-W{iso[1]:02d} Haftalık", f"hafta:{iso[0]}-W{iso[1]:02d}", text)
        text += "\n\n" + weekly_backup(log)
        log(git_sync(log))
        _deliver(text, log)
    return 0
