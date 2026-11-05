"""m0003 — UZEM ders dosyaları git ve Syncthing dışında: `.gitignore` ve `.stignore` dosyalarına `40-Kaynaklar/UZEM` satırlarını ekler.

Neden: `sb uzem sync` ders dosyalarını (telifli, büyük) kasanın içine, `40-Kaynaklar/UZEM/` altına indirir; kasa her gün GitHub'a gider ve
telefona eşitlenir. Bu göç satırlar yoksa ekler (idempotent); `sb uzem sync` yazmadan önce `git check-ignore` ile ayrıca doğrular.
"""
from __future__ import annotations

from pathlib import Path

VERSION = 3
DESCRIPTION = "UZEM ders dosyalarını (40-Kaynaklar/UZEM) .gitignore ve .stignore'a ekle"

FILES = {
    ".gitignore": ("# UZEM ders dosyaları: kasada durur ama GitHub'a gitmez (telif, boyut)",
                   ["40-Kaynaklar/UZEM/**", "!40-Kaynaklar/UZEM/**/*.md"]),
    ".stignore": ("// UZEM ders dosyalari (telif, buyuk): telefona gitmesin. Telefonda da istersen bu satiri sil.",
                  ["40-Kaynaklar/UZEM"]),
}


def up(vault: Path, dry_run: bool) -> list[str]:
    out: list[str] = []
    for name, (comment, lines) in FILES.items():
        p = vault / name
        if not p.exists() and name == ".stignore":          # Syncthing kullanılmıyor: dosya oluşturma
            continue
        text = p.read_text(encoding="utf-8") if p.exists() else ""
        have = {ln.strip() for ln in text.splitlines()}
        missing = [ln for ln in lines if ln not in have]
        if not missing:
            continue
        out.append(f"{name}: + {', '.join(missing)}")
        if not dry_run:
            add = ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "") + comment + "\n" + "\n".join(missing) + "\n"
            p.write_text(text + add, encoding="utf-8", newline="\n")
    return out
