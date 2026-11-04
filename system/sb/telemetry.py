"""Yerel ölçüm ve hata raporlama: süre kaydı (perf.jsonl), çökme raporu, günlük/rapor görüntüleme, "Yenilikler".

Hiçbir şey dışarı gönderilmez; paylaşım kullanıcının elindedir (`sb logs --bundle` tek dosya üretir).
Telemetri hatası asıl işi asla bozmaz (kayıt yazılamazsa sessizce geçilir).
"""
from __future__ import annotations

import json
import platform
import re
import sys
import time
import traceback
import zipfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from .config import DATA, SYSTEM

MAX_PERF_BYTES = 5 * 1024 * 1024
KEEP_CRASHES = 5


def _perf_path() -> Path:
    return DATA / "perf.jsonl"


def _trim(path: Path, limit: int = MAX_PERF_BYTES) -> None:
    """Dosya sınırı aşarsa eski yarısını atar (satır sınırından)."""
    try:
        if path.stat().st_size <= limit:
            return
        data = path.read_bytes()
        cut = data.find(b"\n", len(data) // 2)
        path.write_bytes(data[cut + 1:] if cut >= 0 else b"")
    except OSError:
        pass


def record(kind: str, name: str, ms: float, ok: bool = True) -> None:
    try:
        p = _perf_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": datetime.now().isoformat(timespec="seconds"), "kind": kind, "name": name, "ms": round(ms), "ok": ok}
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        _trim(p)
    except OSError:
        pass


@contextmanager
def timed(kind: str, name: str):
    """Bloğun süresini kaydeder; blokta istisna olursa ok=false yazar ve istisnayı yeniden fırlatır."""
    t0 = time.perf_counter()
    ok = True
    try:
        yield
    except BaseException:
        ok = False
        raise
    finally:
        record(kind, name, (time.perf_counter() - t0) * 1000, ok)


def _rows(days: int) -> list[dict]:
    p = _perf_path()
    if not p.exists():
        return []
    since = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict) and str(r.get("ts", "")) >= since:
            rows.append(r)
    return rows


def _p95(vals: list[float]) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(0.95 * len(s)))] if s else 0.0


def perf_summary(days: int = 7) -> str:
    rows = _rows(days)
    if not rows:
        return f"Son {days} günde ölçüm yok."
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        groups.setdefault((str(r.get("kind")), str(r.get("name"))), []).append(r)
    lines = [f"Performans — son {days} gün ({len(rows)} kayıt)", "",
             f"{'tür':<11}{'ad':<26}{'sayı':>5}{'ort ms':>9}{'p95 ms':>9}{'hata %':>8}"]
    for (kind, name), g in sorted(groups.items()):
        ms = [float(x.get("ms", 0)) for x in g]
        bad = sum(1 for x in g if not x.get("ok", True))
        lines.append(f"{kind:<11}{name[:25]:<26}{len(g):>5}{sum(ms) / len(ms):>9.0f}{_p95(ms):>9.0f}{100 * bad / len(g):>8.0f}")
    lines += ["", "En yavaş 5:"]
    for r in sorted(rows, key=lambda x: -float(x.get("ms", 0)))[:5]:
        lines.append(f"  {float(r.get('ms', 0)):>8.0f} ms  {r.get('kind')}/{r.get('name')}  {str(r.get('ts'))[:16]}"
                     + ("" if r.get("ok", True) else "  [hata]"))
    return "\n".join(lines)


# ---- çökme raporu ----

def _crash_dir() -> Path:
    return DATA / "crashes"


def _safe_args(args: str) -> str:
    """Komut satırı argümanları: e-posta/telefon/kart maskelenir, uzun metin kısaltılır."""
    from .redact import redact
    out = redact(args)
    out = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[e-posta gizlendi]", out)
    out = re.sub(r"(?<!\d)\+?\d[\d ()-]{8,}\d", "[telefon gizlendi]", out)
    return out if len(out) <= 200 else out[:200] + f"... [{len(out) - 200} karakter kesildi]"


def crash(exc: BaseException, context: str = "") -> Path | None:
    """Çökme raporu yazar (ortam değişkeni YOK); yolu döner, yazılamazsa None."""
    from .redact import redact
    try:
        from .update import version
        ver = version()
    except Exception:
        ver = "?"
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    body = "\n".join([
        f"Zaman: {datetime.now().isoformat(timespec='seconds')}",
        f"Sürüm: {ver}",
        f"Komut: sb {_safe_args(context)}".rstrip(),
        f"Platform: {platform.platform()}",
        f"Python: {sys.version.split()[0]}",
        "",
        redact(re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[e-posta gizlendi]", tb)),
    ])
    try:
        d = _crash_dir()
        d.mkdir(parents=True, exist_ok=True)
        stamp = f"{datetime.now():%Y%m%d-%H%M%S-%f}"
        path = d / f"{stamp}.txt"
        n = 1
        while path.exists():                                     # Windows saat çözünürlüğü ~15 ms: aynı anda iki çökme birbirini ezmesin
            path = d / f"{stamp}-{n}.txt"
            n += 1
        path.write_text(body, encoding="utf-8")
        for old in sorted(d.glob("*.txt"))[:-50]:                # klasör şişmesin
            old.unlink(missing_ok=True)
        return path
    except OSError:
        return None


def crash_list() -> list[Path]:
    d = _crash_dir()
    return sorted(d.glob("*.txt"), reverse=True) if d.exists() else []


def crash_bundle() -> Path:
    """Son 5 çökme raporu + `sb doctor` çıktısı → tek zip. Hiçbir yere gönderilmez."""
    import contextlib
    import io
    buf = io.StringIO()
    try:
        from . import doctor
        with contextlib.redirect_stdout(buf):
            doctor.run()
    except BaseException as e:                                   # doktor da çökebilir; paket yine üretilsin
        buf.write(f"\n(doctor çalıştırılamadı: {type(e).__name__})")
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"sb-rapor-{datetime.now():%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("doctor.txt", buf.getvalue())
        for p in crash_list()[:KEEP_CRASHES]:
            z.write(p, f"crashes/{p.name}")
    return out


# ---- günlükler ----

def logs(n: int = 40, kind: str = "daily") -> str:
    if kind == "crash":
        cl = crash_list()
        return cl[0].read_text(encoding="utf-8") if cl else "Çökme raporu yok."
    d = DATA / "logs"
    files = sorted(d.glob(f"{kind}-*.log"), key=lambda p: p.stat().st_mtime, reverse=True) if d.exists() else []
    if not files:
        return f"'{kind}' günlüğü yok."
    lines = files[0].read_text(encoding="utf-8", errors="replace").splitlines()
    return f"# {files[0].name}\n" + "\n".join(lines[-n:])


# ---- yenilikler ----

def _changelog() -> Path | None:
    cands = []
    try:
        info = json.loads((DATA / "kit.json").read_text(encoding="utf-8"))
        cands.append(Path(info["kit"]) / "CHANGELOG.md")
    except (OSError, ValueError, KeyError):
        pass
    cands.append(SYSTEM / "kit" / "CHANGELOG.md")
    return next((c for c in cands if c.exists()), None)


def whatsnew(show_all: bool = False) -> str:
    """Son görülen sürümden yeni CHANGELOG bölümleri; görüldü işaretlenir. İlk çağrıda yalnız en yeni bölüm."""
    from .update import changes, version
    cl = _changelog()
    if not cl:
        return "CHANGELOG.md bulunamadı."
    seen_f = DATA / "seen_version"
    seen = seen_f.read_text(encoding="utf-8").strip() if seen_f.exists() else ""
    if show_all:
        text = changes(cl, "")
    elif seen:
        text = changes(cl, seen)
    else:
        parts = [x for x in re.split(r"(?m)^(?=##\s+v?\d+\.\d+\.\d+)", changes(cl, "")) if x.strip()]
        text = parts[0].strip() if parts else ""
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        seen_f.write_text(version(), encoding="utf-8")
    except OSError:
        pass
    return text or "Yeni bir şey yok; son sürümdesin."


def run_e2e(live: bool = False) -> int:
    """`sb e2e`: tools/e2e.py'yi yoldan yükleyip çalıştırır (tools bir paket değil)."""
    import importlib.util
    f = SYSTEM / "tools" / "e2e.py"
    if not f.exists():
        print("tools/e2e.py bulunamadı.")
        return 1
    spec = importlib.util.spec_from_file_location("sb_e2e", f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run(live)
