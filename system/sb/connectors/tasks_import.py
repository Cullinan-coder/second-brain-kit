"""Görev yöneticisi yedekleri → `25-Görevler` görev notları (yalnız açık görevler, kimlikle tekrarsız).

Todoist/TickTick/Jira/Linear CSV, Microsoft To Do ve Trello JSON; biçim içerikten anlaşılır.
Not: `sb.tasks.add` görevi yazar; kimlik `source_id` alanına `import:<kaynak>:<id>` olarak konur.
"""
from __future__ import annotations

import csv
import io
import json
import re
from datetime import date
from pathlib import Path

from .. import tasks, vault_ops
from ..notes import dump_note, safe_filename, split_note
from ._common import _summary, clean, sid
from .bank import date_ms

DONE_WORDS = {"done", "closed", "resolved", "completed", "complete", "canceled", "cancelled", "duplicate", "tamamlandı", "kapalı", "won't do"}
TICK_HEAD = re.compile(r'^"?Folder Name"?,', re.I)


def _task(src, tid, title, text="", project="", due=None) -> dict:
    return {"src": src, "id": str(tid), "title": " ".join(clean(title).split()), "text": clean(text),
            "project": clean(project), "due": due}


def _iso(s: str | None) -> str | None:
    s = (s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return m.group(0)
    ms = date_ms(s[:10]) if s else None
    return date.fromtimestamp(ms / 1000).isoformat() if ms else None


def _csv(text: str) -> list[dict]:
    lines = text.splitlines()
    for i, l in enumerate(lines):  # TickTick başlık öncesi açıklama satırları içerir
        if TICK_HEAD.match(l):
            lines = lines[i:]
            break
    delim = max(";,\t", key=lines[0].count) if lines else ","
    return [{(k or "").strip().lower().replace("i̇", "i"): (v or "").strip() for k, v in r.items()}
            for r in csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delim)]


def _from_csv(text: str, stem: str) -> list[dict]:
    rows = _csv(text)
    if not rows:
        return []
    h = rows[0].keys()
    out = []
    if "folder name" in h and "list name" in h:  # TickTick (Status 0 açık)
        for r in rows:
            if r.get("status", "0") == "0" and r.get("title"):
                out.append(_task("ticktick", r.get("taskid") or sid(r["title"], r.get("due date")), r["title"],
                                 r.get("content", ""), r.get("list name", ""), _iso(r.get("due date"))))
    elif "issue key" in h or "issue id" in h:  # Jira
        for r in rows:
            st = (r.get("status category") or r.get("status", "")).lower()
            if r.get("summary") and st not in DONE_WORDS:
                out.append(_task("jira", r.get("issue key") or r.get("issue id"), f"{r.get('issue key', '')} {r['summary']}".strip(),
                                 r.get("description", ""), r.get("project name", ""), _iso(r.get("due date"))))
    elif "team" in h and "title" in h and "status" in h:  # Linear
        for r in rows:
            if r.get("title") and r.get("status", "").lower() not in DONE_WORDS | {"backlog-done"}:
                out.append(_task("linear", r.get("id") or sid(r["title"]), f"{r.get('id', '')} {r['title']}".strip(),
                                 r.get("description", ""), r.get("project") or r.get("team", ""), _iso(r.get("due date"))))
    elif "type" in h and "content" in h:  # Todoist (yedekte yalnız açık görevler)
        for r in rows:
            if r.get("type", "").lower() == "task" and r.get("content"):
                out.append(_task("todoist", sid(r["content"], r.get("date", "")), r["content"], r.get("description", ""),
                                 stem, _iso(r.get("date"))))
    return out


def _from_json(d, stem: str) -> list[dict]:
    out = []
    if isinstance(d, dict) and "cards" in d:  # Trello
        lists = {l["id"]: l for l in d.get("lists", [])}
        checks = {c["id"]: c for c in d.get("checklists", [])}
        for c in d["cards"]:
            lst = lists.get(c.get("idList"), {})
            if c.get("closed") or lst.get("closed") or c.get("dueComplete") or lst.get("name", "").lower() in DONE_WORDS:
                continue
            todo = [f"- [ ] {i['name']}" for cid in c.get("idChecklists", []) for i in checks.get(cid, {}).get("checkItems", [])
                    if i.get("state") != "complete"]
            out.append(_task("trello", c.get("id") or sid(c["name"]), c["name"],
                             "\n".join(x for x in [c.get("desc", ""), *todo] if x), d.get("name", stem), _iso(c.get("due"))))
    else:  # Microsoft To Do / Graph: {"value": [...]} ya da liste
        items = d.get("value", []) if isinstance(d, dict) else d
        for t in items:
            if isinstance(t, dict) and t.get("title") and t.get("status") != "completed":
                due = (t.get("dueDateTime") or {}).get("dateTime")
                out.append(_task("mstodo", t.get("id") or sid(t["title"]), t["title"], (t.get("body") or {}).get("content", ""),
                                 stem, _iso(due)))
    return out


def parse(path) -> list[dict]:
    p = Path(path)
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    if p.suffix.lower() == ".json":
        return _from_json(json.loads(text), p.stem)
    return _from_csv(text, p.stem)


def _existing() -> set[str]:
    ids = set()
    folder = vault_ops.VAULT / tasks.FOLDER
    for f in folder.glob("*.md") if folder.exists() else []:
        sidv = split_note(f.read_text(encoding="utf-8"))[0].get("source_id")
        if sidv:
            ids.add(str(sidv))
    return ids


def run(path, con=None, dry_run: bool = False, me: str = "", **_) -> dict:
    owner = me or "Ayşe"
    rows = parse(path)
    known, new, titles = _existing(), 0, []
    for r in rows:
        key = f"import:{r['src']}:{r['id']}"
        titles.append(r["title"])
        if key in known or not r["title"]:
            continue
        if dry_run:
            new += 1
            continue
        res = tasks.add(r["title"], r["text"], owner=owner, project=r["project"], due=r["due"], status="aktif", actor="import")
        if not res.startswith("Görev oluşturuldu"):
            continue
        new += 1
        p = vault_ops.VAULT / tasks.FOLDER / f"{safe_filename(r['title'])}.md"
        fm, body = split_note(p.read_text(encoding="utf-8"))
        fm["source"], fm["source_id"] = r["src"], key
        p.write_text(dump_note(fm, body), encoding="utf-8")
        tasks._commit(p, f"görev içe aktarıldı: {p.stem}", key, "import")
        known.add(key)
    out = _summary(rows[0]["src"] if rows else "tasks", [{"date_ms": None}] * len(rows), titles, new)
    return out
