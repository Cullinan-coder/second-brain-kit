"""ÖBS verisi (`_system/data/obs.yaml`, elle aktarılır) → akademik notlar.

- `10-Dersler/Akademik Durum.md`: özet, riskler, eksik dersler, dönem dönem notlar.
- Bu dönemki dersler (takvimden gelen `ders:<KOD>` notları): sadece "Not geçmişi" otomatik bölümü yazılır.
- Geçmiş dersler: `10-Dersler/Geçmiş/<KOD Ad>.md` (status tamamlandi / tekrar).
Kimlik bilgileri (TCKN, doğum tarihi) veri dosyasında yoktur ve buraya yazılmaz.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

import yaml

from .config import SYSTEM
from .notes import NoteSpec

ROOT = "10-Dersler"
PASS = {"AA", "BA", "BB", "CB", "CC", "G"}


def load() -> dict:
    return yaml.safe_load((SYSTEM / "data" / "obs.yaml").read_text(encoding="utf-8"))


def _history(data: dict) -> dict[str, list[tuple[str, str, str, str, int]]]:
    """kod → [(dönem, ad, not, durum, akts), ...] (eskiden yeniye)."""
    h: dict[str, list] = defaultdict(list)
    for d in data["donemler"]:
        for code, name, akts, grade, status in d["dersler"]:
            h[code].append((d["ad"], name, grade, status, akts))
    return h


def _history_md(rows: list) -> str:
    lines = ["| Dönem | Not | Durum |", "|---|---|---|"]
    lines += [f"| {t} | {g} | {s} |" for t, _, g, s, _ in rows]
    return "\n".join(lines)


def build_specs(data: dict) -> list[NoteSpec]:
    hist = _history(data)
    content = data.get("icerikler") or {}
    active = {c for d in data["donemler"] if d.get("aktif") for c, *_ in d["dersler"]}
    specs = [_summary_spec(data, hist, active)]
    for code, rows in sorted(hist.items()):
        name = rows[-1][1]
        if code in active:
            # Takvimden gelen mevcut ders notuna sadece not geçmişi bölümü yazılır.
            specs.append(NoteSpec(
                folder=f"{ROOT}/{code} {name}", title=f"{code} {name}",
                frontmatter={"type": "ders", "status": "aktif", "tags": ["ders"], "source": "gcal",
                             "source_id": f"ders:{code}", "due": None},
                owned=(), auto={"not-gecmisi": _history_md(rows), **({"icerik": content[code]} if code in content else {})},
            ))
            continue
        passed = rows[-1][3] == "Başarılı"
        specs.append(NoteSpec(
            folder=f"{ROOT}/Geçmiş", title=f"{code} {name}",
            frontmatter={"type": "ders", "status": "tamamlandi" if passed else "tekrar", "tags": ["ders", "gecmis"],
                         "source": "obs", "source_id": f"ders:{code}", "due": None, "code": code,
                         "semester": rows[-1][0], "akts": rows[-1][4], "grade": rows[-1][2]},
            owned=("status", "semester", "akts", "grade"),
            body=f"# {code} {name}\n\n## Ders içeriği\n<!-- sb:auto:icerik:start -->\n<!-- sb:auto:icerik:end -->\n\n"
                 "## Not geçmişi\n<!-- sb:auto:not-gecmisi:start -->\n<!-- sb:auto:not-gecmisi:end -->\n\n"
                 "## Notlar ve dosyalar\n",
            auto={"not-gecmisi": _history_md(rows), "icerik": content.get(code, "ÖBS ders içeriği belgesinde yok.")},
        ))
    return specs


def _summary_spec(data: dict, hist: dict, active: set[str]) -> NoteSpec:
    o, s = data["ozet"], data["ogrenci"]
    need = o["gereken_akts"]
    lines = [
        f"**{s['program']}** · {s['sinif']} · öğrenci no {s['numara']} · ÖBS anlık görüntüsü: {data['snapshot']}",
        "",
        f"- **AGNO: {o['agno']}** (DC = koşullu geçer; GNO 2.00 altındayken DC dersler başarısız sayılabilir)",
        f"- Başarılan AKTS: **{o['basarilan_akts']} / {need['zorunlu']}** zorunlu "
        f"(+ seçmeli I {need['secmeli_grup_I']}, II {need['secmeli_grup_II']}, III {need['secmeli_grup_III']}, "
        f"IV {need['secmeli_grup_IV']}, üniversite seçmeli {need['universite_secmeli']})",
        "",
        "### Dikkat",
    ]
    for code, rows in sorted(hist.items()):
        fails = [r for r in rows if r[3] == "Başarısız"]
        if len(fails) >= 2 or (fails and code in active):
            tag = "bu dönem tekrar alınıyor" if code in active else "henüz geçilmedi"
            lines.append(f"- {code} {rows[-1][1]}: {len(fails)} kez başarısız ({', '.join(r[2] for r in fails)}) — {tag}")
    lines += ["", "### Eksik / alınmamış dersler", "| Kod | Ders | AKTS | Not |", "|---|---|---|---|"]
    for code, name, akts, note in data["eksikler"]:
        lines.append(f"| {code or '—'} | {name} | {akts} | {note} |")
    for d in reversed(data["donemler"]):
        head = f"### {d['ad']}" + (" (aktif dönem)" if d.get("aktif") else f" — DNO {d['dno']}, GNO {d['gno']}")
        lines += ["", head, "| Kod | Ders | AKTS | Not | Durum |", "|---|---|---|---|---|"]
        lines += [f"| {c} | {n} | {a} | {g} | {st} |" for c, n, a, g, st in d["dersler"]]
    return NoteSpec(
        folder=ROOT, title="Akademik Durum",
        frontmatter={"type": "akademik", "status": "aktif", "tags": ["akademik", "obs"], "source": "obs",
                     "source_id": "obs:durum", "due": None, "agno": o["agno"], "akts": o["basarilan_akts"],
                     "obs_snapshot": date.fromisoformat(str(data["snapshot"]))},
        owned=("agno", "akts", "obs_snapshot"),
        body="# Akademik Durum\n\nKaynak: ÖBS (elle aktarım, `_system/data/obs.yaml`). Kimlik bilgileri bilerek yazılmaz.\n\n"
             "<!-- sb:auto:durum:start -->\n<!-- sb:auto:durum:end -->\n\n## Notlar\n",
        auto={"durum": "\n".join(lines)},
    )
