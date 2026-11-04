"""Model yönlendirici (Faz 0.3): hangi istek hangi modele gider, hata olursa sıradaki hangisi, aynı istek tekrar edilir mi.

Ayar `config/llm.yaml`:
  tasks:     görev → varsayılan hedef ("ollama" | "claude" | "<sağlayıcı>:<model>")
  routing:   (isteğe bağlı) ilk eşleşen kural hedefi değiştirir:
               - {when: {min_chars: 40000}, use: "gemini:gemini-2.5-flash"}     # uzun metin
               - {when: {task: [project_deep]}, use: claude}
  fallback:  (isteğe bağlı) görev ya da "*" → hata olursa denenecek sıradakiler; yoksa fallback_to_local → ["ollama"]
  cache:     {enabled: true, ttl_days: 7, tasks: [...]}  — aynı (hedef, istem, şema) için önceki cevap
Gizlilik (madde 32): istem hassas veri (şifre, kart, TC kimlik, IBAN) içeriyorsa ya da çağıran `private=True` derse
zincirdeki BÜTÜN bulut hedefleri atılır; yalnız yerel hedefler (ollama, lmstudio, llamacpp, vllm) kalır. Hiç yerel hedef
yoksa "ollama" eklenir. Böylece gizli içerik hiçbir koşulda bilgisayardan çıkmaz.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from . import sensitive as _sensitive
from .config import DATA

LOCAL = {"ollama", "lmstudio", "llamacpp", "vllm"}
SENSITIVE_RE = _sensitive.TOPIC_RE           # tek kaynak sb/sensitive.py (D-30): sır konusu da buluta gitmez
CACHE_DIR = DATA / "llm_cache"


def provider_of(target: str) -> str:
    return target.split(":", 1)[0] if ":" in target else target


def is_local(target: str) -> bool:
    return provider_of(target) in LOCAL


def sensitive(text: str) -> bool:
    """Hassas içerik (bulut için sıkı): sır değeri ya da sır konusu sözcüğü YA DA redact.redact() metni değiştiriyorsa
    (API anahtarı, `*_PASSWORD=`, OTP, geçerli kart/TCKN/IBAN). "şifreli/şifreleme" hassas sayılmaz."""
    return _sensitive.is_sensitive(text, strict=True)


def cloud_safe_messages(messages: list[dict]) -> tuple[list[dict], bool]:
    """Asistan sohbeti için: mesajlardan biri hassassa `forced_local=True` döner (çağıran yalnız yerel modele gitmeli).
    Mesajlar değiştirilmez; içerik (str ya da parça listesi) taranır."""
    def _texts(m: dict):
        c = m.get("content") if isinstance(m, dict) else None
        if isinstance(c, str):
            yield c
        elif isinstance(c, list):
            for part in c:
                if isinstance(part, str):
                    yield part
                elif isinstance(part, dict) and isinstance(part.get("text"), str):
                    yield part["text"]
    def _hit(m: dict, t: str) -> bool:
        # Sistem talimatı (asistan kuralları, hafıza) kullanıcının kendi metnidir ve "kart numarası forma girilmez" gibi sır
        # KONUSU kurallar içerir: konu sözcüğü yüzünden her sohbet yerele düşüyordu. Orada yalnız sır DEĞERİ aranır;
        # kullanıcı mesajı ve araç/dış içerik sonuçları eskisi gibi sıkı (konu sözcüğü dahil) taranır.
        if isinstance(m, dict) and m.get("role") == "system":
            return _sensitive.is_sensitive(t, strict=False)
        return sensitive(t)
    forced = any(_hit(m, t) for m in messages for t in _texts(m))
    return messages, forced


def _match(when: dict, task: str, prompt: str) -> bool:
    tasks = when.get("task")
    if tasks and task not in ([tasks] if isinstance(tasks, str) else tasks):
        return False
    if "min_chars" in when and len(prompt) < int(when["min_chars"]):
        return False
    if "max_chars" in when and len(prompt) > int(when["max_chars"]):
        return False
    return True


def chain(cfg: dict, task: str, prompt: str = "", private: bool = False, default: str = "claude") -> list[str]:
    """Denenecek hedefler sırayla (ilk = asıl)."""
    target = str((cfg.get("tasks") or {}).get(task, default))
    for rule in cfg.get("routing") or []:
        if _match(rule.get("when") or {}, task, prompt):
            target = str(rule["use"])
            break
    fb = cfg.get("fallback") or {}
    rest = fb.get(task, fb.get("*")) if isinstance(fb, dict) else None
    if rest is None:
        rest = ["ollama"] if cfg.get("fallback_to_local") else []
    out = list(dict.fromkeys([target, *[str(x) for x in rest]]))
    if private or sensitive(prompt) or _strict_local():      # gizli/hassas ya da sıkı izin profili: yalnız bu bilgisayar
        out = [t for t in out if is_local(t)] or ["ollama"]
    return out


def _strict_local() -> bool:
    """İzin profili 'bulut' onayı istiyorsa (sıkı) hiçbir istek buluta gitmez."""
    try:
        from . import privacy
        return privacy.needs_approval("bulut")
    except Exception:                                         # noqa: BLE001 — profil okunamazsa SIKI: buluta gitme (D-26)
        return True


# ---------------------------------------------------------------- önbellek (madde 33)
def _cache_cfg(cfg: dict) -> dict:
    c = cfg.get("cache") or {}
    return {"enabled": bool(c.get("enabled", False)), "ttl_days": float(c.get("ttl_days", 7)), "tasks": c.get("tasks")}


def cacheable(cfg: dict, task: str) -> bool:
    c = _cache_cfg(cfg)
    return c["enabled"] and (c["tasks"] is None or task in c["tasks"]) and task not in ("chat", "flush")


def _path(target: str, prompt: str, schema: dict | None) -> Path:
    h = hashlib.sha256(json.dumps([target, prompt, schema], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return CACHE_DIR / h[:2] / f"{h}.json"


def cache_get(cfg: dict, target: str, prompt: str, schema: dict | None) -> tuple[str, str] | None:
    p = _path(target, prompt, schema)
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > _cache_cfg(cfg)["ttl_days"] * 86400:
        p.unlink(missing_ok=True)
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["text"], d["label"] + " (önbellek)"


def cache_put(target: str, prompt: str, schema: dict | None, text: str, label: str) -> None:
    p = _path(target, prompt, schema)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"text": text, "label": label}, ensure_ascii=False), encoding="utf-8")


def cache_clear() -> int:
    n = 0
    for p in CACHE_DIR.rglob("*.json") if CACHE_DIR.exists() else []:
        p.unlink()
        n += 1
    return n


# ---------------------------------------------------------------- uzun metin (madde 36)
def chunks(text: str, size: int, overlap: int = 400) -> list[str]:
    """Paragraf sınırında bölünmüş parçalar (her biri ≤ size karakter, küçük örtüşmeyle)."""
    if len(text) <= size:
        return [text]
    out, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            cut = text.rfind("\n\n", start + size // 2, end)
            end = cut if cut > 0 else end
        out.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return out
