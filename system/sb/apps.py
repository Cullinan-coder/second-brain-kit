"""Hazır uygulamalar (ClipBoardLine, Nashi): resmî açık kaynak sürümleri OLDUĞU GİBİ kurar, başlatır, başlangıca ekler.

Yeniden yazma yok: GitHub Releases'tan resmî paket indirilir, SHA-256 ile doğrulanır, sonra
  nsis-silent  → electron-builder NSIS kurucusu `/S` ile sessiz (çalışmazsa normal kurulum penceresi açılır, kullanıcıya bırakılır)
  zip-extract  → zip güvenli açılır (zip-slip / bomba korumalı) ve kurulum klasörüne konur.
Katalog `plugins/module/<id>.yaml` içindeki `app:` bölümünden okunur. Uygulamanın kendi ayarlarına ve verisine DOKUNULMAZ;
başlangıç için uygulamanın ayarı yerine kaldırılabilir bir Run anahtarı (HKCU\\...\\Run) yazılır (macOS: LaunchAgents plist).

GÜVEN ZİNCİRİ (0.13.1): kurulan sürüm "en son" değil, katalogda SABİTLENMİŞ bilinen iyi sürümdür (sürüm + etiket + dosya + SHA-256).
`install` indirileni SABİT özetle karşılaştırır (uyuşmazsa dosyayı siler, durur); sürümdeki SHA256SUMS yalnız ikinci denetimdir
(yayıncı hesabı ele geçirilirse dosya ve SHA256SUMS birlikte değişebilir, sabit özet değişmez). `update` yalnız BİLDİRİR;
kullanıcı `--accept <sürüm>` ile onaylarsa yeni sürüm+özet `~/.secondbrain/apps_pins.json` içinde kullanıcı tarafında sabitlenir.

Deneme kipinde (`SB_SETUP_SANDBOX`) indirme, kurulum ve başlangıç yazımı "[deneme] atlandı" olur.
İşlevler: catalog(), status(id), install(id, progress), start(id), set_autostart(id, mode), update_available(id), accept_update(id, sürüm), sync(id).
Ağ ve sistem çağrıları `_open`, `_run`, `_spawn`, `_proc_running`, `_reg_*` ile yapılır (testte taklit edilir).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

MODES = ("login", "startup", "off")                 # bilgisayar açılınca | Second Brain "Çalışmaya başla" ile | başlamasın
DEFAULT_MODE = "login"
ALLOWED_HOSTS = {"api.github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com",
                 "github-releases.githubusercontent.com"}
GITHUB_OWNER = "orkunisitmak"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
MAX_ZIP_FILES = 20000
MAX_ZIP_BYTES = 2 * 1024 ** 3
NSIS_WAIT = 120                                       # sessiz kurulum bittikten sonra programın görünmesini bekleme (sn)
UA = "SecondBrain-apps/1"


class AppsError(Exception):
    """Kullanıcıya gösterilecek Türkçe, sırsız hata."""


# ------------------------------------------------------------------ yollar ve durum dosyası
def sandbox_dir() -> Path | None:
    v = os.environ.get("SB_SETUP_SANDBOX")
    return Path(os.path.expanduser(v)).resolve() if v else None


def _data() -> Path:
    sb = sandbox_dir()
    if sb:
        return sb / "data"
    from . import config
    return Path(config.DATA)


def plat() -> str | None:
    return "win" if sys.platform == "win32" else "mac" if sys.platform == "darwin" else None


def expand(s: str) -> Path:
    """%LOCALAPPDATA% / %APPDATA% / ~ açar (Windows dışında da çalışır; ortam değişkeni yoksa varsayılan alt klasör)."""
    home = Path.home()
    dflt = {"LOCALAPPDATA": home / "AppData" / "Local", "APPDATA": home / "AppData" / "Roaming"}

    def sub(m):
        k = m.group(1)
        return os.environ.get(k) or str(dflt.get(k.upper(), home))
    if os.sep != "\\":
        s = s.replace("\\", "/")                 # katalogdaki Windows ayırıcıları POSIX'te yol parçası sayılmasın
    return Path(os.path.expanduser(re.sub(r"%([A-Za-z_]+)%", sub, s)))


def downloads_dir() -> Path:
    if plat() == "mac":
        return Path.home() / "Library" / "Caches" / "SecondBrain" / "downloads"
    return expand(r"%LOCALAPPDATA%\SecondBrain\downloads")


def _state_file() -> Path:
    return _data() / "apps.json"


def load_state() -> dict:
    try:
        d = json.loads(_state_file().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(st: dict) -> None:
    f = _state_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)


def _set_state(app_id: str, **kw) -> dict:
    st = load_state()
    cur = st.setdefault(app_id, {})
    cur.update(kw)
    save_state(st)
    return cur


# ------------------------------------------------------------------ katalog
def _plugins():
    from . import plugins
    return plugins


def catalog() -> list[dict]:
    """`app:` bölümü olan modül manifestleri: [{id, name, desc, app{...}}]. Ad/açıklama {tr,en} sözlüğü olarak kalır."""
    out = []
    for m in _plugins().all("module"):
        if isinstance(m.get("app"), dict):
            out.append({"id": m["id"], "name": m["name"], "desc": m["desc"], "app": m["app"], "module": m.get("module")})
    return out


def ids() -> list[str]:
    return [c["id"] for c in catalog()]


def get(app_id: str) -> dict:
    for c in catalog():
        if c["id"] == app_id:
            return c
    raise AppsError(f"Bilinmeyen uygulama: {app_id} (seçenekler: {', '.join(ids())})")


def _vkey(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v))


# ------------------------------------------------------------------ kullanıcı sabitleri (apps_pins.json)
PIN_FIELDS = ("version", "tag", "asset", "sha256")


def _pins_file() -> Path:
    return _data() / "apps_pins.json"


def load_pins() -> dict:
    try:
        d = json.loads(_pins_file().read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_pins(pins: dict) -> None:
    f = _pins_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(pins, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, f)


def _valid_pin(app: dict, base: dict, pin) -> bool:
    """Kullanıcı sabiti yalnız KATALOGDAN DAHA YENİ ve biçimi sağlam ise geçerli (eski/bozuk dosya sürümü geri çekemez)."""
    if not isinstance(pin, dict) or not all(isinstance(pin.get(k), str) for k in PIN_FIELDS):
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) or not re.fullmatch(r"[\w][\w .+-]*", pin["asset"]):
        return False
    try:
        if not re.match(app.get("tag_pattern") or r".+", pin["tag"]) or not (_vkey(pin["version"]) > _vkey(base["version"])):
            return False
    except (ValueError, re.error):
        return False
    return True


def spec(app_id: str, p: str | None = None) -> dict:
    """Bu platformun bölümü (win/mac); platform desteklenmiyorsa AppsError. Kullanıcının kabul ettiği daha yeni sürüm varsa
    (apps_pins.json) sürüm/etiket/dosya/özet alanları onunla değişir; geri kalan (kurulum yolu, yöntem ...) katalogdan."""
    c = get(app_id)
    p = p or plat()
    s = (c["app"].get(p) if p else None)
    if not s:
        raise AppsError(f"{c['app'].get('name', app_id)} bu işletim sisteminde desteklenmiyor.")
    pin = (load_pins().get(app_id) or {}).get(p)
    if pin and _valid_pin(c["app"], s, pin):
        return {**s, **{k: pin[k] for k in PIN_FIELDS}, "pinned_by_user": True}
    return s


def _label(c: dict, lang: str = "tr") -> str:
    n = c["name"]
    return n.get(lang) or n.get("tr") if isinstance(n, dict) else str(n)


# ------------------------------------------------------------------ süreç ve kayıt defteri (testte taklit)
def _run(cmd: list[str], timeout: int = 600) -> tuple[int, str]:
    flags = 0x08000000 if sys.platform == "win32" else 0
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, creationflags=flags)
    except subprocess.TimeoutExpired:
        return 124, "zaman aşımı"
    except OSError as e:
        return 127, str(e)
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def _spawn(cmd: list[str], cwd: str | None = None) -> None:
    """Uygulamayı Second Brain'den bağımsız (ayrık) süreç olarak başlatır."""
    kw: dict = {"cwd": cwd, "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform == "win32":
        kw["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000         # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
    else:
        kw["start_new_session"] = True
    subprocess.Popen(cmd, **kw)                                              # noqa: S603


def _proc_running(name: str) -> bool:
    if sys.platform == "win32":
        rc, out = _run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"], 20)
        return rc == 0 and name.lower() in out.lower()
    rc, _ = _run(["pgrep", "-x", name], 10)
    return rc == 0


def _reg_set(name: str, value: str) -> None:
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)


def _reg_get(name: str) -> str | None:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            return str(winreg.QueryValueEx(k, name)[0])
    except OSError:
        return None


def _reg_del(name: str) -> None:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, name)
    except OSError:
        pass


def run_value_name(app_id: str) -> str:
    return "SecondBrain-" + get(app_id)["app"].get("name", app_id).replace(" ", "")


def _launch_agent(app_id: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"com.secondbrain.app.{app_id}.plist"


# ------------------------------------------------------------------ durum
def exe_path(app_id: str, p: str | None = None) -> Path:
    return expand(spec(app_id, p)["exe"])


def data_path(app_id: str, p: str | None = None) -> Path:
    return expand(spec(app_id, p)["data"])


def installed(app_id: str, p: str | None = None) -> bool:
    try:
        return exe_path(app_id, p).exists()
    except AppsError:
        return False


def running(app_id: str, p: str | None = None) -> bool:
    try:
        return _proc_running(spec(app_id, p)["process"])
    except AppsError:
        return False


def autostart_mode(app_id: str) -> str:
    m = load_state().get(app_id, {}).get("autostart")
    return m if m in MODES else DEFAULT_MODE


def status(app_id: str, p: str | None = None) -> dict:
    c = get(app_id)
    p = p or plat()
    st = load_state().get(app_id, {})
    out = {"id": app_id, "name": c["app"].get("name", app_id), "platform": p, "supported": bool(p and c["app"].get(p)),
           "installed": False, "version": None, "running": False, "exe": "", "data_dir": "", "data_exists": False,
           "autostart": autostart_mode(app_id), "autostart_active": False, "size_mb": c["app"].get("size_mb"),
           "last_sync": st.get("last_sync"), "records": st.get("records"), "skipped_secret": st.get("skipped_secret"),
           "last_error": st.get("last_error"), "pinned_version": None, "pinned_sha256": None, "pinned_by_user": False}
    if not out["supported"]:
        return out
    s = spec(app_id, p)
    out.update(pinned_version=s["version"], pinned_sha256=s.get("sha256"), pinned_by_user=bool(s.get("pinned_by_user")))
    exe = expand(s["exe"])
    out.update(exe=str(exe), data_dir=str(expand(s["data"])), data_exists=expand(s["data"]).exists(), installed=exe.exists())
    if out["installed"]:
        out["version"] = st.get("version")
        out["running"] = _proc_running(s["process"])
        out["autostart_active"] = _autostart_active(app_id, p)
    return out


def _autostart_active(app_id: str, p: str) -> bool:
    if sandbox_dir():
        return False
    try:
        if p == "win":
            return bool(_reg_get(run_value_name(app_id)))
        return _launch_agent(app_id).exists()
    except Exception:                                                        # noqa: BLE001
        return False


def detect_version(app_id: str, p: str | None = None) -> str | None:
    """Kurulu ama sürümü kayıtlı olmayan uygulamanın (ör. kurulum penceresiyle kurulan) sürümünü exe dosya bilgisinden okur ve kaydeder."""
    p = p or plat()
    if p != "win" or not installed(app_id, p):
        return None
    ps = f"(Get-Item -LiteralPath '{exe_path(app_id, p)}').VersionInfo.ProductVersion"
    rc, out = _run(["powershell", "-NoProfile", "-Command", ps], 30)
    m = re.search(r"\d+(?:\.\d+){1,3}", out) if rc == 0 else None
    if not m:
        return None
    v = m.group(0)[:-2] if m.group(0).count(".") == 3 and m.group(0).endswith(".0") else m.group(0)
    _set_state(app_id, version=v)
    return v


def status_all() -> list[dict]:
    return [status(i) for i in ids()]


# ------------------------------------------------------------------ indirme
class _Guard(HTTPRedirectHandler):
    """Yönlendirmede de yalnız izinli adreslere gider."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def check_url(url: str) -> str:
    u = urlparse(url)
    if u.scheme != "https":
        raise AppsError("Yalnızca https adreslerinden indirilir.")
    host = (u.hostname or "").lower()
    if host == "github.com":
        if not u.path.lower().startswith(f"/{GITHUB_OWNER}/"):
            raise AppsError(f"İzin verilmeyen GitHub adresi: {u.path[:60]}")
    elif host not in ALLOWED_HOSTS:
        raise AppsError(f"İzin verilmeyen indirme adresi: {host}")
    return url


def _open(url: str, headers: dict | None = None, timeout: int = 60):
    """İzinli adrese istek açar; yanıt: read() ve headers/status olan nesne. Testte taklit edilir."""
    check_url(url)
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*", **(headers or {})})
    return build_opener(_Guard).open(req, timeout=timeout)


def _get_text(url: str, limit: int = 1 << 20) -> str:
    with _open(url) as r:
        return r.read(limit).decode("utf-8", "replace")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sums(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\s*([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line)
        if m:
            out[m.group(2)] = m.group(1).lower()
    return out


def expected_sha(sums: dict[str, str], asset: str) -> str | None:
    if asset in sums:
        return sums[asset]
    low = {k.lower(): v for k, v in sums.items()}
    return low.get(asset.lower())


def release_url(repo: str, tag: str, name: str) -> str:
    return f"https://github.com/{repo}/releases/download/{tag}/{name}"


def resolve_asset(app: dict, s: dict, name: str) -> tuple[str, int | None]:
    """Sürüm varlığının indirme adresi ve boyutu: önce Releases API, olmazsa deterministik sürüm adresi."""
    api = f"https://api.github.com/repos/{app['repo']}/releases/tags/{s['tag']}"
    try:
        for a in json.loads(_get_text(api, 4 << 20)).get("assets") or []:
            if a.get("name") == name and a.get("browser_download_url"):
                return check_url(a["browser_download_url"]), int(a.get("size") or 0) or None
    except (AppsError, OSError, ValueError):
        pass
    return release_url(app["repo"], s["tag"], name), None


def download(url: str, dest: Path, max_bytes: int, progress=None, expect_size: int | None = None) -> Path:
    """`dest.part` dosyasına indirir (kesilirse kaldığı yerden), bitince `dest`e taşır. Boyut sınırı aşılırsa durur ve siler."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    have = part.stat().st_size if part.exists() else 0
    headers = {"Range": f"bytes={have}-"} if have else {}
    try:
        r = _open(url, headers, 120)
    except AppsError:
        raise
    except Exception as e:                                                   # noqa: BLE001
        raise AppsError(f"İndirilemedi: {type(e).__name__}: {str(e)[:120]}") from None
    with r:
        status_code = getattr(r, "status", 200)
        total = int((getattr(r, "headers", {}) or {}).get("Content-Length") or 0)
        if status_code == 206:
            total += have
        else:
            have = 0                                                         # sunucu aralığı desteklemedi: baştan
        if total and total > max_bytes:
            raise AppsError(f"Dosya beklenenden büyük ({total // 2**20} MB > {max_bytes // 2**20} MB); indirme durduruldu.")
        done, t0 = have, time.time()
        with open(part, "ab" if have else "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                done += len(chunk)
                if done > max_bytes:
                    f.close()
                    part.unlink(missing_ok=True)
                    raise AppsError("İndirme boyut sınırını aştı; durduruldu ve silindi.")
                f.write(chunk)
                if progress:
                    progress(min(100, int(100 * done / total)) if total else 0, f"{done // 2**20} MB indirildi")
    if expect_size and done != expect_size:
        part.unlink(missing_ok=True)
        raise AppsError(f"İndirilen boyut ({done}) beklenenle ({expect_size}) uyuşmuyor; silindi.")
    os.replace(part, dest)
    return dest


# ------------------------------------------------------------------ zip (zip-slip korumalı)
def safe_extract(zpath: Path, dest: Path) -> int:
    """zip'i `dest` içine açar. Mutlak yol, `..`, sürücü harfi, sembolik bağ, aşırı dosya sayısı/boyutu → AppsError (hiçbir şey açılmaz)."""
    dest = dest.resolve()
    with zipfile.ZipFile(zpath) as z:
        infos = z.infolist()
        if len(infos) > MAX_ZIP_FILES or sum(i.file_size for i in infos) > MAX_ZIP_BYTES:
            raise AppsError("Zip dosyası aşırı büyük ya da çok dosyalı; açılmadı.")
        targets = []
        for i in infos:
            name = i.filename.replace("\\", "/")
            if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in name.split("/"):
                raise AppsError(f"Zip içinde güvensiz yol bulundu ({name[:60]}); açılmadı.")
            if (i.external_attr >> 16) & 0o170000 == 0o120000:
                raise AppsError(f"Zip içinde sembolik bağ var ({name[:60]}); açılmadı.")
            t = (dest / name).resolve()
            if t != dest and dest not in t.parents:
                raise AppsError(f"Zip içinde klasör dışına çıkan yol var ({name[:60]}); açılmadı.")
            targets.append((i, t))
        dest.mkdir(parents=True, exist_ok=True)
        n = 0
        for i, t in targets:
            if i.is_dir():
                t.mkdir(parents=True, exist_ok=True)
                continue
            t.parent.mkdir(parents=True, exist_ok=True)
            with z.open(i) as src, open(t, "wb") as out:
                shutil.copyfileobj(src, out)
            n += 1
    return n


def _flatten(root: Path, exe_name: str) -> None:
    """Zip tek bir üst klasör içeriyorsa (ve çalıştırılabilir dosya orada ise) içeriği bir üste taşır."""
    if (root / exe_name).exists():
        return
    kids = [p for p in root.iterdir()]
    if len(kids) == 1 and kids[0].is_dir() and (kids[0] / exe_name).exists():
        inner = kids[0]
        for p in inner.iterdir():
            shutil.move(str(p), str(root / p.name))
        inner.rmdir()


# ------------------------------------------------------------------ kurulum
def _noop(*_a) -> None:
    return None


def install(app_id: str, progress=None, p: str | None = None, force: bool = False) -> dict:
    """İndir → doğrula → kur. Döner: {ok, installed, message, skipped?, manual?}. AppsError yükseltir (mesaj kullanıcıya gösterilir)."""
    progress = progress or _noop
    c = get(app_id)
    app = c["app"]
    p = p or plat()
    s = spec(app_id, p)
    name = app.get("name", app_id)
    if sandbox_dir():
        msg = f"[deneme] atlandı: {name} indirilmedi/kurulmadı ({s['asset']})"
        return {"ok": True, "installed": False, "skipped": True, "message": msg}
    if installed(app_id, p) and not force:
        v = load_state().get(app_id, {}).get("version")
        if v == s["version"]:
            progress(100, "Zaten kurulu")
            return {"ok": True, "installed": True, "message": f"{name} zaten kurulu (sürüm {v})."}
    if _proc_running_safe(s) and s["method"] == "zip-extract" and installed(app_id, p):
        raise AppsError(f"{name} çalışıyor; güncellemek için önce kapat.")
    size_mb = int(app.get("size_mb") or 0)
    max_bytes = int(size_mb * 1.25 + 20) * 1024 * 1024
    dl = downloads_dir()
    dl.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(dl).free
    if free < max_bytes * 2:
        raise AppsError(f"Diskte yer yetersiz: {free // 2**20} MB boş, en az {max_bytes * 2 // 2**20} MB gerekir.")
    want = str(s.get("sha256") or "").lower()                                # SABİT bilinen iyi özet (katalog ya da kullanıcının kabul ettiği)
    if not re.fullmatch(r"[0-9a-f]{64}", want):
        raise AppsError(f"{name} için sabit SHA-256 özeti tanımlı değil; güvenle doğrulanamadığı için kurulmadı.")
    progress(1, "Sürüm bilgisi alınıyor")
    url, api_size = resolve_asset(app, s, s["asset"])
    sums_url, _ = resolve_asset(app, s, s["sums"])
    try:
        sums = parse_sums(_get_text(sums_url))
    except AppsError:
        raise
    except Exception as e:                                                   # noqa: BLE001
        raise AppsError(f"Sürümün SHA256SUMS dosyası okunamadı: {type(e).__name__}: {str(e)[:100]}") from None
    rel = expected_sha(sums, s["asset"])                                     # ikinci denetim: yayıncının kendi özeti sabitle çelişmemeli
    if not rel:
        raise AppsError(f"SHA256SUMS içinde {s['asset']} için özet yok; güvenle doğrulanamadığı için kurulmadı.")
    if rel != want:
        raise AppsError(f"Sürümün SHA256SUMS özeti ({rel[:12]}…) sabitlenmiş bilinen iyi özetle ({want[:12]}…) çelişiyor; "
                        f"{name} indirilmedi, kurulum durdu (yayıncı dosyası değişmiş olabilir).")
    f = dl / s["asset"]
    if not (f.exists() and sha256_file(f) == want):
        f.unlink(missing_ok=True)
        download(url, f, max_bytes, lambda pc, m: progress(2 + int(pc * 0.78), m), api_size)
    progress(82, "SHA-256 doğrulanıyor")
    got = sha256_file(f)
    if got != want:
        f.unlink(missing_ok=True)
        raise AppsError(f"SHA-256 sabit özetle uyuşmuyor (beklenen {want[:12]}…, gelen {got[:12]}…); dosya silindi, kurulum durdu.")
    progress(88, "Kuruluyor")
    res = _install_method(app_id, s, f, p)
    if res.get("installed"):
        _set_state(app_id, version=s["version"], tag=s["tag"], installed_at=datetime.now().isoformat(timespec="seconds"))
        st = load_state().get(app_id, {})
        if st.get("autostart") not in MODES:
            _set_state(app_id, autostart=DEFAULT_MODE)
        try:
            set_autostart(app_id, autostart_mode(app_id), p)
        except AppsError as e:
            res["message"] += f" (başlangıç ayarı yazılamadı: {e})"
        f.unlink(missing_ok=True)
    progress(100, res["message"])
    return res


def _proc_running_safe(s: dict) -> bool:
    try:
        return _proc_running(s["process"])
    except Exception:                                                        # noqa: BLE001
        return False


def _install_method(app_id: str, s: dict, f: Path, p: str) -> dict:
    name = get(app_id)["app"].get("name", app_id)
    exe = expand(s["exe"])
    if s["method"] == "nsis-silent":
        rc, out = _run([str(f), "/S"], 900)
        deadline = time.time() + NSIS_WAIT
        while not exe.exists() and time.time() < deadline and rc == 0:
            time.sleep(2)
        if exe.exists():
            return {"ok": True, "installed": True, "message": f"{name} {s['version']} kuruldu: {exe}"}
        _spawn([str(f)])                                                     # sessiz kurulum olmadı: normal kurulum penceresi
        return {"ok": False, "installed": False, "manual": True,
                "message": f"Sessiz kurulum tamamlanamadı (kod {rc}). {name} kurulum penceresini açtım; "
                           f"bitirdikten sonra `sb apps status {app_id}` ile denetle."}
    if s["method"] == "zip-extract":
        if p == "mac":
            return _install_mac_zip(app_id, s, f)
        dest = expand(s["install_dir"])
        stage = dest.with_name(dest.name + ".new")
        if stage.exists():
            shutil.rmtree(stage)
        safe_extract(f, stage)
        _flatten(stage, Path(s["exe"].replace("\\", "/")).name)
        if not (stage / Path(s["exe"].replace("\\", "/")).name).exists():
            shutil.rmtree(stage, ignore_errors=True)
            raise AppsError(f"Zip içinde {Path(s['exe'].replace(chr(92), '/')).name} bulunamadı; kurulmadı.")
        old = dest.with_name(dest.name + ".old")
        if old.exists():
            shutil.rmtree(old, ignore_errors=True)
        if dest.exists():
            os.replace(dest, old)
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(stage, dest)
        shutil.rmtree(old, ignore_errors=True)
        lnk = start_menu_shortcut(name, exe)                                 # taşınabilir zip'in kısayolu yok: Başlat'ta bulunsun
        msg = f"{name} {s['version']} kuruldu: {dest}" + (f" · Başlat menüsü kısayolu: {lnk}" if lnk else "")
        return {"ok": True, "installed": exe.exists(), "shortcut": str(lnk) if lnk else None, "message": msg}
    raise AppsError(f"Bilinmeyen kurulum yöntemi: {s['method']}")


def _start_menu_dir() -> Path:
    return Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def start_menu_shortcut(name: str, exe: Path) -> Path | None:
    """Windows Başlat menüsüne <ad>.lnk yazar (WScript.Shell). Başarısızlık kurulumu bozmaz: None döner."""
    if sys.platform != "win32":
        return None
    lnk = _start_menu_dir() / f"{name}.lnk"
    q = lambda v: str(v).replace("'", "''")
    ps = (f"$s=New-Object -ComObject WScript.Shell; $l=$s.CreateShortcut('{q(lnk)}'); $l.TargetPath='{q(exe)}'; "
          f"$l.WorkingDirectory='{q(exe.parent)}'; $l.IconLocation='{q(exe)}'; $l.Save()")
    try:
        lnk.parent.mkdir(parents=True, exist_ok=True)
        rc, _ = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], 30)
    except (OSError, AppsError):
        return None
    return lnk if rc == 0 and lnk.exists() else None


def _install_mac_zip(app_id: str, s: dict, f: Path) -> dict:
    name = get(app_id)["app"].get("name", app_id)
    with zipfile.ZipFile(f) as z:                                            # açmadan önce yol denetimi (zip-slip)
        for n in z.namelist():
            if n.startswith("/") or ".." in n.replace("\\", "/").split("/"):
                raise AppsError(f"Zip içinde güvensiz yol bulundu ({n[:60]}); açılmadı.")
    dest = expand(s["install_dir"])
    dest.mkdir(parents=True, exist_ok=True)
    rc, out = _run(["ditto", "-x", "-k", str(f), str(dest)], 600)          # .app paketinin izinlerini/bağlarını korur
    if rc != 0:
        raise AppsError(f"macOS'ta zip açılamadı: {out[:120]}")
    exe = expand(s["exe"])
    if not exe.exists():
        apps = sorted(dest.glob("*.app"))
        if len(apps) == 1:
            exe = apps[0]
    if not exe.exists():
        raise AppsError("Zip açıldı ama .app bulunamadı (macOS dalı denenmedi; bilinen sınır).")
    return {"ok": True, "installed": True, "message": f"{name} {s['version']} kuruldu: {exe} (macOS: ilk açılışta Gatekeeper onayı gerekebilir)"}


# ------------------------------------------------------------------ başlatma
def start(app_id: str, background: bool = False, p: str | None = None) -> dict:
    c = get(app_id)
    name = c["app"].get("name", app_id)
    p = p or plat()
    s = spec(app_id, p)
    exe = expand(s["exe"])
    if sandbox_dir():
        return {"ok": True, "skipped": True, "message": f"[deneme] atlandı: {name} başlatılmadı"}
    if not exe.exists():
        raise AppsError(f"{name} kurulu değil. Kurmak için: sb apps install {app_id}")
    if _proc_running(s["process"]):
        return {"ok": True, "started": False, "message": f"{name} zaten çalışıyor."}
    args = list(s.get("background_args" if background else "start_args") or [])
    if p == "mac":
        _spawn(["open", "-a", str(exe), *(["--args", *args] if args else [])])
    else:
        _spawn([str(exe), *args], str(exe.parent))
    return {"ok": True, "started": True, "message": f"{name} başlatıldı."}


# ------------------------------------------------------------------ başlangıç
def run_command(app_id: str, p: str | None = None) -> str:
    s = spec(app_id, p)
    args = " ".join(f'"{a}"' if " " in a else a for a in (s.get("background_args") or s.get("start_args") or []))
    return f'"{expand(s["exe"])}"' + (f" {args}" if args else "")


def set_autostart(app_id: str, mode: str, p: str | None = None) -> dict:
    """mode: login (bilgisayar açılınca; Run anahtarı), startup (Second Brain 'Çalışmaya başla' ile), off. Seçim kaydedilir;
    Run anahtarı yalnız uygulama kuruluysa ve login için yazılır, diğer kiplerde kaldırılır."""
    if mode not in MODES:
        raise AppsError(f"Geçersiz başlangıç kipi: {mode} (login|startup|off)")
    c = get(app_id)
    name = c["app"].get("name", app_id)
    p = p or plat()
    _set_state(app_id, autostart=mode)
    if sandbox_dir():
        return {"ok": True, "skipped": True, "mode": mode, "message": f"[deneme] atlandı: {name} başlangıç kaydı yazılmadı (seçim: {mode})"}
    if not p or not c["app"].get(p):
        return {"ok": False, "mode": mode, "message": "Bu işletim sisteminde desteklenmiyor."}
    if p == "win":
        key = run_value_name(app_id)
        if mode == "login" and installed(app_id, p):
            _reg_set(key, run_command(app_id, p))
            msg = f"{name}: bilgisayar açılınca başlayacak (Run anahtarı {key})."
        else:
            _reg_del(key)
            msg = (f"{name}: seçim kaydedildi ({mode})." if mode == "login" else
                   f"{name}: bilgisayar açılınca başlamayacak" + (" (Second Brain 'Çalışmaya başla' ile başlar)." if mode == "startup" else "."))
    else:
        pl = _launch_agent(app_id)
        if mode == "login" and installed(app_id, p):
            import plistlib
            s = spec(app_id, p)
            pl.parent.mkdir(parents=True, exist_ok=True)
            pl.write_bytes(plistlib.dumps({"Label": f"com.secondbrain.app.{app_id}", "RunAtLoad": True,
                                           "ProgramArguments": ["open", "-a", str(expand(s["exe"])), *(["--args", *s.get("background_args", [])] if s.get("background_args") else [])]}))
            msg = f"{name}: oturum açılınca başlayacak (LaunchAgent)."
        else:
            if pl.exists():
                pl.unlink()
            msg = f"{name}: seçim kaydedildi ({mode})."
    return {"ok": True, "mode": mode, "message": msg}


def start_startup_apps(log=print) -> list[dict]:
    """'Çalışmaya başla': başlangıç kipi 'startup' olan kurulu uygulamaları arka planda başlatır."""
    out = []
    for i in ids():
        if autostart_mode(i) == "startup" and installed(i):
            try:
                out.append({"id": i, **start(i, background=True)})
            except AppsError as e:
                out.append({"id": i, "ok": False, "message": str(e)})
            log(out[-1]["message"])
    return out


# ------------------------------------------------------------------ sürüm denetimi (yalnız BİLDİRİR; kurmaz)
def _new_asset(s: dict, latest: str, release: dict) -> str:
    """Yeni sürümün dosya adı: sürümün varlık listesinde eski adla aynı biçimde (yalnız sayılar farklı) olan; yoksa eski addaki sürümü değiştirir."""
    pat = re.compile("^" + re.sub(r"\d+", r"\\d+", re.escape(s["asset"])) + "$")
    names = [a.get("name") for a in (release.get("assets") or []) if isinstance(a, dict) and a.get("name")]
    hits = [n for n in names if pat.match(n)]
    if hits:
        return next((n for n in hits if latest in n), hits[0])
    return s["asset"].replace(s["version"], latest)


def update_available(app_id: str, p: str | None = None) -> dict:
    """Ağa çıkar (yalnız api.github.com ve sürümün SHA256SUMS dosyası). KURMAZ, sabitlemez. Dönüş: {available, current, latest, tag,
    notes_url, asset, digest, accept_cmd, error?}. `digest`: yeni sürümün SHA256SUMS'undaki özet (kullanıcı görüp onaylar)."""
    c = get(app_id)
    app = c["app"]
    s = spec(app_id, p)
    cur = load_state().get(app_id, {}).get("version") or s["version"]
    pat = re.compile(app.get("tag_pattern") or r".+")
    try:
        rels = json.loads(_get_text(f"https://api.github.com/repos/{app['repo']}/releases?per_page=30", 4 << 20))
    except (AppsError, OSError, ValueError) as e:
        return {"available": False, "current": cur, "latest": None, "error": str(e)[:120]}
    best = None
    for r in rels:
        m = pat.match(str(r.get("tag_name") or ""))
        if m and not r.get("draft") and not r.get("prerelease"):
            key = tuple(_vkey(g) for g in m.groups())
            if best is None or key > best[0]:
                best = (key, r, m.group(1))
    if not best:
        return {"available": False, "current": cur, "latest": None}
    rel, latest = best[1], best[2]
    tag = rel["tag_name"]
    out = {"available": _vkey(latest) > _vkey(s["version"]) and _vkey(latest) > _vkey(cur), "current": cur, "latest": latest, "tag": tag,
           "pinned": s["version"]}
    if not out["available"]:
        return out
    out["notes_url"] = rel.get("html_url") or f"https://github.com/{app['repo']}/releases/tag/{tag}"
    out["asset"] = _new_asset(s, latest, rel)
    out["accept_cmd"] = f"sb apps update {app_id} --accept {latest}"
    try:
        sums = parse_sums(_get_text(resolve_asset(app, {"tag": tag}, s["sums"])[0]))
        out["digest"] = expected_sha(sums, out["asset"])
    except (AppsError, OSError, ValueError) as e:
        out["digest"], out["error"] = None, f"yeni sürümün SHA256SUMS dosyası okunamadı: {str(e)[:100]}"
    return out


def accept_update(app_id: str, version: str, p: str | None = None) -> dict:
    """Kullanıcının AÇIK onayı: bildirilen yeni sürümü + özetini kullanıcı tarafında sabitler (apps_pins.json). Kurmaz (kurmak için `install --force`)."""
    p = p or plat()
    u = update_available(app_id, p)
    if u.get("error") and not u.get("digest"):
        raise AppsError(f"Sürüm bilgisi alınamadı: {u['error']}")
    if not u.get("available") or u.get("latest") != str(version).strip():
        raise AppsError(f"Kabul edilecek {version!r} sürümü yok (bulunan: {u.get('latest') or 'yok'}"
                        f"{'' if u.get('available') else ', kurulu/sabit sürümden yeni değil'}); önce `sb apps update {app_id}` ile bak.")
    if not u.get("digest"):
        raise AppsError(f"{u.get('asset')} için yayıncının SHA256SUMS dosyasında özet yok; sabitlenmedi.")
    pin = {"version": u["latest"], "tag": u["tag"], "asset": u["asset"], "sha256": u["digest"],
           "accepted_at": datetime.now().isoformat(timespec="seconds"), "notes_url": u["notes_url"]}
    if not _valid_pin(get(app_id)["app"], spec(app_id, p), pin):
        raise AppsError("Sabit biçimi geçersiz (sürüm etiketi ya da özet beklenen biçimde değil); sabitlenmedi.")
    pins = load_pins()
    pins.setdefault(app_id, {})[p] = pin
    _save_pins(pins)
    return {"ok": True, "pinned": pin, "message": f"{get(app_id)['app'].get('name', app_id)} {u['latest']} sabitlendi (SHA-256 {u['digest'][:12]}…). "
            f"Kurmak için: sb apps install {app_id} --force"}


# ------------------------------------------------------------------ senkron (bağlayıcılar salt okunur)
def _connector(app_id: str):
    if app_id == "clipboardline":
        from .connectors import clipboardline as m
    elif app_id == "nashi":
        from .connectors import nashi as m
    else:
        raise AppsError(f"{app_id} için bağlayıcı yok")
    return m


def sync(app_id: str, dry_run: bool = False, require_enabled: bool = False) -> dict:
    """Uygulamanın verisini beyin arşivine (mail.db items) okur. Kurulu/veri yoksa 0 kayıt ve açıklama."""
    from . import features, maildb
    from .config import MAIL_DB
    get(app_id)
    if require_enabled and not features.enabled(app_id):
        return {"kaynak": app_id, "not": "modül kapalı", "okunan": 0, "yeni": 0}
    if plat() != "win":
        return {"kaynak": app_id, "not": "bağlayıcı yalnız Windows veri biçimini okur (macOS denenmedi)", "okunan": 0, "yeni": 0}
    mod = _connector(app_id)
    d = data_path(app_id)
    if not d.exists():
        r = {"kaynak": app_id, "not": f"veri klasörü yok ({d}); uygulama henüz açılmamış olabilir", "okunan": 0, "yeni": 0}
        if not dry_run:
            _set_state(app_id, last_sync=datetime.now().isoformat(timespec="seconds"), records=_count(app_id), last_error=None)
        return r
    con = maildb.connect(MAIL_DB if not dry_run or MAIL_DB.exists() else Path(":memory:"))
    try:
        r = mod.run(d, con, dry_run=dry_run)
    finally:
        con.close()
    if not dry_run:
        err = r.get("not") if r.get("locked") or r.get("error") else None
        _set_state(app_id, last_sync=datetime.now().isoformat(timespec="seconds"), records=_count(app_id),
                   skipped_secret=r.get("atlanan_sir", 0), last_error=err)
    return r


def _count(app_id: str) -> int:
    from . import maildb
    from .config import MAIL_DB
    if not Path(MAIL_DB).exists():
        return 0
    con = maildb.connect(MAIL_DB)
    try:
        return int(con.execute("SELECT count(*) FROM items WHERE source = ?", (app_id,)).fetchone()[0])
    finally:
        con.close()


def sync_all(dry_run: bool = False, require_enabled: bool = True) -> list[dict]:
    out = []
    for i in ids():
        try:
            out.append(sync(i, dry_run, require_enabled))
        except Exception as e:                                               # noqa: BLE001 — biri ötekini durdurmasın
            out.append({"kaynak": i, "not": f"hata: {type(e).__name__}: {str(e)[:120]}", "okunan": 0, "yeni": 0, "error": True})
    return out


def format_sync(r: dict) -> str:
    if r.get("not") and not r.get("okunan"):
        return f"{r['kaynak']}: {r['not']}"
    s = f"{r['kaynak']}: okunan {r.get('okunan', 0)}, yeni {r.get('yeni', 0)}"
    if r.get("guncellenen"):
        s += f", güncellenen {r['guncellenen']}"
    if r.get("tekrar"):
        s += f", tekrar {r['tekrar']}"
    if r.get("atlanan_sir"):
        s += f", sır içerdiği için atlanan {r['atlanan_sir']}"
    if r.get("silinmis"):
        s += f", çöpteki/silinmiş {r['silinmis']}"
    return s + (f" — {r['not']}" if r.get("not") else "")


# ------------------------------------------------------------------ CLI
def format_status(s: dict) -> str:
    if not s["supported"]:
        return f"{s['name']}: bu işletim sisteminde desteklenmiyor"
    state = "kurulu" + (f" (sürüm {s['version']})" if s["version"] else "") if s["installed"] else "kurulu değil"
    bits = [state]
    if s["installed"]:
        bits.append("çalışıyor" if s["running"] else "çalışmıyor")
    bits.append(f"başlangıç: {s['autostart']}" + (" (Run kaydı var)" if s["autostart_active"] else ""))
    if s["last_sync"]:
        bits.append(f"son senkron {s['last_sync']}, {s['records'] or 0} kayıt")
    lines = [f"{s['name']}: " + "; ".join(bits)]
    if s["installed"]:
        lines.append(f"  program: {s['exe']}")
    lines.append(f"  veri: {s['data_dir']}" + ("" if s["data_exists"] else " (henüz yok)"))
    return "\n".join(lines)


def _cli_update(args) -> int:
    accept = str(getattr(args, "accept", "") or "").strip()
    if accept:
        r = accept_update(args.id, accept)
        print(r["message"])
        print("Kuruluyor (sabitlenen sürüm ve özet doğrulanarak)...")
        last = [-1]

        def prog(pc, msg):
            if pc // 10 != last[0]:
                last[0] = pc // 10
                print(f"  %{pc:<3} {msg}", flush=True)
        res = install(args.id, prog, force=True)
        print(res["message"])
        return 0 if res.get("ok") else 1
    u = update_available(args.id)
    head = f"{args.id}: kurulu {u['current']}, bilinen iyi (sabit) sürüm {u.get('pinned', u['current'])}"
    if not u["available"]:
        print(head + ", güncel" + (f" (denetim hatası: {u['error']})" if u.get("error") else ""))
        return 0
    print(head + f"; YENİ SÜRÜM VAR: {u['latest']} ({u.get('tag')}). Kendiliğinden KURULMAZ.")
    print(f"  Değişiklik notları : {u['notes_url']}")
    print(f"  Yeni dosya         : {u.get('asset')}")
    print(f"  SHA-256 (yayıncı)  : {u.get('digest') or 'okunamadı'}" + (f"  [{u['error']}]" if u.get("error") else ""))
    print("  Notları okuyup özeti yayıncının sayfasından çapraz denetledikten sonra kabul etmek için:")
    print(f"    {u['accept_cmd']}")
    return 0


def cli(args) -> int:
    act = args.action
    try:
        if act == "list":
            for c in catalog():
                print(f"{c['id']:14} {_label(c)} — {c['app'].get('size_mb')} MB — {c['app'].get('repo')}")
            return 0
        if act == "status":
            for i in ([args.id] if args.id and args.id != "all" else ids()):
                if installed(i) and not load_state().get(i, {}).get("version"):
                    detect_version(i)
                print(format_status(status(i)))
            return 0
        if not args.id:
            print(f"`sb apps {act}` için uygulama kimliği gerekli ({', '.join(ids())})")
            return 1
        if act == "install":
            last = [-1]

            def prog(pc, msg):
                if pc // 10 != last[0]:
                    last[0] = pc // 10
                    print(f"  %{pc:<3} {msg}", flush=True)
            r = install(args.id, prog, force=args.force)
            print(r["message"])
            return 0 if r.get("ok") else 1
        if act == "start":
            r = start(args.id, background=args.background)
            print(r["message"])
            return 0
        if act == "autostart":
            if not args.mode:
                print(f"{args.id}: başlangıç kipi = {autostart_mode(args.id)} (login|startup|off)")
                return 0
            r = set_autostart(args.id, args.mode)
            print(r["message"])
            return 0 if r.get("ok") else 1
        if act == "update":
            return _cli_update(args)
        if act == "sync":
            rows = sync_all(args.dry_run, require_enabled=True) if args.id == "all" else [sync(args.id, args.dry_run)]
            for r in rows:
                print(format_sync(r))
            return 1 if any(r.get("error") for r in rows) else 0
    except AppsError as e:
        print(f"Hata: {e}")
        return 1
    print(f"bilinmeyen eylem: {act}")
    return 1
