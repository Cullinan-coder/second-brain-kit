"""Faz 2 API: görünüm verileri — pano, grafik, zaman çizelgesi, kişi, proje, arama, komut paleti (Paket A).

Kasa taraması pahalı olduğundan not başına özet (frontmatter alanları + wikilink'ler) `(mtime, boyut)` ile önbelleğe alınır
(bellek + `DATA/views_index.json`); bir çağrıda yalnız değişen dosyalar yeniden okunur. Tüm uçlar salt okunurdur.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

from . import config, convstore, vault_ops
from .convstore import fold
from .redact import redact
from .webroutes import ApiError, Ctx, route

SKIP = {".obsidian", ".git", ".trash", "_system", "_templates", ".venv", "90-Arşiv", "node_modules", "_attachments"}
MIRROR = ("40-Kaynaklar/Mail/", "40-Kaynaklar/Bilgisayar/", "40-Kaynaklar/Drive/", "40-Kaynaklar/Analiz/", "40-Kaynaklar/Kümeler/", "00-Inbox/")
LINK_RE = re.compile(r"\[\[([^\]|#]+)")
AUTO_BLOCK = re.compile(r"<!-- sb:auto:(\S+?):start -->.*?<!-- sb:auto:\1:end -->", re.S)
FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
FM_KEYS = ("type", "status", "due", "due_time", "updated", "created", "aliases", "phone", "email", "company", "role", "linkedin",
           "visibility", "local_path", "tags")
OPEN_STATUS_DONE = {"tamamlandi", "iptal", "arsiv", "kabul", "red", "yapildi", "vazgecildi", "pasif"}
TTL = 3.0
VIEWS = [("dashboard", "Pano"), ("graph", "Bilgi grafiği"), ("timeline", "Zaman çizelgesi"), ("memory", "Hafıza düzenleyici"),
         ("cards", "Bilgi kartları"), ("settings", "Ayarlar"), ("errors", "Hata panosu"), ("learn", "Öğrenme yolu"), ("journal", "Ortak günlük")]
_Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

_state: dict = {"vault": None, "entries": {}, "at": 0.0, "graph": None, "loaded": False}


def reset_cache() -> None:
    _state.update({"vault": None, "entries": {}, "at": 0.0, "graph": None, "loaded": False})


# ---------------------------------------------------------------- not dizini
def _plain(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10]
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    return v if isinstance(v, (str, int, float, bool)) or v is None else str(v)


def _read_entry(p: Path, rel: str, mtime: float, size: int) -> dict | None:
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fm: dict = {}
    body = text
    m = FM_RE.match(text)
    if m:
        try:
            raw = yaml.load(m.group(1), Loader=_Loader)
            fm = raw if isinstance(raw, dict) else {}
        except yaml.YAMLError:
            fm = {}
        body = text[m.end():]
    return {"rel": rel, "stem": p.stem, "m": mtime, "s": size, "fm": {k: _plain(fm[k]) for k in FM_KEYS if k in fm},
            "links": sorted(set(t.strip() for t in LINK_RE.findall(body))), "mirror": rel.startswith(MIRROR)}


def _load_disk(vault: str) -> dict:
    p = config.DATA / "views_index.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d["entries"] if d.get("vault") == vault else {}
    except (OSError, json.JSONDecodeError, KeyError, AttributeError):
        return {}


def _save_disk(vault: str, entries: dict) -> None:
    try:
        p = config.DATA / "views_index.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"vault": vault, "entries": entries}, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, p)
    except OSError:
        pass


def index() -> dict[str, dict]:
    """rel yol → not özeti. Önbellek TTL içinde taramaz; sonra yalnız değişen dosyaları okur."""
    vault = vault_ops.VAULT
    key = str(vault)
    if _state["vault"] == key and time.time() - _state["at"] < TTL:
        return _state["entries"]
    old = _state["entries"] if _state["vault"] == key else _load_disk(key)
    new: dict[str, dict] = {}
    changed = False
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            p = Path(root) / f
            try:
                st = p.stat()
            except OSError:
                continue
            rel = p.relative_to(vault).as_posix()
            e = old.get(rel)
            if e and e["m"] == st.st_mtime and e["s"] == st.st_size:
                new[rel] = e
                continue
            e = _read_entry(p, rel, st.st_mtime, st.st_size)
            if e:
                new[rel] = e
                changed = True
    if changed or len(new) != len(old):
        _save_disk(key, new)
    elif _state["vault"] == key:
        new = old                                             # değişiklik yok: aynı nesne, bağlantı grafiği önbelleği geçerli kalır
        _state["at"] = time.time()
        return new
    _state.update({"vault": key, "entries": new, "at": time.time(), "graph": None})
    return new


def _kind(e: dict) -> str:
    t, rel = str(e["fm"].get("type") or ""), e["rel"]
    if t in ("kisi", "proje", "ders", "kavram"):
        return t
    top = rel.split("/")[0]
    if top == "60-Kişiler":
        return "kisi"
    if top == "20-Projeler":
        return "proje"
    if top == "10-Dersler":
        return "ders"
    if rel.startswith("40-Kaynaklar/Kavramlar/"):
        return "kavram"
    return t or "not"


def _private(e: dict) -> bool:
    return e["fm"].get("visibility") == "private"


def _stem_map(entries: dict) -> dict[str, list[str]]:
    sm: dict[str, list[str]] = defaultdict(list)
    for rel, e in entries.items():
        sm[e["stem"].lower()].append(rel)
    return sm


def links(entries: dict) -> tuple[dict[str, set], dict[str, set]]:
    """(giden, gelen) wikilink'ler; kaynak olarak ayna/analiz notları sayılmaz."""
    g = _state.get("graph")
    if g and g[0] is entries:
        return g[1], g[2]
    sm = _stem_map(entries)
    out, inn = defaultdict(set), defaultdict(set)
    for rel, e in entries.items():
        if e["mirror"]:
            continue
        for t in e["links"]:
            for dst in sm.get(Path(t).name.lower(), []):
                if dst != rel:
                    out[rel].add(dst)
                    inn[dst].add(rel)
    _state["graph"] = (entries, out, inn)
    return out, inn


def _date(v) -> date | None:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(v or ""))
    try:
        return date(*map(int, m.groups())) if m else None
    except ValueError:
        return None


def _upd(e: dict) -> str:
    return str(e["fm"].get("updated") or e["fm"].get("created") or datetime.fromtimestamp(e["m"]).strftime("%Y-%m-%d"))


def _list(v) -> list[str]:
    if v in (None, "", "null"):
        return []
    return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else [str(v).strip()]


def _safe(fn, default):
    try:
        return fn()
    except Exception:                                         # noqa: BLE001 — bir bölümün hatası panoyu düşürmesin
        return default


def _read(rel: str) -> str:
    return (vault_ops.VAULT / rel).read_text(encoding="utf-8")


def _section(body: str, head: str, level: int = 2) -> str:
    """`## head` altındaki metin (bir sonraki aynı/üst düzey başlığa kadar)."""
    m = re.search(rf"^{'#' * level} {re.escape(head)}[^\n]*\n(.*?)(?=^#{{1,{level}}} |\Z)", body, re.S | re.M)
    return AUTO_BLOCK.sub("", m.group(1)).strip() if m else ""        # otomatik bölümler insan metni sayılmaz


def _bullets(text: str, limit: int = 15) -> list[str]:
    out = []
    for line in text.splitlines():
        m = re.match(r"^\s*[-*] (?:\[[ xX]\] )?(.+)$", line)
        if m and m.group(1).strip() and "~~" not in m.group(1):
            out.append(redact(m.group(1).strip())[:300])
    return out[:limit]


# ---------------------------------------------------------------- pano
def _greeting() -> str:
    h = datetime.now().hour
    return f"{'Günaydın' if 5 <= h < 12 else 'İyi günler' if 12 <= h < 18 else 'İyi akşamlar' if h < 23 else 'İyi geceler'} {config.USER}"


def _calendar_today(cal) -> list[dict]:
    if cal is None:
        return []
    start = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    out = []
    for ev in cal.list_events(start, start + timedelta(days=1)):
        s = ev.get("start", {})
        t = s.get("dateTime", "")[11:16]
        out.append({"time": t, "title": ev.get("summary", "(başlıksız)"), "kind": "takvim"})
    return out


def _dash_due(entries: dict, days: int = 14) -> tuple[list, list]:
    today = date.today()
    end = today + timedelta(days=days)
    due, tod = [], []
    for rel, e in entries.items():
        if rel.split("/")[0] not in ("10-Dersler", "20-Projeler", "30-Kariyer", "25-Görevler"):
            continue
        d = _date(e["fm"].get("due"))
        if not d or e["fm"].get("status") in OPEN_STATUS_DONE or not (today <= d <= end):
            continue
        row = {"date": d.isoformat(), "title": e["stem"], "kind": str(e["fm"].get("type") or "not"), "path": rel}
        due.append(row)
        if d == today:
            tod.append({"time": str(e["fm"].get("due_time") or ""), "title": e["stem"], "kind": row["kind"]})
    due.sort(key=lambda r: r["date"])
    return due, sorted(tod, key=lambda r: r["time"])


def _dash_tasks(entries: dict) -> list[dict]:
    rows = [(str(e["fm"].get("due") or "9999"), {"text": e["stem"], "path": rel, "due": e["fm"].get("due") or ""})
            for rel, e in entries.items()
            if rel.startswith("25-Görevler/") and e["fm"].get("status") in ("inbox", "aktif", "bekliyor", "engelli")]
    return [r for _, r in sorted(rows, key=lambda x: x[0])][:12]


def _dash_recent(entries: dict) -> list[dict]:
    skip = MIRROR + ("50-Günlük/", "60-Kişiler/")
    rows = sorted((e for e in entries.values() if not e["rel"].startswith(skip) and not _private(e)), key=lambda e: -e["m"])
    return [{"title": e["stem"], "path": e["rel"], "updated": datetime.fromtimestamp(e["m"]).strftime("%Y-%m-%d %H:%M")} for e in rows[:8]]


def _inbox_count(entries: dict) -> int:
    return sum(1 for rel in entries if rel.startswith("00-Inbox/") and not rel.endswith("onay-bekleyenler.md"))


def _pending_lines() -> list[str]:
    p = vault_ops.VAULT / "00-Inbox" / "onay-bekleyenler.md"
    if not p.is_file():
        return []
    return [l[6:].strip()[:200] for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("- [ ] ")][:10]


_stats_cache: dict = {"at": 0.0, "key": None, "val": {}}


def _db_counts() -> dict:
    """Beyin dizini sayıları (60 sn önbellek); dizin yoksa 0."""
    from . import brain
    key = str(brain.DB)
    if _stats_cache["key"] == key and time.time() - _stats_cache["at"] < 60:
        return _stats_cache["val"]
    val = {"mails": 0, "chunks": 0}
    if brain.DB.is_file():
        con = sqlite3.connect(f"file:{brain.DB.as_posix()}?mode=ro", uri=True, timeout=5)
        try:
            val["mails"] = con.execute("SELECT COUNT(*) FROM docs WHERE kind='mail'").fetchone()[0]
            val["chunks"] = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        finally:
            con.close()
    _stats_cache.update({"at": time.time(), "key": key, "val": val})
    return val


def _suggestions(due: list, inbox: int, approvals: list, tasks: list) -> list[str]:
    s = []
    if due and due[0]["date"] == date.today().isoformat():
        s.append(f"Bugün teslim: {due[0]['title']}")
    elif due:
        s.append(f"En yakın tarih: {due[0]['title']} ({due[0]['date']})")
    if approvals:
        s.append(f"{len(approvals)} onay bekliyor")
    if inbox:
        s.append(f"Gelen kutusunda {inbox} not var; dağıtmak ister misin?")
    if tasks:
        s.append(f"{len(tasks)} açık görev var")
    return s or ["Bugün için acil bir şey görünmüyor."]


def _reflection(entries: dict) -> dict | None:
    for back in range(0, 3):
        d = (date.today() - timedelta(days=back)).isoformat()
        rel = f"50-Günlük/{d}.md"
        if rel in entries:
            txt = _section(_read(rel), "Yansıma")
            if txt:
                return {"text": redact(txt)[:800], "date": d}
    return None


@route("GET", "/api/v2/dashboard")
def dashboard(ctx: Ctx) -> dict:
    entries = _safe(index, {})
    due, today_rows = _safe(lambda: _dash_due(entries), ([], []))
    cal = _safe(lambda: _calendar_today(ctx.calendar), [])
    tasks = _safe(lambda: _dash_tasks(entries), [])
    inbox = _safe(lambda: _inbox_count(entries), 0)
    approvals = _safe(lambda: [{"kind": "takvim-adayi", "title": t} for t in _pending_lines()], [])
    approvals += _safe(lambda: _session_proposals(ctx), [])
    counts = _safe(_db_counts, {"mails": 0, "chunks": 0})
    stats = {"notes": len(entries), "people": sum(r.startswith("60-Kişiler/") for r in entries),
             "projects": sum(r.startswith("20-Projeler/") for r in entries), **counts}
    out = {"greeting": _greeting(), "today": sorted(cal + today_rows, key=lambda r: r["time"] or "99"), "due": due, "tasks": tasks,
           "recent": _safe(lambda: _dash_recent(entries), []), "inbox_count": inbox, "approvals": approvals, "stats": stats,
           "suggestions": _safe(lambda: _suggestions(due, inbox, approvals, tasks), [])}
    ref = _safe(lambda: _reflection(entries), None)
    if ref:
        out["reflection"] = ref
    return out


def _session_proposals(ctx: Ctx) -> list[dict]:
    if ctx.session is None:
        return []
    from . import chat
    return chat.pending(ctx.session)


# ---------------------------------------------------------------- grafik
@route("GET", "/api/v2/graph")
def graph(ctx: Ctx) -> dict:
    entries = index()
    out, inn = links(entries)
    try:
        limit = max(1, min(1000, int(ctx.arg("limit", 300))))
        depth = 2 if int(ctx.arg("depth", 1)) >= 2 else 1
    except (TypeError, ValueError):
        raise ApiError(400, "geçersiz limit/depth")
    kinds = {k.strip() for k in str(ctx.arg("kinds", "") or "").split(",") if k.strip()}
    nbr = {r: out.get(r, set()) | inn.get(r, set()) for r in set(out) | set(inn)}
    center = str(ctx.arg("center", "") or "").strip().replace("\\", "/")
    if center:
        if center not in entries:
            raise ApiError(404, "merkez not yok")
        seen, frontier = {center}, {center}
        for _ in range(depth):
            frontier = {n for f in frontier for n in nbr.get(f, ())} - seen
            seen |= frontier
        cand = seen
    else:
        cand = set(nbr)
    if kinds:
        cand = {r for r in cand if _kind(entries[r]) in kinds or r == center}
    pick = sorted(cand, key=lambda r: (r != center, -len(nbr.get(r, ())), r))[:limit]
    ps = set(pick)
    wt: dict[tuple[str, str], int] = defaultdict(int)
    for s in pick:
        for t in out.get(s, ()):
            if t in ps:
                wt[tuple(sorted((s, t)))] += 1
    nodes = [{"id": r, "label": entries[r]["stem"], "kind": _kind(entries[r]), "size": len([n for n in nbr.get(r, ()) if n in ps]) or 1,
              "cluster": r.split("/")[0]} for r in pick]
    return {"nodes": nodes, "edges": [{"s": a, "t": b, "w": w} for (a, b), w in sorted(wt.items())]}


# ---------------------------------------------------------------- zaman çizelgesi
@route("GET", "/api/v2/timeline")
def timeline(ctx: Ctx) -> list:
    q = str(ctx.arg("q", "") or "").strip()
    lo, hi = str(ctx.arg("from", "") or ""), str(ctx.arg("to", "") or "")
    kinds = {k.strip() for k in str(ctx.arg("kinds", "") or "").split(",") if k.strip()}
    rows: list[dict] = []
    seen: set[str] = set()
    if q:
        from . import analysis
        try:
            months = analysis.topic_timeline(q)
        except Exception:                                     # noqa: BLE001 — dizin yoksa yalnız not tarihleri
            months = {}
        for hits in months.values():
            for h in hits:
                s = convstore.to_source(h)
                rows.append({"date": s["date"], "title": s["title"], "kind": s["kind"], "doc_id": s["doc_id"], "snippet": s["snippet"],
                             **({"path": s["path"]} if "path" in s else {})})
                seen.add(s.get("path", ""))
    entries = index()
    fq = fold(q)
    for rel, e in entries.items():
        if rel in seen or e["mirror"] or rel.startswith("50-Günlük/Makbuzlar/"):
            continue
        if fq and not all(w in fold(e["stem"]) for w in fq.split()):
            continue
        rows.append({"date": _upd(e), "title": e["stem"], "kind": _kind(e), "path": rel, "snippet": ""})
    if lo:
        rows = [r for r in rows if r["date"] >= lo]
    if hi:
        rows = [r for r in rows if r["date"] <= hi]
    if kinds:
        rows = [r for r in rows if r["kind"] in kinds]
    rows.sort(key=lambda r: r["date"] or "", reverse=True)
    return rows[:200]


# ---------------------------------------------------------------- kişi
def _find_note(entries: dict, folder: str, name: str) -> dict | None:
    fq = fold(name).strip()
    if not fq:
        return None
    pool = [e for r, e in entries.items() if r.startswith(folder + "/")]
    for test in (lambda e: fold(e["stem"]) == fq,
                 lambda e: fq in [fold(a) for a in _list(e["fm"].get("aliases"))],
                 lambda e: fq in fold(e["stem"]),
                 lambda e: any(fq in fold(a) for a in _list(e["fm"].get("aliases")))):
        hits = [e for e in pool if test(e)]
        if hits:
            return sorted(hits, key=lambda e: len(e["stem"]))[0]
    return None


DATE_LINE = re.compile(r"(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?\s*(.*)")


def _auto(body: str, name: str) -> str:
    m = re.search(rf"<!-- sb:auto:{name}:start -->\n(.*?)<!-- sb:auto:{name}:end -->", body, re.S)
    return m.group(1).strip() if m else ""


@route("GET", "/api/v2/person")
def person(ctx: Ctx) -> dict:
    name = str(ctx.arg("name", "") or "")
    entries = index()
    e = _find_note(entries, "60-Kişiler", name)
    if not e:
        raise ApiError(404, "kişi bulunamadı")
    fm, rel = e["fm"], e["rel"]
    body = _read(rel)
    m = FM_RE.match(body)
    body = body[m.end():] if m else body
    out, inn = links(entries)
    chats = []
    for line in _auto(body, "telefon").splitlines():
        mm = re.match(r"^- (.+)$", line)
        d = DATE_LINE.match(mm.group(1)) if mm else None
        if d:
            chats.append({"date": f"{d.group(1)} {d.group(2) or ''}".strip(), "snippet": redact(d.group(3))[:160]})
    mails = [redact(l[2:].strip())[:200] for l in _auto(body, "mailler").splitlines() if l.startswith("- ")]
    last = max([c["date"] for c in chats] + [d.group(1) for d in (DATE_LINE.search(x) for x in mails) if d] or [""])
    refs = sorted(out.get(rel, set()) | inn.get(rel, set()))
    projects = [{"name": entries[r]["stem"], "path": r} for r in refs if r.startswith("20-Projeler/")]
    mention = [{"title": entries[r]["stem"], "path": r} for r in sorted(inn.get(rel, ())) if not r.startswith("20-Projeler/")][:30]
    declared = _bullets(_section(body, "Beyan"), 30)
    inferred = _bullets(_section(body, "Çıkarım (onay bekliyor)"), 30)
    return {"name": e["stem"], "path": rel, "aliases": _list(fm.get("aliases")), "company": fm.get("company") or "",
            "role": fm.get("role") or "", "phones": _list(fm.get("phone")), "emails": _list(fm.get("email")),
            "linkedin": fm.get("linkedin") or "", "last_contact": last, "mail": mails[:10], "chats": chats[:10],
            "notes_mentioning": mention, "projects": projects, "facts": {"declared": declared, "inferred": inferred}}


# ---------------------------------------------------------------- proje
@route("GET", "/api/v2/project")
def project(ctx: Ctx) -> dict:
    entries = index()
    e = _find_note(entries, "20-Projeler", str(ctx.arg("name", "") or ""))
    if not e:
        raise ApiError(404, "proje bulunamadı")
    rel, fm = e["rel"], e["fm"]
    body = _read(rel)
    m = FM_RE.match(body)
    body = redact(body[m.end():] if m else body)
    summary = re.sub(r"<!--.*?-->", "", _section(body, "Özet", 3) or _section(body, "Özet"), flags=re.S).strip()
    sess_block = _auto(body, "oturumlar")
    sessions = [{"date": d, "title": t.strip()} for d, t in re.findall(r"^#### (\d{4}-\d{2}-\d{2}) — (.+)$", sess_block, re.M)]
    decisions = _bullets(_section(body, "Kararlar"), 15)
    for blk in re.findall(r"\*\*Kararlar[^\n]*\n(.*?)(?=\n\*\*|\n####|\Z)", sess_block, re.S):
        decisions += _bullets(blk, 5)
    open_items = [x for x in _bullets(_section(body, "Yapılacaklar"), 20) if x.strip("[] ")]
    open_items += _bullets(_section(body, "Durum, eksikler ve açık işler", 3), 15)
    out, inn = links(entries)
    people = [{"name": entries[r]["stem"], "path": r} for r in sorted(out.get(rel, set()) | inn.get(rel, set())) if r.startswith("60-Kişiler/")]
    files = _bullets(_section(body, "Klasör ve dosya haritası", 3), 15)
    timeline_rows = _bullets(_section(body, "Zaman çizelgesi", 3) or _section(body, "Son çalışmalar"), 15)
    return {"name": e["stem"], "path": rel, "status": fm.get("status") or "", "summary": summary[:1200], "decisions": decisions[:20],
            "open": open_items[:30], "people": people, "files": files, "timeline": timeline_rows, "sessions": sessions[:15]}


# ---------------------------------------------------------------- arama
@route("GET", "/api/v2/search")
def search(ctx: Ctx) -> list:
    q = str(ctx.arg("q", "") or "").strip()
    try:
        k = max(1, min(50, int(ctx.arg("k", 10))))
    except (TypeError, ValueError):
        k = 10
    if not q:
        return []
    return convstore.search_sources(q, k, smart=True)         # doğal dil süzgeçleri; yoksa brain.find


# ---------------------------------------------------------------- palet
def _commands() -> list[dict]:
    from . import api_conv
    return api_conv.COMMANDS


def _match(fq: str, *texts: str) -> int:
    """0 = öneki eşleşir, 1 = içerir, 9 = eşleşmez (her sözcük aranır)."""
    hay = fold(" ".join(texts))
    if not all(w in hay for w in fq.split()):
        return 9
    return 0 if fold(texts[0]).startswith(fq) else 1


@route("GET", "/api/v2/palette")
def palette(ctx: Ctx) -> list:
    q = str(ctx.arg("q", "") or "").strip().lstrip("/")
    fq = fold(q)
    entries = _safe(index, {})
    items: list[tuple[int, int, dict]] = []                   # (eşleşme, tür sırası, öğe)
    for c in _commands()[: (None if fq else 5)]:
        items.append((_match(fq, c["cmd"][1:], c["desc"]) if fq else 0, 0,
                      {"type": "command", "label": c["cmd"], "sub": c["desc"], "action": {"cmd": c["cmd"]}}))
    for v, label in VIEWS[: (None if fq else 3)]:
        items.append((_match(fq, label, v) if fq else 1, 1, {"type": "view", "label": label, "action": {"view": v, "params": {}}}))
    if fq:
        for rel, e in entries.items():
            k = _kind(e)
            typ = "person" if k == "kisi" else "project" if k == "proje" else "note"
            sc = _match(fq, e["stem"], *_list(e["fm"].get("aliases")))
            if sc < 9:
                act = {"view": "person", "params": {"name": e["stem"]}} if typ == "person" else \
                      {"view": "project", "params": {"name": e["stem"]}} if typ == "project" else {"path": rel}
                items.append((sc, 2 if typ != "note" else 4, {"type": typ, "label": e["stem"], "sub": rel.rsplit("/", 1)[0] if "/" in rel else "", "action": act}))
        for c in _safe(lambda: convstore.list_convs(q, limit=8), []):
            items.append((1, 3, {"type": "conv", "label": c["title"], "sub": c["updated"][:16], "action": {"sid": c["sid"]}}))
    else:                                                     # boş sorgu: son kullanılanlar (son sohbetler + son değişen notlar)
        for c in _safe(lambda: convstore.list_convs(limit=5), []):
            items.append((0, 3, {"type": "conv", "label": c["title"], "sub": c["updated"][:16], "action": {"sid": c["sid"]}}))
        for r in _safe(lambda: _dash_recent(entries), [])[:5]:
            items.append((0, 4, {"type": "note", "label": r["title"], "sub": r["path"], "action": {"path": r["path"]}}))
    items = [i for i in items if i[0] < 9]
    items.sort(key=lambda i: (i[0], i[1]))
    return [i[2] for i in items[:20]]
