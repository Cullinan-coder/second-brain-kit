"""Uygulamayı oturum açılışında başlatma. YALNIZ kullanıcı sihirbazda "evet" derse (`on: true`) bir şey yazılır.

Windows: Başlangıç klasörüne `Second Brain.lnk` (PowerShell + WScript.Shell, `engine._run_capture` üzerinden; ya da `.cmd` yedeği).
macOS: `~/Library/LaunchAgents/com.secondbrain.app.plist` (launchctl çağrılmaz; sonraki oturum açılışında devreye girer).
Komut: paketli exe varsa `Second Brain.exe --minimized`, yoksa `<_system>/.venv/Scripts/pythonw.exe -m app.desktop --minimized`.
"""
from __future__ import annotations

import json
import os
import plistlib
import sys
from pathlib import Path

try:
    from . import engine as E
except ImportError:                                           # pragma: no cover
    import engine as E  # type: ignore

LNK = "Second Brain.lnk"
PLIST = "com.secondbrain.app.plist"
EXE_NAMES = ("Second Brain.exe", "SecondBrain.exe")


def startup_dir() -> Path:
    if E.sandbox_dir():                                       # deneme kipi: gerçek Başlangıç klasörüne yazma
        return E.sandbox_dir() / "Startup"
    return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def launch_agents_dir() -> Path:
    if E.sandbox_dir():
        return E.sandbox_dir() / "LaunchAgents"
    return Path.home() / "Library" / "LaunchAgents"


def _state_file(eng) -> Path:
    return eng.data / "autostart.json"


def launch_command(eng, minimized: bool, plat: str) -> tuple[str, list[str], str]:
    """(program, argümanlar, çalışma dizini)."""
    root = eng.code_root()
    flag = ["--minimized"] if minimized else []
    packed = E.launcher_exe(eng.data, plat)                   # kurulumun yazdığı paketli başlatıcı (Second Brain.exe / .app)
    if packed:
        return str(packed), flag, str(root)
    for base in (root, root / "app", root / "dist", root / "app" / "dist"):
        for n in EXE_NAMES:
            if (base / n).is_file():
                return str(base / n), flag, str(root)
    if plat == "win32":
        py = root / ".venv" / "Scripts" / "pythonw.exe"
        if not py.is_file():
            alt = Path(sys.executable).with_name("pythonw.exe")      # deneme kipinde çalışan kurulumun python'una BAĞLANMA
            py = alt if (alt.is_file() and not E.sandbox_dir()) else py
    else:
        py = root / ".venv" / "bin" / "python"
    return str(py), ["-m", "app.desktop", *flag], str(root)


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def status(eng, plat: str | None = None) -> dict:
    plat = plat or sys.platform
    st = {}
    try:
        st = json.loads(_state_file(eng).read_text(encoding="utf-8"))
    except Exception:                                         # noqa: BLE001
        pass
    if plat == "win32":
        p = startup_dir()
        on = (p / LNK).exists() or (p / "Second Brain.cmd").exists()
    elif plat == "darwin":
        on = (launch_agents_dir() / PLIST).exists()
    else:
        return {"supported": False, "on": False, "minimized": False}
    return {"supported": True, "on": on, "minimized": bool(st.get("minimized", True))}


def apply(eng, on: bool, minimized: bool = True, plat: str | None = None) -> dict:
    plat = plat or sys.platform
    if plat not in ("win32", "darwin"):
        return {"ok": False, "supported": False, "message": "Bu sistemde otomatik başlatma desteklenmiyor"}
    if not isinstance(on, bool):
        raise ValueError("on: true/false olmalı")
    prog, args, cwd = launch_command(eng, bool(minimized), plat)
    if plat == "win32":
        d = startup_dir()
        lnk, cmdf = d / LNK, d / "Second Brain.cmd"
        if not on:
            for f in (lnk, cmdf):
                if f.exists():
                    f.unlink()                                # yalnız bizim yazdığımız kısayol
        else:
            d.mkdir(parents=True, exist_ok=True)
            ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut(" + _ps_quote(str(lnk)) + ");"
                  f"$s.TargetPath={_ps_quote(prog)};$s.Arguments={_ps_quote(' '.join(args))};$s.WorkingDirectory={_ps_quote(cwd)};"
                  "$s.WindowStyle=7;$s.Save()")
            rc, out = E._run_capture(["powershell", "-NoProfile", "-Command", ps], 30)
            if rc != 0 or not lnk.exists():                   # yedek: .cmd
                cmdf.write_text(f'@echo off\r\ncd /d "{cwd}"\r\nstart "" /min "{prog}" {" ".join(args)}\r\n', encoding="utf-8")
    else:
        pl = launch_agents_dir() / PLIST
        if not on:
            if pl.exists():
                pl.unlink()
        else:
            pl.parent.mkdir(parents=True, exist_ok=True)
            pl.write_bytes(plistlib.dumps({"Label": "com.secondbrain.app", "ProgramArguments": [prog, *args], "WorkingDirectory": cwd,
                                           "RunAtLoad": True, "ProcessType": "Interactive"}))
    eng.data.mkdir(parents=True, exist_ok=True)
    _state_file(eng).write_text(json.dumps({"on": on, "minimized": bool(minimized)}), encoding="utf-8")
    return {"ok": True, **status(eng, plat), "command": [prog, *args] if on else []}
