"""Faz 3a Paket V — verimlilik: görev panosu, tekrar/bağımlılık, günlük plan, pomodoro, alışkanlık, hedef, haftalık gözden geçirme.

Görev kaynağı `sb/tasks.py` (`25-Görevler/*.md`, `type: gorev`); burada yeni depo yok. Ek alanlar: `priority` (1 yüksek..3), `repeat`,
`after` (bağımlı olunan görev kimliği = dosya adı), `repeat_spawned`. Sütun eşlemesi: todo = inbox/bekliyor/engelli, doing = aktif,
done = tamamlandi. Kural tabanlıdır (model yok). Kasaya yazılan metin `redact`'tan geçer; hiçbir şey silinmez.
"""
from __future__ import annotations

import calendar as _cal
import json
import re
import unicodedata
import zlib
from datetime import date, datetime, time, timedelta
from pathlib import Path

from . import config, tasks, vault_ops
from .notes import dump_note, split_note
from .redact import redact

OWNER = "Ayşe"
COLUMNS = (("todo", "Yapılacak"), ("doing", "Sürüyor"), ("done", "Bitti"))
STATUS_OF = {"todo": "inbox", "doing": "aktif", "done": "tamamlandi"}
COL_OF = {"inbox": "todo", "bekliyor": "todo", "engelli": "todo", "aktif": "doing", "tamamlandi": "done"}
WEEKDAYS = {"pazartesi": 0, "sali": 1, "carsamba": 2, "persembe": 3, "cuma": 4, "cumartesi": 5, "pazar": 6}
WORK_START, WORK_END = time(9, 0), time(18, 0)
RISK_DAYS = 3
DEADLINE_DIRS = ("00-Inbox", "10-Dersler", "20-Projeler", "30-Kariyer")
DONE_SHOWN = 30
REVIEW_QUESTIONS = ["Bu hafta ne iyi gitti?", "Neler takıldı, neden?", "Gelecek hafta tek ana odak ne?"]


def _fold(s) -> str:
    s = unicodedata.normalize("NFKD", str(s).replace("İ", "i").replace("ı", "i").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _d(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10]) if v else None
    except ValueError:
        return None


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


def _prio(v) -> int:
    s = _fold(v or "")
    if s in ("1", "yuksek", "high", "p1", "acil"):
        return 1
    if s in ("3", "dusuk", "low", "p3"):
        return 3
    return 2


def _commit(p: Path, msg: str, detail: str = "") -> None:
    rel = vault_ops._rel(p)
    sha = vault_ops.commit([rel], msg)
    vault_ops.log("claude", msg.split(":")[0], rel, detail[:160], sha)


def _folder() -> Path:
    return vault_ops.VAULT / tasks.FOLDER


# ---------------------------------------------------------------- görevler
def load_tasks() -> list[dict]:
    rows = []
    folder = _folder()
    for p in sorted(folder.glob("*.md")) if folder.exists() else []:
        try:
            fm = split_note(p.read_text(encoding="utf-8"))[0]
        except OSError:
            continue
        status = str(fm.get("status") or "")
        if status == "iptal" or fm.get("type") not in (None, "gorev"):
            continue
        rows.append({"id": p.stem, "text": p.stem, "due": _d(fm.get("due")), "project": fm.get("project") or "", "path": vault_ops._rel(p),
                     "priority": _prio(fm.get("priority")), "status": status, "col": COL_OF.get(status, "todo"),
                     "repeat": str(fm.get("repeat") or ""), "after": str(fm.get("after") or ""),
                     "created": _d(fm.get("created")) or date.today(), "updated": _d(fm.get("updated")) or date.today()})
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        dep = by_id.get(r["after"])
        r["blocked"] = dep is not None and dep["col"] != "done" and r["col"] != "done"
    return rows


def _card(r: dict) -> dict:
    return {"id": r["id"], "text": r["text"], "due": _iso(r["due"]), "project": r["project"], "path": r["path"], "priority": r["priority"],
            "blocked": r["blocked"], "repeat": r["repeat"], "after": r["after"]}


def board() -> dict:
    rows = load_tasks()
    cols = []
    for cid, title in COLUMNS:
        cs = [r for r in rows if r["col"] == cid]
        if cid == "done":
            cs = sorted(cs, key=lambda r: r["updated"], reverse=True)[:DONE_SHOWN]
        else:
            cs.sort(key=lambda r: (r["priority"], r["due"] or date.max, r["text"]))
        cols.append({"id": cid, "title": title, "cards": [_card(r) for r in cs]})
    return {"columns": cols}


def _path_of(tid: str) -> Path:
    if not tid or Path(tid).name != tid or tid.endswith(".md") or ".." in tid:
        raise ValueError("geçersiz görev kimliği")
    p = _folder() / f"{tid}.md"
    if not p.is_file():
        raise LookupError("görev bulunamadı")
    return p


def _set_fm(p: Path, **kv) -> None:
    fm, body = split_note(p.read_text(encoding="utf-8"))
    for k, v in kv.items():
        if v is None:
            fm.pop(k, None)
        else:
            fm[k] = v
    p.write_text(dump_note(fm, body), encoding="utf-8")


def next_due(repeat: str, base: date) -> date | None:
    """Tekrar kuralına göre `base`'den sonraki tarih (daily|weekly|monthly|gün adı)."""
    r = _fold(repeat)
    if r in ("daily", "gunluk", "her gun"):
        return base + timedelta(days=1)
    if r in ("weekly", "haftalik"):
        return base + timedelta(days=7)
    if r in ("monthly", "aylik"):
        m = base.month % 12 + 1
        y = base.year + (base.month == 12)
        return date(y, m, min(base.day, _cal.monthrange(y, m)[1]))
    if r in WEEKDAYS:
        return base + timedelta(days=(WEEKDAYS[r] - base.weekday()) % 7 or 7)
    return None


def add_task(text: str, due: str = "", project: str = "", priority=None, repeat: str = "", after: str = "") -> dict:
    text = " ".join(str(text or "").split())[:120]
    if not text:
        raise ValueError("görev metni boş")
    if re.search(r'[\\/:*?"<>|]', text):
        raise ValueError('görev metninde \\ / : * ? " < > | olamaz')
    if due and not _d(due):
        raise ValueError("tarih YYYY-AA-GG olmalı")
    if repeat and next_due(str(repeat), date.today()) is None:
        raise ValueError("tekrar: daily|weekly|monthly ya da gün adı (ör. cuma)")
    if after:
        _path_of(str(after))                                # yoksa LookupError
    msg = tasks.add(redact(text), "", OWNER, str(project or ""), _iso(_d(due)), "", "inbox", "claude")
    if not msg.startswith("Görev oluşturuldu"):
        raise ValueError(msg)
    p = vault_ops.VAULT / msg.split(": ", 1)[1].strip()
    _set_fm(p, priority=_prio(priority) if priority not in (None, "") else None, repeat=repeat or None, after=after or None)
    return next(_card(r) for r in load_tasks() if r["id"] == p.stem)


def _spawn_repeat(p: Path) -> str | None:
    fm = split_note(p.read_text(encoding="utf-8"))[0]
    if not fm.get("repeat") or fm.get("repeat_spawned"):
        return None
    nd = next_due(str(fm["repeat"]), max(_d(fm.get("due")) or date.today(), date.today()))
    if not nd:
        return None
    title = re.sub(r"\s*\(\d{4}-\d{2}-\d{2}\)$", "", p.stem)
    card = add_task(f"{title} ({nd})", nd.isoformat(), str(fm.get("project") or ""), fm.get("priority"), str(fm["repeat"]))
    _set_fm(p, repeat_spawned=True)
    return card["id"]


def move_task(tid: str, to: str) -> dict:
    if to not in STATUS_OF:
        raise ValueError("to: todo|doing|done")
    p = _path_of(tid)
    row = next((r for r in load_tasks() if r["id"] == tid), None)
    if row and row["blocked"] and to != "todo":
        raise PermissionError(f"engelli: önce '{row['after']}' bitmeli")
    status = STATUS_OF[to]
    if row and to == "todo" and row["col"] == "todo":
        status = row["status"]
    msg = tasks.update(vault_ops._rel(p), status=status, actor="claude")
    if not msg.startswith("Görev güncellendi"):
        raise ValueError(msg)
    spawned = _spawn_repeat(p) if to == "done" else None
    return {"ok": True, "id": tid, "to": to, "spawned": spawned}


# ---------------------------------------------------------------- teslimler
def deliverables() -> list[dict]:
    """`type: teslim` ya da `due:` alanlı notlar (görev klasörü ve tamamlananlar hariç)."""
    out = []
    for top in DEADLINE_DIRS:
        base = vault_ops.VAULT / top
        for p in sorted(base.rglob("*.md")) if base.exists() else []:
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            if not text.startswith("---") or ("due:" not in text[:1500] and "teslim" not in text[:1500]):
                continue
            fm = split_note(text)[0]
            d = _d(fm.get("due"))
            if not d or (fm.get("type") != "teslim" and "due" not in fm) or str(fm.get("status") or "") in vault_ops.DONE:
                continue
            out.append({"title": str(fm.get("title") or p.stem), "due": d, "path": vault_ops._rel(p), "project": fm.get("project") or ""})
    return sorted(out, key=lambda x: x["due"])


# ---------------------------------------------------------------- günlük not
def daily_path(d: date | None = None) -> Path:
    return vault_ops.VAULT / "50-Günlük" / f"{(d or date.today()).isoformat()}.md"


def append_section(p: Path, heading: str, line: str) -> None:
    line = redact(line)
    if p.exists():
        fm, body = split_note(p.read_text(encoding="utf-8"))
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        fm, body = {"type": "gunluk", "tags": ["gunluk"], "created": date.today(), "updated": date.today()}, f"# {p.stem}\n"
    h = f"## {heading}"
    if h in body:
        i = body.index(h) + len(h)
        j = body.find("\n## ", i)
        if j < 0:
            body = body.rstrip("\n") + "\n" + line + "\n"
        else:
            body = body[:j].rstrip("\n") + "\n" + line + "\n" + body[j:]
    else:
        body = body.rstrip() + f"\n\n{h}\n{line}\n"
    p.write_text(dump_note(fm, body), encoding="utf-8")
    _commit(p, f"günlük: {heading} {p.stem}", line)


def pomodoro(task_id: str, minutes) -> dict:
    minutes = int(minutes)
    if not 1 <= minutes <= 180:
        raise ValueError("dakika 1..180 olmalı")
    name = _path_of(str(task_id)).stem if task_id else ""
    append_section(daily_path(), "Odak", f"- {datetime.now():%H:%M} · {minutes} dk" + (f" · [[{name}]]" if name else ""))
    return {"ok": True, "minutes": minutes, "task": name}


def set_mood(level) -> dict:
    level = int(level)
    if not 1 <= level <= 5:
        raise ValueError("seviye 1..5 olmalı")
    append_section(daily_path(), "Ruh hali", f"- {datetime.now():%H:%M} · seviye {level}")
    return {"ok": True, "level": level}


def get_mood(d: date | None = None) -> int | None:
    p = daily_path(d)
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8")
    if "## Ruh hali" not in text:
        return None
    found = re.findall(r"seviye (\d)", text.split("## Ruh hali", 1)[1].split("\n## ", 1)[0])
    return int(found[-1]) if found else None


# ---------------------------------------------------------------- bugün + plan
def _score(r: dict, today: date) -> tuple:
    soon = r["due"] is not None and r["due"] <= today + timedelta(days=1)
    return (0 if soon else 1, r["priority"], -(today - r["created"]).days, r["due"] or date.max, r["text"])


def candidates(today: date | None = None) -> list[dict]:
    today = today or date.today()
    rows = [r for r in load_tasks() if r["col"] in ("todo", "doing") and not r["blocked"]]
    return sorted(rows, key=lambda r: _score(r, today))


def _naive(s: str) -> datetime:
    a = datetime.fromisoformat(s)
    return a.astimezone().replace(tzinfo=None) if a.tzinfo else a


def day_events(day: date, calendar=None) -> tuple[list[dict], str]:
    """(etkinlikler [{start,end,title}], hata) — takvim okunamazsa boş liste + açıklama."""
    try:
        if calendar is None:
            from .gcal_api import Calendar
            calendar = Calendar("main")
        a = datetime.combine(day, time.min).astimezone()
        evs = calendar.list_events(a, a + timedelta(days=1))
    except Exception as e:                                         # noqa: BLE001 — takvimsiz de plan çıkmalı
        return [], f"Takvim okunamadı ({type(e).__name__}); plan yalnız görevlerden."
    out = []
    for ev in evs:
        s, e = ev.get("start", {}), ev.get("end", {})
        if "dateTime" in s:                                        # tüm gün etkinlikleri zaman bloğu değildir
            a, b = _naive(s["dateTime"]), _naive(e.get("dateTime", s["dateTime"]))
            out.append({"start": a, "end": max(a, b), "title": ev.get("summary") or "(adsız)"})
    return sorted(out, key=lambda x: x["start"]), ""


def conflicts(events: list[dict]) -> list[str]:
    out = []
    for i, a in enumerate(events):
        for b in events[i + 1:]:
            if a["start"] < b["end"] and b["start"] < a["end"]:
                out.append(f"Çakışma: «{a['title']}» ve «{b['title']}» ({max(a['start'], b['start']):%H:%M})")
    return out


def _when(d: date, today: date) -> str:
    n = (d - today).days
    return "gecikti" if n < 0 else "bugün" if n == 0 else "yarın" if n == 1 else f"{n} gün sonra"


def risk_warnings(today: date | None = None, rows: list[dict] | None = None) -> list[dict]:
    """Teslime ≤3 gün kalmış ve ilgili görev hâlâ 'todo' ise uyarı. [{key, text}]"""
    today = today or date.today()
    rows = load_tasks() if rows is None else rows
    out, seen = [], set()
    for r in rows:
        if r["col"] == "todo" and r["due"] and (r["due"] - today).days <= RISK_DAYS:
            out.append({"key": f"task:{r['id']}", "text": f"Teslim riski: «{r['text']}» {_when(r['due'], today)} ama henüz başlanmadı"})
            seen.add(_fold(r["text"]))
    for d in deliverables():
        if (d["due"] - today).days > RISK_DAYS:
            continue
        rel = [r for r in rows if _fold(d["title"]) in _fold(r["text"]) or _fold(r["text"]) in _fold(d["title"])
               or (d["project"] and r["project"] == d["project"])]
        if _fold(d["title"]) in seen or any(r["col"] != "todo" for r in rel):
            continue
        out.append({"key": f"teslim:{d['path']}", "text": f"Teslim riski: «{d['title']}» {_when(d['due'], today)}"
                    + (" ama ilgili görev başlamadı" if rel else " ve ilgili görev yok")})
    return out


def _reason(r: dict, today: date) -> str:
    if r["due"] and r["due"] <= today + timedelta(days=1):
        return "teslim " + _when(r["due"], today)
    return "öncelik " + str(r["priority"])


def plan_today(calendar=None, now: datetime | None = None) -> dict:
    now = now or datetime.now()
    today = now.date()
    events, err = day_events(today, calendar)
    mood = get_mood(today)
    low = mood is not None and mood <= 2
    cands = candidates(today)
    top3 = [dict(_card(r), reason=_reason(r, today)) for r in cands[:3]]
    warnings = ([err] if err else []) + conflicts(events) + [w["text"] for w in risk_warnings(today)]
    order = sorted(cands[:6], key=lambda r: r["priority"] == 1) if low else cands[:6]      # düşük ruh halinde zor iş sona kalır
    cursor = max(datetime.combine(today, WORK_START), (now + timedelta(minutes=4)).replace(second=0, microsecond=0))
    cursor = cursor.replace(minute=cursor.minute - cursor.minute % 5)
    end_day = datetime.combine(today, WORK_END)
    plan = [{"start": e["start"].strftime("%H:%M"), "end": e["end"].strftime("%H:%M"), "title": e["title"], "kind": "etkinlik"} for e in events]
    busy = [(e["start"], e["end"]) for e in events if e["end"] > e["start"]]
    placed = 0
    for r in order:
        while True:                                            # imleç etkinlik içindeyse sonrasına taşı
            hit = next(((a, b) for a, b in busy if a <= cursor < b), None)
            if not hit:
                break
            cursor = hit[1]
        while True:
            nxt = min([a for a, _ in busy if a > cursor] + [end_day])
            if int((nxt - cursor).total_seconds() // 60) >= 25 or nxt >= end_day:
                break
            cursor = next(b for a, b in busy if a == nxt)
        gap = int((nxt - cursor).total_seconds() // 60)
        if gap < 25:
            break
        mins = 50 if (not low and gap >= 50 and r["priority"] <= 2) else 25
        end = cursor + timedelta(minutes=mins)
        plan.append({"start": cursor.strftime("%H:%M"), "end": end.strftime("%H:%M"), "title": r["text"], "kind": "görev", "task_id": r["id"]})
        placed += 1
        cursor = end
        if nxt - cursor >= timedelta(minutes=30):
            br = cursor + timedelta(minutes=10 if mins == 50 else 5)
            plan.append({"start": cursor.strftime("%H:%M"), "end": br.strftime("%H:%M"), "title": "Mola", "kind": "mola"})
            cursor = br
    plan.sort(key=lambda x: x["start"])
    if order and not placed:
        warnings.append("Bugün takvimde görev bloğuna yer kalmadı.")
    return {"top3": top3, "plan": plan, "warnings": warnings, "mood": mood}


def check_risks(today: date | None = None) -> list[str]:
    """Riskleri bildirim merkezine yazar (anahtar başına günde bir kez); yazılan metinleri döndürür."""
    today = today or date.today()
    f = config.DATA / "plan_notified.json"
    try:
        seen = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        seen = {}
    seen = {k: v for k, v in seen.items() if v == today.isoformat()}
    sent = []
    for w in risk_warnings(today):
        if w["key"] in seen:
            continue
        try:
            from . import convstore
            convstore.notify("Teslim riski", w["text"], "reminder")
        except Exception:                                      # noqa: BLE001
            continue
        seen[w["key"]] = today.isoformat()
        sent.append(w["text"])
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return sent


def format_plan(p: dict) -> str:
    if p["top3"]:
        lines = ["Bugünün ilk 3 işi:"] + [f"{i}. {t['text']} ({t['reason']})" for i, t in enumerate(p["top3"], 1)]
    else:
        lines = ["Açık görev yok."]
    if p["plan"]:
        lines += ["", "Plan:"] + [f"{x['start']}-{x['end']} {x['title']} [{x['kind']}]" for x in p["plan"]]
    if p["warnings"]:
        lines += ["", "Uyarılar:"] + [f"! {w}" for w in p["warnings"]]
    return "\n".join(lines)


def morning_text(calendar=None) -> str:
    """Sabah özetine eklenecek kısa metin (hata vermez)."""
    try:
        p = plan_today(calendar)
        check_risks()
    except Exception as e:                                     # noqa: BLE001
        return f"Plan üretilemedi: {type(e).__name__}"
    parts = []
    if p["top3"]:
        parts.append("Bugünün 3 işi: " + "; ".join(t["text"] for t in p["top3"]))
    ev = [x for x in p["plan"] if x["kind"] == "etkinlik"]
    if ev:
        parts.append("Takvim: " + ", ".join(f"{x['start']} {x['title']}" for x in ev[:4]))
    parts += p["warnings"][:3]
    return "\n".join(parts)


def format_board(b: dict) -> str:
    out = []
    for c in b["columns"]:
        out.append(f"{c['title']} ({len(c['cards'])})")
        out += [f"  - {k['text']}" + (f" · son {k['due']}" if k["due"] else "") + (" · ENGELLİ" if k["blocked"] else "") for k in c["cards"]]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    """`sb plan` / `sb tasks-board` için: main(["plan"]) ya da main(["board"])."""
    cmd = argv[0] if argv else "plan"
    print(format_board(board()) if cmd in ("board", "tasks-board") else format_plan(plan_today()))
    return 0


# ---------------------------------------------------------------- alışkanlıklar
def _hfile() -> Path:
    return config.DATA / "habits.json"


def _hload() -> list[dict]:
    try:
        return json.loads(_hfile().read_text(encoding="utf-8")).get("habits", [])
    except (OSError, ValueError, AttributeError):
        return []


def _hsave(hs: list[dict]) -> None:
    f = _hfile()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"habits": hs}, ensure_ascii=False, indent=1), encoding="utf-8")


def streak(done: list[str], today: date | None = None) -> int:
    today = today or date.today()
    s = set(done)
    d = today if today.isoformat() in s else today - timedelta(days=1)
    n = 0
    while d.isoformat() in s:
        n, d = n + 1, d - timedelta(days=1)
    return n


def habits() -> list[dict]:
    t = date.today().isoformat()
    return [{"id": h["id"], "name": h["name"], "done_today": t in h["done"], "streak": streak(h["done"]), "total": len(h["done"])} for h in _hload()]


def habit_add(name: str) -> list[dict]:
    name = " ".join(str(name or "").split())[:60]
    if not name:
        raise ValueError("alışkanlık adı boş")
    hs = _hload()
    if any(_fold(h["name"]) == _fold(name) for h in hs):
        raise ValueError("bu alışkanlık zaten var")
    hs.append({"id": f"h{len(hs) + 1}-{zlib.crc32(name.encode()) % 10000}", "name": name, "created": date.today().isoformat(), "done": []})
    _hsave(hs)
    return habits()


def habit_mark(hid: str, done: bool = True) -> list[dict]:
    hs = _hload()
    h = next((x for x in hs if x["id"] == hid), None)
    if not h:
        raise LookupError("alışkanlık bulunamadı")
    t = date.today().isoformat()
    days = set(h["done"]) - {t}
    h["done"] = sorted(days | ({t} if done else set()))
    _hsave(hs)
    return habits()


# ---------------------------------------------------------------- hedefler
def goals() -> list[dict]:
    folder = vault_ops.VAULT / "40-Kaynaklar" / "Hedefler"
    out = []
    for p in sorted(folder.glob("*.md")) if folder.exists() else []:
        fm, body = split_note(p.read_text(encoding="utf-8"))
        krs = [{"text": m.group(2).strip(), "done": m.group(1).lower() == "x"} for m in re.finditer(r"^\s*- \[([ xX])\]\s*(.+)$", body, re.M)]
        n = sum(k["done"] for k in krs)
        out.append({"title": str(fm.get("title") or p.stem), "path": vault_ops._rel(p), "key_results": krs, "done": n, "total": len(krs),
                    "progress": round(100 * n / len(krs)) if krs else 0})
    return out


# ---------------------------------------------------------------- haftalık gözden geçirme
def week_id(d: date | None = None) -> str:
    y, w, _ = (d or date.today()).isocalendar()
    return f"{y}-W{w:02d}"


def _week_note() -> Path:
    return vault_ops.VAULT / "50-Günlük" / "Haftalık" / f"{week_id()}.md"


def review_week() -> dict:
    today = date.today()
    rows = load_tasks()
    since = today - timedelta(days=7)
    try:
        from . import memory
        rec = [{"date": r["date"].isoformat(), "project": r["project"], "text": r["text"]} for r in memory.receipts(since, today)]
    except Exception:                                          # noqa: BLE001
        rec = []
    p = _week_note()
    return {"week": week_id(), "done": [_card(r) for r in rows if r["col"] == "done" and r["updated"] >= since],
            "remaining": [_card(r) for r in rows if r["col"] != "done"], "receipts": rec,
            "next_week": [{"title": d["title"], "due": d["due"].isoformat(), "path": d["path"]}
                          for d in deliverables() if today <= d["due"] <= today + timedelta(days=7)],
            "questions": REVIEW_QUESTIONS, "note": vault_ops._rel(p) if p.exists() else ""}


def review_save(answers) -> dict:
    if isinstance(answers, dict):
        pairs = [(str(q), str(a)) for q, a in answers.items()]
    elif isinstance(answers, list):
        pairs = [(REVIEW_QUESTIONS[i] if i < len(REVIEW_QUESTIONS) else f"Soru {i + 1}", str(a)) for i, a in enumerate(answers)]
    else:
        raise ValueError("answers: sözlük ya da liste olmalı")
    pairs = [(q[:200], " ".join(a.split())[:2000]) for q, a in pairs if a.strip()]
    if not pairs:
        raise ValueError("cevap boş")
    p = _week_note()
    if p.exists():
        fm, body = split_note(p.read_text(encoding="utf-8"))
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        fm, body = {"type": "haftalik", "tags": ["haftalik"], "created": date.today()}, f"# Haftalık gözden geçirme {week_id()}\n"
    fm["updated"] = date.today()
    body = body.rstrip() + f"\n\n## {date.today()}\n" + "".join(f"- **{redact(q)}** {redact(a)}\n" for q, a in pairs)
    p.write_text(dump_note(fm, body), encoding="utf-8")
    _commit(p, f"haftalık gözden geçirme: {week_id()}")
    return {"ok": True, "path": vault_ops._rel(p)}
