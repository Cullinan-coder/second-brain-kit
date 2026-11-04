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
CODE = ("sb", "tools", "tests", "docs", "skills", "integrations", "setup", "VERSION", "features.yaml", "pyproject.toml", "uv.lock", ".python-version")
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
        subprocess.run(["uv", "sync", "--inexact", "--quiet"], cwd=system)
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


def _latest_tag(git: list[str]) -> str:
    out = subprocess.run(git + ["tag", "--list", "v[0-9]*", "--sort=-v:refname"], capture_output=True, text=True).stdout.split()
    return out[0] if out else ""


def preview(git: list[str], target: str) -> tuple[str, int]:
    """Gelecek commit'lerin özeti (`git log HEAD..<hedef> --oneline`) ve değişen dosya sayısı."""
    log = subprocess.run(git + ["log", f"HEAD..{target}", "--oneline"], capture_output=True, text=True).stdout.strip()
    files = subprocess.run(git + ["diff", "--name-only", f"HEAD...{target}"], capture_output=True, text=True).stdout.split()
    return log, len(files)


def run(check_only: bool = False, yes: bool = False, tags_only: bool = False) -> int:
    k = _kit()
    if not k:
        return 1
    kit, vault = k
    old = version()
    git = ["git", "-C", str(kit)]
    subprocess.run(git + ["fetch", "--quiet", "--tags"], check=True)
    target = "@{u}"
    if tags_only:
        target = _latest_tag(git)
        if not target:
            print("Etiketli sürüm yok (v1.2.3 gibi); --tags-only ile güncellenemez.")
            return 1
    behind = subprocess.run(git + ["rev-list", "--count", f"HEAD..{target}"], capture_output=True, text=True).stdout.strip()
    new = subprocess.run(git + ["show", f"{target}:system/VERSION"], capture_output=True, text=True).stdout.strip() or "?"
    if behind == "0":
        print(f"Güncel: {old}")
        return 0
    print(f"Kurulu: {old} → yeni: {new} ({behind or '?'} değişiklik" + (f", etiket {target}" if tags_only else "") + ")")
    log, nfiles = preview(git, target)
    if log:
        print("\nGelecek commit'ler:\n" + "\n".join("  " + ln for ln in log.splitlines()[:30]) + f"\nDeğişen dosya: {nfiles}\n")
    if check_only:
        return 0
    if not yes:                                              # çekmeden ÖNCE onay: kit deposundaki kod bilgisayarda çalışacak
        try:
            ok = sys.stdin.isatty() and input("Bu değişiklikler çekilsin mi? [e/H] ").strip().lower() in ("e", "evet", "y", "yes")
        except EOFError:
            ok = False
        if not ok:
            print("Onaylanmadı; güncelleme yapılmadı (onaysız çalıştırmak için --yes).")
            return 1
    z = backup()
    print(f"Yedek alındı: {z} (sorun olursa: sb update --rollback)")
    r = subprocess.run(git + (["merge", "--ff-only", "--quiet", target] if tags_only else ["pull", "--ff-only", "--quiet"]))
    if r.returncode:
        print("git pull başarısız (kit klasöründe elle değişiklik mi var?). `git -C <kit> status` ile bak.")
        return 1
    if notes := changes(kit / "CHANGELOG.md", old):
        print("\nYenilikler:\n" + notes + "\n")
    rc = _install(kit, vault)
    if rc == 0:
        mrc = migrate_after_update(vault, yes)
        print("\nGüncellendi. Asistan açıksa yeniden başlat (bilgisayarı yeniden başlatmak da olur).")
        return mrc
    else:
        print("\nGüncelleme yarım kaldı: `sb update --recover` ile tamamla ya da `sb update --rollback` ile geri dön.")
    return rc


def _run_migrate(vault: Path, *args: str) -> subprocess.CompletedProcess:
    """Göçü YENİ kodla çalıştır (bu süreç eski kodu yüklü): kasadaki _system'den ayrı süreç."""
    import os
    return subprocess.run(["uv", "run", "--directory", str(Path(vault) / "_system"), "python", "-X", "utf8", "-m", "sb", "migrate", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "SB_VAULT": str(vault)})


def migrate_after_update(vault: Path, yes: bool = False) -> int:
    """Güncelleme sonrası bekleyen kasa şeması göçlerini listele, onayla (ya da --yes ile) uygula. 0 = göç yok/uygulandı/ertelendi."""
    r = _run_migrate(vault, "--check")
    if r.returncode == 0:
        return 0
    if r.stdout:
        print("\n" + r.stdout.strip())
    if r.returncode != 3:                                       # bekleyen göç değil: sorun (kasa koddan yeni, bozuk sürüm...)
        print(r.stderr.strip()[:300] or "Kasa şeması denetlenemedi; `sb doctor` ile bak.")
        return 0
    if not yes:
        try:
            ok = sys.stdin.isatty() and input("Kasa şeması göçü uygulansın mı? (önce şifreli yedek alınır, tek commit atılır) [e/H] ").strip().lower() in ("e", "evet", "y", "yes")
        except EOFError:
            ok = False
        if not ok:
            print("Göç ertelendi; hazır olunca `sb migrate --yes` (önce `sb migrate --dry-run`).")
            return 0
    m = _run_migrate(vault, "--yes")
    print((m.stdout or "").strip())
    if m.returncode:
        print("Göç uygulanamadı (kasa olduğu gibi bırakıldı); `sb migrate --check` ve `sb doctor` ile bak.")
        return 1
    return 0


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
