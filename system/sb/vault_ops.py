"""Kasaya YAZAN tek kapı: asistan (Qwen) ve günlük kurallar notları buradan değiştirir.

Her değişiklik: (1) yalnız izinli klasörlerde, (2) şemaya uygun durumla, (3) ayrı bir "asistan: ..." git commit'iyle
(geri alınabilir: `undo_last`), (4) ~/.secondbrain/asistan_log.jsonl'e kayıtla yapılır. Hiçbir şey kalıcı SİLİNMEZ;
"arşivle" notu 90-Arşiv'e (aynı alt yolla) taşır. Otomatik bölümlere (sb:auto) dokunulmaz.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import DATA, SYSTEM, VAULT
from .notes import dump_note, split_note
from .config import USER

LOG = DATA / "asistan_log.jsonl"
ARCHIVE = "90-Arşiv"
RULES_NOTE = VAULT / "Asistan kuralları.md"
MEMORY_NOTE = VAULT / "Asistan hafızası.md"
WRITABLE = ("00-Inbox", "10-Dersler", "20-Projeler", "30-Kariyer", "40-Kaynaklar", "50-Günlük", "60-Kişiler")
GRACE_DAYS = 14          # süresi geçen açık iş bu kadar gün sonra arşive
DONE = {"tamamlandi", "iptal", "yapildi", "red", "vazgecildi"}


def _statuses() -> dict[str, set[str]]:
    spec = importlib.util.spec_from_file_location("sb_lint", SYSTEM / "tools" / "lint.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.STATUSES


def _fold(s: str) -> str:
    return " ".join(s.lower().translate(str.maketrans("ıİğüşöç–-_", "iigusoc   ")).split())


def _rel(p: Path) -> str:
    return p.relative_to(VAULT).as_posix()


def _writable(p: Path) -> bool:
    try:
        rel = _rel(p.resolve())
    except ValueError:
        return False
    return p.suffix == ".md" and rel.split("/")[0] in WRITABLE


def find(query: str, limit: int = 8, include_archive: bool = False) -> list[Path]:
    """Not adı/yolu parçasıyla arar. Tam yol verilirse onu döndürür. En iyi eşleşmeler önce."""
    q = query.strip().strip("/")
    direct = VAULT / q if q.endswith(".md") else VAULT / f"{q}.md"
    if direct.is_file() and (_writable(direct) or include_archive):
        return [direct]
    words = _fold(Path(q).stem).split()
    if not words:
        return []
    scored = []
    for p in VAULT.rglob("*.md"):
        rel = _rel(p)
        top = rel.split("/")[0]
        if top not in WRITABLE and not (include_archive and top == ARCHIVE):
            continue
        name = _fold(p.stem)
        hits = sum(w in name for w in words)
        if hits == len(words):
            scored.append((0 if name == " ".join(words) else 1, len(name), p))
        elif hits >= max(1, len(words) - 1) and len(words) >= 3:
            scored.append((2, len(name), p))
    return [p for *_, p in sorted(scored)[:limit]]


def resolve(query: str) -> Path:
    found = find(query)
    if not found:
        raise LookupError(f"'{query}' adlı not bulunamadı (note_find ile ara)")
    if len(found) > 1 and _fold(found[0].stem) != _fold(Path(query).stem) and not query.endswith(".md"):
        raise LookupError("Birden fazla not eşleşti, tam yolu kullan: " + "; ".join(_rel(p) for p in found[:5]))
    return found[0]


# ---------------------------------------------------------------- git + günlük
def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(VAULT), *args], capture_output=True, text=True, encoding="utf-8", timeout=60)


def commit(paths: list[str], message: str) -> str:
    """Yalnız verilen yolları commit'ler (kullanıcının yarım işleri karışmaz). Commit kimliğini döndürür; git yoksa ''."""
    _git("add", "-A", "--", *paths)
    r = _git("commit", "-m", f"asistan: {message}", "--", *paths)
    if r.returncode != 0:
        return ""
    return _git("rev-parse", "--short", "HEAD").stdout.strip()


def log(actor: str, action: str, path: str, detail: str, sha: str) -> dict:
    entry = {"ts": datetime.now().isoformat(timespec="seconds"), "actor": actor, "action": action,
             "path": path, "detail": detail, "commit": sha}
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def recent(hours: int = 26) -> list[dict]:
    if not LOG.exists():
        return []
    since = datetime.now() - timedelta(hours=hours)
    out = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if datetime.fromisoformat(e["ts"]) >= since:
            out.append(e)
    return out


# ---------------------------------------------------------------- işlemler
def update(query: str, status: str | None = None, append: str | None = None, actor: str = "asistan",
           today: date | None = None) -> str:
    p = resolve(query)
    if not _writable(p):
        return f"Hata: {_rel(p)} düzenlenemez (izinli klasör değil)."
    today = today or date.today()
    fm, body = split_note(p.read_text(encoding="utf-8"))
    changes = []
    if status:
        st = _fold(status).replace(" ", "-")
        allowed = _statuses().get(fm.get("type"), set())
        if allowed and st not in allowed:
            return f"Hata: '{fm.get('type')}' notu için geçerli durumlar: {', '.join(sorted(allowed))}"
        if fm.get("status") != st:
            changes.append(f"durum {fm.get('status')} → {st}")
            fm["status"] = st
    if append and append.strip():
        line = f"- {today:%Y-%m-%d}: {append.strip()}"
        if "## Asistan notları" in body:
            body = body.rstrip() + "\n" + line + "\n"
        else:
            body = body.rstrip() + "\n\n## Asistan notları\n" + line + "\n"
        changes.append(f"not eklendi: {append.strip()[:80]}")
    if not changes:
        return f"Değişiklik yok: {_rel(p)}"
    fm["updated"] = today
    p.write_text(dump_note(fm, body), encoding="utf-8")
    rel = _rel(p)
    sha = commit([rel], f"{p.stem}: {'; '.join(changes)}")
    log(actor, "güncelle", rel, "; ".join(changes), sha)
    return f"Güncellendi: {rel} ({'; '.join(changes)})" + (f" [commit {sha}]" if sha else "")


def archive(query: str, reason: str = "", actor: str = "asistan") -> str:
    p = resolve(query)
    if not _writable(p):
        return f"Hata: {_rel(p)} arşivlenemez."
    rel = _rel(p)
    dest = VAULT / ARCHIVE / rel
    n = 2
    while dest.exists():
        dest = dest.with_name(f"{p.stem} ({n}).md")
        n += 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    p.rename(dest)
    sha = commit([rel, _rel(dest)], f"arşivlendi {p.stem}" + (f" ({reason})" if reason else ""))
    log(actor, "arşivle", rel, f"→ {_rel(dest)}" + (f" · {reason}" if reason else ""), sha)
    return f"Arşivlendi: {rel} → {_rel(dest)}" + (f" [commit {sha}]" if sha else "")


def undo_last(actor: str = "asistan") -> str:
    """En son asistan commit'ini geri alır (git revert; geçmiş silinmez)."""
    r = _git("log", "--format=%h %s", "-n", "200")
    for line in r.stdout.splitlines():
        sha, _, msg = line.partition(" ")
        if msg.startswith("asistan: ") and not msg.startswith("asistan: geri alındı"):
            rv = _git("revert", "--no-commit", sha)
            if rv.returncode != 0:
                _git("revert", "--abort")
                return f"Hata: {sha} geri alınamadı (sonradan elle değişmiş olabilir): {rv.stderr.strip()[:200]}"
            _git("commit", "-m", f"asistan: geri alındı — {msg[9:]}")
            log(actor, "geri al", "", msg[9:], sha)
            return f"Geri alındı: {msg[9:]}"
    return "Geri alınacak asistan değişikliği yok."


def add_rule(text: str, actor: str = "asistan") -> str:
    """kullanıcının düzeltmesini kalıcı kural olarak kaydeder; asistan her konuşmada bu notu okur."""
    text = " ".join(text.split())
    if not text:
        return "Hata: boş kural."
    if not RULES_NOTE.exists():
        RULES_NOTE.write_text("---\ntype: dashboard\ntags: [dashboard, asistan]\n---\n# Asistan kuralları\n\n"
                              f"kullanıcının ({USER}) asistana öğrettikleri. Asistan her konuşmada bunları okur; elle de düzenleyebilirsin.\n\n", encoding="utf-8")
    body = RULES_NOTE.read_text(encoding="utf-8")
    if _fold(text) in _fold(body):
        return "Bu kural zaten kayıtlı."
    RULES_NOTE.write_text(body.rstrip() + f"\n- {text} _(eklendi {date.today():%Y-%m-%d})_\n", encoding="utf-8")
    sha = commit([_rel(RULES_NOTE)], f"kural eklendi: {text[:60]}")
    log(actor, "kural", _rel(RULES_NOTE), text, sha)
    return f"Kural kaydedildi: {text}"


def rules_text(limit: int = 3000, note: Path | None = None) -> str:
    note = note or RULES_NOTE
    if not note.exists():
        return ""
    return "\n".join(l for l in note.read_text(encoding="utf-8").splitlines() if l.startswith("- "))[-limit:]


SENSITIVE_RE = re.compile(r"şifre|sifre|parola|password|pin kodu|cvv|iban|kart numara|tc kimlik|(?<!\d)\d{11}(?!\d)|(?:\d[ -]?){13,19}", re.I)


def add_memory(fact: str, actor: str = "asistan") -> str:
    """kullanıcı hakkında kalıcı bilgi ('Ahmet ev arkadaşım', 'sabah 9'dan önce toplantı koyma'). Hassas veri YAZILMAZ."""
    fact = " ".join(fact.split())
    if not fact:
        return "Hata: boş bilgi."
    if SENSITIVE_RE.search(fact):
        return "Hassas veri (şifre, kart, kimlik, IBAN) kasaya yazılmaz; bunu bir şifre yöneticisinde tut."
    if not MEMORY_NOTE.exists():
        MEMORY_NOTE.write_text("---\ntype: dashboard\ntags: [dashboard, asistan]\n---\n# Asistan hafızası\n\n"
                               f"Asistanın {USER} hakkında hatırladıkları. Her konuşmada okunur; yanlışı buradan silebilirsin.\n\n", encoding="utf-8")
    body = MEMORY_NOTE.read_text(encoding="utf-8")
    if _fold(fact) in _fold(body):
        return "Bunu zaten hatırlıyorum."
    MEMORY_NOTE.write_text(body.rstrip() + f"\n- {fact} _({date.today():%Y-%m-%d})_\n", encoding="utf-8")
    sha = commit([_rel(MEMORY_NOTE)], f"hafıza: {fact[:60]}")
    log(actor, "hafıza", _rel(MEMORY_NOTE), fact, sha)
    return f"Hatırlayacağım: {fact}"


CARDS_NOTE = VAULT / "Son oturum.md"
KEEP_CARDS = 6


def compact_cards(keep: int = KEEP_CARDS) -> int:
    """Son oturum.md'de en yeni `keep` kart kalır; eskiler 90-Arşiv/Oturum kartları/<YYYY-MM>.md'ye AYNEN taşınır (silinmez)."""
    if not CARDS_NOTE.exists():
        return 0
    text = CARDS_NOTE.read_text(encoding="utf-8")
    parts = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", text, flags=re.M)
    head, cards = parts[0], [c for c in parts[1:] if c.strip()]
    if len(cards) <= keep:
        return 0
    old = cards[keep:]
    by_month: dict[str, list[str]] = {}
    for c in old:
        by_month.setdefault(c[3:10], []).append(c.rstrip() + "\n")
    paths = [_rel(CARDS_NOTE)]
    for month, cs in by_month.items():
        dest = VAULT / ARCHIVE / "Oturum kartları" / f"{month}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        prev = dest.read_text(encoding="utf-8") if dest.exists() else f"# Oturum kartları {month}\n\n"
        dest.write_text(prev.rstrip() + "\n\n" + "\n".join(cs), encoding="utf-8")
        paths.append(_rel(dest))
    CARDS_NOTE.write_text(head + "".join(cards[:keep]), encoding="utf-8")
    sha = commit(paths, f"{len(old)} eski oturum kartı arşive")
    log("kural", "kart arşivi", _rel(CARDS_NOTE), f"{len(old)} kart → 90-Arşiv/Oturum kartları", sha)
    return len(old)


# ---------------------------------------------------------------- günlük kurallar (model yok, deterministik)
def housekeep(today: date | None = None, dry_run: bool = False) -> list[str]:
    """Süresi geçmiş işleri toparlar:
    - teslim/görüşme: tamamlandı/iptal/yapıldı ise tarihten 1 gün sonra, hâlâ açıksa GRACE_DAYS gün sonra arşive.
    - başvuru: sonuç bekleyen/kabul edilenler kalır; planlanıp geçenler GRACE_DAYS gün sonra arşive.
    Tekrarlayan teslimler (tarih kendiliğinden ilerler) arşivlenmez."""
    today = today or date.today()
    done = []
    for p in sorted(VAULT.rglob("*.md")):
        if not _writable(p):
            continue
        try:
            fm = split_note(p.read_text(encoding="utf-8"))[0]
        except Exception:
            continue
        typ, st, due = fm.get("type"), fm.get("status"), fm.get("due")
        if typ not in ("teslim", "gorusme", "basvuru") or not isinstance(due, date):
            continue
        if "tekrarlayan" in (fm.get("tags") or []):
            continue
        age = (today - due).days
        if typ == "basvuru" and st in ("gonderildi", "sonuc-bekleniyor", "kabul"):
            continue
        if (st in DONE and age >= 1) or age >= GRACE_DAYS:
            why = f"durum {st}, tarih {due} ({age} gün önce)"
            done.append(f"{_rel(p)} — {why}")
            if not dry_run:
                archive(_rel(p), why, actor="kural")
    return done
