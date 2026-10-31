"""Hafıza hijyeni (salt okunur rapor; hiçbir şeyi değiştirmez): `sb hygiene`, haftalık çalışma ve sabah raporu kullanır.

- Tekrar: aynı başlıklı birden çok not (90-Arşiv hariç) → birleştirilmeli mi?
- Kopuk bağlantı: [[hedef]] kasada yok (otomatik bölümler dahil; şablonlar hariç)
- Bayat: `aktif` proje/kaynak notu 120 günden uzun süredir güncellenmemiş
- Büyüyen dosya: Son oturum / Açık konular / kurallar / hafıza sınırı aşıyor (kartlar `compact_cards` ile arşive gider)
- Bekleyen kutu: 00-Inbox/Dump'ta 7 günden eski işlenmemiş not; açık öğrenim adayları
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from .config import VAULT
from .notes import SKIP_DIRS, split_note

LINK_RE = re.compile(r"\[\[([^\]|#^]+)")
LIMITS = {"Son oturum.md": 12_000, "Açık konular.md": 8_000, "Asistan kuralları.md": 4_000, "Asistan hafızası.md": 4_000}
STALE_DAYS = 120


def _notes(vault: Path):
    for p in vault.rglob("*.md"):
        parts = p.relative_to(vault).parts
        if any(x in SKIP_DIRS for x in parts[:-1]) or parts[0] == "90-Arşiv":
            continue
        yield p


def _key(s: str) -> str:
    return " ".join(s.lower().translate(str.maketrans("ıİğüşöç", "iigusoc")).split())


def report(vault: Path = VAULT, today: date | None = None, limit: int = 15) -> dict:
    today = today or date.today()
    notes = list(_notes(vault))
    stems = {_key(p.stem) for p in vault.rglob("*.md")} | {_key(p.relative_to(vault).with_suffix("").as_posix()) for p in notes}
    stems |= {_key(p.name) for p in vault.rglob("*") if p.is_file() and p.suffix != ".md"}     # ek dosyalar (pdf, png)
    by_title, broken, stale = defaultdict(list), [], []
    for p in notes:
        rel = p.relative_to(vault).as_posix()
        by_title[_key(p.stem)].append(rel)
        text = p.read_text(encoding="utf-8", errors="replace")
        for target in {t.strip() for t in LINK_RE.findall(re.sub(r"`[^`\n]*`", "", text))}:   # koddaki [[örnek]] sayılmaz
            if _key(target) not in stems and _key(Path(target).name) not in stems:
                broken.append(f"{rel} → [[{target}]]")
        fm = split_note(text)[0]
        upd = fm.get("updated")
        if fm.get("type") in ("proje", "kaynak") and fm.get("status") == "aktif" and isinstance(upd, date) \
                and (today - upd).days > STALE_DAYS:
            stale.append(f"{rel} ({(today - upd).days} gün)")
    mirror = "40-Kaynaklar/Bilgisayar/"                         # bilgisayar klasör aynaları proje notuyla aynı adı bilerek taşır
    dups = [" | ".join(v) for k, v in by_title.items()
            if len([x for x in v if not x.startswith(mirror)]) > 1 and not k.startswith(("_", "readme"))]
    big = [f"{n}: {len((vault / n).read_text(encoding='utf-8'))} karakter (sınır {lim})" for n, lim in LIMITS.items()
           if (vault / n).exists() and len((vault / n).read_text(encoding="utf-8")) > lim]
    dump = vault / "00-Inbox" / "Dump"
    old = [p.name for p in dump.glob("*.md") if date.fromtimestamp(p.stat().st_mtime) < today - timedelta(days=7)] if dump.exists() else []
    cand = vault / "40-Kaynaklar" / "Kavramlar" / "_Adaylar.md"
    open_c = sum(1 for l in cand.read_text(encoding="utf-8").splitlines() if l.startswith("- [ ]")) if cand.exists() else 0
    return {"duplicates": dups, "broken_links": broken, "stale": stale, "oversized": big, "old_inbox": old,
            "open_candidates": open_c, "limit": limit}


def render(r: dict) -> str:
    lim = r["limit"]
    out = []
    for title, key in (("Aynı başlıklı notlar", "duplicates"), ("Kopuk bağlantılar", "broken_links"),
                       ("Bayat aktif notlar", "stale"), ("Büyüyen dosyalar", "oversized"), ("Kutuda bekleyen (7+ gün)", "old_inbox")):
        items = r[key]
        if items:
            out.append(f"{title} ({len(items)}):\n" + "\n".join(f"- {x}" for x in items[:lim]) + ("\n- ..." if len(items) > lim else ""))
    if r["open_candidates"]:
        out.append(f"Açık öğrenim adayı: {r['open_candidates']} (sb learn --list)")
    return "\n\n".join(out) or "Hijyen temiz: tekrar, kopuk bağlantı, bayat not ve büyüyen dosya yok."


def summary_line(r: dict) -> str:
    n = {k: len(r[k]) for k in ("duplicates", "broken_links", "stale", "oversized", "old_inbox")}
    if not any(n.values()) and not r["open_candidates"]:
        return ""
    return (f"Hafıza hijyeni: {n['duplicates']} tekrar başlık, {n['broken_links']} kopuk bağlantı, {n['stale']} bayat not, "
            f"{n['oversized']} büyüyen dosya, {n['old_inbox']} bekleyen kutu notu, {r['open_candidates']} öğrenim adayı (sb hygiene)")
