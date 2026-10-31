"""`sb` komutunu her klasörden çalışır yapar: ~/.local/bin/sb (macOS/Linux) ya da ~/.local/bin/sb.cmd (Windows).

Kasa yerinden bağımsız: bu betiğin bulunduğu _system'in .venv Python'unu kullanır. Tekrar çalıştırılabilir.
~/.local/bin PATH'te değilse ne yapılacağını söyler.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[1]
BIN = Path.home() / ".local" / "bin"


def main() -> int:
    BIN.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        py = SYSTEM / ".venv" / "Scripts" / "python.exe"
        target = BIN / "sb.cmd"
        target.write_text(f'@echo off\r\nsetlocal\r\nset "PYTHONPATH={SYSTEM}"\r\n"{py}" -X utf8 -m sb %*\r\n', encoding="utf-8")
    else:
        py = SYSTEM / ".venv" / "bin" / "python"
        target = BIN / "sb"
        target.write_text(f'#!/bin/sh\nPYTHONPATH="{SYSTEM}" exec "{py}" -X utf8 -m sb "$@"\n', encoding="utf-8")
        target.chmod(0o755)
    on_path = str(BIN).lower() in os.environ.get("PATH", "").lower()
    print(f"Kuruldu: {target}" + ("" if on_path else f"\nUyarı: {BIN} PATH'te değil; kabuk ayarına ekle."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
