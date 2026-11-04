"""“Çalışmaya başla” boru hattı: güncelleme denetimi → sağlık → günlük işler → model ısıtma → hazır.

Tek seferde tek çalışma, arka plan iş parçacığında. Her adım: {id, title, status, duration_s, message, fix?}.
status: pending | running | ok | warn | error | skipped. Ağır işler `_check_update` vb. işlevlerde; testler bunları taklit eder.
"""
from __future__ import annotations

import contextlib
import io
import re
import threading
import time
from datetime import date
from pathlib import Path

import yaml

from .config import SYSTEM

SETTINGS = SYSTEM / "config" / "uygulama.yaml"
TITLES = [("update", "Güncelleme denetimi"), ("health", "Sağlık kontrolü"), ("daily", "Günlük işler"),
          ("apps", "Uygulamalar"), ("warm", "Modelleri ısıt"), ("ready", "Hazır")]

_lock = threading.Lock()
_state: dict = {}


def app_settings(path: Path | None = None) -> dict:
    try:
        return yaml.safe_load((path or SETTINGS).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}


def auto_update_enabled() -> bool:
    return app_settings().get("auto_update") is True


# ------------------------------------------------------------ ağır işler (testte taklit)
def _check_update() -> dict:
    """{'available': bool, 'current': str, 'new': str, 'ok': bool, 'text': str}. Yan etkisiz (yalnız fetch)."""
    from . import update
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = update.run(check_only=True)
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "available": False, "text": f"{type(e).__name__}: {str(e)[:120]}"}
    text = buf.getvalue()
    m = re.search(r"Kurulu: (\S+) → yeni: (\S+)", text)
    if m:
        return {"ok": True, "available": True, "current": m.group(1), "new": m.group(2), "text": text}
    return {"ok": rc == 0, "available": False, "text": text.strip()[:200]}


def _apply_update() -> int:
    from . import update
    with contextlib.redirect_stdout(io.StringIO()):
        return update.run(yes=True)


def _doctor() -> list[tuple[str, str, str]]:
    from . import doctor
    return doctor.checks()


def _daily_done_today() -> bool:
    from . import runner
    try:
        return runner.MARKER.read_text().strip() == date.today().isoformat()
    except OSError:
        return False


def _run_daily() -> int:
    from . import runner
    return runner.daily()


def _warm_models() -> list[str]:
    """Ollama'yı açıp modeli belleğe alır, whisper'ı yükler. Döner: yapılanların listesi; hata fırlatabilir."""
    done: list[str] = []
    from . import llm
    cfg = llm.config()
    if cfg.get("ollama"):
        llm.ensure_ollama(cfg)
        o = cfg["ollama"]
        llm._http(o["host"], "/api/generate", {"model": o["model"], "prompt": "", "keep_alive": "30m", "stream": False}, 300)
        done.append(f"Ollama ({o['model']})")
    from . import voice
    if voice.WhisperModel is not None:
        voice._get_model(voice.stt_model_name())
        done.append("Whisper")
    return done


# ------------------------------------------------------------ boru hattı
def _fresh() -> dict:
    return {"running": False, "done": False, "ok": None, "started": None, "finished": None, "update": None,
            "steps": [{"id": i, "title": t, "status": "pending", "duration_s": 0.0, "message": ""} for i, t in TITLES]}


_state.update(_fresh())


def _set(step_id: str, **kw) -> None:
    with _lock:
        for s in _state["steps"]:
            if s["id"] == step_id:
                s.update(kw)


def status() -> dict:
    with _lock:
        out = {k: v for k, v in _state.items() if k != "steps"}
        out["steps"] = [dict(s) for s in _state["steps"]]
        if out.get("update"):
            out["update"] = dict(out["update"])
        return out


def _timed(step_id: str, fn) -> None:
    _set(step_id, status="running", message="")
    t0 = time.monotonic()
    try:
        res = fn()
    except Exception as e:                                       # noqa: BLE001 — bir adım diğerlerini durdurmasın
        res = {"status": "error", "message": f"{type(e).__name__}: {str(e)[:160]}"}
    res = dict(res or {})
    res.setdefault("status", "ok")
    _set(step_id, duration_s=round(time.monotonic() - t0, 2), **res)


def _step_update(auto: bool) -> dict:
    info = _check_update()
    with _lock:
        _state["update"] = {k: info.get(k) for k in ("available", "current", "new")}
    if not info.get("ok"):
        return {"status": "warn", "message": "Güncelleme denetlenemedi: " + str(info.get("text", ""))[:120],
                "fix": "İnternet bağlantısını ve kit deposunu (`sb update --check`) kontrol et."}
    if not info.get("available"):
        return {"message": "Güncel."}
    msg = f"Yeni sürüm var: {info.get('current')} → {info.get('new')}."
    if not auto:
        return {"status": "warn", "message": msg + " Otomatik güncelleme kapalı.",
                "fix": "Güncellemek için `sb update` ya da config/uygulama.yaml içine `auto_update: true` yaz."}
    rc = _apply_update()
    if rc:
        return {"status": "error", "message": msg + " Güncelleme tamamlanamadı.", "fix": "`sb update --recover` ya da `sb update --rollback`."}
    return {"message": msg + " Güncellendi; asistanı yeniden başlat."}


def _step_health() -> dict:
    rows = _doctor()
    fails = [r for r in rows if r[0] == "✗"]
    warns = [r for r in rows if r[0] == "!"]
    ok_n = len(rows) - len(fails) - len(warns)
    msg = f"{ok_n}/{len(rows)} kontrol hazır"
    if not fails and not warns:
        return {"message": msg}
    probs = fails + warns
    fix = "\n".join(f"• {n}: {h or 'ayrıntı için `sb doctor`'}" for _, n, h in probs[:8])
    if len(probs) > 8:
        fix += f"\n… ve {len(probs) - 8} madde daha (`sb doctor`)."
    return {"status": "error" if fails else "warn", "message": f"{msg}; {len(fails)} gerekli eksik, {len(warns)} isteğe bağlı.", "fix": fix}


def _step_daily() -> dict:
    if _daily_done_today():
        return {"status": "skipped", "message": "Bugünkü günlük işler zaten yapıldı."}
    rc = _run_daily()
    if rc:
        return {"status": "warn", "message": "Günlük işler bitti, bazı adımlar hata verdi.", "fix": "Ayrıntı: ~/.secondbrain/logs (günlük kaydı)."}
    return {"message": "Günlük işler tamamlandı."}


def _apps_work() -> dict:
    """Başlangıç kipi 'startup' olan kurulu uygulamaları başlatır; ardından ClipBoardLine/Nashi verisini beyne okur (testte taklit)."""
    from . import apps
    started = [r for r in apps.start_startup_apps(log=lambda *_: None) if r.get("started")]
    synced = apps.sync_all(require_enabled=True)
    return {"started": [r["id"] for r in started], "synced": synced}


def _step_apps() -> dict:
    from . import apps
    if not any(apps.installed(i) for i in apps.ids()):
        return {"status": "skipped", "message": "Kurulu hazır uygulama yok (ClipBoardLine, Nashi: `sb apps install <ad>`)."}
    res = _apps_work()
    bits = []
    if res["started"]:
        bits.append("başlatıldı: " + ", ".join(res["started"]))
    bits += [apps.format_sync(r) for r in res["synced"]]
    bad = [r for r in res["synced"] if r.get("error")]
    return {"status": "warn" if bad else "ok", "message": "; ".join(bits)[:300] or "Yapılacak bir şey yok.",
            **({"fix": "Ayrıntı: `sb apps status` ve `sb apps sync all`."} if bad else {})}


def _step_warm() -> dict:
    try:
        done = _warm_models()
    except Exception as e:                                       # noqa: BLE001
        return {"status": "warn", "message": f"Isıtılamadı: {str(e)[:120]}", "fix": "Ollama kurulu ve çalışıyor mu? (`ollama serve`)"}
    if not done:
        return {"status": "skipped", "message": "Isıtılacak model yok."}
    return {"message": ", ".join(done) + " hazır."}


def _pipeline(auto_update: bool) -> None:
    try:
        _timed("update", lambda: _step_update(auto_update))
        _timed("health", _step_health)
        _timed("daily", _step_daily)
        _timed("apps", _step_apps)
        _timed("warm", _step_warm)
        with _lock:
            bad = [s for s in _state["steps"] if s["status"] == "error"]
            warn = [s for s in _state["steps"] if s["status"] == "warn"]
        _set("ready", status="error" if bad else "warn" if warn else "ok",
             message="Hazır." if not bad and not warn else f"Hazır; {len(bad)} hata, {len(warn)} uyarı var.")
        with _lock:
            _state["ok"] = not bad
    finally:
        with _lock:
            _state.update(running=False, done=True, finished=time.time())


def start(background: bool = True) -> bool:
    """Çalışmayı başlatır; zaten çalışıyorsa False. Güncelleme yalnız config/uygulama.yaml `auto_update: true` ise uygulanır
    (istek gövdesindeki auto_update bayrağı bunu açamaz; ayar kapalıyken yalnız “güncelleme var” bilgisi verilir)."""
    with _lock:
        if _state["running"]:
            return False
        _state.clear()
        _state.update(_fresh())
        _state.update(running=True, started=time.time())
    t = threading.Thread(target=_pipeline, args=(auto_update_enabled(),), daemon=True, name="sb-startup")
    if background:
        t.start()
    else:
        t.run()
    return True
