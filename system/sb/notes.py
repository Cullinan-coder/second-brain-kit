"""Kasaya idempotent not yazımı.

Kurallar (CLAUDE.md ile aynı):
- Bir not `source + source_id` ile tanımlanır; aynı anahtarla ikinci not oluşturulmaz.
- Güncellemede sadece kaynağın sahip olduğu alanlar (`owned`) ve
  `<!-- sb:auto:<ad>:start/end -->` bölümleri yeniden yazılır. status, tags ve
  elle yazılmış metin korunur.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
SKIP_DIRS = {".obsidian", ".git", ".trash", "_system", "_templates", ".venv"}
UNSAFE_FILENAME = re.compile(r'[\\/:*?"<>|#^\[\]]')


@dataclass
class NoteSpec:
    folder: str                      # kasaya göre klasör, ör. "10-Dersler/YPZ301 Yapay Sinir Ağları"
    title: str                       # dosya adı (uzantısız) ve H1
    frontmatter: dict                # oluşturmada yazılacak tam frontmatter
    owned: tuple[str, ...]           # güncellemede kaynağın üzerine yazacağı alanlar
    body: str = ""                   # sadece oluşturmada yazılır (auto bölüm yer tutucuları dahil)
    auto: dict[str, str] = field(default_factory=dict)  # her çalıştırmada yeniden yazılan bölümler
    # Sahip olunan bir alan değişince sıfırlanacak alanlar, ör. {"due": {"status": "acik"}}
    # (tekrarlayan ödevde yeni hafta gelince "tamamlandi" tekrar "acik" olur).
    reset_on_change: dict[str, dict] = field(default_factory=dict)
    rename: bool = False             # kaynakta ad değişince notun dosya adı ve H1'i de değişsin (eski ad takma ad olur)

    @property
    def key(self) -> tuple[str, str]:
        return (str(self.frontmatter["source"]), str(self.frontmatter["source_id"]))


def safe_filename(name: str) -> str:
    return re.sub(r"\s+", " ", UNSAFE_FILENAME.sub("", name)).strip()


# Gevşek yedek desen (YAML ayrıştırılamazsa): büyük/küçük harf, tırnak, satır sonu yorumu (D-11).
PRIVATE_RE = re.compile(r"^[ \t]*visibility[ \t]*:[ \t]*['\"]?[ \t]*private[ \t]*['\"]?[ \t]*(?:#.*)?$", re.M | re.I)
FRONTMATTER_READ = 256 * 1024         # ön bilginin tamamı okunur (eskiden 2000 karakter: uzun ön bilgide gizlilik işareti kaçıyordu)


def is_private_text(text: str) -> bool:
    """Not metni `visibility: private` mi. TEK doğruluk kaynağı (notes + agents). Ön bilgi YAML olarak ayrıştırılır; BOM, tırnak,
    büyük harf (`Private`), satır sonu yorumu ve uzun ön bilgi fark etmez. Ayrıştırılamıyorsa gevşek desenle bakar (gizli yönünde hata)."""
    t = text.lstrip("\ufeff")
    if not t.startswith("---"):
        return False
    m = FRONTMATTER_RE.match(t)
    block = m.group(1) if m else t[3:]
    try:
        fm = yaml.safe_load(block)
    except yaml.YAMLError:
        fm = None
    if isinstance(fm, dict):
        return str(fm.get("visibility", "")).strip().lower() == "private" or bool(PRIVATE_RE.search(block))
    return bool(PRIVATE_RE.search(block))


def is_private(path: Path) -> bool:
    """`visibility: private` notlar hiçbir otomatik bağlama (Claude MCP, asistan getirmesi, kanca) girmez."""
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            head = f.read(FRONTMATTER_READ)
    except OSError:
        return False
    return is_private_text(head)


def split_note(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


class _NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):  # Obsidian YAML anchor (&id001) göstermesin
        return True


def dump_note(fm: dict, body: str) -> str:
    head = yaml.dump(fm, Dumper=_NoAliasDumper, allow_unicode=True, sort_keys=False, default_flow_style=None, width=1000)
    return f"---\n{head}---\n{body.lstrip(chr(10))}"


def replace_auto(body: str, name: str, content: str) -> str:
    start, end = f"<!-- sb:auto:{name}:start -->", f"<!-- sb:auto:{name}:end -->"
    block = f"{start}\n{content.rstrip()}\n{end}"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pattern.search(body):
        return pattern.sub(lambda _: block, body)
    return body.rstrip() + f"\n\n{block}\n"


class Vault:
    def __init__(self, root: Path, dry_run: bool = False):
        self.root = root
        self.dry_run = dry_run
        self.index: dict[tuple[str, str], Path] = {}
        self.stats = {"created": 0, "updated": 0, "unchanged": 0, "renamed": 0}
        self.renamed: list[tuple[str, str]] = []           # (eski ad, yeni ad)
        for p in root.rglob("*.md"):
            if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
                continue
            fm, _ = split_note(p.read_text(encoding="utf-8"))
            sid = fm.get("source_id")
            if fm.get("source") and sid not in (None, ""):
                self.index[(str(fm["source"]), str(sid))] = p

    def upsert(self, spec: NoteSpec, today: date) -> Path:
        path = self.index.get(spec.key)
        if path is None:
            return self._create(spec, today)
        text = path.read_text(encoding="utf-8")
        fm, body = split_note(text)
        if spec.rename and "90-Arşiv" not in path.parts:
            path, fm, body = self._maybe_rename(path, fm, body, spec)
        for k in spec.owned:
            if k in spec.frontmatter:
                if fm.get(k) != spec.frontmatter[k]:
                    fm.update(spec.reset_on_change.get(k, {}))
                fm[k] = spec.frontmatter[k]
        for name, content in spec.auto.items():
            body = replace_auto(body, name, content)
        new_text = dump_note(fm, body)
        if new_text == text:
            self.stats["unchanged"] += 1
            return path
        fm["updated"] = today
        self._write(path, dump_note(fm, body))
        self.stats["updated"] += 1
        return path

    def _maybe_rename(self, path: Path, fm: dict, body: str, spec: NoteSpec):
        """Kaynaktaki ad değiştiyse (ör. rehberde düzeltilen isim) dosyayı yeni ada taşır; eski ad takma ad olarak kalır."""
        new = safe_filename(spec.title)
        old = re.sub(r" \(\d+\)$", "", path.stem)
        if not new or new == old:
            return path, fm, body
        target = path.with_name(f"{new}.md")
        if target.exists() and not os.path.samefile(target, path):  # aynı adlı başka not var: dokunma (birleştirme önerisine kalır)
            return path, fm, body
        fm["aliases"] = sorted(set(fm.get("aliases") or []) | {path.stem})
        body = re.sub(rf"^# {re.escape(path.stem)}\s*$", f"# {spec.title}", body, count=1, flags=re.M)
        if not self.dry_run:
            path.rename(target)
        else:
            print(f"[dry-run] yeniden adlandır: {path.stem} → {new}")
        self.index[spec.key] = target
        self.renamed.append((path.stem, new))
        self.stats["renamed"] += 1
        return target, fm, body

    def relink(self, pairs: list[tuple[str, str]] | None = None) -> list[Path]:
        """Kasadaki [[Eski]] / [[Eski|...]] bağlantılarını [[Yeni]]'ye çevirir (yeniden adlandırma sonrası)."""
        pairs = pairs if pairs is not None else self.renamed
        if not pairs or self.dry_run:
            return []
        rx = {old: re.compile(r"\[\[" + re.escape(old) + r"(\|[^\]]*)?\]\]") for old, _ in pairs}
        changed = []
        for p in self.root.rglob("*.md"):
            if any(part in SKIP_DIRS for part in p.relative_to(self.root).parts[:-1]):
                continue
            text = p.read_text(encoding="utf-8")
            new_text = text
            for old, new in pairs:
                if f"[[{old}" in new_text:
                    new_text = rx[old].sub(lambda m, n=new: f"[[{n}{m.group(1) or ''}]]", new_text)
            if new_text != text:
                p.write_text(new_text, encoding="utf-8", newline="\n")
                changed.append(p)
        return changed

    def _create(self, spec: NoteSpec, today: date) -> Path:
        folder = self.root / spec.folder
        path = folder / f"{safe_filename(spec.title)}.md"
        n = 2
        while path.exists():  # aynı adlı ama farklı kaynaklı not varsa üzerine yazma
            path = folder / f"{safe_filename(spec.title)} ({n}).md"
            n += 1
        fm = dict(spec.frontmatter)
        fm.setdefault("created", today)
        fm.setdefault("updated", today)
        body = spec.body or f"# {spec.title}\n"
        for name, content in spec.auto.items():
            body = replace_auto(body, name, content)
        self._write(path, dump_note(fm, body))
        self.index[spec.key] = path
        self.stats["created"] += 1
        return path

    def _write(self, path: Path, text: str) -> None:
        if self.dry_run:
            print(f"[dry-run] {path.relative_to(self.root).as_posix()}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
