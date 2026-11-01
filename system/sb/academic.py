"""Okul (Faz 3a Paket K): ders panosu, GANO + senaryo, sınav takvimi/çalışma planı, program, hoca iletişimi, başvurular, belgeler.

Salt okunur çalışır; yazan tek işlev `write_study_plan` (ders klasörüne `Çalışma planı.md`). Yollar işlev içinde okunur ki testler yönlendirebilsin.
"""
from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

from . import config, vault_ops
from .notes import dump_note, split_note

ROOT = "10-Dersler"
SKIP = {".obsidian", ".git", ".trash", "_system", "_templates", ".venv", "90-Arşiv", "node_modules", "_attachments"}
SCALE = {"AA": 4.0, "BA": 3.5, "BB": 3.0, "CB": 2.5, "CC": 2.0, "DC": 1.5, "DD": 1.0, "FD": 0.5, "FF": 0.0}
TEMPLATE = ("# Not girişi: her ders için code, ad, kredi (AKTS), harf (AA..FF), donem.\n"
            "# Aynı kodlu ders birden çok kez varsa dosyada sonra geleni (tekrar) sayılır.\n"
            "dersler: []\n")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
DATE_TR = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
EXAM_LINE = re.compile(r"(vize|final|bütünleme|butunleme|sınav|sinav|quiz)", re.I)
TYPE_RE = re.compile(r"^type:\s*(\w+)", re.M)
HOCA_RE = re.compile(r"((?:Prof\. ?Dr\.|Doç\. ?Dr\.|Dr\. ?Öğr\. ?Üyesi|Dr\.|Arş\. ?Gör\.|Öğr\. ?Gör\.)\s*[A-ZÇĞİÖŞÜ][\w'çğıöşüÇĞİÖŞÜ]+(?: [A-ZÇĞİÖŞÜ][\w'çğıöşüÇĞİÖŞÜ]+){0,3})")


def _vault() -> Path:
    return Path(vault_ops.VAULT)


def notlar_path() -> Path:
    return config.SYSTEM / "config" / "notlar.yaml"


def ensure_template() -> Path:
    """Yoksa boş şablonu oluşturur (yalnız CLI/ilk kullanım; GET uçları çağırmaz)."""
    p = notlar_path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(TEMPLATE, encoding="utf-8")
    return p


def _iso(v) -> str | None:
    if v in (None, ""):
        return None
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10]
    m = DATE_RE.search(str(v))
    return m.group(0) if m else None


def _read(p: Path) -> tuple[dict, str]:
    try:
        return split_note(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}, ""


# ---------------------------------------------------------------- kasa taraması
def _scan(types: set[str]) -> list[dict]:
    """Kasada istenen `type` değerli notlar: {rel, path, stem, fm}. Önce yalnız başlık okunur."""
    root, out = _vault(), []
    if not root.exists():
        return out
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP]
        for fn in fns:
            if not fn.endswith(".md"):
                continue
            p = Path(dp) / fn
            try:
                with open(p, "r", encoding="utf-8") as f:
                    head = f.read(1500)
            except (OSError, UnicodeDecodeError):
                continue
            if not head.startswith("---"):
                continue
            m = TYPE_RE.search(head)
            if not m or m.group(1) not in types:
                continue
            fm, _ = _read(p)
            out.append({"rel": p.relative_to(root).as_posix(), "path": p, "stem": p.stem, "fm": fm})
    return out


def course_dirs() -> list[Path]:
    base = _vault() / ROOT
    if not base.is_dir():
        return []
    return sorted(d for d in base.iterdir() if d.is_dir() and d.name != "Geçmiş" and not d.name.startswith("."))


def _code_of(d: Path, fm: dict) -> str:
    return str(fm.get("code") or d.name.split()[0]).strip()


def _main_note(d: Path) -> Path:
    return d / f"{d.name}.md"


# ---------------------------------------------------------------- GANO
def load_grades() -> dict:
    """{'entries': [{code, ad, kredi, harf, donem}], 'source': 'notlar'|'obs'|'bos'}. notlar.yaml boşsa ÖBS verisine düşer."""
    entries: list[dict] = []
    try:
        d = yaml.safe_load(notlar_path().read_text(encoding="utf-8")) or {}
        for r in d.get("dersler") or []:
            if isinstance(r, dict) and r.get("code"):
                entries.append({"code": str(r["code"]), "ad": str(r.get("ad") or ""), "kredi": float(r.get("kredi") or 0),
                                "harf": str(r.get("harf") or "").upper(), "donem": str(r.get("donem") or "")})
    except (OSError, yaml.YAMLError, ValueError, TypeError, AttributeError):
        entries = []
    if entries:
        return {"entries": entries, "source": "notlar"}
    try:
        from . import obs
        for t in obs.load().get("donemler") or []:
            for code, name, akts, grade, _st in t.get("dersler") or []:
                if code:
                    entries.append({"code": str(code), "ad": str(name), "kredi": float(akts or 0), "harf": str(grade or "").upper(),
                                    "donem": str(t.get("ad") or "")})
    except Exception:                                            # noqa: BLE001 — veri yoksa boş
        entries = []
    return {"entries": entries, "source": "obs" if entries else "bos"}


def compute_gpa(entries: list[dict], changes: list[dict] | None = None) -> dict:
    """Tekrar edilen derste sonraki kayıt geçerli. changes: [{code, grade, credits?}] senaryo olarak üstüne biner."""
    latest: dict[str, dict] = {}
    for e in entries:
        latest[e["code"]] = dict(e)
    for c in changes or []:
        code = str(c.get("code") or "").strip()
        grade = str(c.get("grade") or "").upper().strip()
        if not code or grade not in SCALE:
            raise ValueError(f"geçersiz değişiklik: {code or '?'} {grade or '?'}")
        cur = latest.get(code)
        if cur is None:
            cr = float(c.get("credits") or 0)
            if cr <= 0:
                raise ValueError(f"{code} kayıtlı değil; 'credits' ver")
            cur = {"code": code, "ad": "", "kredi": cr, "harf": "", "donem": "Senaryo"}
        cur["harf"] = grade
        latest[code] = cur
    counted = [e for e in latest.values() if e["harf"] in SCALE and e["kredi"] > 0]
    credits = sum(e["kredi"] for e in counted)
    gpa = round(sum(SCALE[e["harf"]] * e["kredi"] for e in counted) / credits, 2) if credits else None
    terms: dict[str, list] = {}
    for e in entries:
        terms.setdefault(e["donem"] or "-", []).append(e)
    tl = []
    for name, rows in terms.items():
        cs = [e for e in rows if e["harf"] in SCALE and e["kredi"] > 0]
        cr = sum(e["kredi"] for e in cs)
        tl.append({"term": name, "gpa": round(sum(SCALE[e["harf"]] * e["kredi"] for e in cs) / cr, 2) if cr else None, "credits": cr,
                   "courses": [{"code": e["code"], "ad": e["ad"], "kredi": e["kredi"], "harf": e["harf"]} for e in rows]})
    return {"gpa": gpa, "credits": credits, "terms": tl}


def grade_of(code: str) -> str | None:
    last = None
    for e in load_grades()["entries"]:
        if e["code"] == code and e["harf"] in SCALE:
            last = e["harf"]
    return last


# ---------------------------------------------------------------- sınav / teslim
def _events_in(d: Path, code: str, teslimler: list[dict] | None = None) -> list[dict]:
    out, seen = [], set()
    for t in (teslimler if teslimler is not None else _scan({"teslim"})):
        fm = t["fm"]
        if code not in str(fm.get("course") or "") and code not in t["stem"]:
            continue
        due = _iso(fm.get("due"))
        if due and (due, t["stem"]) not in seen:
            seen.add((due, t["stem"]))
            out.append({"date": due, "title": t["stem"], "kind": str(fm.get("kind") or "teslim"), "status": str(fm.get("status") or ""),
                        "path": t["rel"]})
    main = _main_note(d)
    _, body = _read(main)
    body = re.sub(r"<!-- sb:auto:.*?-->", "", body)
    for line in body.splitlines():
        if not EXAM_LINE.search(line):
            continue
        m = DATE_RE.search(line)
        dt = m.group(0) if m else None
        if not dt:
            m2 = DATE_TR.search(line)
            dt = f"{m2.group(3)}-{int(m2.group(2)):02d}-{int(m2.group(1)):02d}" if m2 else None
        if dt and (dt, line.strip()[:60]) not in seen:
            seen.add((dt, line.strip()[:60]))
            out.append({"date": dt, "title": line.strip(" -*#>")[:80], "kind": "sinav", "status": "acik",
                        "path": main.relative_to(_vault()).as_posix()})
    return sorted(out, key=lambda e: e["date"])


def _files_info(d: Path) -> tuple[int, str | None]:
    n, last = 0, 0.0
    for dp, _dn, fns in os.walk(d):
        for fn in fns:
            n += 1
            try:
                last = max(last, os.path.getmtime(Path(dp) / fn))
            except OSError:
                pass
    return n, (datetime.fromtimestamp(last).date().isoformat() if last else None)


def course_info(d: Path, today: date | None = None, teslimler: list[dict] | None = None) -> dict:
    today = today or date.today()
    fm, _ = _read(_main_note(d))
    code = _code_of(d, fm)
    ev = _events_in(d, code, teslimler)
    upcoming = [e for e in ev if e["date"] >= today.isoformat() and e["status"] not in ("tamamlandi", "iptal")]
    fc, last = _files_info(d)
    out = {"code": code, "name": d.name.removeprefix(code).strip() or d.name, "path": f"{ROOT}/{d.name}/{d.name}.md",
           "next_due": upcoming[0] if upcoming else None, "exams": [e for e in ev if e["kind"] in ("sinav", "sunum")],
           "files_count": fc, "last_activity": last, "status": fm.get("status"), "instructor": fm.get("instructor")}
    g = grade_of(code)
    if g:
        out["grade"] = g
    return out


def courses(today: date | None = None) -> list[dict]:
    tes = _scan({"teslim"})
    return [course_info(d, today, tes) for d in course_dirs()]


def find_course(code: str) -> Path | None:
    code = (code or "").strip().upper()
    for d in course_dirs():
        fm, _ = _read(_main_note(d))
        if _code_of(d, fm).upper() == code:
            return d
    return None


def course_detail(code: str, today: date | None = None) -> dict | None:
    d = find_course(code)
    if d is None:
        return None
    info = course_info(d, today)
    fm, _ = _read(_main_note(d))
    info["events"] = _events_in(d, info["code"])
    info["schedule"] = fm.get("schedule") or []
    info["topics"] = topics_of(d)
    return info


# ---------------------------------------------------------------- konular + çalışma planı
def topics_of(d: Path) -> list[str]:
    """Ders notunun '### Konular' maddeleri (+ NotebookLM/özet notlarının başlıkları); yoksa ders notu başlıkları."""
    _, body = _read(_main_note(d))
    out: list[str] = []
    m = re.search(r"^###\s+Konular\s*\n(.*?)(?=^#{1,3} |\Z)", body, re.S | re.M)
    if m:
        for line in m.group(1).splitlines():
            line = line.strip()
            if line.startswith(("-", "*")):
                t = re.sub(r"[*_`]", "", line.lstrip("-* ")).strip()
                if t:
                    out.append(t[:120])
    for p in sorted(d.glob("*.md")):
        if p != _main_note(d) and ("notebooklm" in p.name.lower() or "özet" in p.name.lower()):
            _, b = _read(p)
            out += [h.strip("# ").strip()[:120] for h in re.findall(r"^#{2,3} .+$", b, re.M)]
    if not out:
        out = [h.strip("# ").strip()[:120] for h in re.findall(r"^#{2,3} .+$", body, re.M)
               if not re.search(r"ders dosyası|not geçmişi|bağlantı", h, re.I)]
    seen, uniq = set(), []
    for t in out:
        if t.lower() not in seen:
            seen.add(t.lower())
            uniq.append(t)
    return uniq


def make_plan(topics: list[str], exam_date: date, hours_per_day: float, today: date | None = None) -> list[dict]:
    today = today or date.today()
    days = (exam_date - today).days                              # bugün dahil, sınav günü hariç
    if days < 1:
        raise ValueError("sınav tarihi bugünden sonra olmalı")
    days = min(days, 120)
    topics = topics or ["Genel tekrar"]
    study_days = days - 1 if days > 1 else 1                      # son gün genel tekrar
    plan = []
    for i in range(days):
        day = today + timedelta(days=i)
        if i == days - 1 and days > 1:
            items = ["Genel tekrar ve örnek/soru çözümü"]
        else:
            lo, hi = i * len(topics) // study_days, (i + 1) * len(topics) // study_days
            items = topics[lo:hi] or [topics[min(lo, len(topics) - 1)]]
        plan.append({"date": day.isoformat(), "hours": float(hours_per_day), "topics": items})
    return plan


def write_study_plan(code: str, exam_date: date, hours_per_day: float, today: date | None = None) -> dict:
    d = find_course(code)
    if d is None:
        raise KeyError(code)
    topics = topics_of(d)
    plan = make_plan(topics, exam_date, hours_per_day, today)
    today = today or date.today()
    fm = {"type": "akademik", "status": "aktif", "tags": ["ders", "calisma-plani"], "source": "manual", "source_id": f"plan:{code}",
          "created": today.isoformat(), "updated": today.isoformat(), "due": exam_date.isoformat(), "course": f"[[{d.name}]]"}
    lines = [f"# Çalışma planı — {d.name}", "", f"Sınav: {exam_date.isoformat()} · günlük {hours_per_day:g} saat", ""]
    for p in plan:
        lines.append(f"- [ ] **{p['date']}** — " + "; ".join(p["topics"]))
    dest = d / "Çalışma planı.md"
    dest.write_text(dump_note(fm, "\n".join(lines) + "\n"), encoding="utf-8")
    return {"plan": plan, "path": dest.relative_to(_vault()).as_posix(), "topics": len(topics)}


# ---------------------------------------------------------------- program / duyuru
def schedule() -> dict:
    items = []
    for d in course_dirs():
        fm, _ = _read(_main_note(d))
        for s in fm.get("schedule") or []:
            items.append({"code": _code_of(d, fm), "course": d.name, "slot": str(s)})
    ann: list = []
    try:
        from . import obs
        ann = list(obs.load().get("duyurular") or [])
    except Exception:                                            # noqa: BLE001
        ann = []
    return {"schedule": items, "announcements": ann}


# ---------------------------------------------------------------- hoca iletişimi
def instructor_contact(code: str, limit: int = 5) -> dict | None:
    d = find_course(code)
    if d is None:
        return None
    fm, body = _read(_main_note(d))
    name = str(fm.get("instructor") or "").strip()
    if not name:
        m = HOCA_RE.search(body)
        name = m.group(1).strip() if m else ""
    out = {"code": fm.get("code") or code, "instructor": name or None, "person": None, "mails": []}
    if not name:
        return out
    core = re.sub(r"^((Prof|Doç|Dr|Öğr|Gör|Arş|Üyesi)\.?\s*)+", "", name, flags=re.I).strip()
    for pn in _scan({"kisi"}):
        if core and (core.lower() in pn["stem"].lower() or pn["stem"].lower() in name.lower()):
            out["person"] = {"path": pn["rel"], "name": pn["stem"], "email": pn["fm"].get("email")}
            break
    email = (out["person"] or {}).get("email")
    try:
        import sqlite3
        if config.MAIL_DB.exists():
            con = sqlite3.connect(f"file:{config.MAIL_DB.as_posix()}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            try:
                q, a = ("from_addr LIKE ?", [f"%{email}%"]) if email else ("from_name LIKE ?", [f"%{core}%"])
                rows = con.execute(f"SELECT subject, from_name, from_addr, date_ms FROM messages WHERE {q} ORDER BY date_ms DESC LIMIT ?",
                                   [*a, limit]).fetchall()
                out["mails"] = [{"subject": r["subject"], "from": r["from_name"] or r["from_addr"],
                                 "date": datetime.fromtimestamp((r["date_ms"] or 0) / 1000).date().isoformat()} for r in rows]
            finally:
                con.close()
    except Exception:                                            # noqa: BLE001 — mail veritabanı yoksa boş
        pass
    return out


# ---------------------------------------------------------------- başvurular, belgeler
def applications() -> list[dict]:
    done = {"kabul", "red", "vazgecildi"}
    rows = [{"title": a["stem"], "status": str(a["fm"].get("status") or ""), "kind": a["fm"].get("kind"), "organizer": a["fm"].get("organizer"),
             "due": _iso(a["fm"].get("due")), "path": a["rel"], "open": str(a["fm"].get("status") or "") not in done}
            for a in _scan({"basvuru"})]
    return sorted(rows, key=lambda r: (not r["open"], r["due"] or "9999"))


def school_docs() -> list[dict]:
    try:
        from . import analysis
        rows = analysis.classify_docs()
    except Exception:                                            # noqa: BLE001 — indeks yoksa boş
        return []
    out = []
    for r in rows:
        low = (r.get("ad") or "").lower()
        if "transkript" in low or "transcript" in low:
            kind = "transkript"
        elif r.get("cls") == "resmi yazı":
            kind = "resmi yazı"
        else:
            continue
        out.append({"doc_id": r["doc_id"], "ad": r["ad"], "kind": kind, "why": r.get("why"),
                    "date": datetime.fromtimestamp(r["date_ms"] / 1000).date().isoformat() if r.get("date_ms") else None})
    return sorted(out, key=lambda x: x["date"] or "", reverse=True)
