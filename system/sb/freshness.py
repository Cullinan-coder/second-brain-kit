"""Kaynak tazeliği: her veri kaynağının son BAŞARILI içe aktarma zamanı, kayıt sayısı ve son dosya özeti.

Neden: dışa aktarma dosyalarıyla beslenen kaynaklar (WhatsApp, Takeout, Spotify, banka…) kendiliğinden güncellenmez; kullanıcı
unuttuğunda veri sessizce eskir. Burası "en son ne zaman aldık, ne kadar eskidi, nasıl güncellenir" sorusunu cevaplar.

Kayıt `~/.secondbrain/freshness.json` (kilit + atomik yazım; süreçler arası güvenli):
    {"version": 1, "seeded": iso|null,
     "sources": {anahtar: {"last_ok", "total", "last_read", "last_new", "data_max", "file": {...}, "via", "last_fail"}},
     "hashes": {sha256: {"ts", "source", "name"}},                # aynı dosya ikinci kez alınmasın
     "steps": {adım adı: {"ts", "rc", "tail"}}}                   # günlük çalışmanın son adım sonuçları

Dolduran TEK kanca noktaları: `connectors._common.ingest_items / ingest_messages / sync_items` (kayıt okunduysa ve dry_run değilse),
`runner.run_step` (günlük adım sonucu) ve izlenen klasör (`sb/import_inbox.py`, dosya özeti + özet karması). Hepsi `record_*`
işlevlerini çağırır; hata hiçbir zaman içe aktarmayı düşürmez.

Anahtarlar: kaynak manifest kimlikleri (plugins/source/*.yaml) + `refresh:` taşıyan modüller (gmail, imap, calendar, drive…).
`status()` yalnız kullanıcının ETKİN kaynaklarını raporlar (hiç kullanmadığı kaynak "bayat" diye bağırmaz):
  - bir kaydı (içe aktarma ya da geçmişten tohum) varsa etkin, AMA kapatılmış (features) ya da hesabı bağlı olmayan otomatik kaynak değil;
  - kaydı yoksa yalnız bağlayıcısı günlük çalışan, özelliği açık ve hesabı bağlı otomatik kaynaklar "hiç" olarak görünür.
Durum: yaş ≤ eşik → taze (otomatik kaynaklarda +0,5 gün hoşgörü) · ≤ 2×eşik → eskiyor · fazlası → bayat · kayıt yok → hiç.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config, filelock

VERSION = 1
FILE = "freshness.json"
AUTO_GRACE_DAYS = 0.5
# items.source değeri → tazelik anahtarı (Takeout birden çok kaynak adı yazar)
ITEM_KEY = {"activity": "takeout", "play": "takeout", "notebooklm": "takeout"}
# messages.account değeri doğrudan anahtardır (içe aktarma hesapları)
MESSAGE_KEYS = {"whatsapp", "telegram", "discord", "slack", "instagram", "linkedin", "sms"}
# günlük adım (sb komutunun ilk argümanı) → anahtarlar
STEP_KEYS = {"sms-sync": ["sms"], "sync-gcal": ["calendar"], "contacts-sync": ["contacts"], "drive-sync": ["drive"],
             "local-files": ["local_files"], "projects-sync": ["projects"], "sessions-sync": ["sessions"], "github-deep": ["github"]}
# kaydı yoksa "hiç" diye gösterilmeyecek otomatik kaynaklar (kurulumu/hesabı ayrıca doğrulanamaz): yalnız kaydı olunca etkin
RECORD_ONLY = {"sms", "clipboardline", "nashi", "github", "sessions", "icloud", "outlook", "local_files", "projects"}


# ------------------------------------------------------------------ dosya
def path() -> Path:
    return Path(config.DATA) / FILE


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _iso(d: datetime) -> str:
    return d.astimezone().isoformat(timespec="seconds")


def _parse(s: str | None) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(s))
    except (TypeError, ValueError):
        return None
    return d if d.tzinfo else d.astimezone()


def _empty() -> dict:
    return {"version": VERSION, "seeded": None, "sources": {}, "hashes": {}, "steps": {}}


def load() -> dict:
    try:
        data = json.loads(path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _empty()
    if not isinstance(data, dict):
        return _empty()
    base = _empty()
    base.update({k: v for k, v in data.items() if k in base})
    for k in ("sources", "hashes", "steps"):
        if not isinstance(base[k], dict):
            base[k] = {}
    return base


def _update(fn) -> None:
    """Kilit altında oku → fn(veri) → atomik yaz."""
    with filelock.locked(path()):
        data = load()
        fn(data)
        filelock.atomic_write(path(), json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True))


# ------------------------------------------------------------------ anahtar evreni
def universe() -> dict[str, dict]:
    """anahtar → {"name", "refresh", "module": bool}. Kaynak manifestleri + refresh taşıyan modüller (kaynak öncelikli)."""
    from . import plugins
    out: dict[str, dict] = {}
    for m in plugins.all("source"):
        out[m["id"]] = {"name": m["name"], "refresh": plugins.refresh_of(m), "type": "source"}
    for m in plugins.all("module"):
        if m.get("refresh") and m["id"] not in out:
            out[m["id"]] = {"name": m["name"], "refresh": plugins.refresh_of(m), "type": "module"}
    return out


def key_for(kaynak: str) -> str:
    return ITEM_KEY.get(kaynak, kaynak)


# ------------------------------------------------------------------ kayıt (kancalar)
def _touch(data: dict, key: str, now: datetime, **kw) -> dict:
    s = data["sources"].setdefault(key, {})
    s["last_ok"] = _iso(now)
    s.pop("last_fail", None)
    s["via"] = kw.get("via", s.get("via", "ingest"))
    if kw.get("read") is not None:
        s["last_read"], s["last_new"] = int(kw["read"]), int(kw.get("new") or 0)
        s["total"] = int(s.get("total") or 0) + int(kw.get("new") or 0)
    if kw.get("data_max"):
        s["data_max"] = max(str(kw["data_max"]), str(s.get("data_max") or ""))
    return s


def record_ingest(kaynak: str, read: int, new: int, data_max: str | None = None, now: datetime | None = None) -> None:
    """Bir içe aktarma BAŞARIYLA kayıt okudu (dry-run değil). Bağlayıcı ortak işlevlerinden çağrılır; hata yutulur."""
    try:
        key = key_for(kaynak)
        if read <= 0 or key not in universe():
            return
        _update(lambda d: _touch(d, key, now or _now(), via="ingest", read=read, new=new, data_max=data_max))
    except Exception:                                            # noqa: BLE001 — tazelik kaydı içe aktarmayı düşürmemeli
        pass


def record_file(kaynak: str, p: str | Path, sha: str, result: dict | None = None, now: datetime | None = None) -> None:
    """İçe aktarılan dosyanın özeti ve özet karması (aynı dosya ikinci kez alınmasın)."""
    try:
        pp = Path(p)
        key = key_for(kaynak)
        t = now or _now()
        try:
            size = pp.stat().st_size if pp.is_file() else sum(f.stat().st_size for f in pp.rglob("*") if f.is_file())
        except OSError:
            size = None

        def fn(d):
            if key in universe():
                s = _touch(d, key, t, via=d["sources"].get(key, {}).get("via", "ingest"))
                s["file"] = {"name": pp.name, "size": size, "sha256": sha[:16], "at": _iso(t),
                             "read": (result or {}).get("okunan"), "new": (result or {}).get("yeni")}
            d["hashes"][sha] = {"ts": _iso(t), "source": kaynak, "name": pp.name}
        _update(fn)
    except Exception:                                            # noqa: BLE001
        pass


def known_hash(sha: str) -> dict | None:
    return load()["hashes"].get(sha)


def step_keys(args: list[str]) -> list[str]:
    if not args:
        return []
    if args[0] == "mail-fetch" and len(args) > 1:
        try:
            acc = config.accounts()
        except Exception:                                        # noqa: BLE001
            return []
        if args[1] in (acc.get("google") or {}):
            return ["gmail"]
        if args[1] in (acc.get("imap") or {}):
            return ["imap"]
        return []
    return STEP_KEYS.get(args[0], [])


def record_step(name: str, args: list[str], rc: int, tail: str = "", now: datetime | None = None) -> None:
    """Günlük adım sonucu: başarılıysa eşlenen kaynak tazelenir; değilse yalnız son hata yazılır (son başarı korunur)."""
    try:
        t = now or _now()
        keys = [k for k in step_keys(args) if k in universe()]

        def fn(d):
            d["steps"][name] = {"ts": _iso(t), "rc": int(rc), "tail": str(tail)[:300]}
            for k in keys:
                if rc == 0:
                    _touch(d, k, t, via="step")
                else:
                    d["sources"].setdefault(k, {})["last_fail"] = {"ts": _iso(t), "msg": str(tail)[:200]}
            if len(d["steps"]) > 200:
                for old in sorted(d["steps"], key=lambda n: d["steps"][n].get("ts", ""))[:len(d["steps"]) - 200]:
                    d["steps"].pop(old, None)
        _update(fn)
    except Exception:                                            # noqa: BLE001
        pass


# ------------------------------------------------------------------ geçmişten tohum
def _utc(s: str | None) -> datetime | None:
    """SQLite datetime('now') (UTC, 'YYYY-AA-GG SS:DD:SS') → saat dilimli zaman."""
    try:
        return datetime.fromisoformat(str(s).replace(" ", "T")).replace(tzinfo=timezone.utc).astimezone()
    except (TypeError, ValueError):
        return None


def _day(ms) -> str | None:
    if not ms:
        return None
    try:
        return (datetime(1970, 1, 1) + timedelta(milliseconds=int(ms))).strftime("%Y-%m-%d")
    except (OverflowError, ValueError, OSError):
        return None


def seed_rows(db_path: Path | None = None) -> dict[str, dict]:
    """mail.db `items` / `messages` tablolarından kaynak başına {last_ok, total, data_max}. Salt okunur; DB yoksa boş."""
    p = Path(db_path) if db_path else Path(config.DATA) / "mail.db"
    if not p.exists():
        return {}
    uni = universe()
    try:
        acc = config.accounts()
    except Exception:                                            # noqa: BLE001
        acc = {}
    out: dict[str, dict] = {}

    def add(key: str, n: int, fetched: str | None, last_ms) -> None:
        if key not in uni:
            return
        o = out.setdefault(key, {"last_ok": None, "total": 0, "data_max": None})
        o["total"] += int(n or 0)
        d = _utc(fetched)
        if d and (o["last_ok"] is None or d > _parse(o["last_ok"])):
            o["last_ok"] = _iso(d)
        dm = _day(last_ms)
        if dm and (o["data_max"] is None or dm > o["data_max"]):
            o["data_max"] = dm
    try:
        con = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True, timeout=10)
    except sqlite3.Error:
        return {}
    try:
        for src, n, fetched, ms in con.execute("SELECT source, COUNT(*), MAX(fetched_at), MAX(date_ms) FROM items GROUP BY source"):
            add(key_for(src), n, fetched, ms)
        for account, n, fetched, ms in con.execute("SELECT account, COUNT(*), MAX(fetched_at), MAX(date_ms) FROM messages GROUP BY account"):
            if account in MESSAGE_KEYS:
                add(account, n, fetched, ms)
            elif account in (acc.get("google") or {}):
                add("gmail", n, fetched, ms)
            elif account in (acc.get("imap") or {}):
                add("imap", n, fetched, ms)
    except sqlite3.Error:
        pass
    finally:
        con.close()
    return {k: v for k, v in out.items() if v["last_ok"]}


def seed(write: bool = True, db_path: Path | None = None, now: datetime | None = None) -> dict:
    """İlk çalıştırmada geçmişten tohumla: kaydı OLMAYAN kaynaklar için son kayıt zamanı yazılır (varsa dokunulmaz).
    write=False: hiçbir şey yazmaz, yazılacakları döndürür. Dönüş: {"seeded": bool, "added": {anahtar: {...}}}."""
    if load().get("seeded"):
        return {"seeded": False, "added": {}}
    if not (Path(db_path) if db_path else Path(config.DATA) / "mail.db").exists():
        return {"seeded": False, "added": {}}            # arşiv henüz yok: sonra tohumlanabilsin
    rows = seed_rows(db_path)
    added: dict[str, dict] = {}

    def fn(d):
        for k, v in rows.items():
            if k in d["sources"] and d["sources"][k].get("last_ok"):
                continue
            s = d["sources"].setdefault(k, {})
            s.update({"last_ok": v["last_ok"], "total": v["total"], "via": "seed"})
            if v["data_max"]:
                s["data_max"] = v["data_max"]
            added[k] = v
        d["seeded"] = _iso(now or _now())
    if write:
        _update(fn)
    else:
        d = load()
        fn(d)
    return {"seeded": True, "added": added}


# ------------------------------------------------------------------ durum
def _auto_connected(key: str) -> bool:
    """Otomatik kaynak: özellik açık ve (gerekiyorsa) hesap bağlı mı?"""
    from . import features
    if not features.enabled(key):
        return False
    if key in ("gmail", "imap", "calendar", "drive", "contacts"):
        try:
            acc = config.accounts()
        except Exception:                                        # noqa: BLE001
            return False
        if key == "imap":
            return bool(acc.get("imap"))
        g = acc.get("google") or {}
        if key == "gmail":
            return any("gmail" in (c.get("scopes") or []) for c in g.values())
        return bool(g)
    return True


def _state(age: float | None, every: int, mode: str) -> str:
    if age is None:
        return "hiç"
    thr = every + (AUTO_GRACE_DAYS if mode == "auto" else 0)
    if age <= thr:
        return "taze"
    return "eskiyor" if age <= 2 * every + (AUTO_GRACE_DAYS if mode == "auto" else 0) else "bayat"


def status(now: datetime | None = None, seed_write: bool = False, db_path: Path | None = None) -> dict:
    """Etkin kaynakların tazeliği. seed_write=False (varsayılan, salt okunur): kayıt dosyası henüz tohumlanmadıysa tohum bellekte
    hesaplanır, diske yazılmaz. Dönüş: {"generated", "seeded", "sources": [...], "counts": {...}, "stale": n}."""
    now = now or _now()
    data = load()
    seeded = bool(data.get("seeded"))
    if not seeded:
        res = seed(write=seed_write, db_path=db_path, now=now)
        if seed_write:
            data = load()
        else:
            for k, v in res["added"].items():
                s = data["sources"].setdefault(k, {})
                if not s.get("last_ok"):
                    s.update({"last_ok": v["last_ok"], "total": v["total"], "via": "seed", "data_max": v["data_max"]})
    rows = []
    for key, u in universe().items():
        rec = data["sources"].get(key) or {}
        r = u["refresh"]
        last = _parse(rec.get("last_ok"))
        mode = r["mode"]
        if last:
            if mode == "auto" and not _auto_connected(key):
                continue
        else:
            if not (mode == "auto" and key not in RECORD_ONLY and _auto_connected(key)):
                continue
        age = max((now - last).total_seconds() / 86400, 0.0) if last else None
        rows.append({"source": key, "name": u["name"], "mode": mode, "last": _iso(last) if last else None,
                     "age_days": round(age, 1) if age is not None else None, "threshold_days": r["every_days"],
                     "state": _state(age, r["every_days"], mode), "hint": r["hint"], "records": rec.get("total"),
                     "last_new": rec.get("last_new"), "data_max": rec.get("data_max"), "file": rec.get("file"),
                     "via": rec.get("via"), "last_fail": rec.get("last_fail")})
    order = {"bayat": 0, "eskiyor": 1, "hiç": 2, "taze": 3}
    rows.sort(key=lambda x: (order[x["state"]], -(x["age_days"] or 0), x["source"]))
    counts = {s: sum(1 for x in rows if x["state"] == s) for s in ("taze", "eskiyor", "bayat", "hiç")}
    return {"generated": _iso(now), "seeded": seeded or seed_write, "sources": rows, "counts": counts,
            "stale": counts["bayat"] + counts["eskiyor"]}


def stale_sources(limit: int = 5, now: datetime | None = None) -> list[dict]:
    """Eskiyen/bayat kaynaklar (en bayat önce), en fazla `limit`. Salt okunur."""
    return [s for s in status(now)["sources"] if s["state"] in ("bayat", "eskiyor")][:limit]


def last_failed_step() -> dict | None:
    """En son başarısız günlük adım (sonradan aynı adım başarılı olduysa sayılmaz)."""
    steps = load()["steps"]
    bad = [(v.get("ts", ""), n, v) for n, v in steps.items() if v.get("rc") not in (0, None)]
    if not bad:
        return None
    ts, name, v = max(bad)
    return {"name": name, "ts": ts, "rc": v.get("rc"), "tail": v.get("tail", "")}


def render(st: dict, lang: str = "tr") -> str:
    """İnsan okunur tablo."""
    if not st["sources"]:
        return "Etkin kaynak yok (henüz bir şey içe aktarılmadı)."
    sym = {"taze": "✓", "eskiyor": "~", "bayat": "!", "hiç": "·"}
    lines = []
    for s in st["sources"]:
        age = "hiç alınmadı" if s["age_days"] is None else f"{s['age_days']:g} gün önce"
        lines.append(f" {sym[s['state']]} {s['state']:8} {s['name'][lang]:32} {age:>16}  (eşik {s['threshold_days']} gün)")
        if s["state"] != "taze":
            lines.append(f"      → {s['hint'][lang]}")
    c = st["counts"]
    lines.append(f"\n{c['taze']} taze, {c['eskiyor']} eskiyor, {c['bayat']} bayat, {c['hiç']} hiç alınmamış.")
    return "\n".join(lines)


def cli(args) -> int:
    if getattr(args, "action", "status") == "seed":
        r = seed(write=not args.dry_run)
        print(("Tohum (yazılmadı): " if args.dry_run else "Tohumlandı: ") + (", ".join(sorted(r["added"])) or ("zaten tohumlanmış" if not r["seeded"] else "kayıt yok")))
        return 0
    st = status(seed_write=not args.dry_run)
    print(json.dumps(st, ensure_ascii=False, indent=1) if args.json else render(st))
    return 0


def sha256_of(p: Path, chunk: int = 1 << 20) -> str:
    """Dosyanın (ya da klasörün: sıralı göreli ad + içerik karması) SHA-256 özeti."""
    h = hashlib.sha256()
    if p.is_dir():
        for f in sorted(x for x in p.rglob("*") if x.is_file()):
            h.update(f.relative_to(p).as_posix().encode("utf-8") + b"\0")
            h.update(sha256_of(f).encode())
        return h.hexdigest()
    with p.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()
