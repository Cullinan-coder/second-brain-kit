"""Kurulum motoru: hazır seçimler, donanım, alanlar, adımlar, bağlantı testleri, profil, sürdürme, güncelleme, sağlık, kaldırma.

Yalnız stdlib (+ varsa `keyring`, `yaml`, `psutil`) kullanır; `sb` paketi henüz kurulu olmasa da çalışır.
Panelsiz: python setup/engine.py --preset ogrenci --profile profil.json --yes   |   --verify <zip> <sha256>
Kurallar: sırlar yalnız keyring'e gider (dosyaya/günlüğe/profile asla; günlükte ***); kalıcı silme yok; kasa notlarına dokunulmaz.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

WIN, MAC = sys.platform == "win32", sys.platform == "darwin"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KEYRING_SERVICE = "second-brain"
GB = 1024 ** 3
TASK_NAMES = ("SecondBrain-Daily", "SecondBrain-Weekly", "SecondBrain-Chat")


def data_dir() -> Path:
    return Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain")


def kit_dir() -> Path | None:
    """Kit kökü (içinde system/ ve vault/ var) ya da None (kasadaki _system/setup'tan çalışıyorsak)."""
    return ROOT if (ROOT / "system" / "sb").exists() else None


def code_dir() -> Path | None:
    """sb paketinin bulunduğu klasör (kitte system/, kasada _system/)."""
    for p in (ROOT / "system", ROOT):
        if (p / "sb").is_dir():
            return p
    return None


# ------------------------------------------------------------------ modüller ve hazır seçimler
CATEGORIES = {
    "Mail ve takvim": ["gmail", "imap", "calendar", "dates", "contacts", "drive", "derived", "digest"],
    "Telefon ve mesaj": ["sms", "phone", "telegram", "whatsapp"],
    "Okul ve proje": ["courses", "projects", "github", "sessions", "cards", "local_files", "linkedin", "browser"],
    "Asistan ve hafıza": ["assistant", "memory_ui", "capture", "inbox", "brain", "claude_hooks", "flush", "night", "automation"],
    "Bilgisayar ve ses": ["computer", "media", "vision", "voice", "wake_word", "screen_watch", "image_gen"],
}


def modules_meta() -> dict[str, dict]:
    """`sb/features.py` MODULES sözlüğünü import etmeden (ast ile) okur: {anahtar: {name, desc, requires, default, category}}."""
    out: dict[str, dict] = {}
    cd = code_dir()
    src = cd / "sb" / "features.py" if cd else None
    if src and src.exists():
        try:
            for node in ast.parse(src.read_text(encoding="utf-8")).body:
                t = node.target if isinstance(node, ast.AnnAssign) else (node.targets[0] if isinstance(node, ast.Assign) else None)
                if isinstance(t, ast.Name) and t.id == "MODULES":
                    for k, (ad, desc, req, dflt) in ast.literal_eval(node.value).items():
                        out[k] = {"name": ad, "desc": desc, "requires": req, "default": dflt}
        except Exception:
            out = {}
    cat = {k: c for c, ks in CATEGORIES.items() for k in ks}
    for k, m in out.items():
        m["category"] = cat.get(k, "Diğer")
    return out


_ALL = [k for ks in CATEGORIES.values() for k in ks]
_OFF_BY_DEFAULT = {"wake_word", "screen_watch", "image_gen"}


def _preset(on: set[str] | None, label: str, desc: str, local_model: bool = True) -> dict:
    keys = set(_ALL) - _OFF_BY_DEFAULT if on is None else on
    return {"label": label, "desc": desc, "local_model": local_model, "modules": {k: k in keys for k in _ALL}}


PRESETS: dict[str, dict] = {
    "tam": _preset(None, "Tam", "Varsayılan her şey açık (ek özellikler hariç)."),
    "bulut": _preset(None, "Bulut", "Yerel model yok; asistan için bulut API anahtarı kullanılır.", local_model=False),
    "minimal": _preset({"assistant", "capture", "inbox", "claude_hooks"}, "Minimal", "Yalnız kasa + Obsidian + asistan."),
    "ogrenci": _preset({"gmail", "calendar", "dates", "courses", "cards", "local_files", "assistant", "memory_ui", "capture", "inbox",
                        "brain", "claude_hooks", "flush", "sessions"}, "Öğrenci", "Okul, ders, kartlar."),
    "ajans": _preset({"gmail", "imap", "calendar", "dates", "contacts", "drive", "derived", "digest", "projects", "github", "sessions",
                      "assistant", "memory_ui", "capture", "inbox", "brain", "claude_hooks", "flush", "automation", "whatsapp"},
                     "Ajans", "CRM, mail, projeler."),
}


def preset_modules(name: str) -> dict[str, bool]:
    if name not in PRESETS:
        raise ValueError(f"Bilinmeyen hazır seçim: {name}")
    return dict(PRESETS[name]["modules"])


# ------------------------------------------------------------------ alanlar (bilgi girişi)
FIELDS: list[dict] = [
    {"key": "name", "label": "Asistan sana nasıl hitap etsin (ad)", "kind": "text", "modules": [], "required": True},
    {"key": "full_name", "label": "Adın soyadın", "kind": "text", "modules": []},
    {"key": "bio", "label": "Kendini bir cümleyle anlat", "kind": "text", "modules": []},
    {"key": "timezone", "label": "Saat dilimi", "kind": "text", "modules": [], "default": "Europe/Istanbul"},
    {"key": "vault", "label": "Kasa (Obsidian vault) klasörü", "kind": "path", "modules": [], "required": True},
    {"key": "workspace", "label": "Kod projeleri klasörü", "kind": "path", "modules": ["projects", "github", "sessions"], "default": "~/Projects"},
    {"key": "github_user", "label": "GitHub kullanıcı adı", "kind": "text", "modules": ["projects", "github"]},
    {"key": "gmail", "label": "Ana Gmail adresi", "kind": "email", "modules": ["gmail", "calendar", "contacts", "drive"]},
    {"key": "client_secret", "label": "Google client_secret.json yolu", "kind": "path", "modules": ["gmail", "calendar", "contacts", "drive"]},
    {"key": "imap_alias", "label": "IMAP takma adı (ör. is)", "kind": "text", "modules": ["imap"], "default": "is"},
    {"key": "imap_email", "label": "IMAP e-posta", "kind": "email", "modules": ["imap"]},
    {"key": "imap_host", "label": "IMAP sunucusu", "kind": "text", "modules": ["imap"]},
    {"key": "imap_password", "label": "IMAP şifresi", "kind": "secret", "modules": ["imap"], "keyring": "imap-{imap_alias}"},
    {"key": "openai_key", "label": "OpenAI API anahtarı", "kind": "secret", "modules": ["image_gen"], "keyring": "api-openai", "cloud": True},
    {"key": "anthropic_key", "label": "Anthropic API anahtarı", "kind": "secret", "modules": [], "keyring": "api-anthropic", "cloud_only": True},
    {"key": "gemini_key", "label": "Gemini API anahtarı", "kind": "secret", "modules": ["image_gen"], "keyring": "api-gemini", "cloud": True},
    {"key": "telegram_token", "label": "Telegram bot belirteci", "kind": "secret", "modules": ["telegram"], "keyring": "telegram-bot"},
]
SECRET_KEYS = {f["key"] for f in FIELDS if f["kind"] == "secret"}


def fields_for(modules: dict[str, bool], local_model: bool = True) -> list[dict]:
    """Seçime göre gereken alanlar. Yerel model yoksa (bulut) bulut API anahtarları da istenir."""
    out = []
    for f in FIELDS:
        need = f["modules"]
        show = not need or any(modules.get(m) for m in need)
        if f.get("cloud") and not local_model:
            show = True
        if f.get("cloud_only"):
            show = not local_model
        if show:
            d = {k: v for k, v in f.items() if k not in ("modules", "keyring", "cloud", "cloud_only")}
            d["secret"] = f["kind"] == "secret"
            out.append(d)
    return out


# ------------------------------------------------------------------ yardımcılar: günlük, sır, süreç
_PATTERNS = [re.compile(r"sk-[A-Za-z0-9_\-]{8,}"), re.compile(r"AIza[0-9A-Za-z_\-]{20,}"), re.compile(r"\b\d{6,}:[A-Za-z0-9_\-]{30,}\b"),
             re.compile(r"(?i)\b(password|şifre|passwd|token|api[_-]?key)(\s*[=:]\s*)\S+")]


def redact(text: str, secrets: list[str] | None = None) -> str:
    for s in sorted({s for s in (secrets or []) if s}, key=len, reverse=True):
        text = text.replace(s, "***")
    for p in _PATTERNS:
        text = p.sub(lambda m: (m.group(1) + m.group(2) + "***") if p.groups >= 2 else "***", text)
    return text


def _keyring():
    try:
        import keyring
        return keyring
    except Exception:
        return None


def _run_capture(cmd: list[str], timeout: int = 15, cwd: Path | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 127, str(e)


def _run_stream(cmd: list[str], log, cwd: Path | None = None) -> int:
    """Komutu çalıştırır, çıktıyı satır satır günlüğe yazar (günlük sırları maskeler)."""
    log("$ " + " ".join(cmd))
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    except Exception as e:
        log(f"  başlatılamadı: {e}")
        return 127
    for line in p.stdout or []:
        if line.strip():
            log("  " + line.rstrip())
    return p.wait()


def _http(url: str, headers: dict | None = None, timeout: int = 5) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(200000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file(path: str | Path, expected: str) -> bool:
    return sha256_file(path) == expected.strip().lower()


# ------------------------------------------------------------------ donanım
PROFILES = {
    "full": {"model": "qwen3:14b", "vision_model": "qwen3-vl:8b", "download_gb": 15.4, "why": "16 GB sınıfı ekran kartı: 14B yazı + 8B görüntü modeli."},
    "medium": {"model": "qwen3:8b", "vision_model": "qwen3-vl:4b", "download_gb": 8.5, "why": "8-14 GB VRAM: 8B yazı modeli, 4B görüntü modeli."},
    "small": {"model": "qwen3:4b", "vision_model": "", "download_gb": 2.6, "why": "4-8 GB VRAM: yalnız 4B yazı modeli."},
    "cloud": {"model": "qwen3:1.7b", "vision_model": "", "download_gb": 1.4, "why": "Ekran kartı yok ya da < 4 GB: asistan için bulut API önerilir."},
}


def _parse_nvidia(out: str) -> tuple[str | None, float | None]:
    best: tuple[str | None, float | None] = (None, None)
    for line in (out or "").splitlines():
        if "," in line:
            name, _, mem = line.rpartition(",")
            try:
                gb = round(float(mem.strip()) / 1024, 1)
            except ValueError:
                continue
            if best[1] is None or gb > best[1]:
                best = (name.strip(), gb)
    return best


def _ram_gb() -> float | None:
    try:
        import psutil
        return round(psutil.virtual_memory().total / GB, 1)
    except Exception:
        pass
    try:
        if WIN:
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                            ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong),
                            ("av", ctypes.c_ulonglong), ("ae", ctypes.c_ulonglong)]
            s = MS()
            s.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
            return round(s.tp / GB, 1)
        if MAC:
            _, out = _run_capture(["sysctl", "-n", "hw.memsize"])
            return round(int(out.strip()) / GB, 1) if out.strip().isdigit() else None
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal"):
                return round(int(line.split()[1]) / 1024 / 1024, 1)
    except Exception:
        pass
    return None


def hardware() -> dict:
    hw = {"os": platform.system(), "ram_gb": _ram_gb(), "cpu_cores": os.cpu_count(), "gpu": None, "vram_gb": None,
          "disk_free_gb": None, "note": ""}
    try:
        hw["disk_free_gb"] = round(shutil.disk_usage(Path.home()).free / GB, 1)
    except Exception:
        pass
    if MAC and platform.machine() == "arm64" and hw["ram_gb"]:
        hw.update(gpu="Apple Silicon (birleşik bellek)", vram_gb=round(hw["ram_gb"] * 0.7, 1),
                  note="birleşik bellek: RAM'in ~%70'i VRAM sayıldı")
        return hw
    _, out = _run_capture(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"], timeout=30)
    name, gb = _parse_nvidia(out)
    if gb is not None:
        hw["gpu"], hw["vram_gb"] = name, gb
        return hw
    if WIN:
        _, out = _run_capture(["powershell", "-NoProfile", "-Command",
                               "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json"], 20)
        try:
            data = json.loads(out)
            for g in data if isinstance(data, list) else [data]:
                gbv = round((g.get("AdapterRAM") or 0) / GB, 1)
                if g.get("Name") and (hw["vram_gb"] is None or gbv > hw["vram_gb"]):
                    hw["gpu"], hw["vram_gb"] = g["Name"], gbv
            if hw["gpu"]:
                hw["note"] = "VRAM doğrulanamadı (nvidia-smi yok); Windows 4 GB üstünü eksik gösterebilir"
        except Exception:
            pass
    return hw


def recommend(hw: dict) -> dict:
    v = hw.get("vram_gb")
    name = "cloud" if v is None or v < 4 else "full" if v >= 14 else "medium" if v >= 8 else "small"
    return {"profile": name, **PROFILES[name]}


# ------------------------------------------------------------------ dosya işleri (kit/install.py'nin kopyası)
def copy_missing(src: Path, dst: Path) -> int:
    n = 0
    for p in src.rglob("*"):
        if p.is_file():
            t = dst / p.relative_to(src)
            if not t.exists():
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, t)
                n += 1
    return n


def sync_code(src: Path, dst: Path) -> None:
    for item in ("sb", "tools", "tests", "docs", "skills", "integrations", "setup", "pyproject.toml", "uv.lock", ".python-version",
                 "VERSION", "features.yaml"):
        s, d = src / item, dst / item
        if s.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        elif s.exists():
            shutil.copy2(s, d)
    (dst / "config").mkdir(parents=True, exist_ok=True)
    for ex in (src / "config").glob("*"):
        if ex.name.endswith(".example.yaml") or not (dst / "config" / ex.name).exists():
            shutil.copy2(ex, dst / "config" / ex.name)


def _yaml():
    try:
        import yaml
        return yaml
    except Exception:
        raise RuntimeError("PyYAML yok: paneli `uv run --with pyyaml setup/app.py` ile başlat")


def write_features(system: Path, modules: dict[str, bool]) -> None:
    y = _yaml()
    p = system / "config" / "features.yaml"
    data = (y.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None) or {}
    data.setdefault("modules", {}).update({k: bool(v) for k, v in modules.items()})
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# Hangi modüller açık (kurulum paneli yazdı; sb features --on/--off ile de değişir).\n"
                 + y.safe_dump(data, allow_unicode=True, sort_keys=True), encoding="utf-8")


# ------------------------------------------------------------------ motor
STEPS = [("vault", "Kasa ve kod"), ("config", "Ayarlar"), ("secrets", "Sırlar (şifre kasası)"), ("deps", "Python ortamı"),
         ("claude", "Claude Code bağlantısı"), ("model", "Yerel model"), ("schedule", "Zamanlayıcı"), ("git", "Kasa git deposu"),
         ("doctor", "Kontrol")]


def _res(ok: bool, message: str) -> dict:
    return {"ok": bool(ok), "message": message}


def _trash():
    try:
        from send2trash import send2trash
        return send2trash
    except Exception:
        return None


def _imap_login(host: str, user: str, pw: str) -> tuple[bool, str]:
    import imaplib
    try:
        m = imaplib.IMAP4_SSL(host, 993, timeout=8)
        m.login(user, pw)
        m.logout()
        return True, "IMAP girişi başarılı"
    except Exception as e:
        return False, f"IMAP girişi başarısız: {type(e).__name__}"


def parse_doctor(text: str) -> dict:
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\s*([✓!✗])\s+(.*?)(?:\s+→\s+(.*))?$", line)
        if m:
            rows.append({"status": {"✓": "ok", "!": "warn", "✗": "fail"}[m.group(1)], "name": m.group(2).strip(), "hint": (m.group(3) or "").strip()})
    summ = next((ln.strip() for ln in text.splitlines() if ln.strip().startswith("Sürüm")), "")
    return {"ok": bool(rows) and not any(r["status"] == "fail" for r in rows), "rows": rows, "summary": summ}


def _vtuple(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def latest_tag(ls_remote_out: str) -> str | None:
    tags = [m.group(1) for m in re.finditer(r"refs/tags/v?(\d+\.\d+\.\d+)$", ls_remote_out, re.M)]
    return max(tags, key=_vtuple) if tags else None


class Engine:
    def __init__(self, vault: str | Path | None = None, data: Path | None = None):
        self.data = Path(data) if data else data_dir()
        self.vault = Path(os.path.expanduser(str(vault))).resolve() if vault else None
        self.lines: deque[str] = deque(maxlen=200)
        self.steps = [{"id": i, "title": t, "status": "pending"} for i, t in STEPS]
        self.running = False
        self.error = ""
        self.job = ""
        self.selection: dict = {"preset": "tam", "modules": preset_modules("tam"), "fields": {}}
        self._secrets: list[str] = []
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    # -- günlük ve ilerleme
    def log(self, msg: str) -> None:
        with self._lock:
            self.lines.append(redact(str(msg), self._secrets))

    def progress(self) -> dict:
        with self._lock:
            done = sum(1 for s in self.steps if s["status"] in ("done", "skipped"))
            return {"running": self.running, "job": self.job, "percent": round(100 * done / len(self.steps)),
                    "steps": [dict(s) for s in self.steps], "log": list(self.lines), "error": self.error}

    # -- durum (sürdürme)
    @property
    def state_file(self) -> Path:
        return self.data / "setup_state.json"

    def public_selection(self) -> dict:
        f = {k: v for k, v in (self.selection.get("fields") or {}).items() if k not in SECRET_KEYS}
        return {"preset": self.selection.get("preset"), "modules": self.selection.get("modules"), "fields": f}

    def save_state(self, done: list[str]) -> None:
        self.data.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps({"selection": self.public_selection(), "done": done,
                                               "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False, indent=1), encoding="utf-8")

    def state(self) -> dict:
        try:
            st = json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {"resumable": False, "done": [], "pending": [i for i, _ in STEPS], "selection": None}
        done = st.get("done", [])
        pending = [i for i, _ in STEPS if i not in done]
        return {"resumable": bool(pending) and bool(done), "done": done, "pending": pending,
                "selection": st.get("selection"), "updated": st.get("updated")}

    # -- seçim ve profil
    def set_selection(self, sel: dict) -> None:
        preset = sel.get("preset") or self.selection.get("preset") or "tam"
        mods = preset_modules(preset)
        bad = [k for k in (sel.get("modules") or {}) if k not in _ALL]
        if bad:
            raise ValueError(f"Bilinmeyen modül: {', '.join(bad)}")
        mods.update({k: bool(v) for k, v in (sel.get("modules") or {}).items()})
        fields = {k: str(v) for k, v in (sel.get("fields") or {}).items() if isinstance(v, (str, int, float))}
        self.selection = {"preset": preset, "modules": mods, "fields": fields}
        self._secrets = [v for k, v in fields.items() if k in SECRET_KEYS and v]
        if fields.get("vault"):
            self.vault = Path(os.path.expanduser(fields["vault"])).resolve()

    def export_profile(self) -> dict:
        return {"format": "second-brain-setup-profile", "version": 1, **self.public_selection(),
                "local_model": PRESETS.get(self.selection.get("preset"), {}).get("local_model", True)}

    def import_profile(self, prof: dict) -> dict:
        if not isinstance(prof, dict):
            raise ValueError("Profil bir JSON nesnesi olmalı")
        fields = {k: v for k, v in (prof.get("fields") or {}).items() if k not in SECRET_KEYS}
        self.set_selection({"preset": prof.get("preset"), "modules": prof.get("modules"), "fields": fields})
        return self.public_selection()

    # -- bağlantı testleri
    def test(self, kind: str, fields: dict | None = None) -> dict:
        f = {**(self.selection.get("fields") or {}), **(fields or {})}
        self._secrets += [str(v) for k, v in f.items() if k in SECRET_KEYS and v]

        def key(field: str, ring: str) -> str:
            if f.get(field):
                return str(f[field])
            kr = _keyring()
            try:
                return (kr.get_password(KEYRING_SERVICE, ring) if kr else "") or ""
            except Exception:
                return ""
        try:
            if kind == "ollama":
                code, _ = _http("http://localhost:11434/api/tags", timeout=3)
                return _res(code == 200, "Ollama çalışıyor" if code == 200 else "Ollama'ya ulaşılamadı (ollama.com'dan kur)")
            if kind in ("openai", "anthropic", "gemini"):
                k = key(f"{kind}_key", f"api-{kind}")
                if not k:
                    return _res(False, "Anahtar girilmedi")
                url, hdr = {"openai": ("https://api.openai.com/v1/models", {"Authorization": f"Bearer {k}"}),
                            "anthropic": ("https://api.anthropic.com/v1/models", {"x-api-key": k, "anthropic-version": "2023-06-01"}),
                            "gemini": ("https://generativelanguage.googleapis.com/v1beta/models", {"x-goog-api-key": k})}[kind]
                code, _ = _http(url, hdr, timeout=6)
                return _res(code == 200, "Anahtar geçerli" if code == 200 else f"Reddedildi ya da ulaşılamadı (kod {code})")
            if kind == "imap":
                host, user = f.get("imap_host"), f.get("imap_email")
                pw = key("imap_password", f"imap-{f.get('imap_alias') or 'is'}")
                if not (host and user and pw):
                    return _res(False, "Sunucu, e-posta ve şifre gerekli")
                return _res(*_imap_login(host, user, pw))
            if kind == "google":
                cs = Path(os.path.expanduser(f["client_secret"])) if f.get("client_secret") else self.data / "secrets" / "client_secret.json"
                if not cs.is_file():
                    return _res(False, "client_secret.json bulunamadı (Sihirbazlar › Google Cloud)")
                try:
                    ok = bool({"installed", "web"} & set(json.loads(cs.read_text(encoding="utf-8"))))
                except Exception:
                    ok = False
                return _res(ok, "client_secret.json geçerli görünüyor" if ok else "Dosya geçerli bir OAuth istemcisi değil")
            if kind == "tailscale":
                rc, _ = _run_capture(["tailscale", "status"], 8)
                return _res(rc == 0, "Tailscale bağlı" if rc == 0 else "Tailscale kurulu/bağlı değil")
            if kind == "obsidian":
                v = self.vault or (Path(os.path.expanduser(f["vault"])) if f.get("vault") else None)
                ok = bool(v and (v / ".obsidian").exists()) or bool(shutil.which("obsidian"))
                return _res(ok, "Obsidian kasası hazır" if ok else "Obsidian'da bu klasörü 'Open folder as vault' ile aç")
        except Exception as e:
            return _res(False, redact(f"Test hatası: {type(e).__name__}", self._secrets))
        return _res(False, f"Bilinmeyen test: {kind}")

    # -- kurulum adımları
    def apply(self, sel: dict | None = None, resume: bool = False, wait: bool = False) -> bool:
        with self._lock:
            if self.running:
                return False
            self.running, self.error, self.job = True, "", "apply"
        try:
            if resume and not sel and self.state().get("selection"):
                st = self.state()["selection"]
                sel = {**st, "fields": {**(st.get("fields") or {}), **(self.selection.get("fields") or {})}}
            if sel:
                self.set_selection(sel)
            done = list(self.state()["done"]) if resume else []
        except Exception:
            self.running = False
            raise
        for s in self.steps:
            s["status"] = "done" if s["id"] in done else "pending"
        self._thread = threading.Thread(target=self._run_steps, args=(done,), daemon=True)
        self._thread.start()
        if wait:
            self._thread.join()
        return True

    def _run_steps(self, done: list[str]) -> None:
        try:
            for step in self.steps:
                if step["id"] in done:
                    continue
                step["status"] = "running"
                self.log(f"== {step['title']} ==")
                try:
                    skipped = getattr(self, "_step_" + step["id"])()
                except Exception as e:
                    step["status"] = "error"
                    self.error = redact(f"{step['title']}: {e}", self._secrets)
                    self.log("HATA: " + self.error)
                    return
                step["status"] = "skipped" if skipped else "done"
                done.append(step["id"])
                self.save_state(done)
            self.log("Kurulum bitti.")
        finally:
            self.running = False

    def _system(self) -> Path:
        if not self.vault:
            raise RuntimeError("Kasa klasörü belirtilmedi")
        return self.vault / "_system"

    def _py(self) -> list[str]:
        return ["uv", "run", "--directory", str(self._system()), "python", "-X", "utf8"]

    def _step_vault(self):
        kit = kit_dir()
        if not kit:
            self.log("  kit yok (panel kasadan çalışıyor): atlandı")
            return True
        v = self.vault
        if v == kit or kit in v.parents:
            raise RuntimeError(f"Kasa kurulum paketinin içine kurulamaz: {v}")
        v.mkdir(parents=True, exist_ok=True)
        self.log(f"  şablondan {copy_missing(kit / 'vault', v)} dosya eklendi (var olanlar korundu)")
        sync_code(kit / "system", self._system())
        if (kit / "setup").is_dir():
            shutil.copytree(kit / "setup", self._system() / "setup", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.data.mkdir(parents=True, exist_ok=True)
        ver = (kit / "system" / "VERSION").read_text(encoding="utf-8").strip() if (kit / "system" / "VERSION").exists() else "?"
        (self.data / "kit.json").write_text(json.dumps({"kit": str(kit), "vault": str(v), "version": ver}, ensure_ascii=False, indent=1), encoding="utf-8")

    def _step_config(self):
        y, sysd, f = _yaml(), self._system(), self.selection["fields"]
        cfg = sysd / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        for ex in cfg.glob("*.example.yaml"):
            real = cfg / ex.name.replace(".example", "")
            if not real.exists():
                shutil.copy2(ex, real)

        def load(n):
            p = cfg / n
            return (y.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None) or {}
        prof = load("profile.yaml")
        for k in ("name", "full_name", "bio", "timezone", "github_user", "workspace"):
            if f.get(k):
                prof[k] = f[k]
        (cfg / "profile.yaml").write_text("# Kişi profili (kurulum paneli yazdı)\n" + y.safe_dump(prof, allow_unicode=True, sort_keys=False), encoding="utf-8")
        acc = load("accounts.yaml")
        if "@" in (f.get("gmail") or ""):
            g = acc.setdefault("google", {}).setdefault("main", {"source": "gmail-main", "scopes": ["gmail", "calendar", "contacts", "drive"]})
            g["email"] = f["gmail"]
            acc.setdefault("notify", {}).setdefault("to", [f["gmail"]])
        if f.get("imap_email") and f.get("imap_host"):
            alias = _alias(f)
            acc.setdefault("imap", {})[alias] = {"email": f["imap_email"], "host": f["imap_host"], "source": f"imap-{alias}"}
        (cfg / "accounts.yaml").write_text("# Hesaplar (gizli bilgi YOK; şifreler işletim sistemi şifre kasasında)\n"
                                           + y.safe_dump(acc, allow_unicode=True, sort_keys=False), encoding="utf-8")
        write_features(sysd, self.selection["modules"])
        cs = f.get("client_secret")
        if cs and Path(os.path.expanduser(cs)).is_file():
            dst = self.data / "secrets" / "client_secret.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(Path(os.path.expanduser(cs)), dst)
        self.log("  profil, hesaplar ve özellik seçimi yazıldı")

    def _step_secrets(self):
        f = self.selection["fields"]
        todo = [(fd, f[fd["key"]]) for fd in FIELDS if fd["kind"] == "secret" and f.get(fd["key"])]
        if not todo:
            self.log("  girilecek sır yok")
            return True
        kr = _keyring()
        if not kr:
            raise RuntimeError("keyring yok: sırlar dosyaya yazılmaz; `uv sync` sonrası bu adımı yeniden çalıştır")
        for fd, val in todo:
            name = fd["keyring"].format(imap_alias=_alias(f))
            kr.set_password(KEYRING_SERVICE, name, val)
            self.log(f"  şifre kasasına yazıldı: {name} = ***")
        for k in SECRET_KEYS:                                 # bellekten de sil
            f.pop(k, None)

    def _step_deps(self):
        sysd = self._system()
        if not (sysd / "pyproject.toml").exists():
            raise RuntimeError(f"{sysd} içinde pyproject.toml yok (kod kopyalanmadı)")
        if _run_stream(["uv", "sync"], self.log, sysd):
            raise RuntimeError("uv sync başarısız")
        if (sysd / "tools" / "install_cli.py").exists():
            _run_stream(["uv", "run", "--directory", str(sysd), "python", str(sysd / "tools" / "install_cli.py")], self.log)

    def _step_claude(self):
        claude = shutil.which("claude")
        if not self.selection["modules"].get("claude_hooks") or not claude:
            self.log("  Claude Code kapalı ya da kurulu değil: atlandı")
            return True
        sysd = self._system()
        _run_stream([claude, "mcp", "remove", "second-brain", "-s", "user"], lambda m: None)
        _run_stream([claude, "mcp", "add", "second-brain", "--scope", "user", "--", "uv", "run", "--directory", str(sysd), "python", "-m", "sb.mcp_server"], self.log)

    def _step_model(self):
        if not PRESETS.get(self.selection["preset"], {}).get("local_model", True) or not shutil.which("ollama"):
            self.log("  yerel model seçilmedi ya da Ollama yok: atlandı")
            return True
        rec = recommend(hardware())
        self.log(f"  önerilen profil: {rec['profile']} ({rec['model']})")
        if rec["profile"] == "cloud":
            return True
        _run_stream(["ollama", "pull", rec["model"]], self.log)
        if rec.get("vision_model") and self.selection["modules"].get("vision"):
            _run_stream(["ollama", "pull", rec["vision_model"]], self.log)
        _run_stream(self._py() + ["-m", "sb", "models", "--apply", rec["profile"], "--yes"], self.log)

    def _step_schedule(self):
        sysd = self._system()
        if WIN and (sysd / "tools" / "schedule.ps1").exists():
            _run_stream(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(sysd / "tools" / "schedule.ps1")], self.log)
        elif MAC and (sysd / "tools" / "schedule_macos.py").exists():
            _run_stream([sys.executable, str(sysd / "tools" / "schedule_macos.py")], self.log)
        else:
            self.log("  otomatik zamanlayıcı yok (cron ile `sb daily` / `sb weekly` kur)")
            return True

    def _step_git(self):
        v = self._system().parent
        if not shutil.which("git") or (v / ".git").exists():
            self.log("  git yok ya da kasa zaten depo: atlandı")
            return True
        for cmd in (["git", "init", "-b", "main"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "Second Brain kurulumu"]):
            _run_stream(cmd, self.log, v)

    def _step_doctor(self):
        h = self.health()
        self.log("  " + (h.get("summary") or h.get("message", "")))

    # -- sağlık
    def health(self) -> dict:
        sysd = self._system() if self.vault else (code_dir() or ROOT)
        if not (sysd / "sb").is_dir():
            return {"ok": False, "rows": [], "summary": "", "message": "sb henüz kurulu değil"}
        rc, out = _run_capture(["uv", "run", "--directory", str(sysd), "python", "-X", "utf8", "-m", "sb", "doctor"], 120)
        return {**parse_doctor(out), "returncode": rc}

    # -- güncelleme
    def version_info(self) -> dict:
        cur = None
        for p in ((self._system() if self.vault else None), code_dir()):
            if p and (p / "VERSION").exists():
                cur = (p / "VERSION").read_text(encoding="utf-8").strip()
                break
        kit, remote = kit_dir(), ""
        info = self.data / "kit.json"
        if info.exists():
            try:
                kit = Path(json.loads(info.read_text(encoding="utf-8"))["kit"])
            except Exception:
                pass
        if kit and (kit / ".git").exists():
            rc, out = _run_capture(["git", "-C", str(kit), "remote", "get-url", "origin"], 8)
            remote = out.strip() if rc == 0 else ""
        latest = None
        if remote:
            rc, out = _run_capture(["git", "ls-remote", "--tags", remote], 20)
            latest = latest_tag(out) if rc == 0 else None
        return {"current": cur, "latest": latest, "source": "git ls-remote" if latest else None,
                "update_available": bool(cur and latest and _vtuple(latest) > _vtuple(cur))}

    def run_update(self) -> bool:
        with self._lock:
            if self.running:
                return False
            self.running, self.error, self.job = True, "", "update"

        def job():
            try:
                self.log("== sb update ==")
                rc = _run_stream(self._py() + ["-m", "sb", "update"], self.log)
                if rc:
                    self.error = f"sb update çıkış kodu {rc}"
            except Exception as e:
                self.error = str(e)
            finally:
                self.running = False
        self._thread = threading.Thread(target=job, daemon=True)
        self._thread.start()
        return True

    # -- modül geri alma (dosya silmeden)
    def disable_modules(self, keys: list[str]) -> dict:
        bad = [k for k in keys if k not in _ALL]
        if bad:
            raise ValueError(f"Bilinmeyen modül: {', '.join(bad)}")
        write_features(self._system(), {k: False for k in keys})
        self.selection["modules"].update({k: False for k in keys})
        return {"disabled": keys, "note": "Günlük çalışma bu modüllerin adımını atlar; hiçbir dosya silinmedi."}

    # -- temiz kaldırma
    def uninstall_plan(self) -> list[dict]:
        acts = []
        if WIN:
            acts.append({"id": "tasks", "desc": "Zamanlanmış görevleri kaldır: " + ", ".join(TASK_NAMES), "auto": True})
        elif MAC:
            acts.append({"id": "tasks", "desc": "launchd görevlerini durdur: com.secondbrain.*", "auto": True})
        sysd = self._system() if self.vault else None
        if sysd and sysd.is_dir():
            can = _trash() is not None
            acts.append({"id": "code", "auto": can, "desc": f"Kodu Geri Dönüşüm Kutusu'na taşı: {sysd} (kasa notları kalır)" if can
                         else f"Kodu elle taşı/sil: {sysd} (send2trash yok; kasa notlarına dokunma)"})
        acts.append({"id": "notes", "desc": "Kasa notlarına dokunulmaz", "auto": False})
        return acts

    def uninstall(self, confirm: bool = False) -> dict:
        plan = self.uninstall_plan()
        if not confirm:
            return {"applied": False, "plan": plan}
        done = []
        for a in plan:
            if not a["auto"]:
                continue
            if a["id"] == "tasks":
                if WIN:
                    _run_capture(["powershell", "-NoProfile", "-Command",
                                  "Get-ScheduledTask -TaskName 'SecondBrain-*' -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false"], 60)
                elif MAC:
                    for pl in (Path.home() / "Library" / "LaunchAgents").glob("com.secondbrain.*.plist"):
                        _run_capture(["launchctl", "unload", str(pl)])
                done.append("tasks")
            elif a["id"] == "code":
                t = self._system()
                if t.name == "_system" and t.is_dir():          # yalnız _system klasörü; kasa köküne asla
                    _trash()(str(t))
                    done.append("code")
        return {"applied": True, "plan": plan, "done": done}


def _alias(f: dict) -> str:
    return re.sub(r"[^a-z0-9_-]", "", (f.get("imap_alias") or "is").lower()) or "is"


# ------------------------------------------------------------------ komut satırı
def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Second Brain kurulum motoru (panelsiz)")
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--profile", help="profil JSON (seçimler + alanlar; sırlar SB_SECRET_<ALAN> ortam değişkeninden)")
    ap.add_argument("--vault")
    ap.add_argument("--yes", action="store_true", help="onay (sessiz kurulum)")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--verify", nargs=2, metavar=("ZIP", "SHA256"))
    a = ap.parse_args(argv)
    if a.verify:
        ok = verify_file(*a.verify)
        print("SHA-256 eşleşti" if ok else "SHA-256 EŞLEŞMEDİ — dosyayı kullanma")
        return 0 if ok else 2
    if not a.yes:
        print("Sessiz kurulum için --yes ekle (panel için setup/app.py).")
        return 1
    sel: dict = {}
    if a.profile:
        sel = json.loads(Path(a.profile).read_text(encoding="utf-8"))
    sel = {"preset": a.preset or sel.get("preset") or "tam", "modules": sel.get("modules"), "fields": dict(sel.get("fields") or {})}
    for k in SECRET_KEYS:
        if os.environ.get(f"SB_SECRET_{k.upper()}"):
            sel["fields"][k] = os.environ[f"SB_SECRET_{k.upper()}"]
    if a.vault:
        sel["fields"]["vault"] = a.vault
    sel["fields"].setdefault("vault", str(Path.home() / "SecondBrain"))
    sel["fields"].setdefault("name", os.environ.get("USERNAME") or os.environ.get("USER") or "Kullanıcı")
    eng = Engine()
    eng.apply(sel, resume=a.resume, wait=True)
    print("\n".join(eng.progress()["log"]))
    return 1 if eng.error else 0


if __name__ == "__main__":
    sys.exit(main())
