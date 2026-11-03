"""Second brain MCP sunucusu (stdio, SALT OKUNUR): Claude Code her projede kasayı bağlam olarak kullanır.

Araçlar: brain_overview, brain_project, brain_course, brain_person, brain_note, brain_search, brain_today.
Kasadaki .md notlarını ve mail.db'yi (mode=ro) okur; hiçbir şeyi yazmaz, silmez, göndermez.
Çıktılar `redact` ile maskelenir. Kayıt: `claude mcp add --scope user second-brain -- <python> -m sb.mcp_server`
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .config import MAIL_DB, VAULT
from .notes import SKIP_DIRS, is_private, split_note
from .redact import redact
from .config import FULL_NAME

mcp = FastMCP("second-brain", instructions=(
    f"{FULL_NAME} adlı kullanıcının kişisel second brain'i (Obsidian kasası + yerel arşiv). Yeni bir işe başlarken önce brain_project / "
    "brain_overview ile ilgili projeyi, geçmiş kararları ve açık işleri oku; belge, mail ve SMS içinde aramak için brain_search kullan. "
    "Notlardaki 'Proje dosyası', 'Oturum günlüğü' ve 'Ders dosyası' bölümleri otomatik derlenmiştir; çelişki varsa kaynağa bak."))

MAX_NOTE = 30_000


def _norm(s: str) -> str:
    return " ".join(s.lower().translate(str.maketrans("ıığşçöüİ", "iigscoui")).split())


def _notes(folder: str) -> list[Path]:
    base = VAULT / folder
    return sorted(p for p in base.rglob("*.md") if not any(part in SKIP_DIRS for part in p.relative_to(VAULT).parts[:-1])
                  and not is_private(p)) if base.is_dir() else []


def _find(folder: str, query: str) -> list[Path]:
    q = _norm(query)
    notes = _notes(folder)
    exact = [p for p in notes if _norm(p.stem) == q]
    return exact or [p for p in notes if q in _norm(p.stem)]


def _read(p: Path, limit: int = MAX_NOTE) -> str:
    text = p.read_text(encoding="utf-8")
    note = f"# {p.relative_to(VAULT).as_posix()}\n\n{text}"
    return redact(note if len(note) <= limit else note[:limit] + f"\n\n… (kısaltıldı: {len(text)} karakter; tamamı için brain_note kullan)")


def _pick(folder: str, query: str, what: str) -> str:
    hits = _find(folder, query)
    if not hits:
        names = ", ".join(p.stem for p in _notes(folder)[:40])
        return f"'{query}' adında {what} notu yok. Mevcutlar (ilk 40): {names}"
    if len(hits) > 1:
        return f"'{query}' birden çok notla eşleşti, birini seç: " + "; ".join(p.stem for p in hits[:15])
    return _read(hits[0])


@mcp.tool()
def brain_overview() -> str:
    """Kasanın genel görünümü: projeler (durum, son etkinlik, teknolojiler), aktif dersler, akademik durum ve sayılar."""
    lines = ["## Projeler"]
    for p in _notes("20-Projeler"):
        fm = split_note(p.read_text(encoding="utf-8"))[0]
        tech = ", ".join((fm.get("technologies") or fm.get("stack") or [])[:6])
        lines.append(f"- {p.stem} · {fm.get('status')} · son etkinlik {fm.get('last_activity')} · {tech}")
    lines.append("\n## Aktif dersler")
    for p in _notes("10-Dersler"):
        fm = split_note(p.read_text(encoding="utf-8"))[0]
        if fm.get("type") == "ders" and fm.get("status") == "aktif":
            lines.append(f"- {p.stem} · devam: {fm.get('devam')}")
    lines.append(f"\nNot sayıları: proje {len(_notes('20-Projeler'))}, ders {len(_notes('10-Dersler'))}, kişi {len(_notes('60-Kişiler'))}, "
                 f"teknoloji {len(_notes('40-Kaynaklar/Teknolojiler'))}, konu {len(_notes('40-Kaynaklar/Konular'))}")
    lines.append("Akademik durum için brain_note('10-Dersler/Akademik Durum.md').")
    return redact("\n".join(lines))


@mcp.tool()
def brain_project(name: str) -> str:
    """Bir projenin tam notu: derlenmiş proje dosyası (mimari, teknoloji, zaman çizelgesi, açık işler), oturum günlüğü, son çalışmalar."""
    return _pick("20-Projeler", name, "proje")


@mcp.tool()
def brain_course(name_or_code: str) -> str:
    """Bir dersin notu: ÖBS notları, ders içeriği, dosyalar ve derlenmiş ders dosyası. Kod (YPZ204) ya da ad parçası verilebilir."""
    return _pick("10-Dersler", name_or_code, "ders")


@mcp.tool()
def brain_recap(days: int = 7, project: str = "") -> str:
    """Son günlerde ne yapıldı: makbuzlardan (ajanların yazdığı iş sonuçları, kaynak bağlantılı) gün gün liste.
    Satırlar beyandır; önemliyse kaynak notunu brain_note ile aç."""
    from .memory import recap
    return redact(recap(max(1, min(days, 90)), project))


@mcp.tool()
def local_work(instruction: str, paths: list[str] | None = None, text: str = "") -> str:
    """Ücretsiz yerel işçi (Qwen, bu bilgisayarda): büyük log/belge/metin yığınını okuyup kısa sonuç döndürür; Claude'un
    bağlamını ve limitini korur. paths: ev klasörü altındaki dosyalar (pdf/docx/xlsx/txt/md...). Sonuç özet/çıkarımdır;
    kritik bilgiyi kaynaktan doğrula. Hiçbir şey yazmaz."""
    from .worker import run
    return run(instruction, paths or [], text)


@mcp.tool()
def brain_person(name: str) -> str:
    """Bir kişinin notu (rehber): telefon, şirket, son mesaj ve aramalar."""
    return _pick("60-Kişiler", name, "kişi")


@mcp.tool()
def brain_note(path: str) -> str:
    """Kasadaki herhangi bir notu yoldan okur (ör. '40-Kaynaklar/Teknolojiler/Laravel.md'). Sadece kasa içi .md dosyaları."""
    p = (VAULT / path).resolve()
    if VAULT.resolve() not in p.parents or p.suffix != ".md" or not p.is_file():
        return "Geçersiz yol: sadece kasa içindeki .md notları okunabilir."
    if "_system" in p.relative_to(VAULT.resolve()).parts:
        return "Geçersiz yol: _system altı (kod, yapılandırma, sırlar) okunamaz."
    if is_private(p):
        return (f"Bu not gizli (visibility: private); içeriği otomatik okunmaz. Başlık: {p.stem}. "
                "Kullanıcı açıkça isterse kendisi açar.")
    return _read(p, 60_000)


@mcp.tool()
def brain_search(query: str, limit: int = 12) -> str:
    """Belge içeriği, mail, SMS ve Drive dosya adlarında tam metin arar (yerel arşiv). Her sonuç kaynak türüyle başlar."""
    from . import content
    try:
        con = sqlite3.connect(f"file:{MAIL_DB.as_posix()}?mode=ro", uri=True, timeout=10)
        hits = content.search(con, query, limit=min(limit, 30))
    except sqlite3.Error as e:
        return f"Arama arşivine ulaşılamadı: {e}"
    return redact("\n".join(f"[{k}] {line}" for k, line in hits) or "Sonuç yok.")


@mcp.tool()
def brain_find(query: str, kind: str = "", since: str = "", until: str = "", k: int = 10) -> str:
    """Beyin dizininde doğal dille arar (kelime + anlam; notlar, mail/SMS, belgeler, diğer kaynaklar). Sorguda 'geçen ay', 'ekimde',
    'hocadan gelen mailler' gibi ifadeler süzgeç olur. kind: note | mail | file | item (boş = hepsi); since/until: YYYY-AA-GG."""
    from . import search
    hits = search.smart_find(query, k=max(1, min(k, 30)), log=False, kinds=[kind] if kind else None, since=since or None, until=until or None)
    lines = [f"[{h['kind']}] {h['date']} {h['title']} — {h['ref']}\n    {' '.join(h['text'].split())[:300]}" for h in hits]
    return redact("\n".join(lines) or "Sonuç yok.")


@mcp.tool()
def brain_answer(question: str) -> str:
    """Soruyu yerel modelle, YALNIZ beyin dizininden bulunan kaynaklara dayanarak cevaplar; her cümle [n] kaynağına bağlanır."""
    from . import brain, search
    search._log_question(question)
    return redact(brain.answer(question))


@mcp.tool()
def brain_today(days: int = 14) -> str:
    """Önümüzdeki günlerde teslim/sınav/başvuru tarihi olan açık notlar ve onay bekleyen takvim adayları."""
    today, end = date.today(), date.today() + timedelta(days=days)
    rows = []
    for folder in ("10-Dersler", "30-Kariyer", "20-Projeler"):
        for p in _notes(folder):
            fm = split_note(p.read_text(encoding="utf-8"))[0]
            due = fm.get("due")
            if isinstance(due, date) and today <= due <= end and fm.get("status") not in ("tamamlandi", "iptal", "arsiv", "kabul", "red"):
                rows.append((due, f"{due} {fm.get('due_time') or ''} · {p.stem} ({fm.get('type')}, {fm.get('status')})"))
    out = [r[1] for r in sorted(rows)] or ["Yaklaşan tarihli açık not yok."]
    pending = VAULT / "00-Inbox" / "onay-bekleyenler.md"
    if pending.exists():
        items = [l for l in pending.read_text(encoding="utf-8").splitlines() if l.startswith("- [ ]")]
        out += ["", f"Onay bekleyen takvim adayları ({len(items)}):"] + items[:10]
    return redact("\n".join(out))


if __name__ == "__main__":
    mcp.run()
