"""Claude Code hafıza kancaları (kullanıcı geneli, her proje): oturum başında Second Brain'den kısa bağlam enjekte eder.

Kullanım (~/.claude/settings.json hooks): python cc_hook.py start | prompt | precompact | end   (stdin: kanca JSON'u)
- start     : kurallar (projeye kapsamlı olanlar süzülür), hafıza, açık konular, son oturum kartları, bu klasörün projesi
              (+ projenin "## Kurallar" bölümü), yaklaşan tarihler, uyarılar (kartsız kapanan oturum).
              Bütçe config/hafiza.yaml: normal 9.500 / ekonomik 4.000 karakter / manuel yalnız uyarı.
- prompt    : mesaj sayacı; 15 (ekonomikte 30) mesajda bir "kart/makbuz" hatırlatması; ilk mesajda paralel oturum uyarısı.
- precompact: konuşma sıkıştırılmadan önce yerel model özetini ARKA PLANDA günlük nota yazdırır (sb hook-flush).
- end       : kartı/makbuzu yazılmadan biten ≥4 mesajlık oturumu arka planda özetletir + sonraki açılışta uyarır.
Kancanın kendisi model çağırmaz, ağa çıkmaz, beklemez; hata olursa sessizce çıkar. SB_NO_HOOK=1 iken hiçbir şey yapmaz.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
STATE = Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain") / "hooks"
CARDS = VAULT / "Son oturum.md"
THREADS = VAULT / "Açık konular.md"
RULES = VAULT / "Asistan kuralları.md"
MEMORY = VAULT / "Asistan hafızası.md"
WORKSPACE = Path.home() / "Workspace" / "projects"   # profil (workspace) okunursa aşağıda değişir
BUDGET = 10_000
NUDGE_EVERY = 15
PARALLEL_HOURS = 12


def _user() -> str:
    """Profil adı (config/profile.yaml); kanca paket dışında çalıştığı için doğrudan okunur."""
    try:
        import yaml
        cfg = VAULT / "_system" / "config"
        for n in ("profile.yaml", "profile.example.yaml"):
            if (cfg / n).exists():
                return str((yaml.safe_load((cfg / n).read_text(encoding="utf-8")) or {}).get("name") or "kullanıcı")
    except Exception:
        pass
    return "kullanıcı"


def _profile_value(key: str, default: str) -> str:
    try:
        import yaml
        cfg = VAULT / "_system" / "config"
        for n in ("profile.yaml", "profile.example.yaml"):
            if (cfg / n).exists():
                return str((yaml.safe_load((cfg / n).read_text(encoding="utf-8")) or {}).get(key) or default)
    except Exception:
        pass
    return default


def _settings() -> dict:
    defaults = {"profile": "normal", "context_chars": 9500, "economy_chars": 4000, "parallel_warning": True, "flush_min_prompts": 4}
    try:
        import yaml
        cfg = VAULT / "_system" / "config"
        for n in ("hafiza.yaml", "hafiza.example.yaml"):
            if (cfg / n).exists():
                return {**defaults, **(yaml.safe_load((cfg / n).read_text(encoding="utf-8")) or {})}
    except Exception:
        pass
    return defaults


USER = _user()
WORKSPACE = Path(os.path.expanduser(_profile_value("workspace", str(WORKSPACE))))


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


SCOPE_RE = re.compile(r"\[(?:kapsam|scope):\s*([^\]]+)\]", re.I)


def _in_scope(line: str, project: str) -> bool:
    """`[kapsam: a, b]` etiketli kural yalnız o projelerde; etiketsiz ya da genel/global her yerde."""
    m = SCOPE_RE.search(line)
    if not m:
        return True
    names = {x.strip().lower() for x in m.group(1).split(",")}
    return bool(names & {"genel", "global"}) or (project.lower() in names if project else False)


def _bullets(p: Path, cap: int, project: str = "") -> str:
    text = "\n".join(l for l in _read(p).splitlines() if l.startswith("- ") and _in_scope(l, project))
    return text if len(text) <= cap else text[:cap].rsplit("\n", 1)[0] + f"\n[kırpıldı — tamamı: {p.name}]"


def _section(text: str, heading: str) -> str:
    m = re.search(rf"^(#{{2,3}}) {re.escape(heading)}\s*\n(.*?)(?=^#{{2,3}} |\Z)", text, re.S | re.M)
    return m.group(2).strip() if m else ""


def _active_threads(cap: int) -> str:
    """'## Aktif' ile '## Kapanan' arası (içindeki ### konu başlıkları dahil)."""
    m = re.search(r"^## Aktif\s*\n(.*?)(?=^## |\Z)", _read(THREADS), re.S | re.M)
    text = m.group(1).strip() if m else ""
    return text if len(text) <= cap else text[:cap].rsplit("\n", 1)[0] + f"\n[kırpıldı — tamamı: {THREADS.name}]"


def _cards(project: str, cap: int) -> str:
    """En yeni 2 kart + (varsa) bu projenin en yeni kartı. Kart başlığı: ## YYYY-MM-DD HH:MM · <proje> · <oturum>"""
    body = _read(CARDS)
    parts = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", body, flags=re.M)
    cards = [c.strip() for c in parts if re.match(r"## \d{4}-\d{2}-\d{2}", c)]
    pick = cards[:2]
    if project:
        own = next((c for c in cards if f"· {project.lower()} ·" in c.splitlines()[0].lower()), None)
        if own and own not in pick:
            pick.append(own)
    out = "\n\n".join(pick)
    return out if len(out) <= cap else out[:cap] + f"\n[kırpıldı — tamamı: {CARDS.name}]"


def _project(cwd: str) -> tuple[str, str]:
    """cwd ~/Workspace/projects/<ad>/... ise (<ad>, kasadaki proje notunun durum bölümü)."""
    try:
        rel = Path(cwd).resolve().relative_to(WORKSPACE.resolve())
    except (ValueError, OSError):
        return "", ""
    name = rel.parts[0] if rel.parts else ""
    note = VAULT / "20-Projeler" / f"{name}.md"
    if not name or not note.exists():
        return name, ""
    text = _read(note)
    status = _section(text, "Durum, eksikler ve açık işler") or _section(text, "Özet")
    status = re.sub(r"<!--.*?-->\s*", "", status)               # otomatik bölüm işaretleri bağlama gerekmez
    if re.search(r"^visibility:\s*private", text, re.M):
        return name, f"Not: 20-Projeler/{name}.md (gizli not; içerik bağlama alınmadı)"
    rules = _section(text, "Kurallar")
    rules = f"\nProje kuralları (bu projede uy):\n{rules[:1200]}" if rules else ""
    return name, f"Not: 20-Projeler/{name}.md\n{status[:1500]}{rules}"


def _upcoming() -> str:
    try:
        sys.path.insert(0, str(VAULT / "_system"))
        from sb.digest import upcoming
        return "\n".join(upcoming(VAULT, date.today(), 7)[:8])
    except Exception:
        return ""


def _warnings() -> str:
    out = []
    for f in sorted(STATE.glob("needs_card.*")):
        out.append(_read(f).strip())
        f.unlink(missing_ok=True)
    return "\n".join(f"⚠️ {w}" for w in out if w)


def _others(key: str, project: str) -> str:
    """Aynı anda açık başka oturumlar (son 12 saatte başlamış, kapanmamış)."""
    out, now = [], time.time()
    for f in STATE.glob("active.*"):
        if f.name == f"active.{key}":
            continue
        try:
            d = json.loads(_read(f))
        except ValueError:
            continue
        age = (now - float(d.get("t", 0))) / 3600
        if age > PARALLEL_HOURS:
            f.unlink(missing_ok=True)
            continue
        same = " (AYNI PROJE)" if project and d.get("project") == project else ""
        out.append(f"{d.get('id', '?')[:8]} · {d.get('project') or 'genel'}{same} · {int(age * 60)} dk önce açıldı")
    if not out:
        return ""
    return ("⚠️ Aynı anda açık başka Claude Code oturumu var: " + "; ".join(out) + ". Aynı dosyaya dokunmadan önce diskten "
            "yeniden oku; git reset/checkout/stash ile başkasının işine dokunma; commit öncesi `git status` bak.")


def build_context(session_id: str, cwd: str) -> str:
    cfg = _settings()
    project, project_status = _project(cwd)
    if cfg["profile"] == "manuel":
        return _warnings()
    budget = int(cfg["economy_chars"] if cfg["profile"] == "ekonomik" else cfg["context_chars"])
    eco = cfg["profile"] == "ekonomik"
    sections = [
        ("", _warnings()),
        (f"Second Brain kuralları (kullanıcının ({USER}) öğrettikleri — uy)", _bullets(RULES, 1500 if eco else 2500, project)),
        (f"{USER} hakkında hafıza", _bullets(MEMORY, 1200)),
        ("Açık konular", _active_threads(1000 if eco else 2000)),
        ("Son oturum kartları", _cards(project, 1000 if eco else 2500)),
        (f"Bu klasörün projesi: {project}", project_status),
        ("7 gün içindeki teslim/sınav/başvuru", _upcoming()),
    ]
    tail = (f"[Süreklilik protokolü] Bu oturumun kimliği: {session_id[:8]}. Anlamlı bir iş bitince `{CARDS}` dosyasının "
            f"EN ÜSTÜNE (başlığın altına) kart yaz/güncelle: `## {datetime.now():%Y-%m-%d %H:%M} · {project or 'genel'} · "
            f"{session_id[:8]}` + Ne yapıldı / Kararlar / Nerede kaldık / Sıradaki. Yalnız kendi kartını düzenle. Yarım kalan, "
            f"sonraki oturumlara taşınan işleri `{THREADS}` içinde '## Aktif' altında yerinde güncelle; biten konuyu '## Kapanan'a taşı. "
            "Kasa ayrıntısı gerekiyorsa second-brain MCP araçlarını (brain_project, brain_search, brain_recap...) kullan. "
            "İş bitince `sb receipt --summary \"...\" --ref <kasa-yolu> --learned \"...\" --project <p> --session "
            f"{session_id[:8]}` ile makbuz yaz (öğrenim yoksa --learned boş). Kalıcı öğrenim → `sb concept`, olgunlaşmamış → `sb learn`. "
            "Dosya değişmeyen anlamlı sohbette `sb trace \"≤450 karakter\"`. Aynı hata ikinci kez → `sb error-log \"hata\" --fix \"çözüm\"`.")
    out = "\n\n".join(f"[{h}]\n{t}" if h else t for h, t in sections if t)
    out = (out + "\n\n" + tail).strip()
    budget = min(budget, BUDGET)
    return out if len(out) <= budget else out[:budget - len(tail) - 30] + "\n[bağlam kırpıldı]\n\n" + tail


def _spawn_flush(payload: dict, key: str, reason: str) -> None:
    """Yerel model özetini ARKA PLANDA başlat (kanca beklemez; Claude Code kapanabilir)."""
    import subprocess
    tr = str(payload.get("transcript_path") or "")
    if not tr or not Path(tr).is_file():
        return
    project = _project(str(payload.get("cwd") or ""))[0]
    sysdir = VAULT / "_system"
    py = sysdir / ".venv" / ("Scripts/pythonw.exe" if os.name == "nt" else "bin/python")
    args = [str(py), "-X", "utf8", "-m", "sb", "hook-flush", "--transcript", tr, "--session", key, "--project", project,
            "--reason", reason]
    env = dict(os.environ, SB_NO_HOOK="1", PYTHONPATH=str(sysdir))
    log = open(STATE / f"flush.{key[:8]}.log", "a", encoding="utf-8")
    flags = 0x00000008 | 0x00000200 | 0x08000000 if os.name == "nt" else 0     # DETACHED | NEW_GROUP | NO_WINDOW
    subprocess.Popen(args, cwd=str(sysdir), env=env, stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                     creationflags=flags, start_new_session=os.name != "nt")


def _receipt_written(key: str, since: float) -> bool:
    folder = VAULT / "50-Günlük" / "Makbuzlar"
    return any(f.stat().st_mtime > since and f" · {key[:8]} · " in _read(f) for f in folder.glob("*.md")) if folder.exists() else False


def _key(payload: dict) -> str:
    return re.sub(r"[^\w-]", "", str(payload.get("session_id") or ""))[:64]


def main(event: str) -> None:
    if os.environ.get("SB_NO_HOOK"):
        return
    try:
        payload = json.loads(sys.stdin.read().lstrip("﻿") or "{}")
    except (ValueError, OSError):
        payload = {}
    STATE.mkdir(parents=True, exist_ok=True)
    key = _key(payload)
    cfg = _settings()
    if event == "start":
        cwd = str(payload.get("cwd") or os.getcwd())
        if key:
            (STATE / f"start.{key}").write_text(str(time.time()), encoding="utf-8")
            (STATE / f"count.{key}").write_text("0", encoding="utf-8")
            (STATE / f"active.{key}").write_text(json.dumps({"id": key, "t": time.time(), "cwd": cwd,
                                                             "project": _project(cwd)[0]}), encoding="utf-8")
        ctx = build_context(key or "bilinmiyor", cwd)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}, ensure_ascii=False))
    elif event == "prompt" and key:
        f = STATE / f"count.{key}"
        n = int(_read(f).strip() or 0) + 1
        f.write_text(str(n), encoding="utf-8")
        msgs = []
        if n == 1 and cfg["parallel_warning"] and cfg["profile"] != "manuel":
            cwd = str(payload.get("cwd") or os.getcwd())
            msgs.append(_others(key, _project(cwd)[0]))
        every = NUDGE_EVERY * (2 if cfg["profile"] == "ekonomik" else 1)
        if n % every == 0 and cfg["profile"] != "manuel":
            msgs.append(f"[Hafıza] {n}. mesaj. Anlamlı iş bittiyse `{CARDS.name}` kartını, `{THREADS.name}`ı ve `sb receipt` makbuzunu yaz.")
        msg = "\n".join(m for m in msgs if m)
        if msg:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}, ensure_ascii=False))
    elif event == "precompact" and key:
        if cfg["profile"] != "manuel":
            _spawn_flush(payload, key, "precompact")
    elif event == "end" and key:
        start = float(_read(STATE / f"start.{key}").strip() or 0)
        n = int(_read(STATE / f"count.{key}").strip() or 0)
        touched = (CARDS.exists() and CARDS.stat().st_mtime > start) or _receipt_written(key, start)
        if n >= int(cfg["flush_min_prompts"]) and not touched and cfg["profile"] == "normal":
            _spawn_flush(payload, key, "end")
        if n >= 5 and not touched:
            where = str(payload.get("cwd") or "")
            (STATE / f"needs_card.{key}").write_text(
                f"Önceki oturum ({key[:8]}, {n} mesaj, {where}) devir kartı yazılmadan kapandı. Önemli bir şey olduysa "
                f"oturum günlüğünden (sessions-sync) ya da kullanıcıya sorarak `{CARDS.name}`'a kısa kart ekle.", encoding="utf-8")
        for f in (STATE / f"start.{key}", STATE / f"count.{key}", STATE / f"active.{key}"):
            f.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main(sys.argv[1] if len(sys.argv) > 1 else "")
    except Exception:
        pass                                  # kanca hiçbir koşulda Claude Code'u bozmasın
    sys.exit(0)
