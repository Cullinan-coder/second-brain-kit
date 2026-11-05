"""İzlenen klasör: `00-Inbox/İçe aktar/` — dışa aktarma dosyasını (zip, json, csv…) buraya bırak, gerisini sistem yapar.

Günlük çalışma (`sb import-inbox`) ve asistan açıkken 10 dakikada bir (`chat.import_inbox_loop`) klasöre bakar. Her yeni öğe için:
  1. yazılmakta mı (boyut değişiyor / son değişiklik çok yeni)? → bu turda dokunulmaz, sonra denenir;
  2. çok büyük / zip bombası mı (D-28: `content.guard_zip`, boyut ve dosya sayısı sınırı)? → `_tanınmadı/` + onay kartı;
  3. içerik SHA-256'sı daha önce alınmış mı (`freshness.json`)? → ikinci kez alınmaz, `_işlendi/<tarih>/` altına taşınır ("zaten alınmıştı");
  4. `connectors.detect()` ile tanı → içe aktar → başarılıysa dosya `_işlendi/<tarih>/` altına TAŞINIR (silme yok);
  5. tanınmadı ya da içe aktarılamadı → `_tanınmadı/` altına taşınır ve onay deposuna "bu dosya tanınmadı, kaynağını seç" kartı düşer;
     kaynağı sen seçince: `sb import-inbox --assign "<dosya>" <kaynak>`.
Klasör git'e girmez: ilk oluşturulurken kasa `.gitignore` dosyasına eklenir. Dosyalar hiçbir yere gönderilmez, yerelde okunur.
"""
from __future__ import annotations

import os
import shutil
import time
from datetime import date, datetime
from pathlib import Path

from . import approvals, config, freshness

REL = ("00-Inbox", "İçe aktar")
DONE, UNKNOWN = "_işlendi", "_tanınmadı"
GITIGNORE_LINE = "00-Inbox/İçe aktar/"
TEMP_EXT = {".part", ".crdownload", ".tmp", ".download", ".partial", ".filepart", ".opdownload"}
SETTLE_SECONDS = 15           # son değişiklik bundan yeniyse dosya hâlâ yazılıyor sayılır
PROBE_SECONDS = 1.0           # iki boyut ölçümü arası bekleme
MAX_BYTES = 2 * 1024 ** 3     # tek dosya / klasör toplamı (apps.MAX_ZIP_BYTES ile aynı)
MAX_FILES = 20000


def folder(vault: Path | None = None) -> Path:
    return Path(vault or config.VAULT).joinpath(*REL)


def ensure(vault: Path | None = None) -> Path:
    """Klasörü oluşturur ve kasa .gitignore'una ekler (zaten varsa dokunmaz)."""
    root = Path(vault or config.VAULT)
    d = folder(root)
    d.mkdir(parents=True, exist_ok=True)
    gi = root / ".gitignore"
    try:
        text = gi.read_text(encoding="utf-8") if gi.exists() else ""
        if GITIGNORE_LINE not in text.splitlines():
            gi.write_text(text + ("" if not text or text.endswith("\n") else "\n")
                          + "\n# İçe aktarma klasörü: dışa aktarma dosyaları (zip, json…) git'e girmesin\n" + GITIGNORE_LINE + "\n", encoding="utf-8")
    except OSError:
        pass
    return d


# ------------------------------------------------------------------ yardımcılar
def _signature(p: Path) -> tuple[int, int]:
    """(toplam bayt, dosya sayısı) — klasörde tüm dosyalar; sınırı aşınca erken döner."""
    if p.is_file():
        return p.stat().st_size, 1
    size = n = 0
    for root, _dirs, files in os.walk(p):
        for f in files:
            n += 1
            try:
                size += (Path(root) / f).stat().st_size
            except OSError:
                pass
            if n > MAX_FILES or size > MAX_BYTES:
                return size, n
    return size, n


def _newest_mtime(p: Path) -> float:
    if p.is_file():
        return p.stat().st_mtime
    latest = p.stat().st_mtime
    for root, _d, files in os.walk(p):
        for f in files:
            try:
                latest = max(latest, (Path(root) / f).stat().st_mtime)
            except OSError:
                pass
    return latest


def is_settled(p: Path, settle: float = SETTLE_SECONDS, probe: float = PROBE_SECONDS, sleep=time.sleep, now=time.time) -> bool:
    """Dosya yazılmıyor mu? Son değişiklik `settle` sn'den eskiyse ve kısa aralıkla iki ölçümde boyut aynıysa evet."""
    try:
        if p.suffix.lower() in TEMP_EXT:
            return False
        if now() - _newest_mtime(p) < settle:
            return False
        a = _signature(p)
        if probe:
            sleep(probe)
        return a == _signature(p)
    except OSError:
        return False


def _move(p: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / p.name
    i = 2
    while dest.exists():
        dest = dest_dir / (f"{p.stem}-{i}{p.suffix}" if p.is_file() else f"{p.name}-{i}")
        i += 1
    shutil.move(str(p), str(dest))
    return dest


def _card(p: Path, sha: str, reason: str, dest: Path) -> None:
    """Onay deposuna "kaynağını seç" kartı (aynı dosya için tek kart: kimlik karmadan)."""
    rid = "ice" + sha[:8]
    try:
        if approvals.get(rid):
            return
        from . import connectors
        approvals.add("kaynak-sec", f"Bu dosya tanınmadı, kaynağını seç: {p.name}",
                      f"{reason} Dosya {UNKNOWN} klasörüne taşındı. "
                      f"Kaynağı biliyorsan: sb import-inbox --assign \"{dest.name}\" <kaynak>  (kaynaklar: {', '.join(sorted(connectors.REGISTRY))})",
                      origin="içe-aktar", rid=rid, ttl_hours=24 * 30,
                      extra={"dosya": dest.name, "neden": reason, "kaynaklar": sorted(connectors.REGISTRY)})
    except Exception:                                            # noqa: BLE001 — kart yazılamasa da dosya güvende
        pass


def _guard(p: Path) -> str | None:
    """Boyut / zip bombası denetimi; sorun varsa nedeni."""
    size, n = _signature(p)
    if size > MAX_BYTES:
        return f"çok büyük ({size // 1024 ** 2} MB; sınır {MAX_BYTES // 1024 ** 2} MB)."
    if n > MAX_FILES:
        return f"çok fazla dosya ({n}; sınır {MAX_FILES})."
    if p.is_file() and p.suffix.lower() == ".zip":
        from .content import guard_zip
        try:
            guard_zip(p)
        except ValueError as e:
            return f"zip güvenlik denetimi: {e}."
        except Exception as e:                                   # noqa: BLE001 — bozuk zip
            return f"zip açılamadı ({type(e).__name__})."
    return None


def _run_connector(name: str, p: Path, con, me: str | None = None) -> dict:
    from . import connectors
    return connectors.REGISTRY[name](str(p), con, dry_run=False, me=me, days=365)


# ------------------------------------------------------------------ ana işlev
def scan(vault: Path | None = None, con=None, *, settle: float = SETTLE_SECONDS, probe: float = PROBE_SECONDS,
         today: date | None = None, create: bool = True) -> list[dict]:
    """Klasördeki bekleyen öğeleri işler. Dönüş: öğe başına {"name", "action", "source", "message", ...};
    action: imported | duplicate | unrecognized | failed | rejected | waiting."""
    from . import connectors, maildb
    d = ensure(vault) if create else folder(vault)
    if not d.is_dir():
        return []
    items = sorted(x for x in d.iterdir() if not x.name.startswith(("_", ".")))
    if not items:
        return []
    own_con = con is None
    if own_con:
        con = maildb.connect(Path(config.DATA) / "mail.db")
    day = (today or date.today()).isoformat()
    out: list[dict] = []
    try:
        for p in items:
            rec: dict = {"name": p.name}
            out.append(rec)
            if not is_settled(p, settle, probe):
                rec.update(action="waiting", message="dosya hâlâ yazılıyor olabilir; sonraki turda denenecek.")
                continue
            bad = _guard(p)
            if bad:
                dest = _move(p, d / UNKNOWN)
                _card(p, _short_id(p.name, dest), bad, dest)
                rec.update(action="rejected", message=bad, moved_to=str(dest))
                continue
            sha = freshness.sha256_of(p)
            seen = freshness.known_hash(sha)
            if seen:
                dest = _move(p, d / DONE / day)
                rec.update(action="duplicate", source=seen.get("source"), moved_to=str(dest),
                           message=f"zaten alınmıştı ({seen.get('ts', '')[:10]}, {seen.get('source')}); taşındı, tekrar içe aktarılmadı.")
                continue
            name = connectors.detect(p)
            if not name:
                dest = _move(p, d / UNKNOWN)
                _card(p, sha, "Dosya hiçbir bağlayıcıyla eşleşmedi.", dest)
                rec.update(action="unrecognized", message="kaynak tanınmadı; _tanınmadı klasörüne taşındı, onay kartı eklendi.", moved_to=str(dest))
                continue
            try:
                res = _run_connector(name, p, con)
            except Exception as e:                               # noqa: BLE001 — bozuk dosya diğerlerini durdurmasın
                dest = _move(p, d / UNKNOWN)
                _card(p, sha, f"{name} olarak tanındı ama okunamadı: {type(e).__name__}: {str(e)[:120]}.", dest)
                rec.update(action="failed", source=name, message=f"{name}: okunamadı — {type(e).__name__}: {str(e)[:120]}", moved_to=str(dest))
                continue
            freshness.record_file(name, p, sha, res)
            dest = _move(p, d / DONE / day)
            rec.update(action="imported", source=name, read=res.get("okunan"), new=res.get("yeni"), moved_to=str(dest),
                       message=f"{name}: okunan {res.get('okunan')}, yeni {res.get('yeni')}.")
    finally:
        if own_con:
            con.close()
    return out


def _short_id(name: str, p: Path) -> str:
    import hashlib
    try:
        size = _signature(p)[0]
    except OSError:
        size = 0
    return hashlib.sha256(f"{name}|{size}".encode("utf-8")).hexdigest()


def assign(name: str, source: str, vault: Path | None = None, con=None, me: str | None = None) -> dict:
    """`_tanınmadı/` altındaki dosyayı kullanıcının seçtiği kaynakla içe aktarır; başarılıysa `_işlendi/<tarih>/` altına taşır."""
    from . import connectors, maildb
    d = folder(vault)
    p = d / UNKNOWN / name
    if not p.exists():
        raise FileNotFoundError(f"{UNKNOWN} altında yok: {name}")
    if source not in connectors.REGISTRY:
        raise ValueError(f"bilinmeyen kaynak: {source} (seçenekler: {', '.join(sorted(connectors.REGISTRY))})")
    bad = _guard(p)
    if bad:
        raise ValueError(bad)
    own_con = con is None
    if own_con:
        con = maildb.connect(Path(config.DATA) / "mail.db")
    try:
        res = _run_connector(source, p, con, me)
    finally:
        if own_con:
            con.close()
    sha = freshness.sha256_of(p)
    freshness.record_file(source, p, sha, res)
    dest = _move(p, d / DONE / date.today().isoformat())
    return {"name": name, "action": "imported", "source": source, "read": res.get("okunan"), "new": res.get("yeni"), "moved_to": str(dest)}


def cli(args) -> int:
    if getattr(args, "assign", None):
        try:
            r = assign(args.assign[0], args.assign[1], me=getattr(args, "me", None))
        except (FileNotFoundError, ValueError, OSError) as e:
            print(f"içe aktarılamadı: {e}")
            return 1
        print(f"{r['source']}: okunan {r['read']}, yeni {r['new']} → {r['moved_to']}")
        return 0
    res = scan(create=not getattr(args, "no_create", False))
    if not res:
        print(f"{'/'.join(REL)}: bekleyen dosya yok.")
        return 0
    for r in res:
        print(f"[{r['action']}] {r['name']}: {r['message']}")
    return 1 if any(r["action"] in ("failed", "rejected") for r in res) else 0


def loop(stop, interval: int = 600) -> None:
    """Asistan açıkken 10 dakikada bir klasöre bakar (chat.serve iş parçacığı). Hata iş parçacığını öldürmez."""
    while not stop.is_set():
        try:
            if folder().is_dir():                                # klasör yoksa oluşturma: kullanıcı henüz kullanmıyor
                scan(create=False, probe=0.5)
        except BaseException as e:                               # noqa: BLE001
            print(f"[içe aktarma klasörü] {type(e).__name__}: {e}", flush=True)
        stop.wait(interval)
