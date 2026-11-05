"""Dizin notları: hiçbir yere bağlı olmayan (gelen/giden [[bağlantısı]] olmayan) notlar grafikte kopuk nokta olarak dağılıyordu.
Her klasör grubu için bir dizin notu yazılır (`40-Kaynaklar/Dizinler/`), hepsi tek `Dizinler.md` notundan, o da Dashboard'dan bağlanır.
Otomatik bölüm (sb:auto) her çalışmada yenilenir; elle yazılan kısım korunur. Hiçbir şey gizlenmez: arşiv ve sistem notları da dizinlere girer."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .config import VAULT
from .notes import dump_note, replace_auto, split_note

DIR = "40-Kaynaklar/Dizinler"
SKIP = {".obsidian", ".git", ".trash", ".venv", "node_modules", "Dizinler"}
IGNORED = ("_system/ingest/", "_system/tools/", "_system/sb/")            # Obsidian userIgnoreFilters
LINK = re.compile(r"\[\[([^\]|#]+)")
BAD = set('|[]#^')


def _notes(v: Path) -> list[str]:
    out = []
    for p in v.rglob("*.md"):
        rel = p.relative_to(v).as_posix()
        if set(rel.split("/")[:-1]) & SKIP or rel.startswith(IGNORED):
            continue
        out.append(rel)
    return out


def _group(rel: str) -> str:
    parts = rel.split("/")
    if len(parts) == 1:
        return "Kök notlar"
    if parts[0] == "40-Kaynaklar" and len(parts) > 2:
        return parts[1]
    if parts[0] in ("90-Arşiv", "_system", "_templates", "_attachments"):
        base = {"90-Arşiv": "Arşiv", "_system": "Sistem", "_templates": "Şablonlar", "_attachments": "Ekler"}[parts[0]]
        return f"{base} {parts[1]}" if len(parts) > 2 else base
    return parts[0].split("-", 1)[-1] if re.match(r"\d\d-", parts[0]) else parts[0]


def orphans(v: Path | None = None) -> list[str]:
    v = v or VAULT
    notes = _notes(v)
    stems = defaultdict(list)
    for r in notes:
        stems[Path(r).stem.lower()].append(r)
    linked: set[str] = set()
    for r in notes:
        try:
            t = (v / r).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in LINK.findall(t):
            hit = stems.get(Path(m.strip()).name.lower())
            if hit and r not in hit:
                linked.add(r)
                linked.update(hit)
            elif hit:
                linked.update(x for x in hit if x != r)
    return sorted(r for r in notes if r not in linked)


def _write(path: Path, title: str, intro: str, name: str, body_md: str, tags: list[str]) -> None:
    block = f"<!-- sb:auto:{name}:start -->\n{body_md}\n<!-- sb:auto:{name}:end -->"
    if path.exists():
        fm, body = split_note(path.read_text(encoding="utf-8"))
        body = replace_auto(body, name, body_md) if f"sb:auto:{name}" in body else body + "\n" + block + "\n"
    else:
        fm = {"type": "dashboard", "tags": ["dashboard", *tags], "source": "derived", "source_id": ""}
        body = f"# {title}\n\n{intro}\n\n{block}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_note(fm, body), encoding="utf-8")


def build(vault: Path | None = None) -> str:
    v = vault or VAULT
    groups: dict[str, list[str]] = defaultdict(list)
    for r in orphans(v):
        if r.startswith(DIR + "/") or Path(r).stem in ("Dizinler",) or any(c in BAD for c in Path(r).stem):
            continue
        groups[_group(r)].append(r)
    d = v / DIR
    d.mkdir(parents=True, exist_ok=True)
    names = []
    for g, rels in sorted(groups.items()):
        title = f"Dizin – {g}"
        names.append((title, len(rels)))
        lines = [f"- [[{r[:-3]}|{Path(r).stem}]]" for r in rels]
        _write(d / f"{title}.md", title, f"«{g}» altında başka notlara bağlı olmayan notlar. Grafikte kopuk durmasınlar diye burada toplanır.",
               "dizin", "\n".join(lines), ["dizin"])
    keep = {f"{t}.md" for t, _ in names} | {"Dizinler.md"}
    for f in d.glob("Dizin – *.md"):
        if f.name not in keep:
            f.unlink()                                                       # artık bağlantısız not kalmayan grup
    top = "\n".join(f"- [[{DIR}/{t}|{t}]] ({n})" for t, n in names) or "_Bağlantısız not yok._"
    _write(d / "Dizinler.md", "Dizinler", "Bağlantısız notların klasör dizinleri. Her gün otomatik yenilenir.", "dizinler", top, ["dizin"])
    dash = v / "Dashboard.md"
    if dash.exists():
        t = dash.read_text(encoding="utf-8")
        if "[[Dizinler" not in t:
            dash.write_text(t.rstrip("\n") + f"\n\n- [[{DIR}/Dizinler|Dizinler]] — bağlantısız notların dizini\n", encoding="utf-8")
    return f"dizinler: {sum(n for _, n in names)} bağlantısız not, {len(names)} dizin"
