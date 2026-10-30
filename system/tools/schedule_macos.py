"""macOS zamanlanmış görevleri (launchd, kullanıcı oturumu): Windows'taki tools/schedule.ps1'in karşılığı.

  python3 tools/schedule_macos.py            # kur / güncelle
  python3 tools/schedule_macos.py --remove   # kaldır
  python3 tools/schedule_macos.py --restart-chat

Görevler: günlük (13:00 + oturum açılınca; aynı gün ikinci kez çalışmaz), haftalık (Pazar 15:00), asistan sunucusu (oturum açılınca,
çökerse yeniden başlar). Kayıtlar ~/.secondbrain/logs/. NOT: Windows'ta yazıldı, macOS'ta gerçek cihazda doğrulanmadı.
"""
from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[1]
AGENTS = Path.home() / "Library" / "LaunchAgents"
LOGS = Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain") / "logs"
PREFIX = "com.secondbrain."
UV = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")


def _job(cmd: str) -> list[str]:
    return [UV, "run", "--directory", str(SYSTEM), "python", "-X", "utf8", "-m", "sb", cmd]


JOBS = {
    "daily": {"ProgramArguments": _job("daily"), "RunAtLoad": True,
              "StartCalendarInterval": {"Hour": 13, "Minute": 0}},
    "weekly": {"ProgramArguments": _job("weekly"), "StartCalendarInterval": {"Weekday": 0, "Hour": 15, "Minute": 0}},
    "chat": {"ProgramArguments": _job("chat"), "RunAtLoad": True, "KeepAlive": True},
}


def _domain() -> str:
    return f"gui/{os.getuid()}"


def install() -> None:
    AGENTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    for name, spec in JOBS.items():
        label = PREFIX + name
        plist = AGENTS / f"{label}.plist"
        body = {"Label": label, "WorkingDirectory": str(SYSTEM), "StandardOutPath": str(LOGS / f"{name}.out.log"),
                "StandardErrorPath": str(LOGS / f"{name}.err.log"),
                "EnvironmentVariables": {"PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + str(Path(UV).parent)}, **spec}
        subprocess.run(["launchctl", "bootout", _domain(), str(plist)], capture_output=True)
        plist.write_bytes(plistlib.dumps(body))
        r = subprocess.run(["launchctl", "bootstrap", _domain(), str(plist)], capture_output=True, text=True)
        print(f"{'Kuruldu' if r.returncode == 0 else 'HATA'}: {label} {r.stderr.strip()}")


def remove() -> None:
    for name in JOBS:
        plist = AGENTS / f"{PREFIX}{name}.plist"
        subprocess.run(["launchctl", "bootout", _domain(), str(plist)], capture_output=True)
        plist.unlink(missing_ok=True)
        print(f"Kaldırıldı: {PREFIX}{name}")


def restart_chat() -> None:
    subprocess.run(["launchctl", "kickstart", "-k", f"{_domain()}/{PREFIX}chat"], check=False)
    print("Asistan yeniden başlatıldı.")


if __name__ == "__main__":
    if sys.platform != "darwin":
        raise SystemExit("Bu betik macOS içindir; Windows'ta tools/schedule.ps1 kullan.")
    {"--remove": remove, "--restart-chat": restart_chat}.get(sys.argv[1] if len(sys.argv) > 1 else "", install)()
