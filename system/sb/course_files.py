"""Bilgisayardaki ders dosyaları → ders notlarının "Dosyalar" otomatik bölümü (sadece link, kopya yok).

Eşleştirme `_system/config/course_files.yaml`. Linkler `file:///` biçimindedir; Obsidian masaüstünde
tıklanınca dosyayı açar. Ders notu takvimden (`gcal`) ya da ÖBS'den (`obs`) gelmiş olabilir; hangisi
varsa o güncellenir, yoksa yeni not oluşturulmaz.
"""
from __future__ import annotations

import fnmatch
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import yaml

from .config import LMS, SYSTEM
from .notes import NoteSpec, Vault

MAX_PER_COURSE = 300


def load() -> dict:
    return yaml.safe_load((SYSTEM / "config" / "course_files.yaml").read_text(encoding="utf-8"))


def _expand(pattern: str, roots: dict[str, str]) -> list[Path]:
    head, _, rest = pattern.partition("/")
    base = Path(roots[head]).expanduser() if head in roots else Path(pattern).expanduser()
    if head not in roots:
        rest = ""
    target = base / rest if rest else base
    if not any(ch in rest for ch in "*?["):
        if target.is_dir():
            return [p for p in target.rglob("*") if p.is_file()]
        return [target] if target.is_file() else []
    out = []
    for p in base.glob(rest):
        out += [q for q in p.rglob("*") if q.is_file()] if p.is_dir() else [p]
    return out


def files_for(cfg: dict) -> dict[str, list[Path]]:
    skip = cfg.get("skip", [])
    result: dict[str, list[Path]] = {}
    for code, patterns in cfg["courses"].items():
        seen: dict[str, Path] = {}
        for pat in patterns:
            for p in _expand(pat, cfg["roots"]):
                if any(fnmatch.fnmatch(p.name, s) for s in skip) or any(part in (".git", "node_modules", ".venv", "build") for part in p.parts):
                    continue
                seen[str(p).lower()] = p
        result[code] = sorted(seen.values(), key=lambda p: str(p).lower())
    return result


def _link(p: Path) -> str:
    return "file:///" + quote(p.as_posix(), safe=":/")


def render(files: list[Path], home: Path) -> str:
    if not files:
        return "### Dosyalar\nEşleşen dosya yok (`_system/config/course_files.yaml`)."
    groups: dict[str, list[Path]] = defaultdict(list)
    for p in files[:MAX_PER_COURSE]:
        try:
            folder = p.parent.relative_to(home).as_posix()
        except ValueError:
            folder = p.parent.as_posix()
        groups[folder].append(p)
    lines = ["### Dosyalar", f"{len(files)} dosya · bilgisayardaki konumuna link (Obsidian masaüstünde açılır)."]
    for folder, items in groups.items():
        lines.append(f"\n**~/{folder}**")
        for p in items:
            name = p.name.replace("[", "(").replace("]", ")")
            lines.append(f"- [{name}]({_link(p)})")
    if len(files) > MAX_PER_COURSE:
        lines.append(f"\n… ve {len(files) - MAX_PER_COURSE} dosya daha.")
    return "\n".join(lines)


LMS_FROM = str(LMS.get("from") or "")
LMS_LINK = str(LMS.get("link_regex") or r"https://\S+?(?=[\s\]\)>\"']|$)")
LMS_NAME = str(LMS.get("name") or "LMS")


def uzem_items(con, course_name: str, limit: int = 15) -> str:
    """ÜNİ LMS (Moodle) bildirim maillerinden bu derse ait olanlar: duyuru, ödev, teslim, yeni içerik (en yeni üstte)."""
    import re
    if con is None or len(course_name) < 4 or not LMS_FROM:
        return ""
    rows = con.execute(
        "SELECT date_ms, subject, body FROM messages WHERE from_addr = ? AND (subject LIKE ? OR body LIKE ?) "
        "ORDER BY date_ms DESC LIMIT ?", (LMS_FROM, f"%{course_name}%", f"%{course_name}%", limit)).fetchall()
    from datetime import datetime
    out = []
    for ms, subj, body in rows:
        link = next(iter(re.findall(LMS_LINK, body or "")), "")
        subj = re.sub(r"\{\$a->\s*\w+\}", "ödev", subj or "", flags=re.I)
        out.append(f"- {datetime.fromtimestamp(ms / 1000):%Y-%m-%d} · {subj[:110]}" + (f" ([aç]({link}))" if link else ""))
    return "\n".join(out)


def build_specs(vault: Vault, cfg: dict, home: Path | None = None, con=None) -> tuple[list[NoteSpec], list[str]]:
    home = home or Path.home()
    specs, missing = [], []
    files = files_for(cfg)
    course_keys = {sid.split(":", 1)[1]: (src, sid) for (src, sid) in vault.index if src in ("gcal", "obs") and sid.startswith("ders:")}
    for code in list(files) + sorted(set(course_keys) - set(files)):      # önce ayar sırası, sonra dosyasız dersler
        key = next((k for k in (("gcal", f"ders:{code}"), ("obs", f"ders:{code}")) if k in vault.index), None)
        if not key:
            missing.append(code)
            continue
        auto = {}
        if code in files:
            auto["dosyalar"] = render(files[code], home)
        name = vault.index[key].stem[len(code):].strip()
        uz = uzem_items(con, name)
        if uz:
            auto["uzem"] = f"**{LMS_NAME} duyuruları ve ödevler:**\n" + uz
        if auto:
            specs.append(NoteSpec(folder="", title=code, frontmatter={"source": key[0], "source_id": key[1]}, owned=(), auto=auto))
    return specs, missing
