"""Second Brain skill'lerini Claude Code'a kurar: _system/skills/<ad>/ → ~/.claude/skills/<ad>/ (kullanıcı geneli, her proje).

Tekrar çalıştırılabilir. Aynı adla kullanıcının kendi yazdığı (bu paketten gelmeyen) skill varsa ÜZERİNE YAZMAZ, uyarır.
Paket skill'leri `.sb-skill` işaret dosyası taşır; yalnız işaretliler güncellenir.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "skills"
DST = Path.home() / ".claude" / "skills"
MARK = ".sb-skill"


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    for s in sorted(p for p in SRC.iterdir() if (p / "SKILL.md").exists()):
        d = DST / s.name
        if d.exists() and not (d / MARK).exists():
            print(f"Atlandı (aynı adla senin skill'in var): {d}")
            continue
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(s, d)
        (d / MARK).write_text("Second Brain paketinden; tools/install_skills.py günceller.\n", encoding="utf-8")
        print(f"Kuruldu: {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
