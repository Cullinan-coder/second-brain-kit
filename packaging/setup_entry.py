"""PyInstaller giriş noktası: `Second Brain Setup.exe` / `.app` — kurulum sihirbazını açar.

Gömülü dosyalar (`sys._MEIPASS`): `kit/system`, `kit/vault` (kurulacak kod ve şablon kasa), `uv/` (uv.exe ya da uv),
`launcher/` (derlenmiş `Second Brain.exe`/`.app`; kurulum sonunda kalıcı yere kopyalanır), `setup/ui` (sihirbaz arayüzü).
Motor (`setup/engine.py`) kit_dir() ile `_MEIPASS/kit`'i bulur; kasa/kod sihirbazın seçtiği konuma kopyalanır, geçici klasöre değil.
Paketli değilken de çalışır: `python packaging/setup_entry.py` (kit kökü ya da _system içinden).
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent


def bundle_root() -> Path | None:
    mp = getattr(sys, "_MEIPASS", None)
    return Path(mp) if mp else None


def uv_name(plat: str | None = None) -> str:
    return "uv.exe" if (plat or sys.platform) == "win32" else "uv"


def find_bundled_uv(root: Path | None, plat: str | None = None) -> Path | None:
    if not root:
        return None
    p = root / "uv" / uv_name(plat)
    return p if p.is_file() else None


def configure_environment(env=None, root: Path | None = None, plat: str | None = None) -> dict:
    """Gömülü uv'yi `SB_UV` ile motora bildirir (PATH'te uv varsa motor onu tercih eder). Döner: eklenen değişkenler."""
    env = os.environ if env is None else env
    root = root if root is not None else bundle_root()
    added = {}
    uv = find_bundled_uv(root, plat)
    if uv and not env.get("SB_UV"):
        added["SB_UV"] = str(uv)
    env.update(added)
    return added


def _ensure_streams() -> None:
    """Pencereli (konsolsuz) paketli uygulamada stdout/stderr None olur; print çökmesin."""
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


def _log_error(text: str) -> Path | None:
    try:
        d = Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain")
        d.mkdir(parents=True, exist_ok=True)
        p = d / "setup-error.log"
        p.write_text(text, encoding="utf-8")
        return p
    except Exception:                                            # noqa: BLE001
        return None


def _add_dev_paths() -> None:
    """Paketli değilken: kit kökü (system/) ya da _system içinden çalışıyoruz."""
    for base in (HERE.parent, HERE.parent / "system"):
        if (base / "setup" / "app.py").is_file() and str(base) not in sys.path:
            sys.path.insert(0, str(base))
            break


def main(argv: list[str] | None = None) -> int:
    _ensure_streams()
    if bundle_root() is None:
        _add_dev_paths()
    configure_environment()
    try:
        from setup import app as setup_app, server as setup_server
        sys.modules.setdefault("server", setup_server)           # app._load_server() `import server` der
        return int(setup_app.main(argv if argv is not None else sys.argv[1:]) or 0)
    except SystemExit:
        raise
    except Exception:                                            # noqa: BLE001
        log = _log_error(traceback.format_exc())
        print(f"Second Brain Setup başlatılamadı. Ayrıntı: {log}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
