"""Second Brain Kit kurucusu (Windows + macOS). install.ps1 / install.sh bunu çağırır:

    uv run --no-project --python 3.12 --with pyyaml install.py [--vault YOL] [--answers cevaplar.json]

Adımlar (her biri tekrar çalıştırılabilir; var olan notlarına ve ayarlarına dokunmaz):
 1. Profil soruları (ad, kasa yeri, saat dilimi, GitHub, proje klasörü)
 2. Kasa: şablondan oluşturulur (varsa yalnız eksik dosyalar eklenir); kod kasa/_system'e kopyalanır
 3. Ayarlar: config/*.example.yaml → config/*.yaml (+ profil ve hesaplar cevaplarınla)
 4. Python ortamı (uv sync)
 5. Google OAuth istemcisi (client_secret.json) + hesap girişleri; IMAP şifreleri (işletim sistemi şifre kasasına)
 6. Claude Code: MCP sunucusu + hafıza kancaları + 365 gün sohbet saklama + genel talimat
 7. Yerel model (Ollama: qwen3:14b, isteğe bağlı görsel model)
 8. Zamanlayıcı (Windows Görev Zamanlayıcı / macOS launchd)
 9. Kasada git deposu
10. sb doctor ile kontrol
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parent
WIN, MAC = sys.platform == "win32", sys.platform == "darwin"
DATA = Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain")
ANSWERS: dict = {}
AUTO = False


def say(msg: str = "") -> None:
    print(msg, flush=True)


def head(n: int, title: str) -> None:
    say(f"\n=== {n}. {title} ===")


def ask(key: str, prompt: str, default: str = "") -> str:
    if key in ANSWERS:
        return str(ANSWERS[key]).strip() or default          # boş cevap → varsayılan (boş yol kasayı yanlış yere kurmasın)
    if AUTO:
        return default
    v = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return v or default


def yes(key: str, prompt: str, default: bool = True) -> bool:
    if key in ANSWERS:
        return bool(ANSWERS[key])
    if AUTO:
        return default
    v = input(f"{prompt} [{'E/h' if default else 'e/H'}]: ").strip().lower()
    return default if not v else v.startswith(("e", "y"))


def run(cmd: list[str], cwd: Path | None = None, check: bool = False) -> int:
    say("  $ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=check).returncode


def copy_missing(src: Path, dst: Path) -> int:
    """src ağacını dst'ye kopyala; var olan dosyaların üzerine YAZMA (kullanıcının notları korunur)."""
    n = 0
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        t = dst / p.relative_to(src)
        if not t.exists():
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, t)
            n += 1
    return n


def sync_code(src: Path, dst: Path) -> None:
    """Kodu (sb/, tools/, tests/, docs/, pyproject, kit örnek ayarları) güncelle; config/*.yaml (kişisel) korunur."""
    for item in ("sb", "tools", "tests", "docs", "skills", "integrations", "setup", "pyproject.toml", "uv.lock", ".python-version", "VERSION", "features.yaml"):
        s, d = src / item, dst / item
        if not s.exists():
            continue
        if s.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(s, d)
    (dst / "config").mkdir(parents=True, exist_ok=True)
    for ex in (src / "config").glob("*"):
        if ex.name.endswith(".example.yaml") or not (dst / "config" / ex.name).exists():
            shutil.copy2(ex, dst / "config" / ex.name)


def remember(vault: Path) -> None:
    """sb update'in kiti ve kasayı bulabilmesi için (yerel veri klasöründe, kasada değil)."""
    DATA.mkdir(parents=True, exist_ok=True)
    ver = (KIT / "system" / "VERSION").read_text(encoding="utf-8").strip() if (KIT / "system" / "VERSION").exists() else "?"
    (DATA / "kit.json").write_text(json.dumps({"kit": str(KIT), "vault": str(vault), "version": ver}, ensure_ascii=False, indent=1),
                                   encoding="utf-8")


def update(vault: Path) -> int:
    """`sb update` buradan geçer: soru sormadan yalnız kodu yeniler (notlara ve config/*.yaml'a dokunmaz)."""
    system = vault / "_system"
    if not system.exists():
        raise SystemExit(f"Kasa bulunamadı: {vault}")
    n = copy_missing(KIT / "vault", vault)
    sync_code(KIT / "system", system)
    say(f"  kod güncellendi: {system} (şablondan {n} yeni dosya)")
    run(["uv", "sync"], cwd=system)
    run(["uv", "run", "--directory", str(system), "python", str(system / "tools" / "install_cli.py")])
    py = system / ".venv" / ("Scripts/python.exe" if WIN else "bin/python")
    if (Path.home() / ".claude" / "skills").exists() or shutil.which("claude"):
        run([str(py), str(system / "tools" / "install_skills.py")])
    if WIN and (system / "tools" / "hotkey.ps1").exists():
        run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(system / "tools" / "hotkey.ps1")])
    remember(vault)
    run(["uv", "run", "--directory", str(system), "python", "-X", "utf8", "-m", "sb", "doctor"])
    return 0


def write_yaml(path: Path, data: dict, header: str = "") -> None:
    path.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def main() -> int:
    global ANSWERS, AUTO
    for stream in (sys.stdout, sys.stderr):              # Türkçe karakterler eski kod sayfalı konsolda çökmesin
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Second Brain Kit kurucusu")
    ap.add_argument("--vault", help="kasa klasörü (varsayılan ~/SecondBrain)")
    ap.add_argument("--answers", help="soruların cevapları (JSON) — otomatik/test kurulumu")
    ap.add_argument("--yes", action="store_true", help="sorulmayanlarda varsayılanı seç")
    ap.add_argument("--update", action="store_true", help="yalnız kodu güncelle (sb update çağırır)")
    a = ap.parse_args()
    if a.update:
        return update(Path(os.path.expanduser(a.vault or Path.home() / "SecondBrain")).resolve())
    if a.answers:
        ANSWERS = json.loads(Path(a.answers).read_text(encoding="utf-8"))
    AUTO = a.yes or bool(a.answers)

    say("Second Brain Kit kurulumu — Obsidian kasası + yerel arşiv + yerel asistan + Claude Code hafızası")
    say("Her adım tekrar çalıştırılabilir; var olan notlarına dokunulmaz. Ctrl+C ile istediğin an çıkabilirsin.")

    head(1, "Profil")
    name = ask("name", "Asistan sana nasıl hitap etsin (ad)", os.environ.get("USERNAME") or os.environ.get("USER") or "Kullanıcı")
    full = ask("full_name", "Adın soyadın", name)
    bio = ask("bio", "Kendini bir cümleyle anlat (okul/bölüm/iş)", "")
    tz = ask("timezone", "Saat dilimi", "Europe/Istanbul")
    gh = ask("github_user", "GitHub kullanıcı adın (yoksa boş bırak)", "")
    ws = ask("workspace", "Kod projelerinin durduğu klasör", "~/Projects")
    vault = Path(os.path.expanduser(a.vault or ask("vault", "Kasa (Obsidian vault) nerede olsun", str(Path.home() / "SecondBrain"))))
    vault = vault.resolve()
    if vault == KIT or KIT in vault.parents:
        raise SystemExit(f"Kasa kurulum paketinin içine kurulamaz: {vault}. Başka bir klasör seç (ör. ~/SecondBrain).")

    head(2, f"Kasa: {vault}")
    vault.mkdir(parents=True, exist_ok=True)
    n = copy_missing(KIT / "vault", vault)
    say(f"  şablondan {n} dosya eklendi (var olanlar korundu)")
    system = vault / "_system"
    sync_code(KIT / "system", system)
    say(f"  kod güncellendi: {system}")

    head(3, "Ayarlar")
    cfg = system / "config"
    for ex in cfg.glob("*.example.yaml"):
        real = cfg / ex.name.replace(".example", "")
        if not real.exists():
            shutil.copy2(ex, real)
            say(f"  oluşturuldu: config/{real.name}")
    prof = yaml.safe_load((cfg / "profile.yaml").read_text(encoding="utf-8")) or {}
    prof.update({"name": name, "full_name": full, "bio": bio, "timezone": tz, "github_user": gh, "workspace": ws})
    write_yaml(cfg / "profile.yaml", prof, "# Kişi profili (install.py yazdı; elle düzenleyebilirsin)\n")
    acc = yaml.safe_load((cfg / "accounts.yaml").read_text(encoding="utf-8")) or {}
    gmail = ask("gmail", "Ana Gmail adresin (mail + takvim + rehber + Drive için)", (acc.get("google") or {}).get("main", {}).get("email", ""))
    if gmail and "@" in gmail:
        acc.setdefault("google", {}).setdefault("main", {"source": "gmail-main", "scopes": ["gmail", "calendar", "contacts", "drive"]})
        acc["google"]["main"]["email"] = gmail
        acc.setdefault("notify", {}).setdefault("to", [])
        if not acc["notify"]["to"]:
            acc["notify"]["to"] = [gmail]
    write_yaml(cfg / "accounts.yaml", acc, "# Hesaplar (gizli bilgi YOK). Ek Gmail/IMAP için accounts.example.yaml'daki örneklere bak.\n")
    say("  profil ve hesaplar yazıldı (config/profile.yaml, config/accounts.yaml)")

    head(4, "Python ortamı (uv sync) + `sb` komutu")
    run(["uv", "sync"], cwd=system)
    run(["uv", "run", "--directory", str(system), "python", str(system / "tools" / "install_cli.py")])
    sb = ["uv", "run", "--directory", str(system), "python", "-X", "utf8", "-m", "sb"]

    head(5, "Google bağlantısı")
    secret = DATA / "secrets" / "client_secret.json"
    if not secret.exists():
        say("  Google Cloud'da bir OAuth istemcisi gerekir (5 dk, ücretsiz): docs/KURULUM-GOOGLE.md")
        p = ask("client_secret", "İndirdiğin client_secret...json dosyasının yolu (şimdilik atlamak için boş)", "")
        if p and Path(os.path.expanduser(p)).exists():
            secret.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(os.path.expanduser(p)), secret)
            say(f"  kopyalandı → {secret} (kasaya/git'e girmez)")
    if secret.exists() and gmail and yes("google_login", "Şimdi Google'a giriş yapılsın mı (tarayıcı açılır)?"):
        run(sb + ["login", "main"])
    for alias in (acc.get("imap") or {}):
        if yes(f"imap_{alias}", f"IMAP '{alias}' şifresi şimdi girilsin mi?"):
            run(sb + ["set-secret", f"imap-{alias}"])

    head(6, "Claude Code bağlantısı")
    claude = shutil.which("claude")
    if not claude:
        say("  Claude Code bulunamadı (claude.com/code). Kurduktan sonra bu kurucuyu tekrar çalıştır.")
    elif yes("claude", "Claude Code'a MCP sunucusu + hafıza kancaları eklensin mi?"):
        subprocess.run([claude, "mcp", "remove", "second-brain", "-s", "user"], capture_output=True)
        run([claude, "mcp", "add", "second-brain", "--scope", "user", "--", "uv", "run", "--directory", str(system), "python", "-m", "sb.mcp_server"])
        py = system / ".venv" / ("Scripts/python.exe" if WIN else "bin/python")
        hook = system / "tools" / "cc_hook.py"
        st = Path.home() / ".claude" / "settings.json"
        cur = json.loads(st.read_text(encoding="utf-8")) if st.exists() else {}
        if st.exists():
            shutil.copy2(st, st.with_suffix(".json.bak"))
        cur["cleanupPeriodDays"] = max(int(cur.get("cleanupPeriodDays", 30)), 365)
        hooks = cur.setdefault("hooks", {})
        for ev, arg, to in (("SessionStart", "start", 20), ("UserPromptSubmit", "prompt", 10), ("PreCompact", "precompact", 10),
                            ("SessionEnd", "end", 10)):
            lst = [h for h in hooks.get(ev, []) if "cc_hook.py" not in json.dumps(h)]
            lst.append({"hooks": [{"type": "command", "command": py.as_posix(), "args": ["-X", "utf8", hook.as_posix(), arg], "timeout": to}]})
            hooks[ev] = lst
        if "statusLine" not in cur or "statusline.py" in json.dumps(cur.get("statusLine")):
            cur["statusLine"] = {"type": "command", "command": f"{py.as_posix()} -X utf8 {(system / 'tools' / 'statusline.py').as_posix()}",
                                 "padding": 0}
        st.parent.mkdir(parents=True, exist_ok=True)
        st.write_text(json.dumps(cur, indent=2, ensure_ascii=False), encoding="utf-8")
        say(f"  kancalar, durum çubuğu ve 365 gün saklama yazıldı ({st}; yedek: settings.json.bak)")
        run([str(py), str(system / "tools" / "install_skills.py")])
        gmd = Path.home() / ".claude" / "CLAUDE.md"
        snippet = (KIT / "claude-global.md").read_text(encoding="utf-8").replace("{{VAULT}}", str(vault)).replace("{{NAME}}", name)
        if "<!-- second-brain-kit -->" not in (gmd.read_text(encoding="utf-8") if gmd.exists() else ""):
            if yes("claude_md", "Claude Code genel talimatlarına (~/.claude/CLAUDE.md) 'önce beyne bak' kuralı eklensin mi?"):
                with gmd.open("a", encoding="utf-8") as f:
                    f.write("\n" + snippet)

    head(7, "Yerel model (Ollama)")
    if shutil.which("ollama"):
        if yes("ollama_pull", "qwen3:14b indirilsin mi (~9 GB; asistan + yerel özetler)?"):
            run(["ollama", "pull", "qwen3:14b"])
        if yes("ollama_vl", "Görsel model qwen3-vl:8b indirilsin mi (~6 GB; ekran/kamera anlatma)?", False):
            run(["ollama", "pull", "qwen3-vl:8b"])
    else:
        say("  Ollama yok: ollama.com'dan kur (16 GB ekran kartı önerilir; daha azsa llm.yaml'da qwen3:4b seç).")

    head(8, "Zamanlayıcı (günlük güncelleme, haftalık denetim, asistan sunucusu)")
    if yes("schedule", "Zamanlanmış görevler kurulsun mu?"):
        if WIN:
            run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(system / "tools" / "schedule.ps1")])
        elif MAC:
            run([sys.executable, str(system / "tools" / "schedule_macos.py")])
        else:
            say("  Linux: cron/systemd ile `sb daily` (13:00), `sb weekly` (Pazar), `sb chat` (oturum açılışı) kur.")

    head(9, "Kasa git deposu")
    if shutil.which("git") and not (vault / ".git").exists() and yes("git", "Kasada git deposu açılsın mı (her değişiklik geri alınabilir)?"):
        run(["git", "init", "-b", "main"], cwd=vault)
        run(["git", "add", "-A"], cwd=vault)
        run(["git", "commit", "-q", "-m", "Second Brain Kit kurulumu"], cwd=vault)
        say("  Yedek için GitHub'da ÖZEL bir repo açıp: git remote add origin <adres> && git push -u origin main")

    remember(vault)
    head(10, "Kontrol (sb doctor)")
    run(sb + ["doctor"])
    say(f"\nBitti. Obsidian'da '{vault}' klasörünü kasa olarak aç. Sonraki adımlar: README.md › 'Kurulumdan sonra'.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say("\nİptal edildi. Kurucuyu tekrar çalıştırdığında kaldığın yerden devam eder.")
        sys.exit(1)
