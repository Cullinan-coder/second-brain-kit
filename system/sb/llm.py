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


def complete(task: str, prompt: str, *, schema: dict | None = None, model: str = "sonnet", timeout: int = 1200) -> tuple[str, str]:
    cfg = config()
    if cfg["tasks"].get(task, "claude") == "ollama":
        return ollama_chat(prompt, cfg, schema, timeout), label(cfg)
    try:
        return claude_text(prompt, model, timeout, schema), "claude"
    except Exception as e:
        if not cfg.get("fallback_to_local"):
            raise
        return ollama_chat(prompt, cfg, schema, timeout), label(cfg, f"Claude yedeği: {str(e)[:70]}")


def is_local(lbl: str) -> bool:
    return lbl.startswith("yerel")
