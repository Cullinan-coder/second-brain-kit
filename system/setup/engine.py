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


# ------------------------------------------------------------------ deneme kipi (SB_SETUP_SANDBOX=<klasör>)
SANDBOX_SKIPPED: list[str] = []                                # atlanan yan etkili komutlar (test ve günlük için)
_sandbox_sink = None                                           # günlük işlevi (Engine.log) — _run_capture günlük almaz


def sandbox_dir() -> Path | None:
    """Deneme kipi klasörü (yoksa None). Kasa, veri, şifre kasası, Başlangıç/Claude yapılandırması hep bunun altına gider."""
    v = os.environ.get("SB_SETUP_SANDBOX")
    return Path(os.path.expanduser(v)).resolve() if v else None


def data_dir() -> Path:
    sb = sandbox_dir()
    if sb:
        return sb / "data"
    return Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain")


def default_vault() -> Path:
    """Kasa klasörü boş bırakılınca kullanılan konum: ~/SecondBrain (deneme kipinde <deneme>/SecondBrain)."""
    sb = sandbox_dir()
    return (sb / "SecondBrain") if sb else Path.home() / "SecondBrain"


def default_name() -> str:
    return os.environ.get("USERNAME") or os.environ.get("USER") or "Kullanıcı"


class JsonKeyring:
    """Deneme kipinin şifre kasası: gerçek keyring yerine <deneme>/keyring.json (düz dosya; yalnız deneme için)."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:                                      # noqa: BLE001
            return {}

    def _save(self, d: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    def get_password(self, service, name):
        return self._load().get(f"{service}/{name}")

    def set_password(self, service, name, value):
        with self._lock:
            d = self._load()
            d[f"{service}/{name}"] = value
            self._save(d)

    def delete_password(self, service, name):
        with self._lock:
            d = self._load()
            if d.pop(f"{service}/{name}", None) is None:
                raise KeyError(name)
            self._save(d)


def which_cmd(name: str) -> str | None:
    """shutil.which; deneme kipinde claude/ollama kurulu sayılır (komutlar zaten çalıştırılmaz)."""
    if sandbox_dir() and name in ("claude", "ollama"):
        return name
    return shutil.which(name)


def _cmd_text(cmd) -> str:
    out, mask = [], False
    for x in map(str, cmd):
        out.append("***" if mask else x)
        mask = x == "-e"                                       # claude mcp add -e KEY=değer: değeri yazma
    return " ".join(out)[:300]


def _sandbox_skip(cmd) -> bool:
    """Deneme kipinde gerçek sistemi değiştiren komutlar (zamanlanmış görev, kısayol, claude mcp, ollama, winget, büyük indirme)."""
    if not sandbox_dir() or not cmd:
        return False
    c = [str(x) for x in cmd]
    exe = Path(c[0]).name.lower().removesuffix(".exe")
    j = " ".join(c).lower()
    if exe in ("schtasks", "launchctl", "winget", "docker", "brew", "apt", "apt-get"):
        return True
    if exe in ("powershell", "pwsh") and any(k in j for k in ("scheduledtask", "createshortcut", "ollamasetup", "invoke-webrequest", "schedule.ps1")):
        return True
    if exe == "claude" and c[1:3] in (["mcp", "add"], ["mcp", "remove"]):
        return True
    if exe == "ollama" and len(c) > 1 and c[1] in ("pull", "rm", "run", "create", "serve", "push", "cp"):
        return True
    if exe in ("sh", "bash") and any(k in j for k in ("ollama.com", "ollama-darwin")):
        return True
    if "install_cli.py" in j or "--extra" in c or ("voice" in c and "--setup" in c) or ("models" in c and "--apply" in c):
        return True
    if "sb" in c and (c[-1] == "update" or (len(c) > 1 and c[-2] == "login")):
        return True
    return False


def _skipped(cmd, log=None) -> None:
    line = "[deneme] atlandı: " + _cmd_text(cmd)
    SANDBOX_SKIPPED.append(line)
    if log:
        log(line)
    elif _sandbox_sink:
        _sandbox_sink(line)


def bundle_dir() -> Path | None:
    """PyInstaller paketinde (Second Brain Setup.exe) açılmış gömülü dosyaların klasörü; paketli değilse None."""
    mp = getattr(sys, "_MEIPASS", None)
    return Path(mp) if mp else None


def kit_dir() -> Path | None:
    """Kit kökü (içinde system/ ve vault/ var) ya da None (kasadaki _system/setup'tan çalışıyorsak).
    Paketli Setup'ta gömülü kit `sys._MEIPASS/kit` (ya da doğrudan `_MEIPASS`) altındadır."""
    b = bundle_dir()
    if b:
        for c in (b / "kit", b):
            if (c / "system" / "sb").exists():
                return c
    return ROOT if (ROOT / "system" / "sb").exists() else None


def code_dir() -> Path | None:
    """sb paketinin bulunduğu klasör (kitte system/, kasada _system/)."""
    k = kit_dir()
    packed = [k / "system"] if (k and bundle_dir()) else []          # paketli Setup: gömülü kit önce
    for p in (*packed, ROOT / "system", ROOT):
        if (p / "sb").is_dir():
            return p
    return None


# ------------------------------------------------------------------ uygulama başlatıcısı ve kısayollar
APP_NAME = "Second Brain"


def bundled_launcher() -> Path | None:
    """Setup içine gömülü `Second Brain.exe` / `Second Brain.app` (paketli değilse None)."""
    b = bundle_dir()
    if not b:
        return None
    p = b / "launcher" / (APP_NAME + (".app" if sys.platform == "darwin" else ".exe"))
    return p if p.exists() else None


def apps_dir() -> Path:
    """macOS uygulama klasörü (kullanıcıya özel, yönetici gerektirmez); `SB_APPS_DIR` ile değiştirilebilir."""
    sb = sandbox_dir()
    if sb:
        return sb / "Applications"
    return Path(os.environ.get("SB_APPS_DIR") or Path.home() / "Applications")


def launcher_path(data: Path, plat: str | None = None) -> Path:
    """Kurulu başlatıcının yeri: Windows `<veri>/bin/Second Brain.exe`, macOS `~/Applications/Second Brain.app`."""
    if (plat or sys.platform) == "darwin":
        return apps_dir() / (APP_NAME + ".app")
    return data / "bin" / (APP_NAME + ".exe")


def launcher_exe(data: Path, plat: str | None = None) -> Path | None:
    """Kurulu başlatıcının çalıştırılabilir dosyası (yoksa None)."""
    p = launcher_path(data, plat)
    if (plat or sys.platform) == "darwin":
        p = p / "Contents" / "MacOS" / APP_NAME
    return p if p.is_file() else None


def install_launcher(data: Path, plat: str | None = None) -> Path | None:
    """Gömülü başlatıcıyı kalıcı yere kopyalar (yoksa None döner; çağıran pythonw yoluna düşer)."""
    src = bundled_launcher()
    if not src:
        return None
    dst = launcher_path(data, plat)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
        exe = dst / "Contents" / "MacOS" / APP_NAME
        if exe.exists():
            exe.chmod(0o755)
    else:
        shutil.copy2(src, dst)
    return dst


def make_stub_app(dest: Path, system: Path) -> Path:
    """Paketli başlatıcı yokken (kaynak koddan kurulum) macOS'ta `Second Brain.app` iskeleti: venv python'u `-m app.desktop` açar."""
    import plistlib
    mac = dest / "Contents" / "MacOS"
    mac.mkdir(parents=True, exist_ok=True)
    (dest / "Contents" / "Info.plist").write_bytes(plistlib.dumps({
        "CFBundleName": APP_NAME, "CFBundleDisplayName": APP_NAME, "CFBundleExecutable": APP_NAME,
        "CFBundleIdentifier": "com.secondbrain.app", "CFBundlePackageType": "APPL"}))
    sh = mac / APP_NAME
    sh.write_text(f'#!/bin/sh\ncd "{system}" || exit 1\nexec "{system}/.venv/bin/python" -m app.desktop "$@"\n', encoding="utf-8")
    sh.chmod(0o755)
    return dest


def cli_shim_text(code: Path, vault: Path | None, data: Path, plat: str) -> str:
    """`sb` komutu için başlatıcı içeriği: hangi klasörde olursan ol `sb <komut>` çalışır (göreli yol argümanları korunur)."""
    if plat == "win32":
        py = Path(code) / ".venv" / "Scripts" / "python.exe"
        lines = ["@echo off", "setlocal", f'set "PYTHONPATH={code};%PYTHONPATH%"']
        if vault:
            lines.append(f'set "SB_VAULT={vault}"')
        lines += [f'set "SB_DATA={data}"', f'"{py}" -X utf8 -m sb %*']
        return "\r\n".join(lines) + "\r\n"
    q = lambda v: "'" + str(v).replace("'", "'\\''") + "'"
    py = Path(code) / ".venv" / "bin" / "python"
    env = [f"PYTHONPATH={q(code)}\"${{PYTHONPATH:+:$PYTHONPATH}}\"", f"SB_DATA={q(data)}"] + ([f"SB_VAULT={q(vault)}"] if vault else [])
    return "#!/bin/sh\n" + "".join(f"export {e}\n" for e in env) + f"exec {q(py)} -X utf8 -m sb \"$@\"\n"


def cli_shim_dir(data: Path, plat: str) -> Path:
    return Path(data) / "bin" if plat == "win32" else Path.home() / ".local" / "bin"


def install_cli_shim(code: Path, vault: Path | None, data: Path, plat: str, sandbox: bool = False) -> str:
    """`sb` başlatıcısını yazar ve (Windows) klasörünü kullanıcı PATH'ine ekler. Hata kurulumu durdurmaz: mesaj döner."""
    d = cli_shim_dir(data, plat)
    name = "sb.cmd" if plat == "win32" else "sb"
    try:
        d.mkdir(parents=True, exist_ok=True)
        f = d / name
        f.write_text(cli_shim_text(code, vault, data, plat), encoding="utf-8", newline="")
        if plat != "win32":
            f.chmod(0o755)
    except OSError as e:
        return f"`sb` komutu yazılamadı: {e}"
    if sandbox:
        return f"[deneme] `sb` başlatıcısı yazıldı ({d / name}); PATH değiştirilmedi"
    if plat == "win32":
        # Kayıt defterinden açılmamış (%DEĞİŞKEN%'li) haliyle oku, ExpandString türünü koruyarak yaz; değişikliği duyur.
        ps = ("$d='" + str(d).replace("'", "''") + "'; $k=[Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment',$true); "
              "$p=[string]$k.GetValue('Path','',[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames); "
              "if(-not (($p -split ';') -contains $d)){ $k.SetValue('Path', (($p.TrimEnd(';')), $d -join ';').TrimStart(';'), "
              "[Microsoft.Win32.RegistryValueKind]::ExpandString); "
              "[Environment]::SetEnvironmentVariable('SB_PATH_REFRESH','1','User'); [Environment]::SetEnvironmentVariable('SB_PATH_REFRESH',$null,'User') }; $k.Close()")
        rc, out = _run_capture(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], 30)
        if rc != 0:
            return f"`sb` başlatıcısı yazıldı ({d / name}) ama PATH'e eklenemedi: {out.strip()[:120]}"
        return f"`sb` komutu hazır ({d / name}); yeni açılan terminallerde `sb <komut>` yaz"
    on_path = str(d) in os.environ.get("PATH", "").split(os.pathsep)
    return f"`sb` komutu hazır ({d / name})" + ("" if on_path else f"; {d} PATH'te değil: kabuk ayarına `export PATH=\"{d}:$PATH\"` ekle")


def shortcut_script(prog: str, args: list[str], cwd: str) -> str:
    """PowerShell: masaüstü + Başlat menüsü (kullanıcı) klasörüne `Second Brain.lnk` yazar (OneDrive'a taşınmış masaüstünü de bulur)."""
    q = lambda s: "'" + str(s).replace("'", "''") + "'"       # noqa: E731
    return ("$sh=New-Object -ComObject WScript.Shell;"
            "foreach($f in @([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Programs'))){"
            "if(-not $f){continue};New-Item -ItemType Directory -Force $f|Out-Null;"
            f"$s=$sh.CreateShortcut((Join-Path $f {q(APP_NAME + '.lnk')}));"
            f"$s.TargetPath={q(prog)};$s.Arguments={q(' '.join(args))};$s.WorkingDirectory={q(cwd)};"
            f"$s.Description={q(APP_NAME)};$s.IconLocation={q(prog + ',0')};$s.Save()}}")


# ------------------------------------------------------------------ modüller ve hazır seçimler
CATEGORIES = {
    "Mail ve takvim": ["gmail", "imap", "calendar", "dates", "contacts", "drive", "derived", "digest"],
    "Telefon ve mesaj": ["sms", "phone", "telegram", "whatsapp"],
    "Okul ve proje": ["courses", "projects", "github", "sessions", "cards", "local_files", "linkedin", "browser"],
    "Asistan ve hafıza": ["assistant", "memory_ui", "capture", "inbox", "brain", "claude_hooks", "flush", "night", "automation"],
    "Bilgisayar ve ses": ["computer", "media", "vision", "voice", "wake_word", "screen_watch", "image_gen", "clipboardline", "nashi"],
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


_SECRET_KEY_RE = re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|(^|_)key$|_pat$|şifre|credential|private)")


def strip_secrets(obj, secrets: list[str] | None = None):
    """Sihirbaz durumundan sır gibi görünen anahtarları atar, kalan metinleri maskeler (sır diske girmez)."""
    if isinstance(obj, dict):
        return {k: strip_secrets(v, secrets) for k, v in obj.items() if not (_SECRET_KEY_RE.search(str(k)) or str(k) in SECRET_KEYS)}
    if isinstance(obj, list):
        return [strip_secrets(v, secrets) for v in obj]
    if isinstance(obj, str):
        return redact(obj, secrets)
    return obj


_SB_KR: dict = {}


def _keyring():
    sb = sandbox_dir()
    if sb:                                                     # deneme kipi: gerçek şifre kasasına hiç dokunma
        return _SB_KR.setdefault(str(sb), JsonKeyring(sb / "keyring.json"))
    try:
        import keyring
        return keyring
    except Exception:
        return None


_NOWIN = 0x08000000 if WIN else 0                              # CREATE_NO_WINDOW (paketli pencereli uygulamada konsol açılmasın)


def uv_bin() -> str:
    """`uv` komutu: PATH'te varsa "uv"; yoksa `SB_UV` (paketli Setup'ın gömülü uv'si, ya da kalıcı kopyası); yoksa "uv"."""
    p = os.environ.get("SB_UV")
    if p and Path(p).is_file() and not shutil.which("uv"):
        return p
    return "uv"


def install_uv(data: Path) -> str:
    """Gömülü uv geçici klasörde (Setup kapanınca silinir) durur: PATH'te uv yoksa `data/bin/` altına kalıcı kopyala."""
    p = os.environ.get("SB_UV")
    if not p or not Path(p).is_file() or shutil.which("uv"):
        return uv_bin()
    dst = data / "bin" / Path(p).name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(p, dst)
        try:
            dst.chmod(0o755)
        except OSError:
            pass
    os.environ["SB_UV"] = str(dst)
    return str(dst)


def _run_capture(cmd: list[str], timeout: int = 15, cwd: Path | None = None) -> tuple[int, str]:
    if _sandbox_skip(cmd):
        _skipped(cmd)
        return 0, ""
    return _exec_capture(cmd, timeout, cwd)


def _run_stream(cmd: list[str], log, cwd: Path | None = None) -> int:
    """Komutu çalıştırır, çıktıyı satır satır günlüğe yazar (günlük sırları maskeler)."""
    if _sandbox_skip(cmd):
        _skipped(cmd, log)
        return 0
    return _exec_stream(cmd, log, cwd)


def proc_env(cmd, cwd: Path | None = None) -> dict:
    """Alt süreç ortamı. `uv` komutlarında sanal ortam HER ZAMAN `<proje>/.venv` olur (proje = `--directory` ya da cwd): dışarıdan gelen
    UV_PROJECT_ENVIRONMENT / VIRTUAL_ENV (ör. paneli çalıştıran uv'nin ortamı) kasa köküne ya da çalışan kuruluma sızmasın."""
    env = dict(os.environ)
    c = [str(x) for x in cmd]
    if c and re.split(r"[\\/]", c[0])[-1].lower().removesuffix(".exe") == "uv":        # Windows ve macOS yol ayırıcısı
        for k in ("UV_PROJECT_ENVIRONMENT", "VIRTUAL_ENV", "UV_ACTIVE", "CONDA_PREFIX"):
            env.pop(k, None)
        proj = None
        if "--directory" in c and c.index("--directory") + 1 < len(c):
            proj = c[c.index("--directory") + 1]
        base = Path(cwd) if cwd else Path.cwd()
        proj_dir = (base / proj) if proj else base
        env["UV_PROJECT_ENVIRONMENT"] = str(proj_dir / ".venv")
    return env


def _exec_capture(cmd: list[str], timeout: int = 15, cwd: Path | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, encoding="utf-8", errors="replace",
                           creationflags=_NOWIN, env=proc_env(cmd, cwd))
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 127, str(e)


def _exec_stream(cmd: list[str], log, cwd: Path | None = None) -> int:
    log("$ " + " ".join(cmd))
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                             creationflags=_NOWIN, env=proc_env(cmd, cwd))
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
def vault_is_new(v: Path) -> bool:
    """Kasa klasörü yok ya da boş (gizli girdiler sayılmaz) → yeni kasa; var olan kasaya şema sürümü DAMGALANMAZ (göç gerekebilir)."""
    return not v.exists() or not any(not e.name.startswith(".") for e in v.iterdir())


def stamp_schema(vault: Path, system: Path, log=lambda *_: None) -> bool:
    """Yeni kasaya kodun `sb/schema.py` `CURRENT` değerini `config/kasa.yaml`a `schema_version: N` olarak yazar (var olan dosyaya dokunmaz)."""
    src = system / "sb" / "schema.py"
    m = re.search(r"^CURRENT\s*=\s*(\d+)", src.read_text(encoding="utf-8"), re.M) if src.exists() else None
    target = system / "config" / "kasa.yaml"
    if not m or target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Kasa şeması — `sb migrate` yönetir, elle değiştirme.\n" f"schema_version: {m.group(1)}\n", encoding="utf-8")
    log(f"  kasa şema sürümü {m.group(1)} yazıldı")
    return True


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


CODE_ITEMS = ("sb", "app", "plugins", "tools", "tests", "skills", "integrations", "setup", "pyproject.toml", "uv.lock", ".python-version",
              "VERSION", "features.yaml")
_NO_COPY = shutil.ignore_patterns("__pycache__", "*.pyc", ".venv", "*.example.bak")


def internal_doc(name: str) -> bool:
    """Kullanıcıya gitmeyen iç belgeler: şartnameler, iş planı, deneme bulguları."""
    return name == "v1-plan.md" or "sartname" in name or "bulgulari" in name


def sync_code(src: Path, dst: Path) -> None:
    """Yalnız KOD kopyalanır (sb, app, plugins, tools, tests, skills, integrations, setup, pyproject, uv.lock, VERSION, features.yaml,
    docs/*.md kullanıcı belgeleri) + `config/*.example.yaml`. `config/*.yaml` (örnek olmayan = kişisel ayarlar), `data`, `.venv`,
    `__pycache__` ASLA kopyalanmaz; hedefte var olan dosyalara (kişisel ayarlar dahil) dokunulmaz."""
    src, dst = Path(src), Path(dst)
    if src.resolve() == dst.resolve():
        raise RuntimeError(f"Kaynak ve hedef aynı klasör: {dst} (çalışan kuruluma yazılmaz)")
    for item in CODE_ITEMS:
        s, d = src / item, dst / item
        if s.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True, ignore=_NO_COPY)
        elif s.exists():
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
    if (src / "docs").is_dir():
        (dst / "docs").mkdir(parents=True, exist_ok=True)
        for p in (src / "docs").iterdir():
            if p.is_file() and p.suffix in (".md", ".json") and not internal_doc(p.name):
                shutil.copy2(p, dst / "docs" / p.name)
    (dst / "config").mkdir(parents=True, exist_ok=True)
    for ex in (src / "config").glob("*.example.yaml"):
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


def write_plugins(system: Path, pl: dict) -> None:
    """`config/plugins.yaml`: sihirbazın 'bütün özellikler' seçimi (modül kimliği → bool, katalog maddesi → bool, sektör)."""
    y = _yaml()
    p = system / "config" / "plugins.yaml"
    data = (y.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None) or {}
    data.setdefault("modules", {}).update({k: bool(v) for k, v in (pl.get("modules") or {}).items()})
    data.setdefault("items", {}).update({str(k): bool(v) for k, v in (pl.get("items") or {}).items()})
    if pl.get("sector"):
        data["sector"] = pl["sector"]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# Seçilen özellikler (kurulum paneli yazdı): modules = manifest modülleri, items = katalog maddeleri.\n"
                 + y.safe_dump(data, allow_unicode=True, sort_keys=True), encoding="utf-8")


# ------------------------------------------------------------------ eklenti kataloğu (sb/plugins.py manifestleri)
def plugins_mod():
    """`sb.plugins` (yalnız okur, ağa çıkmaz). Kasadaki _system'den çalışmıyorsak code_dir() yola eklenir."""
    cd = code_dir()
    if cd and str(cd) not in sys.path:
        sys.path.insert(0, str(cd))
    from sb import plugins
    return plugins


def _lang(lang: str | None) -> str:
    return "en" if str(lang or "").lower().startswith("en") else "tr"


def _t(v, lang: str):
    if isinstance(v, dict):
        return v.get(lang) or v.get("tr") or v.get("en") or ""
    return v


def _loc_fields(fields: list[dict], lang: str) -> list[dict]:
    return [{**f, "label": _t(f.get("label"), lang), **({"help": _t(f["help"], lang)} if f.get("help") else {})} for f in fields or []]


def catalog(lang: str | None = "tr") -> dict:
    """GET /api/catalog: {categories, modules, sources, mcps, sectors} — arayüz bunu çizer; her şey manifestten."""
    lang, P = _lang(lang), plugins_mod()
    cats = P.categories()
    tree = {m["id"]: m for c in P.features_tree() for m in c["modules"]}
    modules = []
    for m in P.all("module"):
        t = tree.get(m["id"]) or {"items": []}
        modules.append({"id": m["id"], "name": _t(m["name"], lang), "desc": _t(m["desc"], lang), "category": m["category"],
                        "default_on": bool(m.get("default_on", True)), "roadmap": bool(m.get("roadmap")),
                        "requires": {**(m.get("requires") or {}), "fields": _loc_fields((m.get("requires") or {}).get("fields"), lang)},
                        "items": [{"id": i["id"], "name": i["ad"], "cat": m["category"], "faz": i.get("faz"), "durum": i.get("durum")}
                                  for i in t["items"]]})
    sources = [{"id": m["id"], "name": _t(m["name"], lang), "desc": _t(m["desc"], lang), "parent": m.get("parent"), "category": m.get("category"),
                "formats": m["import"]["formats"], "how_to": _t(m["import"]["how_to"], lang), "connector": m["import"].get("connector"),
                "apps": (m.get("requires") or {}).get("apps") or []} for m in P.all("source")]
    mcps = []
    for m in P.all("mcp"):
        mc = m["mcp"]
        mcps.append({"id": m["id"], "name": _t(m["name"], lang), "desc": _t(m["desc"], lang), "install": mc.get("install"),
                     "docs_url": mc.get("docs_url"), "remote": bool(mc.get("remote")),
                     "env": _loc_fields((m.get("requires") or {}).get("fields"), lang), "note": _t(mc.get("note"), lang) or "",
                     "default_on": bool(m.get("default_on", False))})
    sectors = [{"id": m["id"], "name": _t(m["name"], lang), "desc": _t(m["desc"], lang), "modules": m.get("modules") or [],
                "sources": m.get("sources") or [], "mcp": m.get("mcp") or [], "presets": m.get("presets") or {},
                "roles": [{"id": r["id"], "name": _t(r.get("name"), lang)} for r in m.get("roles") or []]} for m in P.all("sector")]
    return {"categories": [{"id": k, "name": _t(v, lang)} for k, v in cats.items()], "modules": modules, "sources": sources,
            "mcps": mcps, "sectors": sectors}


def donanim_recommendation() -> str | None:
    """Donanım taramasından 4 eksen 'donanim' değeri (taranamazsa None)."""
    try:
        hw = hardware()
        if str(hw.get("gpu") or "").startswith("Apple"):
            return "mac_apple"
        return {"full": "guclu_gpu", "medium": "orta", "small": "orta", "cloud": "zayif_bulut"}[recommend(hw)["profile"]]
    except Exception:                                         # noqa: BLE001 — tarama başarısızsa öneri yok
        return None


def presets_axes(lang: str | None = "tr") -> dict:
    lang, P = _lang(lang), plugins_mod()
    axes = {ax: [{"id": k, "name": _t(v.get("name"), lang), "desc": _t(v.get("desc"), lang)} for k, v in (P.presets()["axes"].get(ax) or {}).items()]
            for ax in P.AXES}
    rec = donanim_recommendation()
    return {"axes": axes, "recommended": {"donanim": rec} if rec else {}, "defaults": P.presets().get("defaults") or {}}


def combine_axes(body: dict) -> dict:
    P = plugins_mod()
    for ax in P.AXES:
        if body.get(ax) is not None and not isinstance(body[ax], str):
            raise ValueError(f"{ax} metin olmalı")
    ram = body.get("ram_gb")
    res = P.combine(*[body.get(ax) or None for ax in P.AXES], ram_gb=float(ram) if isinstance(ram, (int, float)) else None)
    mods = {m["id"]: bool(res["modules"].get(m["id"]) or res["extras"].get(m["id"])) for m in P.all("module")}
    items = {str(i): mods[m["id"]] for m in P.all("module") for i in m.get("catalog_ids") or []}
    chosen = [m for m in P.for_preset(**{ax: body.get(ax) or None for ax in P.AXES})]
    return {"modules": mods, "items": items, "models": res["models"], "privacy_profile": res["privacy_profile"], "warnings": res["warnings"],
            "sources": [m["id"] for m in chosen if m["type"] == "source"], "mcps": [m["id"] for m in chosen if m["type"] == "mcp"],
            "axes": res["axes"]}


def requirements_for(body: dict, lang: str | None = "tr") -> dict:
    lang, P = _lang(lang), plugins_mod()
    mods = body.get("modules") or {}
    on = [k for k, v in mods.items() if v] if isinstance(mods, dict) else [str(x) for x in mods]
    known = {m["id"] for m in P.all("module")}
    on = [k for k in on if k in known]
    srcs = [m["id"] for m in P.all("source") if m.get("parent") in on]
    srcs += [x for x in body.get("sources") or [] if isinstance(x, str) and x not in srcs and P.get(x, "source")]
    mcps = [x for x in body.get("mcps") or [] if isinstance(x, str) and P.get(x, "mcp")]
    r = P.requirements({"modules": on, "sources": srcs, "mcp": mcps})
    return {"accounts": r["accounts"], "fields": _loc_fields(r["fields"], lang), "secrets": r["secrets"], "imports": srcs, "mcps": mcps,
            "apps": r["apps"], "hardware": r["hardware"]}


# ------------------------------------------------------------------ yol denetimi ve hata ipuçları
WIN_MAX_PATH = 260
LONGEST_PKG_PATH = 150                                         # .venv içindeki en uzun paket dosyası yolu (yaklaşık)
VENV_SUFFIX = "\\_system\\.venv\\Lib\\site-packages\\"


def short_vault_suggestion() -> str:
    return str(Path.home() / "SecondBrain")


def path_warnings(vault) -> list[dict]:
    """Kasa yolu için uyarılar: Windows 260 karakter sınırı (uv sync "os error 3") ve OneDrive/eşitlenen klasör.
    [{code: long_path|onedrive, message, suggest}] — kasa yolunu engellemez, kullanıcıyı bilgilendirir."""
    out: list[dict] = []
    v = str(vault or "")
    if not v:
        return out
    if WIN and len(v) + len(VENV_SUFFIX) + LONGEST_PKG_PATH > WIN_MAX_PATH:
        sug = short_vault_suggestion()
        out.append({"code": "long_path", "suggest": sug,
                    "message": f"Kasa yolu uzun ({len(v)} karakter): Windows 260 karakter sınırı Python paketlerinin kurulumunu bozabilir. "
                               f"Daha kısa bir klasör seç, örneğin {sug}"})
    if any(part.lower().startswith("onedrive") for part in re.split(r"[\\/]", v)):     # Windows yolu macOS'ta da ayrışır
        out.append({"code": "onedrive", "suggest": short_vault_suggestion(),
                    "message": "Kasa OneDrive klasörünün içinde: eşitleme dosyaları kilitleyebilir ve kurulumu yavaşlatır/bozar. "
                               f"OneDrive dışında bir klasör öner: {short_vault_suggestion()}"})
    return out


_HINTS = {
    "vault": "Kasa klasörüne yazılamıyor olabilir. Klasörün var olduğundan ve yazma iznin olduğundan emin ol, gerekirse başka bir klasör seç; sonra «Yeniden dene».",
    "config": "Ayar dosyaları yazılamadı. Kasa klasörünün yazılabilir olduğunu ve diskte yer olduğunu kontrol et; sonra «Yeniden dene».",
    "secrets": "Şifre kasasına (keyring) yazılamadı. İşletim sisteminin şifre kasası açık mı bak; sorun sürerse sırları kurulumdan sonra uygulamadan gir; sonra «Yeniden dene».",
    "deps": "Python ortamı kurulamadı. İnternet bağlantını ve disk alanını kontrol et; sorun sürerse günlüğün son satırlarına bak. Düzelttikten sonra «Yeniden dene».",
    "claude": "Claude Code bağlantısı kurulamadı. Claude Code kurulu mu bak; bu adımı sonra uygulamadan da yapabilirsin. «Yeniden dene» ile tekrar dene.",
    "model": "Yerel model indirilemedi. Ollama çalışıyor mu ve internet var mı bak; model indirme sonra da yapılabilir. «Yeniden dene».",
    "schedule": "Zamanlayıcı kurulamadı (izin gerekebilir). Sonra elle de kurulabilir; şimdilik «Yeniden dene».",
    "git": "Kasa git deposu oluşturulamadı. git kurulu mu bak; zorunlu değil. «Yeniden dene».",
    "doctor": "Kontrol çalıştırılamadı. Python ortamı kurulduysa «Yeniden dene».",
    "shortcuts": "Kısayol oluşturulamadı. Masaüstü/Başlat klasörüne yazma iznini kontrol et; «Yeniden dene».",
}


def step_hint(step_id: str, text: str, vault=None) -> str:
    """Bir adım hata verince kullanıcıya NE OLDUĞU ve NASIL DÜZELTİLECEĞİ (Türkçe, tek paragraf)."""
    low = str(text or "").lower()
    if step_id == "deps":
        long_err = any(k in low for k in ("os error 3", "failed to persist", "path too long", "too long", "çok uzun"))
        wl = {w["code"] for w in path_warnings(vault)}
        if long_err or "long_path" in wl:
            return (f"Kasa yolu Windows'un 260 karakter sınırına takılmış olabilir. Kişisel bilgiler adımına dönüp kasayı kısa bir yola al "
                    f"(ör. {short_vault_suggestion()}), sonra «Yeniden dene».")
        if "onedrive" in wl:
            return "Kasa OneDrive içinde; eşitleme dosyaları kilitliyor olabilir. Kasayı OneDrive dışına al (Kişisel bilgiler adımı), sonra «Yeniden dene»."
        if any(k in low for k in ("network", "dns", "resolve", "timed out", "connection", "bağlan")):
            return "İnternete ulaşılamadı. Bağlantını kontrol et (VPN/proxy kapalıysa dene), sonra «Yeniden dene»."
        if "başlatılamadı" in low or "no such file" in low or "winerror 2" in low:
            return "`uv` bulunamadı. uv'yi kur (astral.sh/uv) ya da kurulum paketini yeniden indir; sonra «Yeniden dene»."
    return _HINTS.get(step_id, "Günlüğün son satırlarına bak, sorunu düzelt ve «Yeniden dene».")


# ------------------------------------------------------------------ motor
STEPS = [("vault", "Kasa ve kod"), ("config", "Ayarlar"), ("secrets", "Sırlar (şifre kasası)"), ("deps", "Python ortamı"),
         ("claude", "Claude Code bağlantısı"), ("model", "Yerel model"), ("schedule", "Zamanlayıcı"), ("git", "Kasa git deposu"),
         ("doctor", "Kontrol"), ("shortcuts", "Kısayollar")]


def _res(ok: bool, message: str) -> dict:
    return {"ok": bool(ok), "message": message}


def _trash():
    try:
        from send2trash import send2trash
        return send2trash
    except Exception:
        return None


def imap_error_message(e: BaseException, host: str = "", port: int = 993) -> str:
    """İstisna adı yerine anlaşılır Türkçe: ne oldu + ne yapmalı."""
    import socket
    import ssl
    where = f"{host}:{port}" if host else "sunucu"
    if isinstance(e, ssl.SSLError):
        return f"Güvenli bağlantı kurulamadı ({where}). IMAP için genellikle port 993 (SSL) kullanılır; sunucu ve portu kontrol et."
    if isinstance(e, socket.gaierror):
        return f"Sunucu bulunamadı: {host or 'adres'}. Sunucu adının yazımını ve internet bağlantını kontrol et."
    if isinstance(e, (socket.timeout, TimeoutError)):
        return f"Bağlanılamadı: {where} zaman aşımına uğradı. Sunucu/port yanlış olabilir ya da bir güvenlik duvarı engelliyor."
    if isinstance(e, ConnectionRefusedError):
        return f"Bağlanılamadı: {where} bağlantıyı reddetti. Sunucu adı ve port (genelde 993) doğru mu?"
    if isinstance(e, OSError):
        return f"Bağlanılamadı: {where}. İnternet bağlantını, sunucu adını ve portu kontrol et."
    txt = str(e).lower()
    if "imap4" in type(e).__module__.lower() or "imaplib" in type(e).__module__ or "authentication" in txt or "login" in txt or "credentials" in txt:
        return ("Kimlik reddedildi: kullanıcı adı ya da şifre yanlış. Gmail, iCloud ve Outlook'ta normal şifre değil UYGULAMA ŞİFRESİ gerekir "
                "(önce 2 adımlı doğrulamayı aç, sonra hesap ayarlarından uygulama şifresi üret).")
    return "IMAP girişi başarısız oldu. Sunucu, port ve şifreyi kontrol et."


def _imap_login(host: str, user: str, pw: str, port: int = 993) -> tuple[bool, str]:
    import imaplib
    try:
        m = imaplib.IMAP4_SSL(host, port, timeout=8)
        m.login(user, pw)
        m.logout()
        return True, "IMAP girişi başarılı"
    except Exception as e:
        return False, imap_error_message(e, host, port)


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
        global _sandbox_sink
        self.data = Path(data) if data else data_dir()
        self.sandbox = sandbox_dir()
        self.vault = Path(os.path.expanduser(str(vault))).resolve() if vault else None
        self.lines: deque[str] = deque(maxlen=200)
        self.steps = [{"id": i, "title": t, "status": "pending"} for i, t in STEPS]
        self.running = False
        self.error = ""
        self.error_info: dict | None = None                    # son hata kartı: {step,title,message,hint,retry}
        self.job = ""
        self._pct: int | None = None                           # yardımcı işlerde (indirme, içe aktarma) elle yüzde
        self.selection: dict = {"preset": "tam", "modules": preset_modules("tam"), "fields": {}}
        self._secrets: list[str] = []
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        if self.sandbox:
            _sandbox_sink = self.log
            self.log("[deneme] DENEME KİPİ — gerçek sisteme dokunulmuyor: " + str(self.sandbox))

    def ensure_vault(self) -> Path:
        """Kasa seçilmediyse varsayılan konumu kullan (kişisel bilgiler adımı atlanmış olabilir)."""
        if not self.vault:
            self.vault = default_vault().resolve()
        return self.vault

    # -- günlük ve ilerleme
    def log(self, msg: str) -> None:
        with self._lock:
            self.lines.append(redact(str(msg), self._secrets))

    def progress(self) -> dict:
        with self._lock:
            done = sum(1 for s in self.steps if s["status"] in ("done", "skipped"))
            pct = self._pct if self._pct is not None else round(100 * done / len(self.steps))
            return {"running": self.running, "job": self.job, "percent": pct,
                    "steps": [dict(s) for s in self.steps], "log": list(self.lines), "error": self.error,
                    "error_info": dict(self.error_info) if self.error_info else None}

    # -- yardımcı işler (model indirme, ollama kurulumu, içe aktarma, ses kurulumu): tek iş kilidi, /api/progress'te izlenir
    def run_job(self, job: str, title: str, fn, wait: bool = False) -> bool:
        """fn(set_percent) arka planda çalışır; hata mesajı sırsız `error`a yazılır. Başka iş sürüyorsa False."""
        with self._lock:
            if self.running:
                return False
            self.running, self.error, self.job, self._pct = True, "", job, 0
            self.steps = [{"id": job, "title": title, "status": "running"}]
            step = self.steps[0]

        def set_pct(p: float) -> None:
            self._pct = max(0, min(100, int(p)))

        def work():
            try:
                fn(set_pct)
                step["status"] = "done"
                self._pct = 100
            except Exception as e:                            # noqa: BLE001
                step["status"] = "error"
                self.error = redact(f"{title}: {e}", self._secrets)
                self.log("HATA: " + self.error)
            finally:
                self.running = False
        self._thread = threading.Thread(target=work, daemon=True)
        self._thread.start()
        if wait:
            self._thread.join()
        return True

    # -- sihirbaz durumu (yarıda kalanı sürdürme): sırlar buraya ASLA yazılmaz
    @property
    def wizard_file(self) -> Path:
        return self.data / "setup_wizard.json"

    def wizard(self) -> dict:
        try:
            d = json.loads(self.wizard_file.read_text(encoding="utf-8"))
            return {"step": d.get("step", 1), "data": d.get("data") or {}}
        except Exception:
            return {"step": 1, "data": {}}

    def save_wizard(self, step, data) -> dict:
        if not isinstance(data, dict):
            raise ValueError("data bir nesne olmalı")
        clean = strip_secrets(data, self._secrets)
        raw = json.dumps({"step": step if isinstance(step, (int, str)) else 1, "data": clean, "updated": time.strftime("%Y-%m-%dT%H:%M:%S")},
                         ensure_ascii=False, indent=1)
        if len(raw) > 512 * 1024:
            raise ValueError("sihirbaz verisi çok büyük")
        self.data.mkdir(parents=True, exist_ok=True)
        self.wizard_file.write_text(raw, encoding="utf-8")
        return {"step": step, "data": clean}

    # -- durum (sürdürme)
    @property
    def state_file(self) -> Path:
        return self.data / "setup_state.json"

    def public_selection(self) -> dict:
        f = {k: v for k, v in (self.selection.get("fields") or {}).items() if k not in SECRET_KEYS}
        out = {"preset": self.selection.get("preset"), "modules": self.selection.get("modules"), "fields": f}
        if self.selection.get("plugins"):
            out["plugins"] = self.selection["plugins"]
        return out

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
        pl = sel.get("plugins") if sel.get("plugins") is not None else self.selection.get("plugins")
        if isinstance(pl, dict):
            self.selection["plugins"] = {"modules": {str(k): bool(v) for k, v in (pl.get("modules") or {}).items()},
                                         "items": {str(k): bool(v) for k, v in (pl.get("items") or {}).items()},
                                         "sector": str(pl.get("sector") or "")}
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
            self.error_info = None
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
        self._pct = None
        self.steps = [{"id": i, "title": t, "status": "done" if i in done else "pending"} for i, t in STEPS]
        self._thread = threading.Thread(target=self._run_steps, args=(done,), daemon=True)
        self._thread.start()
        if wait:
            self._thread.join()
        return True

    def _run_steps(self, done: list[str]) -> None:
        try:
            try:
                for w in path_warnings(self.ensure_vault()):        # apply öncesi aynı denetim: uyar (engelleme)
                    self.log("UYARI: " + w["message"])
            except Exception:                                    # noqa: BLE001
                pass
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
                    self.error_info = {"step": step["id"], "title": step["title"], "message": redact(str(e), self._secrets),
                                       "hint": step_hint(step["id"], str(e), self.vault), "retry": True}
                    self.log("HATA: " + self.error)
                    self.log("NE YAPMALI: " + self.error_info["hint"])
                    return
                step["status"] = "skipped" if skipped else "done"
                done.append(step["id"])
                self.save_state(done)
            self.log("Kurulum bitti.")
        finally:
            self.running = False

    def _system(self) -> Path:
        return self.ensure_vault() / "_system"

    def prepare_code(self) -> None:
        """Hedef kasanın `_system`inde kod yoksa kit'ten (ya da deneme kipinde geliştirme kopyasından) kopyalar; var olana dokunmaz.
        Kurulum tamamlanmadan çalışan komutlar (içe aktarma, Google girişi, MCP) böylece HEDEF kodu kullanır."""
        t = self._system()
        if (t / "sb").is_dir():
            return
        kit = kit_dir()
        src = (kit / "system") if kit else (ROOT if self.sandbox and (ROOT / "sb").is_dir() else None)
        if not src or not (src / "sb").is_dir():
            return
        v = t.parent.resolve()
        for guard_dir in {src.resolve(), (kit or src).resolve()}:
            if v == guard_dir or guard_dir in v.parents:
                raise RuntimeError(f"Kasa kodun/kurulum paketinin içinde olamaz: {v}")
        v.mkdir(parents=True, exist_ok=True)
        sync_code(src, t)
        if kit and (kit / "setup").is_dir():
            shutil.copytree(kit / "setup", t / "setup", dirs_exist_ok=True, ignore=_NO_COPY)

    def code_root(self) -> Path:
        """sb kodunun çalışacağı klasör: HEDEF kasanın `_system`i (kod henüz yoksa kopyalanır). Deneme kipinde HER ZAMAN deneme kasasının
        `_system`i — çalışan kurulumun yolu hiçbir komutta geçmez. Hedef belli değilse (kasa seçilmedi) kit/system, yoksa bu kodun kendisi."""
        if self.sandbox or self.vault:
            t = self._system()
            if not (t / "sb").is_dir():
                self.prepare_code()
            if self.sandbox or (t / "sb").is_dir():
                return t
        k = kit_dir()
        return (k / "system") if k else (code_dir() or ROOT)

    def sb_cmd(self, *args: str) -> list[str]:
        """`sb <args>` komutu; SB_VAULT/SB_DATA ortamı başlatıcı kodla verilir (_run_* ortam parametresi almaz)."""
        boot = ("import os,sys;os.environ['SB_VAULT']=sys.argv[1];os.environ['SB_DATA']=sys.argv[2];sys.argv=['sb']+sys.argv[3:];"
                "from sb.__main__ import main;sys.exit(main())")
        return [uv_bin(), "run", "--directory", str(self.code_root()), "python", "-X", "utf8", "-c", boot,
                str(self.vault or ""), str(self.data), *args]

    def _py(self) -> list[str]:
        return [uv_bin(), "run", "--directory", str(self._system()), "python", "-X", "utf8"]

    def _step_vault(self):
        kit = kit_dir()
        if not kit and self.sandbox and (ROOT / "sb").is_dir():     # deneme kipi: kitsiz geliştirme kurulumu — kodu deneme kasasına kopyala
            v = self.ensure_vault()
            if v == ROOT or ROOT in v.parents:
                raise RuntimeError(f"Deneme kasası kodun içinde olamaz: {v}")
            new_vault = vault_is_new(v)
            v.mkdir(parents=True, exist_ok=True)
            sync_code(ROOT, self._system())
            if new_vault:
                stamp_schema(v, self._system(), self.log)
            self.data.mkdir(parents=True, exist_ok=True)
            self.log(f"  [deneme] kod kasaya kopyalandı: {self._system()}")
            return None
        if not kit:
            self.log("  kit yok (panel kasadan çalışıyor): atlandı")
            return True
        v = self.vault
        if v == kit or kit in v.parents:
            raise RuntimeError(f"Kasa kurulum paketinin içine kurulamaz: {v}")
        new_vault = vault_is_new(v)
        v.mkdir(parents=True, exist_ok=True)
        self.log(f"  şablondan {copy_missing(kit / 'vault', v)} dosya eklendi (var olanlar korundu)")
        sync_code(kit / "system", self._system())
        if new_vault:
            stamp_schema(v, self._system(), self.log)
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
        for k in ("name", "full_name", "bio", "timezone", "github_user", "workspace", "org", "role"):
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
        pl = self.selection.get("plugins")
        if pl:
            write_plugins(sysd, pl)
        cs = f.get("client_secret")
        if cs and Path(os.path.expanduser(cs)).is_file():
            dst = self.data / "secrets" / "client_secret.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(Path(os.path.expanduser(cs)), dst)
        self.log("  profil, hesaplar ve özellik seçimi yazıldı")

    def stored_secret_names(self) -> list[str]:
        """Şifre kasasında dolu olan Second Brain sırlarının ADLARI (değerleri değil)."""
        try:
            try:
                from . import accounts as A
            except ImportError:                               # engine.py doğrudan çalıştırıldı
                import accounts as A  # type: ignore
            return [s["key"] for s in A.list_secrets(self)["secrets"] if s["set"]]
        except Exception:                                     # noqa: BLE001 — keyring yoksa/engelliyse sayma
            return []

    def _step_secrets(self):
        f = self.selection["fields"]
        todo = [(fd, f[fd["key"]]) for fd in FIELDS if fd["kind"] == "secret" and f.get(fd["key"])]
        if not todo:
            have = self.stored_secret_names()
            if have:                                          # sihirbazda kaydedilenler: sayı + yalnız ADLAR (değer asla)
                self.log(f"  {len(have)} sır şifre kasasında: {', '.join(have)}")
                return None
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
        uv = install_uv(self.data)
        tail: list[str] = []

        def lg(line):
            self.log(line)
            if str(line).strip() and not str(line).startswith("$ "):
                tail.append(str(line).strip())
        if _run_stream([uv, "sync", "--inexact", "--directory", str(sysd)], lg, sysd):
            last = redact(" | ".join(tail[-3:]), self._secrets)[:300]
            raise RuntimeError("uv sync başarısız" + (f": {last}" if last else ""))
        if (sysd / "tools" / "install_cli.py").exists():
            _run_stream([uv, "run", "--directory", str(sysd), "python", str(sysd / "tools" / "install_cli.py")], self.log)

    def _step_claude(self):
        claude = which_cmd("claude")
        if not self.selection["modules"].get("claude_hooks") or not claude:
            self.log("  Claude Code kapalı ya da kurulu değil: atlandı")
            return True
        sysd = self._system()
        _run_stream([claude, "mcp", "remove", "second-brain", "-s", "user"], lambda m: None)
        _run_stream([claude, "mcp", "add", "second-brain", "--scope", "user", "--", uv_bin(), "run", "--directory", str(sysd), "python", "-m", "sb.mcp_server"], self.log)

    def _step_model(self):
        if not PRESETS.get(self.selection["preset"], {}).get("local_model", True) or not which_cmd("ollama"):
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
            _run_stream(self._py() + [str(sysd / "tools" / "schedule_macos.py")], self.log)      # paketli Setup'ta sys.executable uygulamanın kendisi
        else:
            self.log("  otomatik zamanlayıcı yok (cron ile `sb daily` / `sb weekly` kur)")
            return True

    def _step_git(self):
        v = self._system().parent
        if not shutil.which("git") or (v / ".git").exists():
            self.log("  git yok ya da kasa zaten depo: atlandı")
            return True
        if self.sandbox and not (v / ".gitignore").exists():
            (v / ".gitignore").write_text(".venv/\n__pycache__/\n*.pyc\n", encoding="utf-8")
        ident = ["-c", "user.name=Second Brain", "-c", "user.email=sb@localhost"] if self.sandbox else []
        def lg(line):                                         # satır sonu uyarıları (yüzlerce satır) günlüğü ve hata ipuçlarını boğmasın
            if "working copy" in str(line) and "will be replaced by" in str(line):
                return
            self.log(line)
        for cmd in (["git", "init", "-b", "main"], ["git", "add", "-A"], ["git", *ident, "commit", "-q", "-m", "Second Brain kurulumu"]):
            _run_stream(cmd, lg, v)

    def _step_doctor(self):
        h = self.health()
        self.log("  " + (h.get("summary") or h.get("message", "")))

    def _step_shortcuts(self):
        """Uygulama başlatıcısını kur + masaüstü ve Başlat menüsü (macOS: ~/Applications) kısayolu `Second Brain`."""
        plat = sys.platform
        if plat not in ("win32", "darwin"):
            self.log("  bu sistemde kısayol yok: atlandı")
            return True
        try:
            from . import autostart
        except ImportError:                                   # engine.py doğrudan çalıştırıldı
            import autostart  # type: ignore
        installed = install_launcher(self.data, plat)
        if plat == "darwin":
            if installed:
                self.log(f"  uygulama kuruldu: {installed}")
            else:
                dest = make_stub_app(launcher_path(self.data, plat), self.code_root())
                self.log(f"  başlatıcı uygulama yazıldı: {dest}")
            self.log("  " + install_cli_shim(self._system(), self.vault, self.data, plat, sandbox=bool(self.sandbox)))
            return
        prog, args, cwd = autostart.launch_command(self, False, plat)
        rc, out = _run_capture(["powershell", "-NoProfile", "-Command", shortcut_script(prog, args, cwd)], 30)
        if rc != 0:
            raise RuntimeError("kısayol oluşturulamadı: " + out.strip()[:200])
        self.log(f"  masaüstü + Başlat menüsü kısayolu: {APP_NAME} → {prog}")
        self.log("  " + install_cli_shim(self._system(), self.vault, self.data, plat, sandbox=bool(self.sandbox)))

    # -- özet ekranı için ayrıntılı durum (sırlar: yalnız ADLAR)
    def summary(self) -> dict:
        try:
            from . import accounts as A
            from . import imports as IM
            from . import mcp as M
        except ImportError:                                   # engine.py doğrudan çalıştırıldı
            import accounts as A  # type: ignore
            import imports as IM  # type: ignore
            import mcp as M  # type: ignore
        out: dict = {"vault": str(self.vault or default_vault()), "sandbox": str(self.sandbox or ""),
                     "timezone": (self.selection.get("fields") or {}).get("timezone") or "", "accounts": {"google": [], "imap": [], "school": None},
                     "secrets": [], "mcps": [], "imports": [], "models": []}
        try:
            acc = A._read_accounts(self)
            out["accounts"] = {"google": [{"alias": a, "email": v.get("email")} for a, v in acc["google"].items()],
                               "imap": [{"alias": a, "email": v.get("email")} for a, v in acc["imap"].items()],
                               "school": ({"url": acc["school"].get("url", ""), "user": acc["school"].get("user", "")}
                                          if isinstance(acc.get("school"), dict) else None)}
        except Exception:                                     # noqa: BLE001
            pass
        out["secrets"] = self.stored_secret_names()
        try:
            out["mcps"] = sorted({i["name"] for i in M.installed()})
        except Exception:                                     # noqa: BLE001
            pass
        try:
            out["imports"] = [x for x in IM.history(self)["imports"] if x.get("ok")]
        except Exception:                                     # noqa: BLE001
            pass
        try:
            out["models"] = [m["name"] for m in A.ollama_info().get("models", [])]
        except Exception:                                     # noqa: BLE001
            pass
        return out

    # -- sağlık
    def health(self) -> dict:
        sysd = self._system() if (self.vault or self.sandbox) else (code_dir() or ROOT)
        if not (sysd / "sb").is_dir():
            return {"ok": False, "rows": [], "summary": "", "message": "sb henüz kurulu değil"}
        rc, out = _run_capture([uv_bin(), "run", "--directory", str(sysd), "python", "-X", "utf8", "-m", "sb", "doctor"], 120)
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
    def _keyring_secret_names(self) -> list[str]:
        """Anahtar zincirinde kalmış Second Brain sırları (vault-key HARİÇ). Yalnız değeri dolu olanlar."""
        kr = _keyring()
        if not kr:
            return []
        aliases = {"is", _alias(self.selection.get("fields") or {}) if getattr(self, "selection", None) else "is"}
        cands = []
        for fd in FIELDS:
            if fd["kind"] == "secret" and fd.get("keyring"):
                for al in aliases:
                    cands.append(fd["keyring"].format(imap_alias=al))
        cands += ["push-vapid-private"]
        out = []
        for n in dict.fromkeys(cands):
            try:
                if n != "vault-key" and kr.get_password(KEYRING_SERVICE, n):
                    out.append(n)
            except Exception:
                continue
        return out

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
        names = self._keyring_secret_names()
        if names:
            acts.append({"id": "secrets", "auto": True, "names": names,
                         "desc": "Şifre kasasındaki (keyring) sırları sil: " + ", ".join(names)})
        kr = _keyring()
        try:
            has_vk = bool(kr and kr.get_password(KEYRING_SERVICE, "vault-key"))
        except Exception:
            has_vk = False
        if has_vk:
            acts.append({"id": "vault_key", "auto": False,
                         "desc": "UYARI: 'vault-key' (kasa şifreleme anahtarı) SİLİNMEZ. Şifreli .md.enc notların tek anahtarıdır; "
                                 "silinirse notlar açılamaz. Önce `sb vault-key --export <dosya>` ile yedekle, gerekirse elle sil."})
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
            elif a["id"] == "secrets":
                kr = _keyring()
                removed = []
                for n in a.get("names", []):
                    if n == "vault-key":                         # asla
                        continue
                    try:
                        kr.delete_password(KEYRING_SERVICE, n)
                        removed.append(n)
                    except Exception:
                        pass
                done.append("secrets")
                pass
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
    sel["fields"].setdefault("vault", str(default_vault()))
    sel["fields"].setdefault("name", default_name())
    eng = Engine()
    eng.apply(sel, resume=a.resume, wait=True)
    print("\n".join(eng.progress()["log"]))
    return 1 if eng.error else 0


if __name__ == "__main__":
    sys.exit(main())
