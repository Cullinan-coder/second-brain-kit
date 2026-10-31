"""Claude Code durum çubuğu: model · proje · git dalı · bağlam doluluğu · kullanım limitleri · hafıza modu.

~/.claude/settings.json: "statusLine": {"type": "command", "command": "<python> <kasa>/_system/tools/statusline.py"}
Girdi stdin'den gelen JSON'dur. Alan yoksa o parça gösterilmez. Ağa çıkmaz; dökümün yalnız son ~300 KB'ını okur.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "config" / "hafiza.yaml"


def _git(cwd: str) -> str:
    try:
        b = subprocess.run(["git", "-C", cwd, "branch", "--show-current"], capture_output=True, text=True, timeout=2).stdout.strip()
        if not b:
            return ""
        dirty = subprocess.run(["git", "-C", cwd, "status", "--porcelain", "-uno"], capture_output=True, text=True, timeout=2).stdout.strip()
        return f"⎇ {b}{'*' if dirty else ''}"
    except Exception:
        return ""


def _context(d: dict) -> str:
    cw = d.get("context_window") or {}
    pct = cw.get("used_percentage") if isinstance(cw, dict) else None
    if pct is None:
        tp = d.get("transcript_path")
        size = (cw.get("context_window_size") if isinstance(cw, dict) else None) or 200_000
        try:
            with open(tp, "rb") as f:
                f.seek(max(0, os.path.getsize(tp) - 300_000))
                lines = f.read().decode("utf-8", "replace").splitlines()
            for line in reversed(lines):
                if '"usage"' not in line:
                    continue
                u = (json.loads(line).get("message") or {}).get("usage") or {}
                used = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                if used:
                    if used > size:                                   # 1M bağlamlı model: pencere boyutu girdide yoksa
                        size = 1_000_000
                    pct = 100 * used / size
                    break
        except Exception:
            return ""
    if pct is None:
        return ""
    full = max(0, min(8, int(pct // 12.5)))
    bar = "▓" * full + "░" * (8 - full)
    return f"{bar} %{pct:.0f}"


def _limits(d: dict) -> str:
    rl = d.get("rate_limits") or {}
    out = []
    for key, label in (("five_hour", "5s"), ("seven_day", "7g")):
        v = rl.get(key) if isinstance(rl, dict) else None
        pct = v.get("used_percentage") if isinstance(v, dict) else v
        if isinstance(pct, (int, float)):
            out.append(f"{label} %{pct:.0f}")
    return " · ".join(out)


def _mode() -> str:
    try:
        m = re.search(r"^profile:\s*(\w+)", CONFIG.read_text(encoding="utf-8"), re.M)
        return "" if not m or m.group(1) == "normal" else f"🧠 {m.group(1)}"
    except OSError:
        return ""


def main() -> None:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        d = {}
    model = (d.get("model") or {}).get("display_name") or ""
    cwd = (d.get("workspace") or {}).get("current_dir") or d.get("cwd") or os.getcwd()
    parts = [model, Path(cwd).name, _git(cwd), _context(d), _limits(d), _mode()]
    sys.stdout.reconfigure(encoding="utf-8")
    print(" · ".join(p for p in parts if p))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("")
