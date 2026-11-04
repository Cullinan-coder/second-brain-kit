"""Tek onay deposu ve API'si (D-30).

Eskiden üç ayrı sistem vardı: sohbetin bellek içi `session.proposals`'ı (sunucu yeniden başlayınca kayboluyordu, telefon ve
bilgisayar oturumları birbirini görmüyordu), otomasyonun `pending_approvals.jsonl`'ı ve tarih çıkarmanın `onay-bekleyenler.md`'si.
Hepsi artık `~/.secondbrain/approvals.jsonl`'a yazar ve buradan karar verilir:

- Kalıcı: kayıt diske yazılır (süreçler arası kilit `filelock` + atomik yazım). Sunucu yeniden başlasa da kart görünür; eylemi
  seri hâle getirilebilenler (komut, WhatsApp, takvim, takvim silme, kasa eylemi, gece işi, otomasyon, tarih) yeniden başlamadan
  sonra da onaylanabilir. Yalnız bellek içi bir işlevle gelen kart (ör. unutma, zaman bloğu) yeniden başlamadan sonra "süresi doldu"
  olur (`expire_orphans`); sessizce kaybolmaz.
- Alanlar: `kind` (komut, takvim, takvim-sil, whatsapp, gece, eylem, kasa, unut, tarih…), `origin` (sohbet, otomasyon, tarih),
  `source` (yerel = bu bilgisayar, telefon), `sid`/`session` (hangi sohbet), `expires` (süre aşımı), `status`
  (bekliyor → onaylandi | reddedildi | hata | suresi-doldu), `result`.
- Telefon kuralı (D-05): telefon YALNIZ kendi (source=telefon) kartına karar verebilir ve onaylayabildiği türler `REMOTE_APPROVABLE`
  (takvim, eylem). Komut, WhatsApp, gece koşusu, silme, kasa, otomasyon ve tarih kartları yalnız bilgisayardan onaylanır.
- Çift yürütme yok: onay önce kilit altında "onaylandi" diye işaretlenir, eylem kilit dışında çalışır, sonuç sonra yazılır.

`00-Inbox/onay-bekleyenler.md` bu deponun Obsidian görünümüdür (`extract.render_view`); orada [x] işaretlemek de onaydır.
"""
from __future__ import annotations

import importlib
import json
import threading
import uuid
from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from . import config, filelock

PENDING, APPROVED, REJECTED, FAILED, EXPIRED = "bekliyor", "onaylandi", "reddedildi", "hata", "suresi-doldu"
REMOTE_APPROVABLE = {"takvim", "eylem"}          # beyaz liste: telefondan yalnız bunlar onaylanır (kendi kartıysa)
LOCAL, PHONE = "yerel", "telefon"
TTL_HOURS = {"komut": 12, "whatsapp": 12, "gece": 12, "eylem": 24, "takvim-sil": 24, "kasa": 24, "unut": 24,
             "takvim": 24 * 7, "tarih": 24 * 60}
DEFAULT_TTL_HOURS = 24 * 7
KEEP_DECIDED_DAYS = 30
MAX_ROWS = 2000
# Seri hâle getirilebilen eylemler: yeniden başlamadan sonra da yürür. "modül:işlev(payload, calendar) -> str".
EXECUTORS = {
    "komut": "sb.chat:_exec_command", "whatsapp": "sb.chat:_exec_whatsapp", "takvim-ekle": "sb.chat:_exec_calendar_add",
    "takvim-sil": "sb.chat:_exec_calendar_delete", "arac": "sb.chat:_exec_tool", "gece": "sb.chat:_exec_night_start",
    "gece-ekle": "sb.chat:_exec_night_add", "otomasyon": "sb.automation:_exec_approval", "tarih": "sb.extract:_exec_tarih",
}
REMOTE_REFUSAL = "Bu onay yalnız bilgisayardan verilebilir (komut, WhatsApp, gece koşusu, silme). Kart bilgisayardaki asistanda bekliyor."

_RUNS: dict[str, Callable[[], object]] = {}      # bu süreçte hazırlanan, diske yazılamayan işlevler (yalnız onay anında çağrılır)
_runs_lock = threading.Lock()
_migrated: set[str] = set()


class ApprovalError(Exception):
    pass


class NotFound(ApprovalError, LookupError):
    pass


class AlreadyDecided(ApprovalError, PermissionError):
    pass


class RemoteForbidden(ApprovalError, PermissionError):
    pass


class Expired(ApprovalError, PermissionError):
    pass


def path() -> Path:
    return Path(config.DATA) / "approvals.jsonl"


def _now() -> datetime:
    return datetime.now()


def _iso(d: datetime) -> str:
    return d.isoformat(timespec="seconds")


# ---------------------------------------------------------------- okuma / yazma
def _parse(text: str) -> list[dict]:
    rows: dict[str, dict] = {}
    for ln in text.splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if isinstance(r, dict) and r.get("id"):
            rows[str(r["id"])] = r                  # aynı kimlik ikinci kez yazıldıysa sonuncusu geçerli
    return list(rows.values())


def _read() -> list[dict]:
    try:
        return _parse(path().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def _write(rows: list[dict]) -> None:
    """Kilit altında çağrılır. Eski kararlı kayıtları budar."""
    cut = _iso(_now() - timedelta(days=KEEP_DECIDED_DAYS))
    rows = [r for r in rows if r.get("status") == PENDING or (r.get("decided") or r.get("created") or "") >= cut][-MAX_ROWS:]
    filelock.atomic_write(path(), "".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows))


def _migrate_legacy() -> None:
    """Eski otomasyon deposu (`pending_approvals.jsonl`) bir kez bu depoya taşınır; eski dosya `.tasindi` uzantısıyla kalır."""
    old = Path(config.DATA) / "pending_approvals.jsonl"
    key = str(old)
    if key in _migrated or not old.exists():
        return
    _migrated.add(key)
    try:
        legacy = _parse(old.read_text(encoding="utf-8"))
    except OSError:
        return
    with filelock.locked(path()):
        try:
            have = {r["id"] for r in _parse(path().read_text(encoding="utf-8"))}
        except FileNotFoundError:
            have = set()
        new = [_from_legacy_automation(r) for r in legacy if r.get("id") not in have]
        if new:
            try:
                body = path().read_text(encoding="utf-8")
            except FileNotFoundError:
                body = ""
            filelock.atomic_write(path(), body + "".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in new))
    try:
        old.replace(old.with_name(old.name + ".tasindi"))
    except OSError:
        pass


def _from_legacy_automation(r: dict) -> dict:
    tur = r.get("tur", "")
    status = {"bekliyor": PENDING, "onaylandi": APPROVED, "reddedildi": REJECTED}.get(r.get("durum"), r.get("durum") or PENDING)
    created = r.get("zaman") or _iso(_now())
    return {"id": r["id"], "kind": "whatsapp" if tur.startswith("whatsapp") else "takvim", "title": r.get("baslik", ""),
            "detail": r.get("ayrinti", ""), "source": LOCAL, "origin": "otomasyon", "sid": "", "session": "",
            "created": created, "expires": _iso(datetime.fromisoformat(created) + timedelta(hours=DEFAULT_TTL_HOURS)),
            "status": status, "result": r.get("sonuc", ""), "decided": "" if status == PENDING else created,
            "action": "otomasyon", "payload": {"tur": tur, "kural": r.get("kural", ""), **(r.get("payload") or {})}, "extra": {}}


# ---------------------------------------------------------------- ekleme
def add(kind: str, title: str, detail: str = "", *, source: str = LOCAL, origin: str = "sohbet", sid: str = "", session: str = "",
        action: str = "", payload: dict | None = None, run: Callable[[], object] | None = None, ttl_hours: float | None = None,
        extra: dict | None = None, rid: str = "") -> dict:
    """Yeni onay kaydı. `action`+`payload` seri hâle getirilebilir eylemdir (yeniden başlamadan sonra da yürür);
    `run` yalnız bu süreçte yaşayan işlevdir (ikisi birden verilirse bu süreçte `run` kullanılır)."""
    if action and action not in EXECUTORS:
        raise ValueError(f"bilinmeyen onay eylemi: {action}")
    now = _now()
    ttl = ttl_hours if ttl_hours is not None else TTL_HOURS.get(kind, DEFAULT_TTL_HOURS)
    rec = {"id": rid or uuid.uuid4().hex[:8], "kind": kind, "title": str(title), "detail": str(detail or ""),
           "source": PHONE if source == PHONE else LOCAL, "origin": origin, "sid": sid, "session": session,
           "created": _iso(now), "expires": _iso(now + timedelta(hours=ttl)), "status": PENDING, "result": "", "decided": "",
           "action": action, "payload": payload or {}, "extra": extra or {}}
    if run is not None:
        with _runs_lock:
            _RUNS[rec["id"]] = run
    _migrate_legacy()
    filelock.append_line(path(), json.dumps(rec, ensure_ascii=False, default=str))   # D-20: süreçler arası kilitli ekleme
    return rec


def upsert(rec: dict) -> None:
    """Kimliği verilen kaydı yazar (yoksa ekler). Tarih görünümünün eşitlemesi kullanır."""
    _migrate_legacy()
    with filelock.locked(path()):
        rows = [r for r in _read() if r.get("id") != rec["id"]]
        _write(rows + [rec])


def update_many(fn: Callable[[list[dict]], list[dict]]) -> list[dict]:
    """Kilit altında oku → fn(kayıtlar) → yaz. fn değiştirilmiş listeyi döndürür."""
    _migrate_legacy()
    with filelock.locked(path()):
        rows = fn(_read())
        _write(rows)
        return rows


# ---------------------------------------------------------------- sorgu
def _expired(r: dict, now: datetime) -> bool:
    return r.get("status") == PENDING and bool(r.get("expires")) and r["expires"] < _iso(now)


def runnable(r: dict) -> bool:
    return bool(r.get("action")) or r["id"] in _RUNS


def get(aid: str) -> dict | None:
    _migrate_legacy()
    return next((r for r in _read() if r.get("id") == aid), None)


def records(*, session: str | None = None, origin: str | None = None, status: str | None = PENDING,
            viewer: str | None = None) -> list[dict]:
    """Kayıtlar (oluşturma sırasıyla). `viewer="telefon"`: telefon yalnız kendi kartlarını ve tarih adaylarını görür
    (bilgisayardaki komut/WhatsApp metni telefona gösterilmez). Süresi dolan bekleyenler "suresi-doldu" görünür."""
    _migrate_legacy()
    now = _now()
    out = []
    for r in _read():
        if _expired(r, now):
            r = dict(r, status=EXPIRED, result=r.get("result") or "süresi doldu")
        if session is not None and r.get("session") != session:
            continue
        if origin is not None and r.get("origin") != origin:
            continue
        if status is not None and r.get("status") != status:
            continue
        if viewer == PHONE and r.get("source") != PHONE and r.get("origin") != "tarih":
            continue
        out.append(r)
    return out


def public(r: dict, viewer: str | None = None) -> dict:
    """Arayüze giden biçim (eylem yükü ve iç alanlar yok)."""
    out = {k: r.get(k) for k in ("id", "kind", "title", "detail", "source", "origin", "created", "expires", "status", "result")}
    out.update(r.get("extra") or {})
    out["runnable"] = runnable(r)
    out["can_decide"] = can_decide(r, viewer == PHONE, ok=True) is None
    return out


def can_decide(r: dict, remote: bool, ok: bool) -> str | None:
    """Karar verilemezse nedeni; verilebilirse None."""
    if remote and r.get("source") != PHONE:
        return REMOTE_REFUSAL
    if remote and ok and r.get("kind") not in REMOTE_APPROVABLE:
        return REMOTE_REFUSAL
    return None


def count(viewer: str | None = None) -> int:
    return len(records(viewer=viewer))


# ---------------------------------------------------------------- karar
def _execute(rec: dict, calendar=None) -> str:
    fn = _RUNS.get(rec["id"])
    if fn is not None:
        return str(fn())
    target = EXECUTORS.get(rec.get("action") or "")
    if not target:
        raise Expired("Bu onay sunucu yeniden başlamadan önce hazırlanmıştı; isteği yeniden yap.")
    mod, name = target.split(":")
    return str(getattr(importlib.import_module(mod), name)(rec.get("payload") or {}, calendar))


def decide(aid: str, ok: bool, *, remote: bool = False, calendar=None, session: str | None = None) -> dict:
    """Bir kayda karar verir. Döner: {"ok", "id", "status", "message", "record"}.
    Hata: NotFound, AlreadyDecided, Expired, RemoteForbidden (hepsi ApprovalError)."""
    _migrate_legacy()
    with filelock.locked(path()):
        rows = _read()
        rec = next((r for r in rows if r.get("id") == aid and (session is None or r.get("session") == session)), None)
        if rec is None:
            raise NotFound("onay kaydı bulunamadı")
        if rec.get("status") != PENDING:
            raise AlreadyDecided("zaten sonuçlandı")
        now = _now()
        if _expired(rec, now):
            rec.update(status=EXPIRED, result="süresi doldu", decided=_iso(now))
            _write(rows)
            raise Expired("Bu onayın süresi doldu; isteği yeniden yap.")
        why = can_decide(rec, remote, ok)
        if why:
            raise RemoteForbidden(why)
        if not ok:
            rec.update(status=REJECTED, decided=_iso(now), result="iptal edildi")
            _write(rows)
            _RUNS.pop(aid, None)
            _after(rec)
            return {"ok": True, "id": aid, "status": REJECTED, "message": "", "record": rec}
        if not runnable(rec):
            rec.update(status=EXPIRED, decided=_iso(now), result="sunucu yeniden başladı")
            _write(rows)
            raise Expired("Bu onay sunucu yeniden başlamadan önce hazırlanmıştı; isteği yeniden yap.")
        rec.update(status=APPROVED, decided=_iso(now))       # önce işaretle: çift yürütme olmasın
        _write(rows)
    status = APPROVED
    try:
        msg = _execute(rec, calendar)                           # yürütme (ağ, komut, WhatsApp) kilit dışında
    except (Exception, SystemExit) as e:                        # noqa: BLE001
        status, msg = FAILED, f"Hata: {type(e).__name__}: {str(e)[:200]}"
    finally:
        _RUNS.pop(aid, None)
    with filelock.locked(path()):
        rows = _read()
        cur = next((r for r in rows if r.get("id") == aid), None)
        if cur is not None:
            cur.update(status=status, result=str(msg)[:1000])
            _write(rows)
            rec = cur
    _after(rec)
    return {"ok": status == APPROVED, "id": aid, "status": status, "message": msg, "record": rec}


def _after(rec: dict) -> None:
    """Karar sonrası görünümleri tazele (tarih adayları → onay-bekleyenler.md)."""
    if rec.get("origin") == "tarih":
        try:
            from . import extract
            extract.render_view()
        except Exception:                                       # noqa: BLE001 — görünüm yazılamasa da karar geçerli
            pass


def cancel_session(session: str, reason: str = "yeni sohbet") -> int:
    """Bir sohbetin bekleyen kartlarını iptal eder (eski davranış: 'Yeni sohbet' kartları düşürürdü)."""
    n = 0

    def fn(rows):
        nonlocal n
        for r in rows:
            if r.get("session") == session and r.get("status") == PENDING:
                r.update(status=REJECTED, decided=_iso(_now()), result=reason)
                _RUNS.pop(r["id"], None)
                n += 1
        return rows
    if any(r.get("session") == session for r in records(session=session)):
        update_many(fn)
    return n


def expire_orphans() -> int:
    """Sunucu açılışında: bellek içi işlevi önceki süreçte kalmış bekleyen kartlar "suresi-doldu" olur (sessiz kaybolma yok)."""
    n = 0

    def fn(rows):
        nonlocal n
        for r in rows:
            if r.get("status") == PENDING and not r.get("action") and r["id"] not in _RUNS:
                r.update(status=EXPIRED, decided=_iso(_now()), result="sunucu yeniden başladı; isteği yeniden yap")
                n += 1
        return rows
    update_many(fn)
    return n


# ---------------------------------------------------------------- sohbet oturumu görünümü
class SessionApprovals(Mapping):
    """`chat.Session.proposals`: bu oturumun kayıtları, sözlük gibi (eski arayüz). Kayıtlar diskte; `_run` yalnız bu süreçte."""

    def __init__(self, key: str) -> None:
        self.key = key

    def _rows(self) -> list[dict]:
        return records(session=self.key, status=None)

    def __getitem__(self, pid: str) -> dict:
        r = next((x for x in self._rows() if x["id"] == pid), None)
        if r is None:
            raise KeyError(pid)
        return legacy_card(r)

    def __iter__(self):
        return iter([r["id"] for r in self._rows()])

    def __len__(self) -> int:
        return len(self._rows())

    def clear(self) -> None:
        cancel_session(self.key)


def legacy_card(r: dict) -> dict:
    """Sohbet kartı biçimi (eski `session.proposals[pid]`): id, status, kind, title, detail (+ takvimde summary/when/reminders)."""
    out = {"id": r["id"], "status": "bekliyor" if r.get("status") == PENDING else r.get("status"), "kind": r.get("kind"),
           "title": r.get("title"), "detail": r.get("detail"), **(r.get("extra") or {})}
    if r["id"] in _RUNS:
        out["_run"] = _RUNS[r["id"]]
    return out
