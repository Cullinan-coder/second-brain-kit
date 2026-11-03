"""PyInstaller giriş noktası: `Second Brain.exe` / `.app` — hafif başlatıcı.

Kurulu kasayı bulur (`<veri>/kit.json` → `vault`; `SB_VAULT` ortamı önceliklidir), `<vault>/_system/.venv` Python'uyla `-m app.desktop`
başlatır (konsol penceresi açmadan, ayrık süreç) ve argümanları (`--minimized`) geçirir. Kurulum yoksa Setup'ı önerir.
Yalnız standart kütüphane kullanır (exe küçük kalsın).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SETUP_NAMES = ("Second Brain Setup.exe", "Second Brain Setup.app")
RELEASE_URL = "https://github.com/Cullinan-coder/second-brain-kit/releases/latest"
MISSING = ("Second Brain bu bilgisayarda kurulu görünmüyor.\n\n'Second Brain Setup' ile kurulum yapılsın mı?\n"
           "(Setup masaüstünde yoksa şu adresten indir: " + RELEASE_URL + ")")
NO_SETUP = "Setup bulunamadı. Şuradan indir:\n" + RELEASE_URL
BROKEN = "Second Brain'in Python ortamı bulunamadı:\n{path}\n\nSetup'ı yeniden çalıştırıp kurulumu onar."


def data_dir() -> Path:
    return Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain")


def read_install(data: Path | None = None) -> dict:
    try:
        return json.loads(((data or data_dir()) / "kit.json").read_text(encoding="utf-8"))
    except Exception:                                            # noqa: BLE001
        return {}


def find_system(data: Path | None = None) -> Path | None:
    """Kurulu `<vault>/_system` (içinde app/desktop.py olan) ya da None."""
    vault = os.environ.get("SB_VAULT") or read_install(data).get("vault")
    if not vault:
        return None
    s = Path(vault).expanduser() / "_system"
    return s if (s / "app" / "desktop.py").is_file() else None


def venv_python(system: Path, plat: str | None = None) -> Path:
    plat = plat or sys.platform
    if plat == "win32":
        py = system / ".venv" / "Scripts" / "pythonw.exe"           # pencereli: konsol açmaz
        return py if py.exists() else system / ".venv" / "Scripts" / "python.exe"
    return system / ".venv" / "bin" / "python"


def build_command(system: Path, argv: list[str], plat: str | None = None) -> list[str]:
    return [str(venv_python(system, plat)), "-m", "app.desktop", *argv]


def popen_kwargs(system: Path, plat: str | None = None) -> dict:
    plat = plat or sys.platform
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONHOME", "PYTHONPATH", "_MEIPASS2")}
    kw = dict(cwd=str(system), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if plat == "win32":
        kw["creationflags"] = 0x08000000 | 0x00000008 | 0x00000200      # NO_WINDOW | DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    return kw


def find_setup(plat: str | None = None, home: Path | None = None) -> Path | None:
    plat = plat or sys.platform
    home = home or Path.home()
    name = SETUP_NAMES[0] if plat == "win32" else SETUP_NAMES[1]
    for d in (home / "Desktop", home / "OneDrive" / "Desktop", home / "Downloads"):
        if (d / name).exists():
            return d / name
    return None


def ask(message: str, plat: str | None = None) -> bool:
    """Evet/Hayır sorusu (Windows MessageBox, macOS osascript); başarısızsa False."""
    plat = plat or sys.platform
    try:
        if plat == "win32":
            import ctypes
            return ctypes.windll.user32.MessageBoxW(0, message, "Second Brain", 0x4 | 0x20) == 6      # YESNO | ICONQUESTION
        if plat == "darwin":
            msg = message.replace("\\", "\\\\").replace('"', '\\"')
            r = subprocess.run(["osascript", "-e", f'button returned of (display dialog "{msg}" with title "Second Brain" '
                                'buttons {"Hayır", "Evet"} default button "Evet")'], capture_output=True, text=True, timeout=300)
            return "Evet" in (r.stdout or "")
    except Exception:                                            # noqa: BLE001
        pass
    print(message, file=sys.stderr)
    return False


def tell(message: str, plat: str | None = None) -> None:
    plat = plat or sys.platform
    try:
        if plat == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "Second Brain", 0x10)
            return
        if plat == "darwin":
            msg = message.replace("\\", "\\\\").replace('"', '\\"')
            subprocess.run(["osascript", "-e", f'display dialog "{msg}" with title "Second Brain" buttons {{"Tamam"}}'], timeout=300)
            return
    except Exception:                                            # noqa: BLE001
        pass
    print(message, file=sys.stderr)


def open_path(p: Path, plat: str | None = None) -> None:
    plat = plat or sys.platform
    if plat == "win32":
        os.startfile(str(p))                                     # type: ignore[attr-defined]
    else:
        subprocess.Popen(["open", str(p)])


def main(argv: list[str] | None = None, popen=subprocess.Popen, plat: str | None = None, data: Path | None = None,
         ask_fn=None, tell_fn=None, open_fn=None, home: Path | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    plat = plat or sys.platform
    ask_fn, tell_fn, open_fn = ask_fn or ask, tell_fn or tell, open_fn or open_path
    system = find_system(data)
    if system is None:
        if ask_fn(MISSING):
            setup = find_setup(plat, home)
            if setup:
                open_fn(setup)
            else:
                tell_fn(NO_SETUP)
        return 2
    py = venv_python(system, plat)
    if not py.exists():
        tell_fn(BROKEN.format(path=py))
        return 3
    popen(build_command(system, argv, plat), **popen_kwargs(system, plat))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
