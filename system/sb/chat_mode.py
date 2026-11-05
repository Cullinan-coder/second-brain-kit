"""Asistan sohbet modu: bulut (config/llm.yaml `tasks.chat`) ya da yerel (Ollama), kullanıcı istediği anda değiştirir.

Durum `~/.secondbrain/chat_mode.json` içinde: {"mode": "cloud"|"local", "ts": ...} (kilit + atomik yazım).
Dosya yoksa varsayılan: `tasks.chat` bir bulut belirtecinde ("gemini:gemini-2.5-pro") ise cloud, yoksa local.
`tasks.chat` bulut değilse cloud istenemez (bir şey yazılmaz). Güvenlik katmanları (hassas içerik, sıkı profil, bütçe) chat.py'de
aynen sürer; bu modül yalnız "bu tur bulut denensin mi" kararını ve tur kaydını (hangi model cevapladı) tutar.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime

from . import config, filelock

MODES = ("cloud", "local")
_turn = threading.local()


def _path():
    return config.DATA / "chat_mode.json"


def _cfg(cfg: dict | None) -> dict:
    if cfg is not None:
        return cfg
    from . import llm
    return llm.config() or {}


def cloud_spec(cfg: dict | None = None) -> str | None:
    """`tasks.chat` bir bulut belirteciyse onu, değilse None."""
    spec = str(((_cfg(cfg).get("tasks") or {}).get("chat")) or "").strip()
    if ":" not in spec:
        return None
    from . import router
    return None if router.is_local(spec) else spec


def local_model(cfg: dict | None = None) -> str:
    return str((_cfg(cfg).get("ollama") or {}).get("model") or "")


def label(spec: str) -> str:
    """"gemini:gemini-2.5-pro" → "Gemini 2.5 Pro"."""
    prov, _, model = spec.partition(":")
    words = model.replace("_", "-").split("-")
    if words and words[0].lower() == prov.lower():
        words = words[1:]
    pretty = " ".join(w.capitalize() if not any(c.isdigit() for c in w) else w for w in words if w)
    return f"{prov.capitalize()} {pretty}".strip()


def stored_mode() -> str | None:
    try:
        d = json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    m = d.get("mode") if isinstance(d, dict) else None
    return m if m in MODES else None


def get_mode(cfg: dict | None = None) -> str:
    """Seçili mod (dosya yoksa varsayılan). Bulut ayarlı değilse her zaman local."""
    if cloud_spec(cfg) is None:
        return "local"
    return stored_mode() or "cloud"


def set_mode(mode: str, cfg: dict | None = None) -> str:
    if mode not in MODES:
        raise ValueError("mod 'cloud' ya da 'local' olmalı")
    if mode == "cloud" and cloud_spec(cfg) is None:
        raise ValueError("bulut modeli ayarlı değil (config/llm.yaml → tasks.chat: gemini:gemini-2.5-pro)")
    p = _path()
    with filelock.locked(p):
        filelock.atomic_write(p, json.dumps({"mode": mode, "ts": datetime.now().astimezone().isoformat(timespec="seconds")}))
    return mode


def active_spec(cfg: dict | None = None) -> str | None:
    """Bu tur denenecek bulut belirteci; yerel modda ya da bulut yoksa None (bulut HİÇ çağrılmaz)."""
    return cloud_spec(cfg) if get_mode(cfg) == "cloud" else None


def status(cfg: dict | None = None) -> dict:
    from . import providers, usage
    cfg = _cfg(cfg)
    cs, mode = cloud_spec(cfg), get_mode(cfg)
    out = {"mode": mode, "cloud_model": cs or "", "cloud_label": label(cs) if cs else "", "local_model": local_model(cfg),
           "cloud_available": False}
    if cs:
        try:
            out["cloud_available"] = providers.has_key(providers.split_spec(cs)[0])
        except Exception:                                           # noqa: BLE001
            pass
    if cs is None:
        out["why_local"] = "bulut modeli ayarlı değil"
    elif mode == "local":
        out["why_local"] = "yerel moda geçildi"
    elif not out["cloud_available"]:
        out["why_local"] = "bulut API anahtarı yok"
    try:
        out["budget"] = {"today_usd": round(usage.spent_today(), 4), "limit_usd": usage._limits()[1]}
    except Exception:                                               # noqa: BLE001
        out["budget"] = {"today_usd": 0.0, "limit_usd": 0.0}
    return out


# ---- tur kaydı: ollama_tools_chat'in gerçekte hangi modelle cevapladığı (iş parçacığı başına)
def note_turn(model: str, reason: str = "", fallback: bool = False) -> None:
    _turn.info = {"model": model, **({"reason": reason} if reason else {}), **({"fallback": True} if fallback else {})}


def reset_turn() -> None:
    _turn.info = None


def last_turn() -> dict | None:
    return getattr(_turn, "info", None)


def short_reason(exc: BaseException) -> str:
    """Hata → kısa, anahtar içermeyen neden."""
    from . import providers, usage
    if isinstance(exc, usage.BudgetExceeded):
        return "bütçe doldu"
    if isinstance(exc, providers.ProviderError):
        c = exc.code
        if c == 429:
            return "kota doldu (HTTP 429)"
        if c in (401, 403):
            return f"anahtar reddedildi (HTTP {c})"
        if c >= 500:
            return f"sunucu hatası (HTTP {c})"
        if c:
            return f"HTTP {c}"
        if "anahtarı yok" in exc.msg:
            return "API anahtarı yok"
        return "ağ hatası"
    return type(exc).__name__
