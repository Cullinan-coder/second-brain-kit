"""Workspace projeleri + GitHub repoları → 20-Projeler notları.

- Her `~/Workspace/projects/<klasör>` bir not (`source: workspace`, `source_id: projects/<klasör>`).
  Klasördeki kendi git repoları (kökte ya da 3 seviyeye kadar altta; uzak adresi kullanıcının hesabı olan
  ya da uzak adresi olmayan) toplanır; başkasından klonlanmış repolar sayılmaz.
- Yerelde karşılığı olmayan GitHub repoları ayrı not olur (`source: github`, `source_id: <sahip/repo>`).
- "Son çalışmalar": son 30 günün commit'leri; git yoksa son değişen dosyalar. "Özet": README/CLAUDE.md ilk paragrafı.
- status sadece ilk oluşturmada tahmin edilir; sonra kullanıcıya aittir.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from .notes import NoteSpec
from .redact import redact
from .config import GITHUB_USER

FOLDER = "20-Projeler"
OWNER = GITHUB_USER
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "build", "dist", ".next", ".idea", ".vscode",
             "vendor", ".gradle", ".dart_tool", "target", ".pytest_cache", ".ipynb_checkpoints"}
SKIP_PROJECTS = {"second-brain"}
ACTIVE_DAYS = 45
RECENT_DAYS = 30


@dataclass
class Repo:
    path: Path
    remote: str | None          # sahip/repo ya da None
    commits: list[tuple[str, str, str]] = field(default_factory=list)   # (tarih, kısa hash, konu)
    last_commit: str | None = None


@dataclass
class Project:
    folder: Path
    repos: list[Repo]
    recent_files: list[tuple[str, str]]   # (tarih, göreli yol)
    last_activity: date | None
    summary: str


def _git(path: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


def _remote(path: Path) -> str | None:
    url = _git(path, "remote", "get-url", "origin")
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
    return m.group(1) if m else (url or None)


def find_repos(folder: Path, since: date) -> list[Repo]:
    repos = []
    for root, dirs, _ in os.walk(folder):
        depth = len(Path(root).relative_to(folder).parts)
        if ".git" in dirs:
            remote = _remote(Path(root))
            if remote is None or remote.lower().startswith(OWNER.lower() + "/"):
                log = _git(Path(root), "log", f"--since={since.isoformat()}", "--format=%cs|%h|%s", "-n", "15")
                repo = Repo(Path(root), remote, [tuple(l.split("|", 2)) for l in log.splitlines() if l.count("|") >= 2])
                repo.last_commit = _git(Path(root), "log", "-1", "--format=%cs") or None
                repos.append(repo)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and depth < 3]
    return repos


def recent_files(folder: Path, limit: int = 8, max_depth: int = 5) -> list[tuple[float, Path]]:
    found: list[tuple[float, Path]] = []
    for root, dirs, files in os.walk(folder):
        depth = len(Path(root).relative_to(folder).parts)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".") and depth < max_depth]
        for f in files:
            if f.startswith((".", "~$")) or f in ("desktop.ini", "Thumbs.db"):
                continue
            p = Path(root) / f
            try:
                found.append((p.stat().st_mtime, p))
            except OSError:
                continue
    found.sort(reverse=True)
    return found[:limit]


def readme_summary(folder: Path) -> str:
    for name in ("README.md", "readme.md", "README.MD", "CLAUDE.md"):
        p = folder / name
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            for para in re.split(r"\n\s*\n", text):
                para = para.strip()
                if para and not para.startswith(("#", "![", "<", "```", "|", "---", "[!")):
                    return redact(" ".join(para.split()))[:500]
    return ""


def scan(workspace: Path, today: date) -> list[Project]:
    since = today - timedelta(days=RECENT_DAYS)
    projects = []
    for folder in sorted(p for p in workspace.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if folder.name in SKIP_PROJECTS:
            continue
        repos = find_repos(folder, since)
        rf = recent_files(folder)
        dates = [date.fromisoformat(r.last_commit) for r in repos if r.last_commit]
        if rf:
            dates.append(datetime.fromtimestamp(rf[0][0]).date())
        projects.append(Project(
            folder=folder, repos=repos,
            recent_files=[(datetime.fromtimestamp(t).strftime("%Y-%m-%d"), p.relative_to(folder).as_posix()) for t, p in rf],
            last_activity=max(dates) if dates else None, summary=readme_summary(folder),
        ))
    return projects


def github_repos() -> list[dict]:
    r = subprocess.run(["gh", "repo", "list", OWNER, "--limit", "200", "--json",
                        "nameWithOwner,description,pushedAt,primaryLanguage,isPrivate,isArchived,url"],
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []


def _norm(s: str) -> str:
    # Kelime sonu "s" yok sayılır: course-credits-system == course-credit-system (yeniden adlandırılmış repo)
    name = re.sub(r"s(?=[-_.\s]|$)", "", s.lower().split("/")[-1])
    return re.sub(r"[^a-z0-9]", "", name)


def _title(folder_name: str) -> str:
    return re.sub(r"\s*\((?:WAİTİNG|WAITING)\)\s*", "", folder_name, flags=re.I).strip()


def _status(name: str, last: date | None, today: date) -> str:
    if re.search(r"WAİTİNG|WAITING", name, re.I):
        return "beklemede"
    return "aktif" if last and (today - last).days <= ACTIVE_DAYS else "beklemede"


def _activity_md(p: Project, gh: dict[str, dict]) -> str:
    lines = [f"Son etkinlik: **{p.last_activity or 'bilinmiyor'}** · yerel klasör: `~/{p.folder.relative_to(Path.home()).as_posix()}`"]
    for r in p.repos:
        meta = gh.get((r.remote or "").lower())
        where = r.path.relative_to(p.folder).as_posix() or "."
        head = f"\n**{r.remote or 'yerel repo'}** (`{where}`), son commit {r.last_commit or '—'}"
        if meta:
            head += f" · {meta.get('primaryLanguage', {}).get('name') if meta.get('primaryLanguage') else '—'}"
        lines.append(head)
        lines += [f"- {d} `{h}` {redact(s)[:100]}" for d, h, s in r.commits[:10]] or [f"- son {RECENT_DAYS} günde commit yok"]
    if p.recent_files:
        lines.append("\n**Son değişen dosyalar**")
        lines += [f"- {d} {path}" for d, path in p.recent_files]
    return "\n".join(lines)


def build_specs(projects: list[Project], gh_list: list[dict], today: date) -> list[NoteSpec]:
    gh = {g["nameWithOwner"].lower(): g for g in gh_list}
    gh_norm = {_norm(k): k for k in gh}
    used: set[str] = set()
    specs = []
    for p in projects:
        remotes = []
        for r in p.repos:
            if r.remote:
                key = r.remote.lower() if r.remote.lower() in gh else gh_norm.get(_norm(r.remote))
                if key:
                    r.remote = gh[key]["nameWithOwner"]
                    used.add(key)
                if r.remote not in remotes:
                    remotes.append(r.remote)
        if not remotes and _norm(p.folder.name) in gh_norm:          # git'siz klasör, aynı adlı GitHub reposu
            key = gh_norm[_norm(p.folder.name)]
            used.add(key)
            remotes.append(gh[key]["nameWithOwner"])
        title = _title(p.folder.name)
        specs.append(NoteSpec(
            folder=FOLDER, title=title,
            frontmatter={
                "type": "proje", "status": _status(p.folder.name, p.last_activity, today), "tags": ["proje"],
                "source": "workspace", "source_id": f"projects/{p.folder.name}", "due": None,
                "area": None, "repo": remotes or None,
                "local_path": f"~/{p.folder.relative_to(Path.home()).as_posix()}",
                "last_activity": p.last_activity,
            },
            owned=("repo", "local_path", "last_activity"),
            body=_body(title),
            auto={"ozet": p.summary or "README bulunamadı.", "son-calismalar": _activity_md(p, gh)},
        ))
    for key, g in sorted(gh.items()):
        if key in used:
            continue
        pushed = date.fromisoformat(g["pushedAt"][:10])
        lang = (g.get("primaryLanguage") or {}).get("name") or "—"
        specs.append(NoteSpec(
            folder=FOLDER, title=g["nameWithOwner"].split("/")[-1],
            frontmatter={
                "type": "proje", "status": "arsiv" if g["isArchived"] else _status("", pushed, today), "tags": ["proje", "github"],
                "source": "github", "source_id": g["nameWithOwner"], "due": None, "area": None,
                "repo": [g["nameWithOwner"]], "local_path": None, "last_activity": pushed,
            },
            owned=("repo", "last_activity"),
            body=_body(g["nameWithOwner"].split("/")[-1]),
            auto={"ozet": redact(g.get("description") or "Açıklama yok."),
                  "son-calismalar": f"Sadece GitHub'da (yerel klasör yok). Son push: **{pushed}** · {lang} · "
                                    f"{'private' if g['isPrivate'] else 'public'} · {g['url']}"},
        ))
    return specs


def _body(title: str) -> str:
    return (f"# {title}\n\n## Özet\n<!-- sb:auto:ozet:start -->\n<!-- sb:auto:ozet:end -->\n\n"
            "## Proje dosyası (derlenmiş)\n<!-- sb:auto:proje-dosyasi:start -->\n<!-- sb:auto:proje-dosyasi:end -->\n\n"
            "## Amaç\n\n## Durum\n\n"
            "## Son çalışmalar\n<!-- sb:auto:son-calismalar:start -->\n<!-- sb:auto:son-calismalar:end -->\n\n"
            "## Kararlar\n\n## Yapılacaklar\n- [ ] \n")
