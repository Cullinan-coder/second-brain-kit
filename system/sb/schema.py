"""Kasa şema sürümü ve göç sistemi.

Kasa biçimi (ön bilgi alanı, klasör/dosya adı kuralı, config anahtarı) değişirse eski kasalar bozulmasın diye:
- Kasa sürümü `_system/config/kasa.yaml` içindeki `schema_version: N`. Dosya/anahtar yoksa **1** (mevcut kasalar).
- Kodun beklediği sürüm `CURRENT`. Göçler `sb/migrations/m000N_*.py` (bkz. oradaki `__init__`).
- Her göç adımı: git temiz mi → şifreli yedek → `up()` → sürüm damgası → tek commit («şema göçü N→M»).
  Herhangi bir adım patlarsa YALNIZ göçün kendi değişiklikleri geri alınır (başka değişikliğe dokunulmaz).
"""
from __future__ import annotations

import importlib
import os
import pkgutil
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

CURRENT = 2
DEFAULT_VERSION = 1
CONFIG_REL = "_system/config/kasa.yaml"
KEY = "schema_version"
EXIT_PENDING = 3


class SchemaError(Exception):
    pass


def _vault(vault: Path | None) -> Path:
    if vault is not None:
        return Path(vault)
    from . import config
    return Path(config.VAULT)


def config_path(vault: Path | None = None) -> Path:
    return _vault(vault) / CONFIG_REL


# ------------------------------------------------------------------ sürüm okuma/yazma
def read_version(vault: Path | None = None) -> int:
    """Kasa şema sürümü; dosya ya da anahtar yoksa 1. Bozuk değer SchemaError."""
    p = config_path(vault)
    if not p.exists():
        return DEFAULT_VERSION
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise SchemaError(f"{CONFIG_REL} okunamadı: {e}") from e
    m = re.search(rf"^{KEY}:[ \t]*(\S+)", text, re.M)
    if not m:
        return DEFAULT_VERSION
    raw = m.group(1).strip("'\"")
    if not raw.isdigit() or int(raw) < 1:
        raise SchemaError(f"{CONFIG_REL}: {KEY} geçersiz ({m.group(1)!r}); pozitif tam sayı olmalı")
    return int(raw)


def write_version(version: int, vault: Path | None = None) -> None:
    """Yalnız `schema_version` satırını yazar/günceller; dosyadaki diğer satırlar korunur."""
    p = config_path(vault)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = p.read_text(encoding="utf-8") if p.exists() else "# Kasa şeması — `sb migrate` yönetir, elle değiştirme.\n"
    line = f"{KEY}: {version}"
    if re.search(rf"^{KEY}:.*$", text, re.M):
        text = re.sub(rf"^{KEY}:.*$", line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(p)


# ------------------------------------------------------------------ göç keşfi
@dataclass
class Migration:
    version: int
    name: str
    description: str
    module: ModuleType

    def up(self, vault: Path, dry_run: bool) -> list[str]:
        return list(self.module.up(vault, dry_run))


def discover() -> list[Migration]:
    from . import migrations
    found: list[Migration] = []
    for mod in pkgutil.iter_modules(migrations.__path__):
        m = re.fullmatch(r"m(\d{4})_(\w+)", mod.name)
        if not m:
            continue
        module = importlib.import_module(f"{migrations.__name__}.{mod.name}")
        n = int(m.group(1))
        if getattr(module, "VERSION", n) != n:
            raise SchemaError(f"{mod.name}: VERSION ({module.VERSION}) dosya numarasıyla ({n}) aynı olmalı")
        found.append(Migration(n, m.group(2), str(getattr(module, "DESCRIPTION", mod.name)), module))
    found.sort(key=lambda x: x.version)
    for prev, nxt in zip(found, found[1:]):
        if nxt.version != prev.version + 1:
            raise SchemaError(f"göç zincirinde boşluk/çift: {prev.version} → {nxt.version}")
    return found


def pending(vault: Path | None = None, target: int | None = None) -> list[Migration]:
    cur, tgt = read_version(vault), CURRENT if target is None else target
    return [m for m in discover() if cur < m.version <= tgt]


# ------------------------------------------------------------------ durum / uyarı
def status(vault: Path | None = None) -> dict:
    """{'vault': N, 'code': CURRENT, 'state': 'ok'|'behind'|'ahead'|'error', 'pending': int, 'message': str}"""
    try:
        v = read_version(vault)
    except SchemaError as e:
        return {"vault": None, "code": CURRENT, "state": "error", "pending": 0, "message": str(e)}
    if v < CURRENT:
        n = len(pending(vault))
        return {"vault": v, "code": CURRENT, "state": "behind", "pending": n,
                "message": f"Kasa şeması {v}, kod {CURRENT} bekliyor ({n} göç bekliyor)"}
    if v > CURRENT:
        return {"vault": v, "code": CURRENT, "state": "ahead", "pending": 0,
                "message": f"Kasa şeması {v}, bu kod yalnız {CURRENT}'i biliyor (kasa koddan yeni): `sb update` ile kodu güncelle"}
    return {"vault": v, "code": CURRENT, "state": "ok", "pending": 0, "message": f"Kasa şeması {v} (güncel)"}


def warn_if_ahead(vault: Path | None = None, stream=None) -> bool:
    """Kasa koddan yeniyse bir uyarı yazar (yazma işlemlerinden önce çağrılır). True = uyarı yazıldı."""
    try:
        st = status(vault)
    except Exception:                                              # noqa: BLE001 — uyarı hiçbir komutu bozmasın
        return False
    if st["state"] != "ahead":
        return False
    print(f"UYARI: {st['message']}. Eski kodla yeni kasaya yazmak notları bozabilir.", file=stream or sys.stderr)
    return True


# ------------------------------------------------------------------ git yardımcıları
def _git(vault: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(vault), *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if check and r.returncode:
        raise SchemaError(f"git {' '.join(args[:2])} başarısız: {(r.stderr or r.stdout).strip()[:300]}")
    return r


def _is_repo(vault: Path) -> bool:
    return (vault / ".git").exists() and _git(vault, "rev-parse", "--git-dir", check=False).returncode == 0


def _status(vault: Path, untracked: bool) -> list[tuple[str, str]]:
    """[(XY, yol)] — `git status --porcelain -z`; yeniden adlandırmada yeni yol."""
    r = _git(vault, "status", "--porcelain", "-z", "--untracked-files=all" if untracked else "--untracked-files=no")
    parts = r.stdout.split("\0")
    out, i = [], 0
    while i < len(parts):
        e = parts[i]
        i += 1
        if len(e) < 4:
            continue
        xy, path = e[:2], e[3:]
        if "R" in xy or "C" in xy:
            i += 1                                                   # eski yol
        out.append((xy, path))
    return out


def _head(vault: Path) -> str:
    return _git(vault, "rev-parse", "HEAD").stdout.strip()


def _backup() -> dict:
    """Göç öncesi şifreli yedek (`privacy.create_backup`); testlerde taklit edilir."""
    from . import privacy
    return privacy.create_backup()


# ------------------------------------------------------------------ çalıştırma
def check(vault: Path | None = None) -> dict:
    """Salt okunur: bekleyen göçler ve her birinin yapacağı değişiklikler (dry-run)."""
    v = _vault(vault)
    st = status(v)
    out = {**st, "steps": []}
    if st["state"] == "behind":
        repo = _is_repo(v)
        for m in pending(v):
            out["steps"].append({"version": m.version, "description": m.description, "changes": m.up(v, True) if repo else None})
    return out


def _rollback(v: Path, before: str, ours: str | None, untracked_before: set[str], log: list[str]) -> None:
    """YALNIZ göçün kendi izini geri alır. Göçten önce izlenen ağaç temizdi; şimdi izlenen dosyalardaki değişiklik göçündür."""
    try:
        if ours and _head(v) == ours and not _status(v, untracked=False):
            _git(v, "reset", "--hard", before)                      # kendi commit'imiz, ağaç temiz: güvenli
            log.append("Göç commit'i geri alındı.")
        else:
            changed = [p for _xy, p in _status(v, untracked=False)]
            if changed:
                _git(v, "reset", "-q", "HEAD", "--", *changed, check=False)
                _git(v, "checkout", "HEAD", "--", *changed, check=False)
                log.append(f"Geri alındı: {len(changed)} dosya.")
    except Exception as e:                                          # noqa: BLE001
        log.append(f"UYARI: otomatik geri alma tamamlanamadı ({e}); `git -C {v} status` ile bak.")
    leftover = [p for xy, p in _status(v, untracked=True) if xy == "??" and p not in untracked_before]
    if leftover:
        log.append("Göçün oluşturduğu izlenmeyen dosyalar (silinmedi, elle bak): " + ", ".join(leftover[:10]))


def _apply_step(v: Path, m: Migration, frm: int, log: list[str]) -> None:
    before = _head(v)
    untracked_before = {p for xy, p in _status(v, untracked=True) if xy == "??"}
    cfg = config_path(v)
    cfg_prev = cfg.read_bytes() if cfg.exists() else None
    cfg_tracked = _git(v, "ls-files", "--error-unmatch", CONFIG_REL, check=False).returncode == 0
    ours: str | None = None
    try:
        r = _backup()
        if not r.get("ok"):
            raise SchemaError("Yedek alınamadı, göç yapılmadı: " + str(r.get("message") or r))
        log.append(f"Yedek alındı: {', '.join(r.get('created') or [])}")
        changes = m.up(v, False)
        log.extend(f"  {m.version}: {c}" for c in changes)
        write_version(m.version, v)
        paths = [p for xy, p in _status(v, untracked=True) if not (xy == "??" and p in untracked_before)]
        if CONFIG_REL not in paths:
            paths.append(CONFIG_REL)
        _git(v, "add", "-A", "--", *paths)
        _git(v, "commit", "-q", "-m", f"şema göçü {frm}→{m.version}: {m.description}")
        ours = _head(v)
    except BaseException as e:                                      # noqa: BLE001 — KeyboardInterrupt dahil geri al
        if not isinstance(e, SchemaError):
            log.append(f"Göç {m.version} başarısız: {type(e).__name__}: {e}")
        _rollback(v, before, ours, untracked_before, log)
        if cfg_prev is None:
            cfg.unlink(missing_ok=True)
        elif not cfg_tracked or cfg.read_bytes() != cfg_prev:
            cfg.write_bytes(cfg_prev)
        if isinstance(e, SchemaError):
            raise
        if not isinstance(e, Exception):
            raise
        raise SchemaError(f"Göç {m.version} başarısız, geri alındı: {e}") from e


def run(vault: Path | None = None, dry_run: bool = False) -> dict:
    """Bekleyen göçleri sırayla uygular. {'ok', 'applied': [sürümler], 'log': [satırlar]}; ok=False → durdu (log nedenini söyler)."""
    v = _vault(vault)
    log: list[str] = []
    st = status(v)
    if st["state"] in ("error", "ahead"):
        return {"ok": False, "applied": [], "log": [st["message"]]}
    todo = pending(v)
    if not todo:
        return {"ok": True, "applied": [], "log": [f"Kasa şeması güncel ({st['vault']})."]}
    if not _is_repo(v):
        return {"ok": False, "applied": [], "log": ["Kasa git deposu değil: geri alınamayacağı için göç yapılmadı (cd kasa && git init)."]}
    if dry_run:
        for m in todo:
            log.append(f"[deneme] {m.version}: {m.description}")
            log.extend(f"    {c}" for c in m.up(v, True))
        return {"ok": True, "applied": [], "log": log}
    applied: list[int] = []
    try:
        for m in todo:
            dirty = _status(v, untracked=False)
            if dirty:
                names = ", ".join(p for _xy, p in dirty[:5])
                log.append(f"Kasada commit edilmemiş değişiklik var ({len(dirty)} dosya: {names}); önce commit'le ya da geri al, sonra `sb migrate --yes` çalıştır. Hiçbir şey değiştirilmedi.")
                return {"ok": False, "applied": applied, "log": log}
            frm = read_version(v)
            _apply_step(v, m, frm, log)
            applied.append(m.version)
            log.append(f"Şema {frm} → {m.version} uygulandı ve commit'lendi.")
    except SchemaError as e:
        log.append(str(e))
        return {"ok": False, "applied": applied, "log": log}
    return {"ok": True, "applied": applied, "log": log}


def print_check(vault: Path | None = None) -> int:
    """`sb migrate --check`: salt okunur. Çıkış 0 = güncel, 3 (EXIT_PENDING) = bekleyen göç var, 1 = sorun (kasa koddan yeni / bozuk sürüm)."""
    c = check(vault)
    print(c["message"])
    for s in c["steps"]:
        print(f"  {s['version']}: {s['description']}")
        if s["changes"] is None:
            print("    (kasa git deposu değil; değişiklikler hesaplanamadı)")
            continue
        for ch in s["changes"][:20]:
            print(f"    {ch}")
        if len(s["changes"]) > 20:
            print(f"    ... +{len(s['changes']) - 20} değişiklik daha")
        if not s["changes"]:
            print("    (not değişmeyecek; yalnız sürüm damgası)")
    if c["state"] == "behind":
        print("Uygulamak için: sb migrate --yes (önce --dry-run ile bakabilirsin)")
    return {"ok": 0, "behind": EXIT_PENDING}.get(c["state"], 1)


def cli(check_only: bool = False, dry_run: bool = False, yes: bool = False, vault: Path | None = None) -> int:
    if check_only:
        return print_check(vault)
    if dry_run:
        r = run(vault, dry_run=True)
    else:
        if not yes:
            st = status(vault)
            if st["state"] != "behind":
                print(st["message"])
                return 0 if st["state"] == "ok" else 1
            print_check(vault)
            print("\nOnaylamak için `sb migrate --yes` çalıştır (önce şifreli yedek alınır, tek git commit'i atılır).")
            return 1
        r = run(vault)
    print("\n".join(r["log"]))
    return 0 if r["ok"] else 1
