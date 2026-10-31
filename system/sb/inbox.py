"""Hızlı not kutusu (00-Inbox/Dump): kullanıcı ne aklına gelirse düzensizce atar; günlük çalışma notları yerine dağıtır.

- add(text): kutuya zaman damgalı not (asistanın "not al" aracı, Obsidian'da elle de eklenebilir).
- process(): her not için yerel model (llm.yaml tasks.inbox) şu kararlardan birini verir:
    append    → var olan proje/ders/kişi/konu notuna tek satır ("## Asistan notları")
    knowledge → 40-Kaynaklar/Notlar/<başlık>.md (yeni bilgi notu ya da var olana ekleme)
    keep      → anlaşılmadı/kararsız; kutuda kalır, sabah raporunda görünür
  İşlenen ham not 90-Arşiv'e taşınır (silinmez). Her değişiklik vault_ops üzerinden git commit + günlük kaydıdır.
"""
from __future__ import annotations

import json
from datetime import date, datetime

from . import llm, vault_ops
from .notes import dump_note, safe_filename, split_note
from .config import USER

DUMP = vault_ops.VAULT / "00-Inbox" / "Dump"
KNOWLEDGE = "40-Kaynaklar/Notlar"
SCHEMA = {"type": "object", "required": ["action", "target", "line", "title"], "properties": {
    "action": {"type": "string", "enum": ["append", "knowledge", "keep"]},
    "target": {"type": "string", "description": "append için adaylardan birinin yolu; değilse boş"},
    "line": {"type": "string", "description": "notun temiz, tek-iki cümlelik hali (Türkçe)"},
    "title": {"type": "string", "description": "knowledge için kısa konu başlığı; değilse boş"}}}


def add(text: str, source: str = "asistan") -> str:
    text = text.strip()
    if not text:
        return "Hata: boş not."
    if vault_ops.SENSITIVE_RE.search(text):
        return "Hassas veri (şifre, kart, kimlik, IBAN) kutuya yazılmaz."
    DUMP.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    p = DUMP / f"{now:%Y-%m-%d %H%M%S}.md"
    n = 2
    while p.exists():                                # aynı saniyede ikinci not üstüne yazmasın
        p = DUMP / f"{now:%Y-%m-%d %H%M%S} ({n}).md"
        n += 1
    p.write_text(dump_note({"type": "inbox", "tags": ["inbox"], "source": source, "created": now.date()}, text + "\n"),
                 encoding="utf-8")
    rel = vault_ops._rel(p)
    sha = vault_ops.commit([rel], f"kutuya not: {text[:50]}")
    vault_ops.log("asistan", "not al", rel, text[:120], sha)
    return f"Kutuya not alındı: {text[:80]} (günlük çalışma yerine dağıtacak)"


def _candidates(text: str) -> list[str]:
    from .chat import keywords
    out: list[str] = []
    for w in keywords(text, limit=8):
        for p in vault_ops.find(w, limit=3):
            rel = vault_ops._rel(p)
            if not rel.startswith("00-Inbox") and rel not in out:
                out.append(rel)
    return out[:10]


def decide(text: str, cands: list[str]) -> dict:
    prompt = (
        f"kullanıcının ({USER}) hızlı notunu ikinci beynine yerleştir. Notu UYDURMA, yalnız temizle ve özetle.\n"
        f"NOT:\n{text[:3000]}\n\nİLGİLİ OLABİLECEK MEVCUT NOTLAR (yol):\n" + ("\n".join(cands) or "(yok)") + "\n\n"
        "Karar: not açıkça bu notlardan birine (proje, ders, kişi, konu) aitse action=append ve target o yol. Not bir ders kodu "
        "(ör. YPZ301) ya da proje adı içeriyorsa o dersin/projenin ANA notuna (klasörle aynı adlı not) append et; genel bir bilgi, "
        "fikir ya da öğrenilen şeyse action=knowledge ve kısa bir title; ne olduğu anlaşılmıyorsa action=keep. "
        "line: notun temiz Türkçe hali (tek-iki cümle). JSON döndür.")
    raw, _ = llm.complete("inbox", prompt, schema=SCHEMA, timeout=600)
    d = json.loads(raw)
    if d.get("action") == "append" and d.get("target") not in cands:
        d["action"] = "keep"                                   # aday dışı yol uydurduysa dokunma
    return d


def _knowledge(title: str, line: str, src: str) -> str:
    folder = vault_ops.VAULT / KNOWLEDGE
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"{safe_filename(title.strip() or 'Not')}.md"
    if p.exists():
        return vault_ops.update(vault_ops._rel(p), append=line, actor="inbox")
    today = date.today()
    fm = {"type": "kaynak", "status": "aktif", "tags": ["not", "inbox"], "source": "manual", "source_id": f"inbox:{src}",
          "created": today, "updated": today, "due": None}
    p.write_text(dump_note(fm, f"# {title.strip()}\n\n- {today:%Y-%m-%d}: {line}\n"), encoding="utf-8")
    rel = vault_ops._rel(p)
    sha = vault_ops.commit([rel], f"yeni bilgi notu: {title[:50]}")
    vault_ops.log("inbox", "bilgi notu", rel, line[:120], sha)
    return f"Yeni bilgi notu: {rel}"


def process(dry_run: bool = False, decider=decide) -> list[str]:
    report = []
    for p in sorted(DUMP.glob("*.md")) if DUMP.exists() else []:
        text = split_note(p.read_text(encoding="utf-8"))[1].strip()
        if not text:
            continue
        try:
            d = decider(text, _candidates(text))
        except Exception as e:                                 # model hatası: not kutuda kalır
            report.append(f"{p.stem}: işlenemedi ({type(e).__name__})")
            continue
        action, line = d.get("action"), (d.get("line") or text).strip()
        if dry_run or action == "keep":
            report.append(f"{p.stem}: {action} → {d.get('target') or d.get('title') or ''} | {line[:80]}")
            continue
        out = (vault_ops.update(d["target"], append=line, actor="inbox") if action == "append"
               else _knowledge(d.get("title") or line[:40], line, p.stem))
        vault_ops.archive(vault_ops._rel(p), f"kutudan işlendi: {action}", actor="inbox")
        report.append(f"{p.stem}: {out}")
    return report
