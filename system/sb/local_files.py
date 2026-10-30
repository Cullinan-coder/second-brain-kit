"""Bu bilgisayardaki dosyalar → mail.db `local_files` + 40-Kaynaklar/Bilgisayar KLASÖR KLASÖR notlar.

Dosyalar kopyalanmaz; ad, yer, boyut, tarih ve `file:///` linki tutulur (Obsidian masaüstünde açılır).
Her klasör (kökten `note_depth` seviyeye kadar) kendi notunu alır: istatistik, alt klasörler (link + sayı),
doğrudan dosyalar (belgelerde çıkarılmış metinden kısa ipucu) ve daha derindeki en yeni dosyalar.
Çok büyük klasörler (`big_dir`) içine girilmeden tek satırla özetlenir. Kökler `_system/config/local_files.yaml`.
"""
from __future__ import annotations

import fnmatch
import os
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml

from .config import SYSTEM
from .course_files import _link
from .notes import NoteSpec, safe_filename
from .redact import redact

NOTE_FOLDER = "40-Kaynaklar/Bilgisayar"
SNIPPET = 110

SCHEMA = """
CREATE TABLE IF NOT EXISTS local_files (
    path   TEXT PRIMARY KEY,
    root   TEXT,
    sub    TEXT,              -- kökten sonraki ilk klasör ("" = kökün kendisi)
    name   TEXT,
    ext    TEXT,
    size   INTEGER,
    mtime  REAL,
    rel    TEXT               -- klasörün köke göre yolu ("a/b/c"), kökteyse ""
);
CREATE TABLE IF NOT EXISTS local_big_dirs (
    path   TEXT PRIMARY KEY,
    root   TEXT,
    rel    TEXT,
    n      INTEGER
);
"""


def load() -> dict:
    return yaml.safe_load((SYSTEM / "config" / "local_files.yaml").read_text(encoding="utf-8"))


def _ensure(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    try:
        con.execute("ALTER TABLE local_files ADD COLUMN rel TEXT")
    except sqlite3.OperationalError:
        pass


def walk(cfg: dict, big_out: list | None = None):
    skip_dirs = set(cfg["skip_dirs"])
    big = cfg.get("big_dir", 3000)
    for name, spec in cfg["roots"].items():
        spec = {"path": spec} if isinstance(spec, str) else spec
        base = Path(spec["path"]).expanduser()
        only = {e.lower() for e in spec.get("only_ext", [])}
        if not base.is_dir():
            continue
        for root, dirs, files in os.walk(base):
            keep = []
            for d in dirs:
                if d in skip_dirs or d.startswith("."):
                    continue
                full = Path(root) / d
                try:
                    n = len(os.listdir(full))
                except OSError:
                    continue
                if n > big:
                    if big_out is not None:
                        big_out.append((str(full), name, full.relative_to(base).as_posix(), n))
                    continue
                keep.append(d)
            dirs[:] = keep
            rel_dir = Path(root).relative_to(base).as_posix()
            rel_dir = "" if rel_dir == "." else rel_dir
            for f in files:
                if any(fnmatch.fnmatch(f, s) for s in cfg["skip_files"]):
                    continue
                ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                if only and ext not in only:
                    continue
                p = Path(root) / f
                try:
                    st = p.stat()
                except OSError:
                    continue
                yield name, rel_dir.split("/")[0] if rel_dir else "", rel_dir, p, ext, st.st_size, st.st_mtime


def sync(con: sqlite3.Connection, cfg: dict, log=print) -> int:
    _ensure(con)
    big_dirs: list = []
    rows = [(str(p), root, sub, p.name, ext, size, mtime, rel)
            for root, sub, rel, p, ext, size, mtime in walk(cfg, big_dirs)]
    seen = {r[0] for r in rows}
    con.executemany("INSERT OR REPLACE INTO local_files(path, root, sub, name, ext, size, mtime, rel) VALUES (?,?,?,?,?,?,?,?)", rows)
    stale = [r[0] for r in con.execute("SELECT path FROM local_files") if r[0] not in seen]
    con.executemany("DELETE FROM local_files WHERE path = ?", [(s,) for s in stale])
    con.execute("DELETE FROM local_big_dirs")
    con.executemany("INSERT INTO local_big_dirs(path, root, rel, n) VALUES (?,?,?,?)", big_dirs)
    con.commit()
    log(f"bilgisayar: {len(rows)} dosya tarandı, {len(stale)} silinen kayıt kaldırıldı, {len(big_dirs)} dev klasör özetlendi")
    return len(rows)


def _size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _part(s: str, n: int = 60) -> str:
    # Windows klasör/dosya adının sonundaki boşluk ve noktayı siler; kısaltma sonrası da temizlenmeli.
    return (safe_filename(s) or "_")[:n].strip(" .") or "_"


MAX_REL = 150     # kasa köküne göre not yolu üst sınırı (Windows 260 karakter sınırı için pay bırakır)


def _loc(root: str, rel: str) -> tuple[str, str]:
    """(not klasörü, not başlığı). Yol çok uzunsa düzleştirilir: kökün altına kısa ad + sabit özet eki."""
    parts = [p for p in rel.split("/") if p]
    title = _part(parts[-1]) if parts else _part(root)
    folder = "/".join([NOTE_FOLDER, _part(root)] + [_part(p) for p in parts])
    if len(folder) + len(title) + 5 <= MAX_REL:
        return folder, title
    import hashlib
    tag = hashlib.sha1(f"{root}/{rel}".encode("utf-8")).hexdigest()[:6]
    return f"{NOTE_FOLDER}/{_part(root)}/{_part(parts[0], 30)}", f"{_part(title, 45)}~{tag}"


def note_dir(root: str, rel: str) -> str:
    return _loc(root, rel)[0]


def note_title(root: str, rel: str) -> str:
    return _loc(root, rel)[1]


def wikilink(root: str, rel: str, label: str) -> str:
    return f"[[{note_dir(root, rel)}/{note_title(root, rel)}|{label}]]"


def _snippets(con: sqlite3.Connection, paths: list[str]) -> dict[str, str]:
    try:
        out = {}
        for i in range(0, len(paths), 500):
            chunk = paths[i:i + 500]
            q = ",".join("?" * len(chunk))
            for p, t in con.execute(f"SELECT path, substr(text, 1, 600) FROM file_text WHERE path IN ({q}) AND chars > 0", chunk):
                t = " ".join((t or "").split())
                if t:
                    out[p] = redact(t)[:SNIPPET].replace("|", "/").replace("[", "(").replace("]", ")")
        return out
    except sqlite3.OperationalError:     # file_text henüz yok
        return {}


def build_specs(con: sqlite3.Connection, cfg: dict) -> list[NoteSpec]:
    _ensure(con)
    depth_max = cfg.get("note_depth", 3)
    min_deep = cfg.get("min_files_deep", 3)
    per_dir, deeper_rows = cfg.get("per_dir", 150), cfg.get("deeper_rows", 60)

    subtree: dict[tuple[str, str], list] = defaultdict(list)       # (root, rel) → alttaki TÜM dosyalar
    for r in con.execute("SELECT path, root, rel, name, ext, size, mtime FROM local_files"):
        parts = [p for p in (r[2] or "").split("/") if p]
        for k in range(0, min(len(parts), depth_max) + 1):
            subtree[(r[1], "/".join(parts[:k]))].append(r)
    big: dict[tuple[str, str], list] = defaultdict(list)
    for path, root, rel, n in con.execute("SELECT path, root, rel, n FROM local_big_dirs"):
        parts = rel.split("/")
        for k in range(0, min(len(parts) - 1, depth_max) + 1):
            big[(root, "/".join(parts[:k]))].append((rel, n))

    def depth(rel: str) -> int:
        return len([p for p in rel.split("/") if p])

    nodes = {k for k, v in subtree.items() if depth(k[1]) <= 1 or len(v) >= min_deep}
    nodes |= {(r, "") for r, _ in subtree if (r, "") in subtree}
    specs = []
    for (root, rel) in sorted(nodes):
        files = subtree[(root, rel)]
        direct = sorted((f for f in files if (f[2] or "") == rel), key=lambda f: -f[6])
        deeper = sorted((f for f in files if (f[2] or "") != rel), key=lambda f: -f[6])
        children = Counter()
        child_size = Counter()
        for f in files:
            frel = f[2] or ""
            if frel != rel:
                rest = frel[len(rel) + 1:] if rel else frel
                head = rest.split("/")[0]
                children[head] += 1
                child_size[head] += f[5]
        exts = Counter((f[4] or "—") for f in files)
        total = sum(f[5] for f in files)
        shown = direct[:per_dir]
        shown_deeper = deeper[:deeper_rows]
        snip = _snippets(con, [f[0] for f in shown + shown_deeper])

        def row(f) -> str:
            name = redact(f[3]).replace("|", "/").replace("[", "(").replace("]", ")")
            where = (f[2] or "")[len(rel) + 1:] if f[2] and f[2] != rel else ""
            return (f"| {datetime.fromtimestamp(f[6]):%Y-%m-%d} | {where or '—'} | [{name}]({_link(Path(f[0]))}) | "
                    f"{_size(f[5])} | {snip.get(f[0], '')} |")

        head_tab = ["| Tarih | Klasör | Dosya | Boyut | İçerik ipucu |", "|---|---|---|---|---|"]
        title = note_title(root, rel)
        ozet = [f"`{root}/{rel}`".replace("/`", "`") + f" · **{len(files)}** dosya (alt klasörler dahil) · {_size(total)} · "
                "kopya değil, bilgisayardaki konuma link (Obsidian masaüstünde açılır).",
                "**Türler:** " + ", ".join(f"{k} ({v})" for k, v in exts.most_common(12))]
        for brel, n in big.get((root, rel), [])[:10]:
            ozet.append(f"⚠ Dev klasör, içine girilmedi: `{brel}` (≥ {n} öğe)")
        alt = []
        for head, n in children.most_common(80):
            crel = f"{rel}/{head}" if rel else head
            label = f"{head} ({n} dosya, {_size(child_size[head])})"
            alt.append(f"- {wikilink(root, crel, label)}" if (root, crel) in nodes else f"- {label}")
        if depth(rel) > 0:
            parent = rel.rsplit("/", 1)[0] if "/" in rel else ""
            alt.insert(0, f"↑ Üst klasör: {wikilink(root, parent, note_title(root, parent))}")
        dosyalar = [f"### Bu klasördeki dosyalar ({len(direct)}" + (f", son {per_dir} gösteriliyor" if len(direct) > per_dir else "") + ")"]
        dosyalar += (head_tab + [row(f) for f in shown]) if shown else ["Doğrudan dosya yok."]
        if shown_deeper:
            dosyalar += ["", f"### Alt klasörlerdeki en yeni {len(shown_deeper)} dosya"] + head_tab + [row(f) for f in shown_deeper]
        specs.append(NoteSpec(
            folder=note_dir(root, rel), title=title,
            frontmatter={"type": "kaynak", "status": "aktif", "tags": ["bilgisayar"], "source": "workspace",
                         "source_id": f"local-folder:{root}/{rel}", "due": None,
                         "file_count": len(files), "size_mb": round(total / 1048576, 1)},
            owned=("file_count", "size_mb"),
            body=f"# {title}\n\n## Notlar\n\n## Özet\n<!-- sb:auto:ozet:start -->\n<!-- sb:auto:ozet:end -->\n\n"
                 "## Alt klasörler\n<!-- sb:auto:alt:start -->\n<!-- sb:auto:alt:end -->\n\n"
                 "## Dosyalar\n<!-- sb:auto:dosyalar:start -->\n<!-- sb:auto:dosyalar:end -->\n",
            auto={"ozet": "\n\n".join(ozet), "alt": "\n".join(alt) or "Alt klasör yok.", "dosyalar": "\n".join(dosyalar)},
        ))
    return specs
