"""`sb doctor`: kurulumun her parçasını kontrol eder, eksikse ne yapılacağını söyler. Hiçbir şey değiştirmez.

✓ hazır · ! isteğe bağlı/eksik ama sistem çalışır · ✗ çalışması için gerekli
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from .config import CLIENT_SECRET, DATA, KEYRING_SERVICE, MAIL_DB, SYSTEM, VAULT

OK, WARN, FAIL = "✓", "!", "✗"


def _kr(name: str) -> bool:
    try:
        import keyring
        return bool(keyring.get_password(KEYRING_SERVICE, name))
    except Exception:
        return False


def _http(url: str, timeout: int = 3) -> int:
    try:
        return urllib.request.urlopen(url, timeout=timeout).status
    except Exception:
        return 0


BACKUP_MAX_DAYS = 14


def backup_check() -> tuple[str, str, str]:
    """Son tüm-kasa yedeğinin yaşı: 14 günden eskiyse (ya da hiç yoksa) ✗."""
    try:
        from . import privacy
        lb = privacy.last_backup()
    except Exception as e:                                       # noqa: BLE001
        return WARN, "Kasa yedeği kontrol edilemedi", str(e)[:80]
    if lb is None:
        return FAIL, "Kasa yedeği: hiç yok", "sb backup (haftalık görev SecondBrain-Weekly de alır); anahtarı da yedekle: sb vault-key --export <dosya>"
    days = lb["age_days"]
    label = f"Kasa yedeği: {days:.0f} gün önce ({lb['name']}{'' if lb['encrypted'] else ', ŞİFRESİZ'})"
    return (OK if days <= BACKUP_MAX_DAYS else FAIL), label, "haftalık görev çalışmıyor olabilir (SecondBrain-Weekly); elle: sb backup"


def schema_check() -> tuple[str, str, str]:
    """Kasa şema sürümü kodla uyumlu mu: gerideyse ✗ (sb migrate), kodun ilerisindeyse ✗ (eski kod + yeni kasa)."""
    from . import schema
    try:
        st = schema.status()
    except Exception as e:                                       # noqa: BLE001
        return WARN, "Kasa şema sürümü kontrol edilemedi", str(e)[:80]
    if st["state"] == "ok":
        return OK, st["message"], ""
    if st["state"] == "behind":
        return FAIL, st["message"], "sb migrate --check (ne değişecek), sonra sb migrate --yes"
    if st["state"] == "ahead":
        return FAIL, st["message"], "sb update (kodu güncelle); kasaya yazma işlemleri yapma"
    return FAIL, st["message"], "_system/config/kasa.yaml içindeki schema_version değerini düzelt (sayı olmalı)"


def checks() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []

    def add(status, name, hint=""):
        out.append((status, name, hint))

    cfg = SYSTEM / "config"
    add(OK if (cfg / "profile.yaml").exists() else FAIL, "Profil (config/profile.yaml)", "install.py'yi çalıştır ya da profile.example.yaml'ı kopyala")
    add(OK if (cfg / "accounts.yaml").exists() else FAIL, "Hesaplar (config/accounts.yaml)", "accounts.example.yaml'ı kopyala ve doldur")
    for name in ("mail_rules", "llm", "local_files", "course_files"):
        add(OK if (cfg / f"{name}.yaml").exists() else WARN, f"Ayar {name}.yaml", f"{name}.example.yaml'dan kopyala")
    add(OK if (VAULT / ".obsidian").exists() else WARN, f"Obsidian kasası ({VAULT})", "Obsidian'da 'Open folder as vault' ile bu klasörü aç")
    add(OK if CLIENT_SECRET.exists() else FAIL, "Google OAuth istemcisi (client_secret.json)", f"docs/KURULUM-GOOGLE.md → {CLIENT_SECRET}")
    try:
        from .config import accounts
        acc = accounts()
        for alias in acc.get("google") or {}:
            add(OK if _kr(f"google:{alias}") else FAIL, f"Google girişi: {alias}", f"sb login {alias}")
        for alias in acc.get("imap") or {}:
            add(OK if _kr(f"imap-{alias}") else FAIL, f"IMAP şifresi: {alias}", f"sb set-secret imap-{alias}")
        to = (acc.get("notify") or {}).get("to") or []
        add(OK if to else WARN, "Sabah özeti maili", "accounts.yaml notify.to + smtp (yoksa özet yalnız kasada)")
    except Exception as e:
        add(FAIL, "accounts.yaml okunamadı", str(e)[:80])
    add(OK if MAIL_DB.exists() else WARN, f"Yerel arşiv ({MAIL_DB})", "ilk `sb daily` ya da `sb mail-fetch main` oluşturur")
    # yerel model
    o = _http("http://localhost:11434/api/tags")
    add(OK if o else WARN, "Ollama (yerel model)", "ollama.com'dan kur; asistan ve yerel özetler için gerekli")
    if o:
        try:
            tags = {m["name"] for m in json.load(urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3))["models"]}
            from .llm import config as llm_config
            lc = llm_config()["ollama"]
            for m in (lc["model"], lc.get("vision_model")):
                if m:
                    add(OK if m in tags else WARN, f"Model {m}", f"ollama pull {m}")
        except Exception:
            pass
    try:
        from . import models as _models
        _hw = _models.hardware()
        add(OK, f"Donanım: RAM {_hw['ram_gb'] or '?'} GB, GPU {_hw['gpu'] or 'yok'}, VRAM {_hw['vram_gb'] if _hw['vram_gb'] is not None else '?'} GB (önerilen profil: {_models.recommend(_hw)['profile']})",
            f"önerilen profil: {_models.recommend(_hw)['profile']} (sb models)")
    except Exception:
        pass
    # bulut API sağlayıcıları (llm.yaml'da "<sağlayıcı>:<model>" ile kullanılanlar)
    try:
        from . import providers
        from .llm import config as llm_config
        used = sorted({str(v).split(":", 1)[0] for v in (llm_config().get("tasks") or {}).values() if ":" in str(v)} - {"ollama", "claude"})
        for prov in used:
            add(OK if providers.has_key(prov) else WARN, f"API anahtarı: {prov}", f"sb set-secret api-{prov} (ya da ortam değişkeni)")
    except Exception as e:
        add(WARN, "Sağlayıcı kontrolü yapılamadı", str(e)[:80])
    # Claude Code
    claude = shutil.which("claude")
    add(OK if claude else WARN, "Claude Code (claude)", "claude.com/code — derin derleme ve MCP için")
    if claude:
        r = subprocess.run([claude, "mcp", "list"], capture_output=True, text=True, timeout=60)
        add(OK if "second-brain" in (r.stdout or "") else WARN, "MCP: second-brain", "install.py adım 'Claude Code bağlantısı'")
        st = Path.home() / ".claude" / "settings.json"
        hooks = st.exists() and "cc_hook.py" in st.read_text(encoding="utf-8")
        add(OK if hooks else WARN, "Claude Code hafıza kancaları", "install.py yeniden çalıştır")
    # zamanlayıcı
    if sys.platform == "win32":
        r = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-ScheduledTask -TaskName 'SecondBrain-*').TaskName -join ','"],
                           capture_output=True, text=True, timeout=30)
        names = r.stdout or ""
        for t in ("SecondBrain-Daily", "SecondBrain-Weekly", "SecondBrain-Chat"):
            add(OK if t in names else WARN, f"Zamanlanmış görev {t}", "powershell -ExecutionPolicy Bypass -File _system/tools/schedule.ps1")
    elif sys.platform == "darwin":
        r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
        for t in ("daily", "weekly", "chat"):
            add(OK if f"com.secondbrain.{t}" in (r.stdout or "") else WARN, f"launchd com.secondbrain.{t}", "python3 _system/tools/schedule_macos.py")
    if sys.platform == "win32":
        import os
        lnk = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Beyne at.lnk"
        add(OK if lnk.exists() else WARN, "Beyne at kısayolu (Ctrl+Alt+B)", "powershell -ExecutionPolicy Bypass -File _system/tools/hotkey.ps1")
    add(OK if _http("http://127.0.0.1:8765/") else WARN, "Asistan sunucusu (127.0.0.1:8765)", "zamanlayıcıyı kur ya da `sb chat`")
    from .spotify_api import client_id
    add(OK if client_id() and _kr("spotify-refresh") else WARN, "Spotify doğrudan çalma (isteğe bağlı)", "docs/KURULUM-SPOTIFY.md")
    add(OK if (DATA / "remote_tokens.json").exists() else WARN, "Telefon erişimi (isteğe bağlı, Tailscale)", "docs/KURULUM-TELEFON.md")
    from .update import PENDING
    if PENDING.exists():
        add(FAIL, "Yarım kalan güncelleme", "sb update --recover (ya da sb update --rollback)")
    codex = shutil.which("codex")
    add(OK if codex else WARN, "Codex (isteğe bağlı alt ajan)", "npm i -g @openai/codex ve codex login")
    out.append(backup_check())
    out.append(schema_check())
    gitdir = VAULT / ".git"
    add(OK if gitdir.exists() else WARN, "Kasa git deposu (geri alma + yedek)", "cd kasa && git init (özel GitHub reposuna bağla)")
    return out


def run() -> int:
    rows = checks()
    for st, name, hint in rows:
        print(f" {st} {name}" + (f"   → {hint}" if st != OK and hint else ""))
    fails = sum(1 for r in rows if r[0] == FAIL)
    from .update import version
    print(f"\nSürüm {version()} · {len(rows)} kontrol: {sum(1 for r in rows if r[0] == OK)} hazır, "
          f"{sum(1 for r in rows if r[0] == WARN)} isteğe bağlı/eksik, {fails} gerekli eksik.")
    return 1 if fails else 0
