"""Görevler (`25-Görevler/`) ve kişi notlarında beyan/çıkarım.

Görev: `type: gorev`, durum inbox|aktif|bekliyor|engelli|tamamlandi|iptal, `owner` (sorumlu), `project`, `revision`.
İsteğe bağlı bitiş sözleşmesi: `completion_criterion` (gözlenebilir ölçüt) verilen görev `tamamlandi` yapılırken kasada var
olan kanıt dosyaları (`evidence`) zorunludur; görevin kendi dosyası kanıt olamaz. Kanıt yolu, işin bağımsız doğrulandığı
anlamına gelmez; yalnız "neye dayanarak bitti dendi" izidir. İptal için kanıt gerekmez.

Kişi: `aliases` (takma adlar; aramada eşleşir), `## Beyan` (kullanıcının söylediği, tarihli), `## Çıkarım (onay bekliyor)`
(modelin tahmini; onaylanana kadar olgu sayılmaz), reddedilen çıkarım `~~...~~ (reddedildi YYYY-AA-GG)` olur ve bağlama girmez.
"""
from __future__ import annotations

import re
from datetime import date

from . import vault_ops
from .notes import dump_note, safe_filename, split_note

FOLDER = "25-Görevler"
STATUSES = ("inbox", "aktif", "bekliyor", "engelli", "tamamlandi", "iptal")


def _commit(p, msg: str, detail: str = "", actor: str = "claude") -> str:
    rel = vault_ops._rel(p)
    sha = vault_ops.commit([rel], msg)
    vault_ops.log(actor, msg.split(":")[0], rel, detail[:160], sha)
    return sha


def add(title: str, text: str = "", owner: str = "", project: str = "", due: str | None = None, criterion: str = "",
        status: str = "aktif", actor: str = "claude") -> str:
    title = " ".join(title.split())
    if not title:
        return "Hata: başlık boş."
    if not owner:
        return "Hata: sorumlu (owner) yaz; uydurma — bilinmiyorsa kullanıcıya sor."
    if status not in STATUSES:
        return f"Hata: durum şunlardan biri olmalı: {', '.join(STATUSES)}"
    if vault_ops.SENSITIVE_RE.search(title + " " + text):
        return "Hassas veri göreve yazılmaz."
    p = vault_ops.VAULT / FOLDER / f"{safe_filename(title)}.md"
    if p.exists():
        return f"Bu adla görev zaten var: {vault_ops._rel(p)} (güncellemek için sb task update)."
    today = date.today()
    fm = {"type": "gorev", "status": status, "tags": ["gorev"], "source": "manual", "source_id": f"gorev:{title.lower()}",
          "created": today, "updated": today, "due": date.fromisoformat(due) if due else None, "owner": owner,
          "project": project or None, "revision": 1}
    if criterion:
        fm["completion_criterion"] = criterion
        fm["evidence"] = []
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_note(fm, f"# {title}\n\n{text.strip()}\n\n## Geçmiş\n- {today}: oluşturuldu ({status})\n"), encoding="utf-8")
    _commit(p, f"görev: {title}", text, actor)
    return f"Görev oluşturuldu: {vault_ops._rel(p)}"


def update(query: str, status: str = "", evidence: list[str] | None = None, note: str = "", expected_revision: int | None = None,
           actor: str = "claude") -> str:
    hits = [p for p in vault_ops.find(query, 5) if vault_ops._rel(p).startswith(FOLDER)]
    if not hits:
        return f"Görev bulunamadı: {query}"
    p = hits[0]
    fm, body = split_note(p.read_text(encoding="utf-8"))
    rev = int(fm.get("revision") or 1)
    if expected_revision is not None and expected_revision != rev:
        return f"Çakışma: görev revizyonu {rev}, sen {expected_revision} bekliyordun. Yeniden oku."
    if status and status not in STATUSES:
        return f"Hata: durum şunlardan biri olmalı: {', '.join(STATUSES)}"
    ev = [e.strip() for e in evidence or [] if e.strip()]
    if ev:
        missing = [e for e in ev if not (vault_ops.VAULT / e).exists()]
        if missing:
            return f"Hata: kanıt dosyası kasada yok: {', '.join(missing)}"
        if any(vault_ops.VAULT / e == p for e in ev):
            return "Hata: görevin kendi dosyası kanıt olamaz."
        fm["evidence"] = sorted(set(fm.get("evidence") or []) | set(ev))
    if status == "tamamlandi" and fm.get("completion_criterion") and not fm.get("evidence"):
        return (f"Bitirilemez: bu görevin bitiş ölçütü var ({fm['completion_criterion']}). Ölçütü karşılayan kanıt dosyasını "
                "--evidence <kasa-yolu> ile ver.")
    old = fm.get("status")
    if status:
        fm["status"] = status
    fm["revision"] = rev + 1
    fm["updated"] = date.today()
    line = f"- {date.today()}: " + ", ".join(x for x in [f"{old} → {status}" if status and status != old else "",
                                                          f"kanıt: {', '.join(ev)}" if ev else "", note.strip()] if x)
    p.write_text(dump_note(fm, body.rstrip() + "\n" + line + "\n"), encoding="utf-8")
    _commit(p, f"görev güncellendi: {p.stem}", line, actor)
    return f"Görev güncellendi (rev {rev + 1}): {vault_ops._rel(p)}"


def listing(status: str = "") -> str:
    folder = vault_ops.VAULT / FOLDER
    rows = []
    for p in sorted(folder.glob("*.md")) if folder.exists() else []:
        fm = split_note(p.read_text(encoding="utf-8"))[0]
        if status and fm.get("status") != status:
            continue
        if not status and fm.get("status") in ("tamamlandi", "iptal"):
            continue
        rows.append(f"- [{fm.get('status')}] {p.stem} · {fm.get('owner') or '?'}" + (f" · {fm.get('project')}" if fm.get("project") else "")
                    + (f" · son {fm.get('due')}" if fm.get("due") else "") + (" · kanıtlı" if fm.get("completion_criterion") else ""))
    return "\n".join(rows) or "Açık görev yok."


# ---------------------------------------------------------------- kişi notları
INFER = "## Çıkarım (onay bekliyor)"


def _sections(body: str) -> str:
    for h in ("## Beyan", INFER, "## Temaslar"):
        if h not in body:
            body = body.rstrip() + f"\n\n{h}\n"
    return body


def person_fact(name: str, fact: str, inference: bool = False, reject: bool = False, alias: str = "", actor: str = "claude") -> str:
    hits = [p for p in vault_ops.find(name, 5) if vault_ops._rel(p).startswith("60-Kişiler")]
    if not hits:
        return f"Kişi notu bulunamadı: {name} (önce rehberde/kasada ara; yeni kişi için not aç)."
    p = hits[0]
    fact = " ".join(fact.split())
    if vault_ops.SENSITIVE_RE.search(fact) or re.search(r"sağlık|hastalık|siyasi|dini|maaş|borç", fact, re.I):
        return "Hassas bilgi (sağlık, siyasi/dini görüş, finans, kimlik) kişi notuna yazılmaz."
    fm, body = split_note(p.read_text(encoding="utf-8"))
    body = _sections(body)
    today = date.today()
    if alias:
        fm["aliases"] = sorted(set(fm.get("aliases") or []) | {alias.strip()})
    if reject:
        lines = body.splitlines()
        for i, l in enumerate(lines):
            if l.startswith("- ") and fact.lower() in l.lower() and "reddedildi" not in l:
                lines[i] = f"- ~~{l[2:]}~~ (reddedildi {today})"
                break
        else:
            return "Reddedilecek çıkarım bulunamadı."
        body = "\n".join(lines) + "\n"
        what = "çıkarım reddedildi"
    elif fact:
        head = INFER if inference else "## Beyan"
        entry = f"- {today} ({'çıkarım' if inference else 'kullanıcı'}): {fact}"
        body = body.replace(head + "\n", head + "\n" + entry + "\n", 1)
        what = "çıkarım" if inference else "beyan"
    else:
        what = "takma ad"
    fm["updated"] = today
    p.write_text(dump_note(fm, body), encoding="utf-8")
    _commit(p, f"kişi {what}: {p.stem}", fact or alias, actor)
    return f"{p.stem}: {what} kaydedildi."


def strip_rejected(text: str) -> str:
    """Reddedilmiş çıkarım satırları bağlama girmez."""
    return "\n".join(l for l in text.splitlines() if "(reddedildi " not in l)
