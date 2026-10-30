"""`sb update`: kit kurulumunu son sürüme getirir — kit klasöründe git pull, sonra install.py --update (yalnız kod).

Notlara, config/*.yaml'a ve şifre kasasına dokunulmaz. Kurulum yeri ~/.secondbrain/kit.json'dan okunur (install.py yazar).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from .config import DATA, SYSTEM


def version(root: Path = SYSTEM) -> str:
    p = root / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.exists() else "?"


def changes(changelog: Path, old: str) -> str:
    """CHANGELOG.md'den kurulu sürümden yeni olan bölümler (## X.Y.Z başlıkları, en yeni üstte)."""
    if not changelog.exists():
        return ""
    out, keep = [], False
    for line in changelog.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"##\s+v?(\d+\.\d+\.\d+)", line):
            keep = m.group(1) != old
            if not keep:
                break
        if keep:
            out.append(line)
    return "\n".join(out).strip()


def run(check_only: bool = False) -> int:
    info = DATA / "kit.json"
    if not info.exists():
        print("Bu kurulum kitten yapılmamış (kit.json yok). Kaynak kasadaysan kiti `tools/build_kit.py` ile üretip yayınla.")
        return 1
    cfg = json.loads(info.read_text(encoding="utf-8"))
    kit, vault = Path(cfg["kit"]), Path(cfg["vault"])
    if not (kit / ".git").exists():
        print(f"Kit klasörü bulunamadı ya da git deposu değil: {kit}. Repoyu yeniden klonlayıp install'ı çalıştır.")
        return 1
    old = version()
    git = ["git", "-C", str(kit)]
    subprocess.run(git + ["fetch", "--quiet"], check=True)
    behind = subprocess.run(git + ["rev-list", "--count", "HEAD..@{u}"], capture_output=True, text=True).stdout.strip()
    new = subprocess.run(git + ["show", "@{u}:system/VERSION"], capture_output=True, text=True).stdout.strip() or "?"
    if behind == "0":
        print(f"Güncel: {old}")
        return 0
    print(f"Kurulu: {old} → yeni: {new} ({behind or '?'} değişiklik)")
    if check_only:
        return 0
    r = subprocess.run(git + ["pull", "--ff-only", "--quiet"])
    if r.returncode:
        print("git pull başarısız (kit klasöründe elle değişiklik mi var?). `git -C <kit> status` ile bak.")
        return 1
    if notes := changes(kit / "CHANGELOG.md", old):
        print("\nYenilikler:\n" + notes + "\n")
    r = subprocess.run(["uv", "run", "--no-project", "--python", "3.12", "--with", "pyyaml", "install.py", "--update",
                        "--vault", str(vault)], cwd=kit)
    if r.returncode == 0:
        print("\nGüncellendi. Asistan açıksa yeniden başlat (bilgisayarı yeniden başlatmak da olur).")
    return r.returncode


if __name__ == "__main__":
    sys.exit(run("--check" in sys.argv))
