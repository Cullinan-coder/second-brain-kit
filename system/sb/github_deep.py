"""GitHub derin tarama: kullanıcının repolarında son N gün issue/PR/yorum/commit/release → mail.db `items` (source `github`).

- `gh` CLI oturumu kullanılır (özel repolar dahil); yalnız GET isteği atılır, GitHub'a hiçbir şey yazılmaz.
- Sayfa sınırı: per_page=100, en çok 3 sayfa. Yorumlarda repo başına ilk 20, commit'te varsayılan dalın son 100'ü.
- Gövde metinleri `redact` ile maskelenir.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from . import maildb
from .config import GITHUB_USER
from .redact import redact

PER_PAGE = 100
MAX_PAGES = 3
COMMENT_LIMIT = 20
COMMIT_LIMIT = 100
BODY_MAX = 4000
KINDS = ("issue", "pr", "comment", "commit", "release")


def _gh(args: list[str]) -> str:
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", creationflags=flags)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "gh hatası").strip()[:200])
    return r.stdout


def _api(path: str, params: dict | None = None, max_pages: int = MAX_PAGES) -> list[dict]:
    """GET <path> (sayfalı). Hata (boş repo 409, erişim 403/404) → o ana kadarki sonuç."""
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        q = "&".join(f"{k}={v}" for k, v in {"per_page": PER_PAGE, "page": page, **(params or {})}.items())
        try:
            data = json.loads(_gh(["api", f"{path}?{q}"]) or "[]")
        except (RuntimeError, json.JSONDecodeError):
            break
        if not isinstance(data, list):
            break
        out += data
        if len(data) < PER_PAGE:
            break
    return out


def list_repos(owner: str = "") -> list[str]:
    """Sahip olunan, arşivlenmemiş repolar (özel dahil): ['sahip/ad', ...]."""
    owner = owner or GITHUB_USER
    args = ["repo", "list", *([owner] if owner else []), "--limit", "200", "--json", "nameWithOwner,isArchived"]
    return [r["nameWithOwner"] for r in json.loads(_gh(args) or "[]") if not r.get("isArchived")]


def _ms(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None


def _login(u: dict | None) -> str:
    return (u or {}).get("login", "")


def _clip(text: str | None) -> str:
    return redact((text or "")[:BODY_MAX])


def _labels(d: dict) -> list[str]:
    return [l["name"] for l in d.get("labels") or [] if isinstance(l, dict) and l.get("name")]


def collect_repo(repo: str, since: datetime) -> list[dict]:
    """Tek repo için item listesi (yazmaz)."""
    iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    items: list[dict] = []

    def add(kind, ident, d, title, body, url, date, **meta):
        items.append({"source": "github", "id": ident, "date_ms": _ms(date), "kind": kind, "title": title,
                      "url": url, "body": _clip(body), "meta": {"repo": repo, **meta}})

    for d in _api(f"repos/{repo}/issues", {"state": "all", "since": iso, "sort": "updated", "direction": "desc"}):
        if "pull_request" in d:
            continue
        add("issue", f"{repo}#issue{d['number']}", d, d.get("title", ""), d.get("body"), d.get("html_url"),
            d.get("updated_at") or d.get("created_at"), state=d.get("state"), number=d["number"],
            author=_login(d.get("user")), labels=_labels(d))
    for d in _api(f"repos/{repo}/pulls", {"state": "all", "sort": "updated", "direction": "desc"}):
        if (d.get("updated_at") or "") < iso:
            break
        state = "merged" if d.get("merged_at") else d.get("state")
        add("pr", f"{repo}#pr{d['number']}", d, d.get("title", ""), d.get("body"), d.get("html_url"),
            d.get("updated_at") or d.get("created_at"), state=state, number=d["number"],
            author=_login(d.get("user")), labels=_labels(d))
    for d in _api(f"repos/{repo}/issues/comments", {"since": iso, "sort": "updated", "direction": "desc"}, 1)[:COMMENT_LIMIT]:
        num = str(d.get("issue_url", "")).rsplit("/", 1)[-1]
        add("comment", f"{repo}#c{d['id']}", d, f"Yorum: {repo}#{num}", d.get("body"), d.get("html_url"),
            d.get("created_at"), number=int(num) if num.isdigit() else None, author=_login(d.get("user")))
    for d in _api(f"repos/{repo}/commits", {"since": iso}, 1)[:COMMIT_LIMIT]:
        c = d.get("commit") or {}
        msg = c.get("message") or ""
        add("commit", f"{repo}@{d['sha']}", d, msg.split("\n", 1)[0][:200], msg, d.get("html_url"),
            (c.get("author") or {}).get("date"), sha=d["sha"][:10],
            author=_login(d.get("author")) or (c.get("author") or {}).get("name", ""))
    for d in _api(f"repos/{repo}/releases", None, 1):
        when = d.get("published_at") or d.get("created_at") or ""
        if when and when < iso:
            continue
        add("release", f"{repo}#rel{d['id']}", d, d.get("name") or d.get("tag_name", ""), d.get("body"),
            d.get("html_url"), when, tag=d.get("tag_name"), author=_login(d.get("author")),
            state="prerelease" if d.get("prerelease") else "release")
    return items


def run(days: int = 90, repo: str = "", dry_run: bool = False, con=None, log=print) -> dict:
    """Taramayı yürütür; {"repos": n, "issue": n, "pr": n, ...} döner. dry_run=True: veritabanına yazmaz."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    repos = list_repos()
    if repo:
        repos = [r for r in repos if r.lower() == repo.lower() or r.split("/")[-1].lower() == repo.lower()]
        if not repos:
            raise SystemExit(f"Repo bulunamadı: {repo}")
    counts = {"repos": len(repos), **{k: 0 for k in KINDS}}
    for r in repos:
        try:
            items = collect_repo(r, since)
        except RuntimeError as e:
            log(f"{r}: atlandı ({e})")
            continue
        for it in items:
            counts[it["kind"]] += 1
            if not dry_run and con is not None:
                maildb.insert_item(con, it, update=True)
        if not dry_run and con is not None:
            con.commit()
    return counts


def cli(args) -> int:
    from .config import MAIL_DB
    con = None if args.dry_run else maildb.connect(MAIL_DB)
    c = run(days=args.days, repo=args.repo or "", dry_run=args.dry_run, con=con)
    print(f"{'(dry-run) ' if args.dry_run else ''}{c['repos']} repo · " + ", ".join(f"{c[k]} {k}" for k in KINDS))
    return 0
