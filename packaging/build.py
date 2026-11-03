"""Yerel derleme: `Second Brain.exe` (başlatıcı) + `Second Brain Setup.exe` (kurulum sihirbazı) — Windows ya da macOS'ta.

  python packaging/build.py [--kit KIT_KLASÖRÜ] [--uv UV_YOLU] [--out DIST] [--only app|setup]

Kit klasörü (system/ + vault/ içeren; `tools/build_kit.py` üretir) varsayılan olarak bu betiğin üst klasörüdür (kit deposunda
packaging/ kök altındadır). Sıra: simgeler → app.spec → Setup'a gömülecek başlatıcı → setup.spec → release/ (GitHub Release dosyaları).
Gereken: `pip install pyinstaller pyyaml pywebview keyring send2trash pillow` (pillow yalnız simge üretimi için), `uv` PATH'te ya da --uv.
Release dosya adları boşluksuzdur (GitHub varlık adlarında boşluk noktaya çevrilir); masaüstüne indirirken boşluklu ada çevrilir.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAC = sys.platform == "darwin"
WIN = sys.platform == "win32"
APP = "Second Brain"
SETUP = "Second Brain Setup"
RELEASE_WIN = {"setup": "Second-Brain-Setup.exe"}
RELEASE_MAC = {"setup": "Second-Brain-Setup-macOS.zip"}


def make_icons(force: bool = False) -> None:
    """icon.png/.ico/.icns yoksa (ya da force) Pillow ile çizer: koyu yuvarlak kare + açık konuşma balonu (sb/web/icon.svg'nin sadeleşmişi)."""
    targets = [HERE / "icon.ico", HERE / "icon.icns"]
    if not force and all(t.exists() for t in targets):
        return
    from PIL import Image, ImageDraw
    n = 1024
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, n - 1, n - 1), radius=int(n * 112 / 512), fill="#1f2937")
    k = n / 512
    d.ellipse((144 * k, 112 * k, 368 * k, 328 * k), fill="#a5b4fc")
    d.polygon([(166 * k, 270 * k), (150 * k, 330 * k), (230 * k, 310 * k)], fill="#a5b4fc")
    d.ellipse((198 * k, 200 * k, 230 * k, 232 * k), fill="#1f2937")
    d.ellipse((282 * k, 200 * k, 314 * k, 232 * k), fill="#1f2937")
    im.resize((512, 512), Image.LANCZOS).save(HERE / "icon.png")
    im.save(HERE / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    try:
        im.save(HERE / "icon.icns")
    except Exception as e:                                        # noqa: BLE001
        print("icns yazılamadı (macOS'ta yeniden denenir):", e)


def run(cmd: list[str], env: dict | None = None) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, env=env)


def pyinstaller(spec: Path, dist: Path, work: Path, env: dict) -> None:
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(dist), "--workpath", str(work), str(spec)], env)


def find_uv(arg: str | None) -> Path:
    p = Path(arg) if arg else Path(shutil.which("uv") or "")
    if not p.is_file():
        raise SystemExit("uv bulunamadı: PATH'e ekle ya da --uv ver (Setup'a gömülür)")
    return p.resolve()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kit", default=str(HERE.parent))
    ap.add_argument("--uv")
    ap.add_argument("--out", default=str(HERE.parent / "dist"))
    ap.add_argument("--only", choices=("app", "setup"))
    a = ap.parse_args(argv)
    kit, out = Path(a.kit).resolve(), Path(a.out).resolve()
    if not (kit / "system" / "sb").is_dir() or not (kit / "vault").is_dir():
        raise SystemExit(f"{kit} bir kit klasörü değil (system/ ve vault/ gerekir). Önce: python tools/build_kit.py")
    make_icons()
    work = out / "_work"
    launcher = out / "launcher"
    release = out / "release"
    for d in (launcher, release):
        d.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "SB_KIT_ROOT": str(kit), "SB_LAUNCHER_DIR": str(launcher)}

    app_item = APP + (".app" if MAC else ".exe")
    if a.only != "setup":
        pyinstaller(HERE / "app.spec", out / "app", work / "app", env)
        built = out / "app" / app_item
        dst = launcher / app_item
        shutil.rmtree(dst) if dst.is_dir() else dst.unlink(missing_ok=True)
        shutil.copytree(built, dst, symlinks=True) if built.is_dir() else shutil.copy2(built, dst)
    if a.only != "app":
        env["SB_UV_BIN"] = str(find_uv(a.uv))
        pyinstaller(HERE / "setup.spec", out / "setup", work / "setup", env)
        if MAC:
            zip_path = release / RELEASE_MAC["setup"]
            zip_path.unlink(missing_ok=True)
            run(["ditto", "-c", "-k", "--keepParent", str(out / "setup" / (SETUP + ".app")), str(zip_path)])
        else:
            shutil.copy2(out / "setup" / (SETUP + ".exe"), release / RELEASE_WIN["setup"])
    print("\nHazır:", ", ".join(sorted(p.name for p in release.iterdir())), "→", release)
    return 0


if __name__ == "__main__":
    sys.exit(main())
