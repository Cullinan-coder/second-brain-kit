"""Claude Code hafıza kancaları (kullanıcı geneli, her proje): oturum başında Second Brain'den kısa bağlam enjekte eder.

Kullanım (~/.claude/settings.json hooks): python cc_hook.py start | prompt | end   (stdin: kanca JSON'u)
- start : kurallar, kullanıcı hakkında hafıza, açık konular, son oturum kartları, bu klasörün projesi, yaklaşan tarihler
          + önceki oturum kartsız kapandıysa uyarı. Toplam ≤ 10.000 karakter.
- prompt: mesaj sayacı; her 15 mesajda "devir kartını unutma" hatırlatması.
- end   : ≥5 mesajlık oturum `Son oturum.md`'ye dokunmadan bittiyse işaret bırakır (sonraki açılışta uyarı).
Model çağırmaz, ağa çıkmaz, hata olursa sessizce çıkar (Claude Code'u asla bozmaz). SB_NO_HOOK=1 iken hiçbir şey yapmaz.
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


USER = _user()
WORKSPACE = Path(os.path.expanduser(_profile_value("workspace", str(WORKSPACE))))


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def _bullets(p: Path, cap: int) -> str:
    text = "\n".join(l for l in _read(p).splitlines() if l.startswith("- "))
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
    return name, f"Not: 20-Projeler/{name}.md\n{status[:1500]}"


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


def build_context(session_id: str, cwd: str) -> str:
    project, project_status = _project(cwd)
    sections = [
        ("", _warnings()),
        (f"Second Brain kuralları (kullanıcının ({USER}) öğrettikleri — uy)", _bullets(RULES, 2500)),
        (f"{USER} hakkında hafıza", _bullets(MEMORY, 1200)),
        ("Açık konular", _active_threads(2000)),
        ("Son oturum kartları", _cards(project, 2500)),
        (f"Bu klasörün projesi: {project}", project_status),
        ("7 gün içindeki teslim/sınav/başvuru", _upcoming()),
    ]
    tail = (f"[Süreklilik protokolü] Bu oturumun kimliği: {session_id[:8]}. Anlamlı bir iş bitince `{CARDS}` dosyasının "
            f"EN ÜSTÜNE (başlığın altına) kart yaz/güncelle: `## {datetime.now():%Y-%m-%d %H:%M} · {project or 'genel'} · "
            f"{session_id[:8]}` + Ne yapıldı / Kararlar / Nerede kaldık / Sıradaki. Yalnız kendi kartını düzenle. Yarım kalan, "
            f"sonraki oturumlara taşınan işleri `{THREADS}` içinde '## Aktif' altında yerinde güncelle; biten konuyu '## Kapanan'a taşı. "
            "Kasa ayrıntısı gerekiyorsa second-brain MCP araçlarını (brain_project, brain_search...) kullan.")
    out = "\n\n".join(f"[{h}]\n{t}" if h else t for h, t in sections if t)
    out = (out + "\n\n" + tail).strip()
    return out if len(out) <= BUDGET else out[:BUDGET - len(tail) - 30] + "\n[bağlam kırpıldı]\n\n" + tail


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
    if event == "start":
        if key:
            (STATE / f"start.{key}").write_text(str(time.time()), encoding="utf-8")
            (STATE / f"count.{key}").write_text("0", encoding="utf-8")
        ctx = build_context(key or "bilinmiyor", str(payload.get("cwd") or os.getcwd()))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}, ensure_ascii=False))
    elif event == "prompt" and key:
        f = STATE / f"count.{key}"
        n = int(_read(f).strip() or 0) + 1
        f.write_text(str(n), encoding="utf-8")
        if n % NUDGE_EVERY == 0:
            msg = f"[Hafıza] {n}. mesaj. Anlamlı iş bittiyse `{CARDS.name}` kartını ve `{THREADS.name}`ı güncelle."
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}, ensure_ascii=False))
    elif event == "end" and key:
        start = float(_read(STATE / f"start.{key}").strip() or 0)
        n = int(_read(STATE / f"count.{key}").strip() or 0)
        touched = CARDS.exists() and CARDS.stat().st_mtime > start
        if n >= 5 and not touched:
            where = str(payload.get("cwd") or "")
            (STATE / f"needs_card.{key}").write_text(
                f"Önceki oturum ({key[:8]}, {n} mesaj, {where}) devir kartı yazılmadan kapandı. Önemli bir şey olduysa "
                f"oturum günlüğünden (sessions-sync) ya da kullanıcıya sorarak `{CARDS.name}`'a kısa kart ekle.", encoding="utf-8")
        for f in (STATE / f"start.{key}", STATE / f"count.{key}"):
            f.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main(sys.argv[1] if len(sys.argv) > 1 else "")
    except Exception:
        pass                                  # kanca hiçbir koşulda Claude Code'u bozmasın
    sys.exit(0)
