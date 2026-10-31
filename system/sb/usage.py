"""Model kullanımı ve maliyet: kayıt (usage.jsonl), fiyat tablosu, günlük/aylık bütçe sınırı, özet.

Yerel sağlayıcılar (ollama, lmstudio, llamacpp, vllm, yerel adres) maliyet 0 ile kaydedilir ve bütçeye takılmaz.
Fiyatı bilinmeyen bulut modelinde maliyet `None` (özette "fiyat bilinmiyor"). Yalnız standart kütüphane.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta

from .config import DATA

FILE = DATA / "usage.jsonl"
WARN_FILE = DATA / "usage_warn.json"
LOCAL = {"ollama", "lmstudio", "llamacpp", "vllm"}

# USD / 1M token (girdi, çıktı). Anahtar, model adının öneki olarak eşleşir (en uzun önek kazanır).
PRICES: dict[str, tuple[float, float]] = {
    "gpt-5-mini": (0.25, 2.0),
    "gpt-5-nano": (0.05, 0.4),
    "gpt-5": (1.25, 10.0),
    "claude-haiku-5-5": (1.0, 5.0),
    "claude-sonnet-5-5": (3.0, 15.0),
    "claude-opus-5-5": (5.0, 25.0),
    "gemini-2.5-flash-lite": (0.1, 0.4),
    "gemini-2.5-flash": (0.3, 2.5),
    "gemini-2.5-pro": (1.25, 10.0),
    "deepseek-chat": (0.28, 0.42),
    "deepseek-reasoner": (0.28, 0.42),
    "mistral-large": (2.0, 6.0),
    "mistral-small": (0.1, 0.3),
    "llama-3.3-70b": (0.59, 0.79),
    "llama-3.1-8b": (0.05, 0.08),
    "text-embedding-3-small": (0.02, 0.0),
    "text-embedding-3-large": (0.13, 0.0),
    "text-embedding-004": (0.0, 0.0),
    "gemini-embedding": (0.15, 0.0),
}


class BudgetExceeded(Exception):
    """Günlük ya da aylık bulut bütçesi aşıldı; çağrı yapılmadı."""


def _cfg() -> dict:
    try:
        from . import llm
        return llm.config() or {}
    except Exception:
        return {}


def is_local(provider: str) -> bool:
    if provider in LOCAL:
        return True
    try:
        from . import providers
        spec = providers.table().get(provider)
        return bool(spec) and providers.keyless(provider, spec)
    except Exception:
        return False


def _prices() -> dict[str, tuple[float, float]]:
    t = dict(PRICES)
    for name, v in (_cfg().get("prices") or {}).items():
        try:
            if isinstance(v, dict):
                t[str(name)] = (float(v.get("input", 0)), float(v.get("output", 0)))
            else:
                t[str(name)] = (float(v[0]), float(v[1]))
        except (TypeError, ValueError, IndexError, KeyError):
            continue
    return t


def cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float | None:
    """USD; yerelde 0.0, fiyatı bilinmeyen bulut modelinde None."""
    if is_local(provider):
        return 0.0
    name = model.lower().split("/")[-1]                       # openrouter: "openai/gpt-5" → "gpt-5"
    table = _prices()
    best = max((k for k in table if name.startswith(k.lower())), key=len, default=None)
    if best is None:
        return None
    pi, po = table[best]
    return round((input_tokens * pi + output_tokens * po) / 1_000_000, 6)


def record(provider: str, model: str, input_tokens: int, output_tokens: int, task: str = "") -> dict:
    """Kullanım satırı ekler; yazma hatası çağrıyı bozmaz."""
    row = {"ts": datetime.now().isoformat(timespec="seconds"), "provider": provider, "model": model,
           "in": int(input_tokens or 0), "out": int(output_tokens or 0),
           "cost_usd": cost(provider, model, int(input_tokens or 0), int(output_tokens or 0)), "task": task or ""}
    try:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        with FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return row


def rows(since: datetime | None = None) -> list[dict]:
    out = []
    try:
        lines = FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for ln in lines:
        try:
            r = json.loads(ln)
            if since and datetime.fromisoformat(r["ts"]) < since:
                continue
            out.append(r)
        except (ValueError, KeyError, TypeError):
            continue
    return out


def _spent(since: datetime) -> float:
    return sum(r.get("cost_usd") or 0.0 for r in rows(since))


def spent_today() -> float:
    return _spent(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))


def spent_month() -> float:
    return _spent(datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))


def _budget() -> dict:
    b = _cfg().get("budget") or {}
    return b if isinstance(b, dict) else {}


def _limits() -> tuple[float, float, float]:
    b = _budget()
    try:
        return float(b.get("monthly_usd") or 0), float(b.get("daily_usd") or 0), float(b.get("warn_at") or 0.8)
    except (TypeError, ValueError):
        return 0.0, 0.0, 0.8


def check(provider: str) -> None:
    """Bulutta bütçe aşıldıysa BudgetExceeded; yerelde her zaman izin. %warn_at aşılınca günde bir uyarı."""
    if is_local(provider):
        return
    monthly, daily, warn_at = _limits()
    day, month = spent_today(), spent_month()
    if daily and day >= daily:
        raise BudgetExceeded(f"günlük bütçe doldu: ${day:.2f} / ${daily:.2f}")
    if monthly and month >= monthly:
        raise BudgetExceeded(f"aylık bütçe doldu: ${month:.2f} / ${monthly:.2f}")
    for name, spent, limit in (("günlük", day, daily), ("aylık", month, monthly)):
        if limit and spent >= limit * warn_at:
            _warn_once(f"Model bütçesi: {name} sınırın %{int(warn_at * 100)}'i aşıldı (${spent:.2f} / ${limit:.2f})")
            break


def _warn_once(msg: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        if json.loads(WARN_FILE.read_text(encoding="utf-8")).get("day") == today:
            return
    except (OSError, ValueError):
        pass
    try:
        WARN_FILE.parent.mkdir(parents=True, exist_ok=True)
        WARN_FILE.write_text(json.dumps({"day": today, "msg": msg}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    try:
        from . import actions
        actions.toast("Second Brain", msg)
    except Exception:
        pass


def _fmt_cost(c: float | None, unknown: bool = False) -> str:
    if unknown and not c:
        return "fiyat bilinmiyor"
    return f"${c:.4f}" + (" + fiyatı bilinmeyenler" if unknown else "")


def summary(days: int = 30) -> str:
    since = datetime.now() - timedelta(days=days)
    data = rows(since)
    if not data:
        return f"Son {days} günde model kullanımı kaydı yok."
    by = defaultdict(lambda: [0, 0, 0.0, 0, 0])               # in, out, usd, çağrı, fiyatsız çağrı
    for r in data:
        a = by[(r["provider"], r["model"], r.get("task") or "-")]
        a[0] += r.get("in", 0)
        a[1] += r.get("out", 0)
        a[3] += 1
        if r.get("cost_usd") is None:
            a[4] += 1
        else:
            a[2] += r["cost_usd"]
    lines = [f"Model kullanımı — son {days} gün", "", f"{'sağlayıcı:model':40} {'görev':14} {'çağrı':>6} {'girdi':>9} {'çıktı':>9}  maliyet"]
    for (prov, model, task), a in sorted(by.items(), key=lambda kv: -kv[1][2]):
        lines.append(f"{prov + ':' + model:40.40} {task:14.14} {a[3]:>6} {a[0]:>9} {a[1]:>9}  {_fmt_cost(a[2], a[4] == a[3])}")
    total = sum(a[2] for a in by.values())
    lines += ["", f"Toplam: {_fmt_cost(total, any(a[4] for a in by.values()))}"]
    monthly, daily, _ = _limits()
    day, month = spent_today(), spent_month()
    lines.append(f"Bugün: ${day:.4f}" + (f" / ${daily:.2f} (%{day / daily * 100:.0f})" if daily else ""))
    lines.append(f"Bu ay: ${month:.4f}" + (f" / ${monthly:.2f} (%{month / monthly * 100:.0f})" if monthly else ""))
    return "\n".join(lines)
