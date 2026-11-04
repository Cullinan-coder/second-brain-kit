"""Pano: yerel pano geçmişi (ClipBoardLine'dan esinlenen yeniden yazım). Üç raf: görsel / metin / bağlantı.

Güvenlik ilkeleri (hepsi varsayılan):
- KAPALI gelir; `sb pano on` ya da ayarlarda açık izin gerekir. Metin ve görsel toplama ayrı ayrı açılır (görsel varsayılan kapalı).
- Sır/şifre/API anahtarı/IBAN/kart/TCKN gibi görünen metin ASLA saklanmaz (redact + ek sezgiler). Parola yöneticisinin
  "gizli" işaretiyle koyduğu içerik ve kara listedeki uygulamalardan gelenler atlanır.
- Veri yalnız `<data>/pano.db` ve `<data>/pano/img/` altındadır; bu modül buluta/modele hiçbir şey göndermez (llm içe aktarılmaz).
- Silme önce çöp kutusuna gider (geri alınabilir); kalıcı silme yalnız açık `hard`/`empty_trash` çağrısıyla.
"""
from __future__ import annotations

import hashlib
import io
import json
import platform
import re
import shutil
import sqlite3
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from . import config, features
from .redact import ASSIGN_RE, KEY_RE, redact

KINDS = ("image", "text", "link")
RETENTION_CHOICES = (1, 3, 7, 15, 30)
TRASH_DAYS = 30
DEFAULT_BLACKLIST = ["keepass", "1password", "bitwarden", "lastpass", "dashlane", "enpass", "nordpass", "proton pass", "keeper"]
DEFAULTS: dict = {
    "enabled": False,
    "collect_text": True,          # links text shelf'in parçasıdır: metin toplama kapalıysa bağlantı da toplanmaz
    "collect_images": False,
    "retention": {"image": 30, "text": 30, "link": 30},
    "blacklist": DEFAULT_BLACKLIST,
    "max_text_kb": 200,
    "max_image_mb": 10,
    "max_img_dir_mb": 500,
}
POLL_SECONDS = 1.0
URL_RE = re.compile(r"^https?://\S+$", re.I)


# ------------------------------------------------------------------ yollar ve ayarlar
def module_on() -> bool:
    """Özellik anahtarı (features.MODULES["pano"], varsayılan KAPALI). Kapalıyken toplama, izleyici ve web uçları çalışmaz."""
    return features.enabled("pano")


def active(cfg: dict | None = None) -> bool:
    """Toplama gerçekten açık mı: modül anahtarı VE kullanıcının kendi pano ayarı açık."""
    return module_on() and bool((cfg or settings())["enabled"])


def _db_path() -> Path:
    return config.DATA / "pano.db"


def _img_dir() -> Path:
    return config.DATA / "pano" / "img"


def _settings_path() -> Path:
    return config.DATA / "pano_settings.json"


def settings() -> dict:
    s = json.loads(json.dumps(DEFAULTS))
    try:
        raw = json.loads(_settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raw = {}
    if isinstance(raw, dict):
        for k in ("enabled", "collect_text", "collect_images"):
            if isinstance(raw.get(k), bool):
                s[k] = raw[k]
        if isinstance(raw.get("retention"), dict):
            for k in KINDS:
                if raw["retention"].get(k) in RETENTION_CHOICES:
                    s["retention"][k] = raw["retention"][k]
        if isinstance(raw.get("blacklist"), list):
            s["blacklist"] = [str(x).strip() for x in raw["blacklist"] if str(x).strip()]
        for k, lo, hi in (("max_text_kb", 1, 1024), ("max_image_mb", 1, 50), ("max_img_dir_mb", 50, 5000)):
            if isinstance(raw.get(k), int) and not isinstance(raw.get(k), bool):
                s[k] = max(lo, min(hi, raw[k]))
    return s


def set_settings(patch: dict) -> dict:
    cur = settings()
    for k in ("enabled", "collect_text", "collect_images"):
        if k in patch:
            if not isinstance(patch[k], bool):
                raise ValueError(f"{k} true/false olmalı")
            cur[k] = patch[k]
    if "retention" in patch:
        r = patch["retention"]
        if not isinstance(r, dict):
            raise ValueError("retention sözlük olmalı")
        for k, v in r.items():
            if k not in KINDS or v not in RETENTION_CHOICES:
                raise ValueError(f"tutma süresi {RETENTION_CHOICES} günden biri olmalı ({k})")
            cur["retention"][k] = v
    if "blacklist" in patch:
        if not isinstance(patch["blacklist"], list):
            raise ValueError("blacklist liste olmalı")
        cur["blacklist"] = [str(x).strip() for x in patch["blacklist"] if str(x).strip()]
    for k in ("max_text_kb", "max_image_mb", "max_img_dir_mb"):
        if k in patch:
            if not isinstance(patch[k], int) or isinstance(patch[k], bool) or patch[k] < 1:
                raise ValueError(f"{k} pozitif tam sayı olmalı")
            cur[k] = patch[k]
    _settings_path().parent.mkdir(parents=True, exist_ok=True)
    _settings_path().write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    return settings()


# ------------------------------------------------------------------ veritabanı
_SCHEMA = """
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, content TEXT NOT NULL DEFAULT '', hash TEXT NOT NULL,
  img TEXT NOT NULL DEFAULT '', ocr TEXT NOT NULL DEFAULT '', name TEXT NOT NULL DEFAULT '', tags TEXT NOT NULL DEFAULT '[]',
  folder TEXT NOT NULL DEFAULT '', pinned INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL, updated REAL NOT NULL,
  removed REAL, size INTEGER NOT NULL DEFAULT 0, app TEXT NOT NULL DEFAULT '');
CREATE UNIQUE INDEX IF NOT EXISTS items_hash ON items(kind, hash);
CREATE INDEX IF NOT EXISTS items_upd ON items(kind, updated);
"""


def _db() -> sqlite3.Connection:
    p = _db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p, timeout=10)
    c.row_factory = sqlite3.Row
    c.executescript(_SCHEMA)
    return c


def _norm_folder(f: str) -> str:
    return "/".join(p.strip() for p in str(f or "").replace("\\", "/").split("/") if p.strip())


def _norm_tags(tags) -> list[str]:
    out: list[str] = []
    for t in tags or []:
        t = str(t).strip().lstrip("#")[:40]
        if t and t.casefold() not in {x.casefold() for x in out}:
            out.append(t)
    return out[:20]


def _protected(r) -> bool:
    return bool(r["pinned"] or r["folder"] or json.loads(r["tags"] or "[]"))


def _item(r, full: bool = False) -> dict:
    text = r["content"]
    d = {"id": r["id"], "kind": r["kind"], "name": r["name"], "tags": json.loads(r["tags"] or "[]"), "folder": r["folder"],
         "pinned": bool(r["pinned"]), "created": r["created"], "updated": r["updated"], "size": r["size"], "app": r["app"],
         "removed": r["removed"], "protected": _protected(r)}
    d["text"] = text if full else text[:600]
    d["truncated"] = (not full) and len(text) > 600
    if r["kind"] == "image":
        d["has_ocr"] = bool(r["ocr"])
        if full:
            d["ocr"] = r["ocr"]
    return d


# ------------------------------------------------------------------ gizli içerik süzgeci
_PRIVKEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_JWT_RE = re.compile(r"\beyJ[\w-]{8,}\.eyJ[\w-]{8,}\.[\w-]{5,}")
_BEARER_RE = re.compile(r"\bbearer\s+[\w.~+/=-]{16,}", re.I)
_PASSWORD_WORD_RE = re.compile(r"(?:parola|şifre|sifre|password|passwd|pwd|secret|token|api[_ -]?key)\s*[:=]\s*\S{4,}", re.I)
_IBAN_ANY_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,4})?\b")


def _iban_ok(s: str) -> bool:
    s = re.sub(r"\s", "", s).upper()
    if not 15 <= len(s) <= 34:
        return False
    n = "".join(str(int(c, 36)) for c in s[4:] + s[:4])
    return int(n) % 97 == 1


def _password_like(t: str) -> bool:
    """Tek parça, boşluksuz, karışık sınıflı kısa dize: büyük olasılıkla parola (URL ve yol değil)."""
    if not 8 <= len(t) <= 64 or re.search(r"\s", t) or "://" in t or t.count("/") > 1 or "\\" in t:
        return False
    classes = sum(bool(re.search(p, t)) for p in (r"[a-zçğıöşü]", r"[A-ZÇĞİÖŞÜ]", r"\d", r"[^\w\s]"))
    return classes >= 4 or (classes >= 3 and len(t) >= 12 and not re.search(r"[aeıioöuü]{2}", t, re.I) and bool(re.search(r"\d", t)))


def looks_secret(text: str) -> bool:
    if redact(text) != text:
        return True
    if KEY_RE.search(text) or ASSIGN_RE.search(text):
        return True
    if _PRIVKEY_RE.search(text) or _JWT_RE.search(text) or _BEARER_RE.search(text) or _PASSWORD_WORD_RE.search(text):
        return True
    if any(_iban_ok(m.group()) for m in _IBAN_ANY_RE.finditer(text)):
        return True
    t = text.strip()
    return _password_like(t)


def classify(text: str) -> str:
    """Yalnız tek başına URL bağlantıdır; paragraf içindeki URL metindir."""
    return "link" if URL_RE.match(text.strip()) else "text"


# ------------------------------------------------------------------ pano arabirimi
@dataclass
class Snapshot:
    text: str = ""
    image_png: bytes = b""
    excluded: bool = False          # parola yöneticisi "gizli" işaretledi
    too_big: bool = False
    app: str = ""
    seq: int | None = None          # panonun değişim sayacı (yoksa None: içerikle karşılaştırılır)


class Backend:
    name = "none"
    available = False
    note = ""

    def snapshot(self, max_text: int, max_image: int) -> Snapshot | None:
        raise NotImplementedError

    def write_text(self, text: str) -> None:
        raise NotImplementedError

    def write_image(self, png: bytes) -> None:
        raise NotImplementedError


def _dib_to_bmp(dib: bytes) -> bytes:
    import struct
    size, = struct.unpack_from("<I", dib, 0)
    bitcount, comp, clr = struct.unpack_from("<HII", dib, 14)
    colors = clr or ((1 << bitcount) if bitcount <= 8 else 0)
    off = 14 + size + colors * 4 + (12 if comp == 3 and size == 40 else 0)
    return b"BM" + struct.pack("<IHHI", 14 + len(dib), 0, 0, off) + dib


def _to_png(data: bytes, dib: bool = False) -> bytes:
    from PIL import Image
    im = Image.open(io.BytesIO(_dib_to_bmp(data) if dib else data))
    im.load()
    if im.mode not in ("RGB", "RGBA", "L"):
        im = im.convert("RGBA")
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


class WindowsBackend(Backend):
    name = "windows"
    available = True
    CF_UNICODETEXT, CF_DIB = 13, 8

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes as wt
        self.ct, self.wt = ctypes, wt
        u, k = ctypes.WinDLL("user32", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
        H, V = ctypes.c_void_p, ctypes.c_void_p
        u.OpenClipboard.argtypes, u.OpenClipboard.restype = [H], wt.BOOL
        u.CloseClipboard.restype = wt.BOOL
        u.EmptyClipboard.restype = wt.BOOL
        u.GetClipboardData.argtypes, u.GetClipboardData.restype = [wt.UINT], H
        u.SetClipboardData.argtypes, u.SetClipboardData.restype = [wt.UINT, H], H
        u.IsClipboardFormatAvailable.argtypes, u.IsClipboardFormatAvailable.restype = [wt.UINT], wt.BOOL
        u.RegisterClipboardFormatW.argtypes, u.RegisterClipboardFormatW.restype = [wt.LPCWSTR], wt.UINT
        u.GetClipboardSequenceNumber.restype = wt.DWORD
        u.GetClipboardOwner.restype = H
        u.GetWindowThreadProcessId.argtypes, u.GetWindowThreadProcessId.restype = [H, ctypes.POINTER(wt.DWORD)], wt.DWORD
        k.GlobalLock.argtypes, k.GlobalLock.restype = [H], V
        k.GlobalUnlock.argtypes, k.GlobalUnlock.restype = [H], wt.BOOL
        k.GlobalSize.argtypes, k.GlobalSize.restype = [H], ctypes.c_size_t
        k.GlobalAlloc.argtypes, k.GlobalAlloc.restype = [wt.UINT, ctypes.c_size_t], H
        k.OpenProcess.argtypes, k.OpenProcess.restype = [wt.DWORD, wt.BOOL, wt.DWORD], H
        k.CloseHandle.argtypes = [H]
        k.QueryFullProcessImageNameW.argtypes = [H, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
        k.QueryFullProcessImageNameW.restype = wt.BOOL
        self.u, self.k = u, k
        self.fmt = {n: u.RegisterClipboardFormatW(n) for n in
                    ("ExcludeClipboardContentFromMonitorProcessing", "CanIncludeInClipboardHistory", "CanUploadToCloudClipboard", "PNG")}

    def _open(self) -> bool:
        for _ in range(8):
            if self.u.OpenClipboard(None):
                return True
            time.sleep(0.01)
        return False

    def _bytes(self, fmt: int, limit: int) -> tuple[bytes, bool]:
        h = self.u.GetClipboardData(fmt)
        if not h:
            return b"", False
        n = self.k.GlobalSize(h)
        if n > limit:
            return b"", True
        p = self.k.GlobalLock(h)
        if not p:
            return b"", False
        try:
            return self.ct.string_at(p, n), False
        finally:
            self.k.GlobalUnlock(h)

    def _owner(self) -> str:
        try:
            hwnd = self.u.GetClipboardOwner()
            if not hwnd:
                return ""
            pid = self.wt.DWORD(0)
            self.u.GetWindowThreadProcessId(hwnd, self.ct.byref(pid))
            h = self.k.OpenProcess(0x1000, False, pid.value)      # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return ""
            try:
                buf = self.ct.create_unicode_buffer(520)
                n = self.wt.DWORD(520)
                return Path(buf.value).name if self.k.QueryFullProcessImageNameW(h, 0, buf, self.ct.byref(n)) else ""
            finally:
                self.k.CloseHandle(h)
        except Exception:                                          # noqa: BLE001 — kaynak uygulama bilgisi isteğe bağlı
            return ""

    def snapshot(self, max_text: int, max_image: int) -> Snapshot | None:
        seq = int(self.u.GetClipboardSequenceNumber())
        if not self._open():
            return None
        try:
            s = Snapshot(seq=seq, app=self._owner())
            if self.u.IsClipboardFormatAvailable(self.fmt["ExcludeClipboardContentFromMonitorProcessing"]):
                s.excluded = True
                return s
            for name in ("CanIncludeInClipboardHistory", "CanUploadToCloudClipboard"):
                if self.u.IsClipboardFormatAvailable(self.fmt[name]):
                    b, _ = self._bytes(self.fmt[name], 16)
                    if len(b) >= 4 and int.from_bytes(b[:4], "little") == 0:
                        s.excluded = True
                        return s
            if self.u.IsClipboardFormatAvailable(self.CF_UNICODETEXT):
                b, big = self._bytes(self.CF_UNICODETEXT, max_text * 4)
                s.too_big = big
                s.text = b.decode("utf-16-le", "ignore").split("\0", 1)[0]
            elif self.u.IsClipboardFormatAvailable(self.fmt["PNG"]):
                b, big = self._bytes(self.fmt["PNG"], max_image)
                s.too_big, s.image_png = big, b
            elif self.u.IsClipboardFormatAvailable(self.CF_DIB):
                b, big = self._bytes(self.CF_DIB, max_image * 6)
                s.too_big = big
                if b:
                    try:
                        s.image_png = _to_png(b, dib=True)
                    except Exception:                              # noqa: BLE001 — bozuk DIB atlanır
                        s.image_png = b""
            return s
        finally:
            self.u.CloseClipboard()

    def _set(self, fmt: int, data: bytes) -> None:
        h = self.k.GlobalAlloc(0x0042, len(data))                   # GMEM_MOVEABLE | GMEM_ZEROINIT
        p = self.k.GlobalLock(h)
        self.ct.memmove(p, data, len(data))
        self.k.GlobalUnlock(h)
        self.u.SetClipboardData(fmt, h)

    def write_text(self, text: str) -> None:
        if not self._open():
            raise RuntimeError("pano açılamadı (başka uygulama kullanıyor)")
        try:
            self.u.EmptyClipboard()
            self._set(self.CF_UNICODETEXT, text.encode("utf-16-le") + b"\0\0")
        finally:
            self.u.CloseClipboard()

    def write_image(self, png: bytes) -> None:
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "BMP")
        if not self._open():
            raise RuntimeError("pano açılamadı (başka uygulama kullanıyor)")
        try:
            self.u.EmptyClipboard()
            self._set(self.CF_DIB, buf.getvalue()[14:])
            self._set(self.fmt["PNG"], png)
        finally:
            self.u.CloseClipboard()


class MacBackend(Backend):
    name = "mac"

    def __init__(self) -> None:
        self.available = bool(shutil.which("pbpaste") and shutil.which("pbcopy"))
        self.note = "" if self.available else "pbpaste/pbcopy bulunamadı; pano izleyici çalışmaz."
        self._osa = shutil.which("osascript")

    def _run(self, cmd: list[str], inp: bytes | None = None, timeout: int = 5) -> bytes:
        return subprocess.run(cmd, input=inp, capture_output=True, timeout=timeout, check=False).stdout

    def snapshot(self, max_text: int, max_image: int) -> Snapshot | None:
        if not self.available:
            return None
        s = Snapshot()
        info = self._run([self._osa, "-e", "clipboard info"]).decode("utf-8", "ignore") if self._osa else ""
        if "concealed" in info.lower() or "nspasteboardtypeconcealed" in info.lower():
            s.excluded = True
            return s
        txt = self._run(["pbpaste"])
        if len(txt) > max_text * 4:
            s.too_big = True
        elif txt:
            s.text = txt.decode("utf-8", "ignore")
        elif self._osa and ("PNGf" in info or "TIFF" in info):
            out = self._run([self._osa, "-e", "the clipboard as «class PNGf»"], timeout=10).decode("ascii", "ignore")
            m = re.search(r"«data PNGf([0-9A-Fa-f]+)»", out)
            if m:
                data = bytes.fromhex(m.group(1))
                if len(data) > max_image:
                    s.too_big = True
                else:
                    s.image_png = data
        return s

    def write_text(self, text: str) -> None:
        self._run(["pbcopy"], text.encode("utf-8"))

    def write_image(self, png: bytes) -> None:
        if not self._osa:
            raise RuntimeError("osascript bulunamadı")
        tmp = config.DATA / "pano" / "_copy.png"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(png)
        self._run([self._osa, "-e", f'set the clipboard to (read (POSIX file "{tmp}") as «class PNGf»)'], timeout=10)
        tmp.unlink(missing_ok=True)


class NoBackend(Backend):
    def __init__(self, note: str) -> None:
        self.note = note

    def snapshot(self, max_text, max_image):
        return None

    def write_text(self, text):
        raise RuntimeError(self.note)

    write_image = write_text


_BACKEND: Backend | None = None


def set_backend(b: Backend | None) -> None:
    """Testlerde sahte pano takmak için (gerçek panoya hiç dokunulmaz)."""
    global _BACKEND
    _BACKEND = b


def backend() -> Backend:
    global _BACKEND
    if _BACKEND is None:
        sysname = platform.system()
        try:
            if sysname == "Windows":
                _BACKEND = WindowsBackend()
            elif sysname == "Darwin":
                _BACKEND = MacBackend()
            else:
                _BACKEND = NoBackend(f"{sysname} için pano izleyici yok (Windows ve macOS desteklenir).")
        except Exception as e:                                     # noqa: BLE001
            _BACKEND = NoBackend(f"Pano arabirimi açılamadı: {e}")
    return _BACKEND


# ------------------------------------------------------------------ OCR
def _ocr(path: Path) -> str:
    """tesseract PATH'te ve pytesseract kuruluysa görseldeki metin; yoksa sessizce boş."""
    if not shutil.which("tesseract"):
        return ""
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(path), timeout=20).strip()[:20000]
    except Exception:                                              # noqa: BLE001 — OCR isteğe bağlı
        return ""


OCR = _ocr


# ------------------------------------------------------------------ toplama
def _blocked_app(app: str, cfg: dict) -> bool:
    a = app.casefold()
    return bool(a) and any(b.casefold() in a for b in cfg["blacklist"])


def _upsert(kind: str, h: str, now: float, **fields) -> tuple[str, int]:
    """Aynı içerik varsa yeni kayıt değil mevcut kaydın zamanı yenilenir (çöpteyse geri gelir)."""
    with _db() as c:
        row = c.execute("SELECT id FROM items WHERE kind=? AND hash=?", (kind, h)).fetchone()
        if row:
            c.execute("UPDATE items SET updated=?, removed=NULL WHERE id=?", (now, row["id"]))
            return "refreshed", row["id"]
        cur = c.execute("INSERT INTO items(kind,content,hash,img,ocr,created,updated,size,app) VALUES(?,?,?,?,?,?,?,?,?)",
                        (kind, fields.get("content", ""), h, fields.get("img", ""), fields.get("ocr", ""), now, now,
                         fields.get("size", 0), fields.get("app", "")))
        return "saved", cur.lastrowid


def capture_text(text: str, app: str = "", now: float | None = None) -> str:
    cfg = settings()
    if not active(cfg):
        return "off"
    if not cfg["collect_text"]:
        return "skipped:text-off"
    if _blocked_app(app, cfg):
        return "skipped:app"
    t = text.strip()
    if not t:
        return "skipped:empty"
    if len(t.encode("utf-8")) > cfg["max_text_kb"] * 1024:
        return "skipped:too-big"
    if looks_secret(t):
        return "skipped:secret"
    kind = classify(t)
    res, _ = _upsert(kind, hashlib.sha256(t.encode("utf-8")).hexdigest(), now or time.time(), content=t, size=len(t.encode("utf-8")), app=app)
    purge(now)
    return res


def _img_total() -> int:
    d = _img_dir()
    return sum(f.stat().st_size for f in d.glob("*.png")) if d.exists() else 0


def capture_image(png: bytes, app: str = "", now: float | None = None) -> str:
    cfg = settings()
    if not active(cfg):
        return "off"
    if not cfg["collect_images"]:
        return "skipped:images-off"
    if _blocked_app(app, cfg):
        return "skipped:app"
    if not png:
        return "skipped:empty"
    if len(png) > cfg["max_image_mb"] * 1024 * 1024:
        return "skipped:too-big"
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png))
        im.load()
        h = hashlib.sha256(im.convert("RGBA").tobytes() + str(im.size).encode()).hexdigest()
    except Exception:                                              # noqa: BLE001 — görüntü çözülemiyorsa kaydetme
        return "skipped:bad-image"
    now = now or time.time()
    with _db() as c:
        row = c.execute("SELECT id FROM items WHERE kind='image' AND hash=?", (h,)).fetchone()
        if row:
            c.execute("UPDATE items SET updated=?, removed=NULL WHERE id=?", (now, row["id"]))
            return "refreshed"
    purge(now)
    if _img_total() + len(png) > cfg["max_img_dir_mb"] * 1024 * 1024:
        return "skipped:dir-full"
    d = _img_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{h[:32]}.png"
    path.write_bytes(png)
    ocr = ""
    try:
        ocr = OCR(path) or ""
    except Exception:                                              # noqa: BLE001
        ocr = ""
    if ocr and looks_secret(ocr):
        ocr = ""                                                   # görselde sır görünüyorsa metni dizine alma
    _upsert("image", h, now, content="", img=path.name, ocr=ocr, size=len(png), app=app)
    return "saved"


class Watcher:
    def __init__(self, be: Backend | None = None) -> None:
        self.be = be
        self.last_seq: int | None = None
        self.last_sig = ""
        self.last_result = ""
        self.error = ""
        self._stop = threading.Event()
        self._th: threading.Thread | None = None
        self.polls = 0

    def poll_once(self) -> str:
        cfg = settings()
        if not active(cfg):
            return "off"
        be = self.be or backend()
        snap = be.snapshot(cfg["max_text_kb"] * 1024, cfg["max_image_mb"] * 1024 * 1024)
        self.polls += 1
        if self.polls % 300 == 0:
            purge()
        if snap is None:
            return "empty"
        sig = ""
        if snap.seq is not None:
            if snap.seq == self.last_seq:
                return "same"
            self.last_seq = snap.seq
        else:
            sig = hashlib.sha256((snap.text or "").encode() + snap.image_png).hexdigest()
            if sig == self.last_sig:
                return "same"
            self.last_sig = sig
        if snap.excluded:
            res = "skipped:excluded"
        elif snap.too_big:
            res = "skipped:too-big"
        elif snap.text.strip() and cfg["collect_text"]:
            res = capture_text(snap.text, snap.app)
        elif snap.image_png and not snap.text.strip():
            res = capture_image(snap.image_png, snap.app)
        else:
            res = "skipped:empty"
        self.last_result = res
        return res

    def _loop(self) -> None:
        while not self._stop.wait(POLL_SECONDS):
            try:
                self.poll_once()
                self.error = ""
            except Exception as e:                                 # noqa: BLE001 — izleyici düşmesin
                self.error = f"{type(e).__name__}: {str(e)[:120]}"

    def start(self) -> bool:
        if self.running or not backend().available:
            return self.running
        self._stop.clear()
        self._th = threading.Thread(target=self._loop, name="pano-watcher", daemon=True)
        self._th.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._th:
            self._th.join(timeout=3)
        self._th = None

    @property
    def running(self) -> bool:
        return bool(self._th and self._th.is_alive())


_WATCHER = Watcher()


def watcher() -> Watcher:
    return _WATCHER


def ensure_running() -> bool:
    """Ayar açıksa izleyiciyi bir kez başlatır, kapalıysa durdurur."""
    if active():
        return _WATCHER.start()
    _WATCHER.stop()
    return False


# ------------------------------------------------------------------ saklama süresi, çöp
def _delete_files(names: list[str]) -> None:
    for n in names:
        if n:
            (_img_dir() / n).unlink(missing_ok=True)


def purge(now: float | None = None) -> dict:
    """Tutma süresi dolan korumasız kayıtları çöpe atar; çöpte 30 günü geçenleri kalıcı siler. Sabit/klasörlü/etiketli kayda dokunmaz."""
    now = now or time.time()
    cfg = settings()
    moved = 0
    with _db() as c:
        for kind in KINDS:
            cutoff = now - cfg["retention"][kind] * 86400
            for r in c.execute("SELECT * FROM items WHERE kind=? AND removed IS NULL AND updated<?", (kind, cutoff)).fetchall():
                if not _protected(r):
                    c.execute("UPDATE items SET removed=? WHERE id=?", (now, r["id"]))
                    moved += 1
        old = c.execute("SELECT id,img FROM items WHERE removed IS NOT NULL AND removed<?", (now - TRASH_DAYS * 86400,)).fetchall()
        for r in old:
            c.execute("DELETE FROM items WHERE id=?", (r["id"],))
    _delete_files([r["img"] for r in old])
    return {"trashed": moved, "deleted": len(old)}


# ------------------------------------------------------------------ sorgu ve düzenleme
def _row(c, id_: int):
    r = c.execute("SELECT * FROM items WHERE id=?", (int(id_),)).fetchone()
    if not r:
        raise KeyError(f"kayıt yok: {id_}")
    return r


def get(id_: int) -> dict:
    with _db() as c:
        return _item(_row(c, id_), full=True)


def _folder_match(f: str, want: str) -> bool:
    return f == want or f.startswith(want + "/")


def search(q: str = "", kinds=None, pinned: bool | None = None, tag: str = "", folder: str = "",
           trash: bool = False, limit: int = 200, offset: int = 0) -> dict:
    kinds = [k for k in (kinds or KINDS) if k in KINDS]
    folder, tag, needle = _norm_folder(folder), tag.strip().lstrip("#").casefold(), q.strip().casefold()
    sql = "SELECT * FROM items WHERE removed IS " + ("NOT NULL" if trash else "NULL")
    sql += f" AND kind IN ({','.join('?' * len(kinds))})" if kinds else " AND 0"
    if pinned is not None:
        sql += " AND pinned=" + ("1" if pinned else "0")
    sql += " ORDER BY pinned DESC, updated DESC" if not trash else " ORDER BY removed DESC"
    with _db() as c:
        rows = c.execute(sql, kinds).fetchall()
    out = []
    for r in rows:
        if folder and not _folder_match(r["folder"], folder):
            continue
        tags = json.loads(r["tags"] or "[]")
        if tag and tag not in {t.casefold() for t in tags}:
            continue
        if needle and needle not in " ".join([r["content"], r["name"], " ".join(tags), r["ocr"]]).casefold():
            continue
        out.append(r)
    return {"total": len(out), "items": [_item(r) for r in out[offset:offset + limit]]}


def list_items(kind: str = "", page: int = 1, per: int = 30, pinned: bool | None = None) -> dict:
    per = max(1, min(200, per))
    page = max(1, page)
    res = search(kinds=[kind] if kind else None, pinned=pinned, limit=per, offset=(page - 1) * per)
    res.update(page=page, per=per, pages=max(1, -(-res["total"] // per)))
    return res


def folders() -> list[dict]:
    with _db() as c:
        rows = c.execute("SELECT folder, COUNT(*) n FROM items WHERE removed IS NULL AND folder!='' GROUP BY folder").fetchall()
    seen: dict[str, int] = {}
    for r in rows:
        parts = r["folder"].split("/")
        for i in range(1, len(parts) + 1):
            p = "/".join(parts[:i])
            seen[p] = seen.get(p, 0) + (r["n"] if i == len(parts) else 0)
    return [{"path": p, "count": n} for p, n in sorted(seen.items())]


def set_pinned(id_: int, value: bool | None = None) -> dict:
    with _db() as c:
        r = _row(c, id_)
        v = (not r["pinned"]) if value is None else bool(value)
        c.execute("UPDATE items SET pinned=? WHERE id=?", (int(v), r["id"]))
        return _item(_row(c, id_))


def set_meta(id_: int, tags=None, name: str | None = None, folder: str | None = None) -> dict:
    with _db() as c:
        r = _row(c, id_)
        if tags is not None:
            c.execute("UPDATE items SET tags=? WHERE id=?", (json.dumps(_norm_tags(tags), ensure_ascii=False), r["id"]))
        if name is not None:
            c.execute("UPDATE items SET name=? WHERE id=?", (str(name).strip()[:120], r["id"]))
        if folder is not None:
            c.execute("UPDATE items SET folder=? WHERE id=?", (_norm_folder(folder)[:200], r["id"]))
        return _item(_row(c, id_))


def remove(id_: int, hard: bool = False) -> dict:
    with _db() as c:
        r = _row(c, id_)
        if hard:
            c.execute("DELETE FROM items WHERE id=?", (r["id"],))
            img = r["img"]
        else:
            c.execute("UPDATE items SET removed=? WHERE id=?", (time.time(), r["id"]))
            img = ""
    _delete_files([img])
    return {"id": int(id_), "hard": hard}


def restore(id_: int) -> dict:
    with _db() as c:
        r = _row(c, id_)
        c.execute("UPDATE items SET removed=NULL WHERE id=?", (r["id"],))
        return _item(_row(c, id_))


def undo_remove() -> dict | None:
    """Son kaldırılan kaydı geri getirir (yoksa None)."""
    with _db() as c:
        r = c.execute("SELECT id FROM items WHERE removed IS NOT NULL ORDER BY removed DESC, id DESC LIMIT 1").fetchone()
    return restore(r["id"]) if r else None


def clear(include_protected: bool = False) -> int:
    """Korumasız (sabit/klasörsüz/etiketsiz) bütün kayıtları çöpe atar (geri alınabilir)."""
    n, now = 0, time.time()
    with _db() as c:
        for r in c.execute("SELECT * FROM items WHERE removed IS NULL").fetchall():
            if include_protected or not _protected(r):
                c.execute("UPDATE items SET removed=? WHERE id=?", (now, r["id"]))
                n += 1
    return n


def empty_trash() -> int:
    with _db() as c:
        rows = c.execute("SELECT id,img FROM items WHERE removed IS NOT NULL").fetchall()
        c.execute("DELETE FROM items WHERE removed IS NOT NULL")
    _delete_files([r["img"] for r in rows])
    return len(rows)


def image_bytes(id_: int, thumb: bool = False) -> bytes:
    with _db() as c:
        r = _row(c, id_)
    if r["kind"] != "image" or not r["img"] or Path(r["img"]).name != r["img"]:
        raise KeyError("görsel değil")
    data = (_img_dir() / r["img"]).read_bytes()
    if thumb:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        im.thumbnail((360, 360))
        buf = io.BytesIO()
        im.save(buf, "PNG")
        return buf.getvalue()
    return data


def copy_back(id_: int) -> dict:
    """Kaydı panoya geri yazar (izleyici açıksa aynı içerik yeni kayıt olmaz, zamanı yenilenir)."""
    with _db() as c:
        r = _row(c, id_)
    be = backend()
    if r["kind"] == "image":
        be.write_image(image_bytes(r["id"]))
    else:
        be.write_text(r["content"])
    with _db() as c:
        c.execute("UPDATE items SET updated=? WHERE id=?", (time.time(), r["id"]))
    return {"ok": True, "id": r["id"], "kind": r["kind"]}


def status() -> dict:
    cfg = settings()
    be = backend()
    with _db() as c:
        counts = {k: c.execute("SELECT COUNT(*) FROM items WHERE kind=? AND removed IS NULL", (k,)).fetchone()[0] for k in KINDS}
        trash = c.execute("SELECT COUNT(*) FROM items WHERE removed IS NOT NULL").fetchone()[0]
    w = _WATCHER
    return {"module": module_on(), "enabled": active(cfg), "collect_text": cfg["collect_text"], "collect_images": cfg["collect_images"],
            "running": w.running, "backend": be.name, "backend_ok": be.available, "note": be.note, "error": w.error,
            "last": w.last_result, "counts": counts, "trash": trash, "image_bytes": _img_total(),
            "ocr": bool(shutil.which("tesseract")), "retention": cfg["retention"]}


# ------------------------------------------------------------------ CLI
def _fmt(it: dict) -> str:
    mark = "*" if it["pinned"] else " "
    body = it["name"] or (it["text"].replace("\n", " ")[:80] if it["kind"] != "image" else f"[görsel {it['size'] // 1024} KB]")
    extra = (" #" + " #".join(it["tags"]) if it["tags"] else "") + (f" [{it['folder']}]" if it["folder"] else "")
    return f"{it['id']:>5}{mark}{it['kind']:<6} {body}{extra}"


def cli(a) -> int:
    act, arg = a.action, (a.arg or "")
    if act == "status":
        s = status()
        print(f"Pano: {'AÇIK' if s['enabled'] else 'kapalı'} · metin {'açık' if s['collect_text'] else 'kapalı'} · "
              f"görsel {'açık' if s['collect_images'] else 'kapalı'} · izleyici {'çalışıyor' if s['running'] else 'durgun'} ({s['backend']})")
        print("Kayıt: " + ", ".join(f"{k} {n}" for k, n in s["counts"].items()) + f" · çöp {s['trash']}")
        if s["note"]:
            print(s["note"])
        return 0
    if act in ("on", "off"):
        patch: dict = {"enabled": act == "on"}
        if act == "on":
            patch["collect_images"] = bool(a.images)
        set_settings(patch)
        if act == "on" and not module_on():
            print("Not: Kopya geçmişi modülü kapalı, toplama başlamaz. Aç: sb features --on pano")
        print("Pano açıldı." + (" Görsel toplama açık." if a.images and act == "on" else "") +
              " Yerel kalır; sır gibi görünen metin saklanmaz. İzleyici için asistan açık olmalı ya da `sb pano watch` çalıştır."
              if act == "on" else "Pano kapatıldı (kayıtlar silinmedi).")
        return 0
    if act == "watch":
        if not module_on():
            print("Kopya geçmişi modülü kapalı: `sb features --on pano`.")
            return 1
        if not settings()["enabled"]:
            print("Pano kapalı; önce `sb pano on`.")
            return 1
        w = Watcher()
        if not backend().available:
            print(backend().note or "Bu sistemde pano izleyici yok.")
            return 1
        print("Pano izleniyor (Ctrl+C ile dur)...")
        try:
            while True:
                w.poll_once()
                time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            return 0
    if act == "list":
        res = list_items(a.kind or "", 1, 50)
    elif act == "search":
        res = search(arg, [a.kind] if a.kind else None)
    elif act in ("pin", "forget"):
        if not arg.isdigit():
            print("Kayıt numarası ver (sb pano list).")
            return 1
        if act == "pin":
            print("Sabitlendi." if set_pinned(int(arg))["pinned"] else "Sabitlik kaldırıldı.")
        else:
            if a.hard and not a.yes:
                print("Kalıcı silme geri alınamaz: --hard ile birlikte --yes ver.")
                return 1
            remove(int(arg), hard=a.hard)
            print("Kalıcı silindi." if a.hard else "Çöp kutusuna taşındı (geri alınabilir).")
        return 0
    elif act == "clear":
        if a.hard and not a.yes:
            print("Kalıcı silme geri alınamaz: --hard ile birlikte --yes ver.")
            return 1
        print(f"{clear()} kayıt çöp kutusuna taşındı (sabit/klasörlü/etiketli olanlar kalır).")
        if a.hard:
            print(f"{empty_trash()} kayıt kalıcı silindi.")
        return 0
    else:
        return 1
    for it in res["items"]:
        print(_fmt(it))
    print(f"-- {res['total']} kayıt")
    return 0
