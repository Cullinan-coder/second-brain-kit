"""Arsenal: kasa kökünde "Araçlar ve erişimler.md" — sistemin neye bağlı olduğu, neyin çalıştığı, kısayollar.

`sb doctor` kontrollerinden ve kasadaki notların kaynak sayımından üretilir (sb:auto bölümleri; elle yazılan kısım korunur).
Şifre, anahtar, belirteç YAZILMAZ: yalnız "bağlı mı" bilgisi.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from . import doctor
from .config import VAULT
from .notes import dump_note, replace_auto, split_note

NOTE = VAULT / "Araçlar ve erişimler.md"
SKIP = {".obsidian", ".git", ".trash", "_system", "90-Arşiv", "_templates"}
SOURCE_NAMES = {
    "gmail-main": "Gmail (ana)", "gmail-side": "Gmail (ikinci)", "gcal": "Google Takvim", "gdrive": "Google Drive",
    "contacts": "Rehber", "sms": "SMS/arama", "linkedin": "LinkedIn", "obs": "ÖBS", "github": "GitHub",
    "workspace": "Bilgisayardaki projeler", "telegram": "Telegram", "mail": "Mail (türetilmiş)", "web": "Beyne at (web/video)",
    "derived": "Türetilmiş (bağlantı notları)", "manual": "Elle / asistan",
}
SHORTCUTS = """| Ne | Nasıl |
|---|---|
| Beyne at | Bağlantıyı ya da metni kopyala → **Ctrl+Alt+B** (video/sayfa özetlenir, metin not kutusuna düşer) |
| Asistan | Obsidian'da `Asistan` notu ya da telefondan Tailscale adresi |
| Hızlı not | Asistana "not al: ..." ya da `00-Inbox/Dump`'a dosya |
| Geri al | Asistana "geri al" ya da `sb asistan-undo` |
| Durum | `sb doctor` |
| Güncelle | `sb update` (kit kullanıyorsan) |"""


def source_counts() -> Counter:
    c: Counter = Counter()
    for p in VAULT.rglob("*.md"):
        if SKIP & set(p.relative_to(VAULT).parts):
            continue
        try:
            fm = split_note(p.read_text(encoding="utf-8"))[0]
        except Exception:
            continue
        if src := fm.get("source"):
            c[str(src)] += 1
    return c


def render(rows: list[tuple[str, str, str]], counts: Counter) -> tuple[str, str]:
    t = ["| Durum | Parça | Eksikse |", "|---|---|---|"]
    t += [f"| {st} | {name} | {hint if st != doctor.OK else ''} |" for st, name, hint in rows]
    ok = sum(1 for r in rows if r[0] == doctor.OK)
    t.append(f"\n_{ok}/{len(rows)} hazır · {datetime.now():%Y-%m-%d %H:%M}_")
    s = ["| Kaynak | Not sayısı |", "|---|---|"]
    s += [f"| {SOURCE_NAMES.get(k, k)} | {v} |" for k, v in counts.most_common()]
    return "\n".join(t), "\n".join(s)


def build(rows=None, counts=None) -> str:
    status, sources = render(rows if rows is not None else doctor.checks(), counts if counts is not None else source_counts())
    if NOTE.exists():
        fm, body = split_note(NOTE.read_text(encoding="utf-8"))
    else:
        fm = {"type": "dashboard", "tags": ["dashboard", "arsenal"]}
        body = ("# Araçlar ve erişimler\n\nSistemin bağlı olduğu her şey ve kısayollar. Otomatik bölümler her gün yenilenir; "
                "altına kendi notlarını yazabilirsin (korunur).\n\n## Kısayollar\n" + SHORTCUTS + "\n\n## Durum\n\n## Veri kaynakları\n")
    body = replace_auto(body, "arsenal-durum", status) if "sb:auto:arsenal-durum" in body else \
        body.replace("## Durum\n", "## Durum\n" + _block("arsenal-durum", status) + "\n", 1)
    body = replace_auto(body, "arsenal-kaynak", sources) if "sb:auto:arsenal-kaynak" in body else \
        body.replace("## Veri kaynakları\n", "## Veri kaynakları\n" + _block("arsenal-kaynak", sources) + "\n", 1)
    NOTE.write_text(dump_note(fm, body), encoding="utf-8")
    return str(NOTE)


def _block(name: str, content: str) -> str:
    return f"<!-- sb:auto:{name}:start -->\n{content}\n<!-- sb:auto:{name}:end -->"
