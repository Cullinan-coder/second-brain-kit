"""Model sağlayıcı katmanı: görev başına Claude (`claude -p`) ya da yerel Qwen (Ollama); Claude hatasında yerele düşme.

`complete(task, prompt)` → (metin, etiket). Etiket "claude" ya da "yerel qwen3:14b" (+ yedek notu); çağıranlar yerel
üretimi notta işaretler. Yerel çağrı sadece localhost'a gider; hiçbir veri dışarı çıkmaz.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

from .config import DATA, SYSTEM

THINK_RE = re.compile(r"<think>.*?</think>", re.S)


def config() -> dict:
    return yaml.safe_load((SYSTEM / "config" / "llm.yaml").read_text(encoding="utf-8"))


def strip_think(text: str) -> str:
    return THINK_RE.sub("", text).strip()


def clip(text: str, max_chars: int) -> str:
    """Çok uzun metinde başın %60'ı ve sonun %40'ı kalır (ortası kısaltılır)."""
    if len(text) <= max_chars:
        return text
    head = int(max_chars * 0.6)
    return text[:head] + "\n\n… (yerel model bağlamına sığmadığı için ortası kısaltıldı) …\n\n" + text[-(max_chars - head):]


def _http(host: str, path: str, payload: dict | None, timeout: int) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(host + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def ollama_up(host: str) -> bool:
    try:
        _http(host, "/api/tags", None, 3)
        return True
    except (OSError, urllib.error.URLError, ValueError):
        return False


def ensure_ollama(cfg: dict, wait: int = 60) -> None:
    host = cfg["ollama"]["host"]
    if ollama_up(host):
        return
    exe = shutil.which("ollama") or str(Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe")
    if not Path(exe).exists() and not shutil.which("ollama"):
        raise RuntimeError("Ollama kurulu değil")
    subprocess.Popen([exe, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                     creationflags=0x00000008 | 0x08000000)           # DETACHED_PROCESS | CREATE_NO_WINDOW
    for _ in range(wait):
        if ollama_up(host):
            return
        time.sleep(1)
    raise RuntimeError(f"Ollama {wait} sn içinde açılmadı")


def ollama_chat(prompt: str, cfg: dict, schema: dict | None = None, timeout: int = 1800) -> str:
    o = cfg["ollama"]
    ensure_ollama(cfg)
    payload = {"model": o["model"], "stream": False, "think": o.get("think", False),
               "messages": [{"role": "user", "content": clip(prompt, o["max_chars"])}],
               "options": {"num_ctx": o["num_ctx"], "temperature": 0.2}}
    if schema:
        payload["format"] = schema
    out = _http(o["host"], "/api/chat", payload, timeout)
    return strip_think(out["message"]["content"])


def claude_text(prompt: str, model: str = "sonnet", timeout: int = 1200, schema: dict | None = None) -> str:
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--tools", "", "--strict-mcp-config", "--no-session-persistence"]
    if schema:
        cmd += ["--json-schema", json.dumps(schema)]
    work = DATA / "work"
    work.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", cwd=work, timeout=timeout,
                          env=dict(os.environ))
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"claude -p hata verdi ({proc.returncode}): {(proc.stderr or proc.stdout).strip()[:300]}")
    if out.get("is_error"):
        raise RuntimeError(f"claude -p hata verdi: {out.get('result')}")
    if schema and out.get("structured_output") is not None:
        return json.dumps(out["structured_output"], ensure_ascii=False)
    return out.get("result", "")


def label(cfg: dict, note: str = "") -> str:
    return f"yerel {cfg['ollama']['model']}" + (f" ({note})" if note else "")


def _run(cfg: dict, target: str, prompt: str, schema: dict | None, model: str, timeout: int, task: str) -> tuple[str, str]:
    if target == "ollama":
        return ollama_chat(prompt, cfg, schema, timeout), label(cfg)
    if target == "claude":
        return claude_text(prompt, model, timeout, schema), "claude"
    from . import providers                                  # "<sağlayıcı>:<model>" → bulut API ya da yerel sunucu
    out = providers.chat(target, [{"role": "user", "content": prompt}], schema=schema, timeout=timeout, task=task)
    return out["content"], f"api {target}"


def complete(task: str, prompt: str, *, schema: dict | None = None, model: str = "sonnet", timeout: int = 1200,
             private: bool = False) -> tuple[str, str]:
    """Yönlendiricinin zincirindeki hedefleri sırayla dener (router.chain). `private=True` ya da istemde hassas veri varsa
    yalnız yerel modeller kullanılır. Önbellek açıksa aynı istek yeniden üretilmez."""
    from . import router
    cfg = config()
    targets = router.chain(cfg, task, prompt, private)
    use_cache = router.cacheable(cfg, task)
    err: tuple[str, Exception] | None = None
    for target in targets:
        if use_cache and (hit := router.cache_get(cfg, target, prompt, schema)):
            return hit
        try:
            text, lbl = _run(cfg, target, prompt, schema, model, timeout, task)
        except Exception as e:
            err = err or (target, e)
            continue
        if err:                                              # yedek hedef cevap verdi: etikette neden düşüldüğü
            first, e = err
            why = f"{'Claude' if first == 'claude' else 'API'} yedeği: {str(e)[:70]}"
            lbl = label(cfg, why) if target == "ollama" else f"{lbl} ({why})"
        if use_cache:
            router.cache_put(target, prompt, schema, text, lbl)
        return text, lbl
    raise err[1] if err else RuntimeError("model zinciri boş")


def long_complete(task: str, instruction: str, text: str, *, chunk_chars: int = 0, timeout: int = 1200,
                  private: bool = False) -> tuple[str, str]:
    """Bağlama sığmayan metin (madde 36): parçalara böl, her parçayı talimatla işle, sonra parça sonuçlarını birleştir."""
    from . import router
    size = chunk_chars or int(config()["ollama"].get("max_chars", 60000)) - len(instruction) - 2000
    if not private and router.sensitive(f"{instruction}\n{text}"):   # hassaslık BÜTÜN metinde bir kez; parçalara taşınır
        private = True
    parts = router.chunks(text, max(size, 4000))
    if len(parts) == 1:
        return complete(task, f"{instruction}\n\n{text}", timeout=timeout, private=private)
    notes, lbl = [], ""
    for i, part in enumerate(parts, 1):
        out, lbl = complete(task, f"{instruction}\n\n[Uzun metnin {i}/{len(parts)}. parçası — yalnız bu parçaya göre çalış, "
                                  f"kısa yaz]\n{part}", timeout=timeout, private=private)
        notes.append(f"### Parça {i}\n{strip_think(out)}")
    final, lbl = complete(task, f"{instruction}\n\nAşağıdakiler aynı metnin {len(parts)} parçasından çıkarılan ara sonuçlar. "
                                f"Bunları birleştirip tek, tekrarsız sonuç yaz:\n\n" + "\n\n".join(notes),
                          timeout=timeout, private=private)
    return final, f"{lbl} · {len(parts)} parça"


def is_local(lbl: str) -> bool:
    return lbl.startswith("yerel")
