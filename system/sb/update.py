"""`sb update`: kit kurulumunu son sürüme getirir — önce kodu yedekler, kit klasöründe git pull, sonra install.py --update.

Notlara, config/*.yaml'a ve şifre kasasına dokunulmaz. Kurulum yeri ~/.secondbrain/kit.json'dan okunur (install.py yazar).
- Yedek: güncellemeden önce _system kodu (sb, tools, tests, VERSION, pyproject, uv.lock) ~/.secondbrain/backups/ altına zip.
- `sb update --rollback`: son yedeği geri yükler (kişisel ayarlar korunur) ve `uv sync` çalıştırır.
- `sb update --recover`: yarım kalan güncellemeyi tamamlar (kodu kitten yeniden kurar).
- Güncelleme sürerken `update.pending` işareti yazılır; biterse silinir. `sb doctor` yarım kalanı gösterir.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from .config import DATA, SYSTEM

BACKUPS = DATA / "backups"
PENDING = DATA / "update.pending"
CODE = ("sb", "tools", "tests", "docs", "skills", "integrations", "VERSION", "features.yaml", "pyproject.toml", "uv.lock", ".python-version")
KEEP = 5


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


def backup(system: Path = SYSTEM, dest: Path = BACKUPS) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    z = dest / f"system-{version(system)}-{datetime.now():%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in CODE:
            src = system / item
            files = [src] if src.is_file() else [p for p in src.rglob("*") if p.is_file() and "__pycache__" not in p.parts] if src.exists() else []
            for f in files:
                zf.write(f, f.relative_to(system).as_posix())
    for old in sorted(dest.glob("system-*.zip"))[:-KEEP]:          # son 5 yedek kalır
        old.unlink()
    return z


def rollback(system: Path = SYSTEM, dest: Path = BACKUPS, sync: bool = True) -> int:
    zips = sorted(dest.glob("system-*.zip")) if dest.exists() else []
    if not zips:
        print("Yedek yok: henüz `sb update` ile güncelleme yapılmamış.")
        return 1
    z = zips[-1]
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        if any(n.startswith(("/", "..")) or ".." in Path(n).parts for n in names):
            print(f"Yedek bozuk ya da güvensiz yol içeriyor: {z.name}")
            return 1
        for d in ("sb", "tools", "tests"):                          # yedekte olmayan yeni dosyalar kalmasın
            if (system / d).exists() and any(n.startswith(d + "/") for n in names):
                shutil.rmtree(system / d)
        zf.extractall(system)
    PENDING.unlink(missing_ok=True)
    print(f"Geri yüklendi: {z.name} (sürüm {version(system)}). Kişisel ayarlar ve notlar değişmedi.")
    if sync:
        subprocess.run(["uv", "sync", "--quiet"], cwd=system)
    return 0


def _kit() -> tuple[Path, Path] | None:
    info = DATA / "kit.json"
    if not info.exists():
        print("Bu kurulum kitten yapılmamış (kit.json yok). Kaynak kasadaysan kiti `tools/build_kit.py` ile üretip yayınla.")
        return None
    cfg = json.loads(info.read_text(encoding="utf-8"))
    kit, vault = Path(cfg["kit"]), Path(cfg["vault"])
    if not (kit / ".git").exists():
        print(f"Kit klasörü bulunamadı ya da git deposu değil: {kit}. Repoyu yeniden klonlayıp install'ı çalıştır.")
        return None
    return kit, vault


def _install(kit: Path, vault: Path) -> int:
    PENDING.parent.mkdir(parents=True, exist_ok=True)
    PENDING.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
    r = subprocess.run(["uv", "run", "--no-project", "--python", "3.12", "--with", "pyyaml", "install.py", "--update",
                        "--vault", str(vault)], cwd=kit)
    if r.returncode == 0:
        PENDING.unlink(missing_ok=True)
    return r.returncode


def recover() -> int:
    k = _kit()
    if not k:
        return 1
    print("Yarım kalan güncelleme tamamlanıyor (kod kitten yeniden kuruluyor)...")
    return _install(*k)


def run(check_only: bool = False) -> int:
    k = _kit()
    if not k:
        return 1
    kit, vault = k
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
    z = backup()
    print(f"Yedek alındı: {z} (sorun olursa: sb update --rollback)")
    r = subprocess.run(git + ["pull", "--ff-only", "--quiet"])
    if r.returncode:
        print("git pull başarısız (kit klasöründe elle değişiklik mi var?). `git -C <kit> status` ile bak.")
        return 1
    if notes := changes(kit / "CHANGELOG.md", old):
        print("\nYenilikler:\n" + notes + "\n")
    rc = _install(kit, vault)
    if rc == 0:
        print("\nGüncellendi. Asistan açıksa yeniden başlat (bilgisayarı yeniden başlatmak da olur).")
    else:
        print("\nGüncelleme yarım kaldı: `sb update --recover` ile tamamla ya da `sb update --rollback` ile geri dön.")
    return rc


def set_mode(profile: str | None, cfg: Path = SYSTEM / "config" / "hafiza.yaml") -> str:
    if not cfg.exists():
        ex = cfg.with_name("hafiza.example.yaml")
        if ex.exists():
            shutil.copy2(ex, cfg)
    text = cfg.read_text(encoding="utf-8") if cfg.exists() else "profile: normal\n"
    cur = (re.search(r"^profile:\s*(\w+)", text, re.M) or [None, "normal"])[1]
    if not profile:
        return f"Hafıza modu: {cur}"
    text = re.sub(r"^profile:.*$", f"profile: {profile}", text, flags=re.M) if re.search(r"^profile:", text, re.M) \
        else f"profile: {profile}\n" + text
    cfg.write_text(text, encoding="utf-8")
    return f"Hafıza modu: {cur} → {profile} (yeni Claude Code oturumlarında geçerli)"


if __name__ == "__main__":
    sys.exit(run("--check" in sys.argv))
