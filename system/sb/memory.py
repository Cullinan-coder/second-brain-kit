"""Hafıza çekirdeği (Avenox V3 desenleri): sonuç makbuzu, son günler özeti, öğrenim adayları, kavram/bağlantı notları,
sohbet izi ve hata kataloğu. Hepsi düz Markdown; her yazım vault_ops.commit ile ayrı git commit'i (geri alınabilir).

- Makbuz  : anlamlı bir işin sonunda tek satır; `50-Günlük/Makbuzlar/YYYY-MM.md` (yalnız ekleme) + o günün günlük notunda
            "Otomatik özet" bölümü. Aynı event_id ikinci kez yazılmaz. `recap(days)` makbuzlardan "son günlerde ne yaptık".
            Satırdaki iddialar ajanın beyanıdır, doğrulanmış olgu değildir (kaynak bağlantısı açılıp kontrol edilir).
- Öğrenim : "Öğrenilen:" makbuzda; olgunlaşmamışı `40-Kaynaklar/Kavramlar/_Adaylar.md` defterine (`learn`).
- Kavram  : `40-Kaynaklar/Kavramlar/<konu>.md` (açıklama, önemli noktalar, sınırlar, kaynaklar) + `_Dizin.md` (tek satır/kavram).
- Bağlantı: `40-Kaynaklar/Bağlantılar/<A> ↔ <B>.md` yalnız gerekçeli gerçek ilişki için.
- İz      : dosya değişmeyen anlamlı sohbetin ≤450 karakterlik özeti → `40-Kaynaklar/Sohbetler/YYYY-MM.md`.
- Hata    : `40-Kaynaklar/Hata kataloğu.md`; aynı hata ikinci kez yazılınca çözümü kalıcı kural olur (Asistan kuralları).
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from . import vault_ops
from .notes import dump_note, replace_auto, safe_filename, split_note

RECEIPTS = "50-Günlük/Makbuzlar"
DAILY = "50-Günlük"
CONCEPTS = "40-Kaynaklar/Kavramlar"
LINKS = "40-Kaynaklar/Bağlantılar"
TRACES = "40-Kaynaklar/Sohbetler"
ERRORS = "40-Kaynaklar/Hata kataloğu.md"
TRACE_MAX = 450
RECEIPT_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) · ([^·]*) · ([^·]*) · (.*?)\s*<!-- r:([0-9a-f]{12}) -->$")


def _vault() -> Path:
    return vault_ops.VAULT


def _commit(paths: list[Path], msg: str, actor: str, detail: str = "") -> str:
    rels = [vault_ops._rel(p) for p in paths]
    sha = vault_ops.commit(rels, msg)
    vault_ops.log(actor, msg.split(":")[0], rels[0], detail[:160], sha)
    return sha


def _clean(s: str) -> str:
    return " ".join(str(s).replace("·", "-").replace("<!--", "").replace("-->", "").split())


def _link(ref: str) -> str:
    ref = ref.strip().replace("\\", "/")
    if re.match(r"https?://", ref):
        return ref
    return f"[[{ref[:-3] if ref.endswith('.md') else ref}]]"


def _check_refs(refs: list[str]) -> list[str]:
    bad = [r for r in refs if not re.match(r"https?://", r) and not (_vault() / r).exists()
           and not (_vault() / f"{r}.md").exists()]
    return bad


# ---------------------------------------------------------------- makbuz
def receipt(summary: str, refs: list[str] | None = None, links: list[str] | None = None, learned: str = "",
            project: str = "", session: str = "", event_id: str = "", when: datetime | None = None,
            actor: str = "claude") -> str:
    summary, learned = _clean(summary), _clean(learned)
    if not summary:
        return "Hata: özet boş."
    if vault_ops.SENSITIVE_RE.search(summary + " " + learned):
        return "Hassas veri (şifre, kart, kimlik, IBAN) makbuza yazılmaz."
    refs = [r.strip() for r in refs or [] if r.strip()]
    if bad := _check_refs(refs):
        return f"Hata: kaynak bulunamadı: {', '.join(bad)} (kasa içi göreli yol ya da https bağlantısı ver)."
    when = when or datetime.now()
    rid = hashlib.sha256((event_id or f"{session}|{summary}").encode("utf-8")).hexdigest()[:12]
    f = _vault() / RECEIPTS / f"{when:%Y-%m}.md"
    if f.exists() and f"<!-- r:{rid} -->" in f.read_text(encoding="utf-8"):
        return f"Zaten kayıtlı (makbuz {rid})."
    parts = [summary]
    if refs or links:
        parts.append("kaynak: " + ", ".join(_link(r) for r in refs + [l for l in links or [] if l.startswith("http")]))
    parts.append(f"Öğrenilen: {learned or 'yok'}")
    line = (f"- {when:%Y-%m-%d %H:%M} · {_clean(project) or 'genel'} · {_clean(session)[:8] or '-'} · "
            + " · ".join(parts) + f" <!-- r:{rid} -->\n")
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text(dump_note({"type": "dashboard", "tags": ["makbuz"]},
                               f"# Makbuzlar {when:%Y-%m}\n\nAjanların yazdığı iş sonuçları (yalnız eklenir, en yeni altta). "
                               "Satırlar beyandır; kaynakları açıp doğrula.\n\n"), encoding="utf-8")
    with f.open("a", encoding="utf-8") as fh:
        fh.write(line)
    day = refresh_daily(when.date())
    _commit([f, day], f"makbuz: {summary[:60]}", actor, summary)
    return f"Makbuz yazıldı ({rid}): {vault_ops._rel(f)}"


def receipts(since: date | None = None, until: date | None = None) -> list[dict]:
    out = []
    folder = _vault() / RECEIPTS
    for f in sorted(folder.glob("*.md")) if folder.exists() else []:
        for line in f.read_text(encoding="utf-8").splitlines():
            m = RECEIPT_RE.match(line)
            if not m:
                continue
            d = date.fromisoformat(m.group(1))
            if (since and d < since) or (until and d > until):
                continue
            out.append({"date": d, "time": m.group(2), "project": m.group(3).strip(), "session": m.group(4).strip(),
                        "text": m.group(5).strip(), "id": m.group(6)})
    return out


def refresh_daily(day: date) -> Path:
    """Günlük notun 'Otomatik özet' bölümünü o günün makbuzlarıyla yeniler (not yoksa şablondan açılır)."""
    p = _vault() / DAILY / f"{day:%Y-%m-%d}.md"
    if p.exists():
        fm, body = split_note(p.read_text(encoding="utf-8"))
    else:
        fm = {"type": "gunluk", "status": "acik", "tags": ["gunluk"], "source": "manual", "source_id": f"gunluk:{day}",
              "created": day, "updated": day, "due": day}
        body = (f"# {day:%Y-%m-%d}\n\n## Bugün\n- [ ] \n\n## Notlar\n\n## Otomatik özet\n"
                "<!-- sb:auto:gunluk-ozet:start -->\n<!-- sb:auto:gunluk-ozet:end -->\n")
    rows = receipts(day, day)
    text = "\n".join(f"- {r['time']} · {r['project']} · {r['text']}" for r in rows) or "Bugün makbuz yok."
    fm["updated"] = date.today()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_note(fm, replace_auto(body, "gunluk-ozet", "Yapılanlar (makbuzlardan):\n" + text)), encoding="utf-8")
    return p


def recap(days: int = 7, project: str = "", today: date | None = None) -> str:
    since = (today or date.today()) - timedelta(days=days - 1)
    rows = [r for r in receipts(since) if not project or project.lower() in r["project"].lower()]
    if not rows:
        return f"Son {days} günde makbuz yok."
    out, cur = [f"Son {days} gün ({len(rows)} makbuz; ajan beyanı, kaynakları açıp doğrula):"], None
    for r in rows:
        if r["date"] != cur:
            cur = r["date"]
            out.append(f"\n{cur:%d.%m.%Y}")
        out.append(f"- {r['time']} [{r['project']}] {r['text']}")
    return "\n".join(out)


# ---------------------------------------------------------------- öğrenim / kavram / bağlantı
def _ensure(p: Path, title: str, intro: str) -> None:
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(dump_note({"type": "dashboard", "tags": ["dashboard", "bilgi"]}, f"# {title}\n\n{intro}\n\n"), encoding="utf-8")


def learn(candidate: str, source: str = "", scope: str = "", actor: str = "claude") -> str:
    candidate = _clean(candidate)
    if not candidate:
        return "Hata: öğrenim boş."
    if vault_ops.SENSITIVE_RE.search(candidate):
        return "Hassas veri öğrenim defterine yazılmaz."
    p = _vault() / CONCEPTS / "_Adaylar.md"
    _ensure(p, "Öğrenim adayları", "Henüz kavram notuna dönüşmemiş öğrenimler. Olgunlaşınca kavram notuna taşı ve satırı [x] yap.")
    text = p.read_text(encoding="utf-8")
    if candidate.lower() in text.lower():
        return "Bu aday zaten defterde."
    line = f"- [ ] {date.today()} · {_clean(scope) or 'genel'} · {candidate}" + (f" · kaynak: {_link(source)}" if source else "") + "\n"
    p.write_text(text.rstrip("\n") + "\n" + line, encoding="utf-8")
    _commit([p], f"öğrenim adayı: {candidate[:60]}", actor, candidate)
    return f"Aday deftere eklendi: {vault_ops._rel(p)}"


def learn_list() -> str:
    p = _vault() / CONCEPTS / "_Adaylar.md"
    rows = [l for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("- [ ]")] if p.exists() else []
    return "\n".join(rows) or "Açık öğrenim adayı yok."


def concept(title: str, text: str, points: list[str] | None = None, limits: str = "", sources: list[str] | None = None,
            actor: str = "claude") -> str:
    """Kavram notu oluşturur ya da var olana tarihli ekleme yapar; dizini günceller."""
    title = _clean(title)
    if not title or not text.strip():
        return "Hata: başlık ve açıklama gerekli."
    if vault_ops.SENSITIVE_RE.search(text):
        return "Hassas veri kavram notuna yazılmaz."
    sources = [s for s in sources or [] if s.strip()]
    if bad := _check_refs(sources):
        return f"Hata: kaynak bulunamadı: {', '.join(bad)}"
    p = _vault() / CONCEPTS / f"{safe_filename(title)}.md"
    src = "\n".join(f"- {_link(s)}" for s in sources) or "- kullanıcı beyanı"
    today = date.today()
    if p.exists():
        fm, body = split_note(p.read_text(encoding="utf-8"))
        add = f"\n### {today} ekleme\n{text.strip()}\n" + "".join(f"- {x}\n" for x in points or []) + (f"Kaynak:\n{src}\n" if sources else "")
        fm["updated"] = today
        p.write_text(dump_note(fm, body.rstrip() + "\n" + add), encoding="utf-8")
        verb = "güncellendi"
    else:
        fm = {"type": "kaynak", "status": "aktif", "tags": ["kavram"], "source": "manual", "source_id": f"kavram:{title.lower()}",
              "created": today, "updated": today, "due": None}
        body = (f"# {title}\n\n{text.strip()}\n\n## Önemli noktalar\n" + ("".join(f"- {x}\n" for x in points or []) or "-\n")
                + f"\n## Sınırlar / gerekçe\n{limits.strip() or '-'}\n\n## Kaynaklar\n{src}\n")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(dump_note(fm, body), encoding="utf-8")
        verb = "oluşturuldu"
    idx = knowledge_index()
    _commit([p, idx], f"kavram {verb}: {title}", actor, text)
    return f"Kavram notu {verb}: {vault_ops._rel(p)}"


def connect(a: str, b: str, why: str, actor: str = "claude") -> str:
    """İki not arasında gerekçeli bağlantı notu. Gerekçesiz bağlantı kurulmaz."""
    why = _clean(why)
    if len(why) < 15:
        return "Hata: bağlantı için gerçek bir gerekçe yaz (en az bir cümle)."
    pa, pb = vault_ops.find(a, 1), vault_ops.find(b, 1)
    if not pa or not pb:
        return f"Hata: not bulunamadı: {a if not pa else b}"
    na, nb = sorted([pa[0].stem, pb[0].stem])
    p = _vault() / LINKS / f"{safe_filename(na)} ↔ {safe_filename(nb)}.md"
    today = date.today()
    if p.exists():
        fm, body = split_note(p.read_text(encoding="utf-8"))
        fm["updated"] = today
        p.write_text(dump_note(fm, body.rstrip() + f"\n- {today}: {why}\n"), encoding="utf-8")
    else:
        fm = {"type": "kaynak", "status": "aktif", "tags": ["baglanti"], "source": "manual", "source_id": f"baglanti:{na}|{nb}",
              "created": today, "updated": today, "due": None}
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(dump_note(fm, f"# {na} ↔ {nb}\n\n[[{na}]] · [[{nb}]]\n\n## Neden bağlı\n- {today}: {why}\n"), encoding="utf-8")
    _commit([p], f"bağlantı: {na} ↔ {nb}", actor, why)
    return f"Bağlantı notu: {vault_ops._rel(p)}"


def knowledge_index() -> Path:
    """Kavramlar/_Dizin.md: her kavram ve bilgi notu tek satır (ilk cümle). Elle yazılan kısım korunur."""
    idx = _vault() / CONCEPTS / "_Dizin.md"
    _ensure(idx, "Bilgi dizini", "Kavram ve bilgi notlarının tek satırlık listesi. Ajan önce burayı, sonra yalnız ilgili notu okur.")
    rows = []
    for folder in (CONCEPTS, "40-Kaynaklar/Notlar"):
        for p in sorted((_vault() / folder).glob("*.md")) if (_vault() / folder).exists() else []:
            if p.name.startswith("_"):
                continue
            body = split_note(p.read_text(encoding="utf-8"))[1]
            first = next((l.strip() for l in body.splitlines() if l.strip() and not l.startswith(("#", "-", "<!--", ">"))), "")
            rows.append(f"- [[{p.stem}]] — {first[:140]}")
    fm, body = split_note(idx.read_text(encoding="utf-8"))
    idx.write_text(dump_note(fm, replace_auto(body, "dizin", "\n".join(rows) or "(henüz kavram yok)")), encoding="utf-8")
    return idx


# ---------------------------------------------------------------- sohbet izi / hata kataloğu
def trace(text: str, session: str = "", project: str = "", actor: str = "claude") -> str:
    text = _clean(text)
    if not text:
        return "Hata: iz boş."
    if len(text) > TRACE_MAX:
        return f"Hata: iz en fazla {TRACE_MAX} karakter ({len(text)} verildi); kısalt."
    if vault_ops.SENSITIVE_RE.search(text):
        return "Hassas veri sohbet izine yazılmaz."
    p = _vault() / TRACES / f"{date.today():%Y-%m}.md"
    _ensure(p, f"Sohbet izleri {date.today():%Y-%m}", "Dosya değişmeyen ama anlamlı sohbetlerin kısa özetleri (ajan beyanı).")
    body = p.read_text(encoding="utf-8")
    if text in body:
        return "Bu iz zaten kayıtlı."
    p.write_text(body.rstrip("\n") + f"\n\n{date.today()} · {_clean(project) or 'genel'} · {_clean(session)[:8] or '-'} · {text}\n",
                 encoding="utf-8")
    _commit([p], f"sohbet izi: {text[:50]}", actor, text)
    return f"İz kaydedildi: {vault_ops._rel(p)}"


def _err_key(s: str) -> str:
    return " ".join(re.findall(r"\w{3,}", vault_ops._fold(s)))[:120]


def error_log(error: str, fix: str = "", actor: str = "claude") -> str:
    """Hata kataloğuna yazar; aynı hata ikinci kez gelirse çözümü kalıcı kurala çevirir."""
    error, fix = _clean(error), _clean(fix)
    if not error:
        return "Hata: hata tanımı boş."
    p = _vault() / ERRORS
    _ensure(p, "Hata kataloğu", "Yaşanan hatalar ve çözümleri. Aynı hata ikinci kez yaşanınca çözüm Asistan kurallarına kural olur.")
    text = p.read_text(encoding="utf-8")
    key = _err_key(error)
    m = re.search(rf"^### (.+?) \(x(\d+)\) <!-- e:{re.escape(key)} -->$", text, re.M)
    today = date.today()
    if m:
        n = int(m.group(2)) + 1
        block = re.search(rf"^### .+? \(x\d+\) <!-- e:{re.escape(key)} -->\n(?:- .*\n?)*", text, re.M).group(0)
        known = fix or next(iter(re.findall(r"çözüm: (.+)", block)), "")
        new = (block.rstrip("\n").replace(f"(x{m.group(2)})", f"(x{n})", 1)
               + f"\n- {today}: tekrar" + (f" — çözüm: {fix}" if fix else "") + "\n")
        p.write_text(text.replace(block, new, 1), encoding="utf-8")
        _commit([p], f"hata tekrarı (x{n}): {error[:50]}", actor, fix)
        if n == 2 and known:
            vault_ops.add_rule(f"{error} → {known}", actor=actor)
            return f"Hata ikinci kez yaşandı; çözüm kalıcı kural oldu: {known}"
        return f"Hata kataloğu güncellendi (x{n})." + ("" if known else " Çözüm bilinmiyor: bulunca `--fix` ile yaz.")
    p.write_text(text.rstrip("\n") + f"\n\n### {error} (x1) <!-- e:{key} -->\n- {today}: ilk kez" + (f" — çözüm: {fix}" if fix else "") + "\n",
                 encoding="utf-8")
    _commit([p], f"hata kataloğu: {error[:50]}", actor, fix)
    return f"Hata kataloğuna eklendi: {vault_ops._rel(p)}"
