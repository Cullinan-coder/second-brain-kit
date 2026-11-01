"""Kariyer + kalan okul (Faz 3b Paket R): mini CRM, teklif taslağı, saat takibi, başvuru panosu, CV/mülakat/portfolyo/LinkedIn taslağı,
pazar takibi, sözleşme arşivi, finans özeti, ders notu/öğretici/kaynakça/yazım yardımcısı, grup projesi.

Hiçbir şey gönderilmez/paylaşılmaz: teklif, CV, gönderi yalnız kasada taslak nottur. Mail veritabanı salt okunur açılır.
Yollar işlev içinde okunur ki testler yönlendirebilsin.
"""
from __future__ import annotations

import json
import re
import sqlite3
import urllib.parse
from datetime import date, datetime
from pathlib import Path

import yaml

from . import academic, config, vault_ops
from .notes import dump_note, safe_filename

CAREER = "30-Kariyer"
THINK_RE = re.compile(r"<think>.*?</think>", re.S)
BOARD_COLS = ["hazirlaniyor", "basvuruldu", "mulakat", "teklif", "kabul", "red", "vazgecildi"]
DONE_STATUS = {"tamamlandi", "bitti", "arsiv", "iptal", "kapali"}


def _vault() -> Path:
    return Path(vault_ops.VAULT)


def _fold(s) -> str:
    t = str(s or "").lower().translate(str.maketrans("ıİğüşöç", "iigusoc"))
    return re.sub(r"\s+", " ", t).strip()


def _iso(v) -> str | None:
    return academic._iso(v)


def _today(today: date | None = None) -> date:
    return today or date.today()


def _commit(rel: str, msg: str) -> None:
    try:
        vault_ops.commit([rel], msg)
    except Exception:                                            # noqa: BLE001 — git yoksa yazma yine geçerli
        pass


def _write_note(rel: str, fm: dict, body: str, msg: str) -> str:
    p = _vault() / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_note(fm, body), encoding="utf-8")
    _commit(rel, msg)
    return rel


def _unique(rel_dir: str, name: str) -> str:
    base = safe_filename(name)[:90] or "not"
    rel = f"{rel_dir}/{base}.md"
    n = 2
    while (_vault() / rel).exists():
        rel = f"{rel_dir}/{base} ({n}).md"
        n += 1
    return rel


def _inside(path: str) -> Path:
    p = (_vault() / str(path or "")).resolve()
    if not str(p).startswith(str(_vault().resolve())) or not p.is_file() or p.suffix.lower() != ".md":
        raise ValueError("path kasada bir .md dosyası olmalı")
    return p


def _mail():
    """Salt okunur mail.db bağlantısı; yoksa None."""
    p = Path(config.MAIL_DB)
    if not p.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        return con
    except sqlite3.Error:
        return None


def _ask(task: str, prompt: str) -> tuple[str, str]:
    from . import llm
    out = llm.complete(task, prompt, private=True)
    text, via = out if isinstance(out, tuple) else (out, "")
    return THINK_RE.sub("", str(text)).strip(), str(via)


def _read(p: Path) -> tuple[dict, str]:
    return academic._read(p)


def _projects() -> list[dict]:
    out = []
    base = _vault() / "20-Projeler"
    if not base.is_dir():
        return out
    for p in sorted(base.rglob("*.md")):
        fm, body = _read(p)
        out.append({"rel": p.relative_to(_vault()).as_posix(), "stem": p.stem, "fm": fm, "body": body})
    return out


# ---------------------------------------------------------------- 204/215 CRM
def _invoices(con) -> list[dict]:
    if con is None:
        return []
    try:
        rows = con.execute("SELECT date_ms, title, meta FROM items WHERE source='invoice' ORDER BY date_ms").fetchall()
    except sqlite3.Error:
        return []
    out = []
    for r in rows:
        try:
            m = json.loads(r["meta"] or "{}")
        except ValueError:
            m = {}
        if m.get("amount") is None:
            continue
        out.append({"date_ms": r["date_ms"], "vendor": str(m.get("vendor") or ""), "amount": float(m["amount"]),
                    "currency": str(m.get("currency") or "TRY")})
    return out


def _last_contact(con, emails: list[str]) -> str | None:
    if con is None or not emails:
        return None
    best = 0
    for e in emails:
        try:
            r = con.execute("SELECT MAX(date_ms) FROM messages WHERE lower(from_addr) = ? OR lower(to_addrs) LIKE ?",
                            (e.lower(), f"%{e.lower()}%")).fetchone()
        except sqlite3.Error:
            return None
        best = max(best, r[0] or 0)
    return datetime.fromtimestamp(best / 1000).date().isoformat() if best else None


def _emails(fm: dict) -> list[str]:
    v = fm.get("email") or fm.get("emails") or []
    v = [v] if isinstance(v, str) else list(v or [])
    return [str(x).strip() for x in v if "@" in str(x)]


def crm() -> list[dict]:
    people = [a for a in academic._scan({"kisi"}) if a["fm"].get("musteri") is True or a["fm"].get("company")]
    con = _mail()
    inv = _invoices(con)
    projects = _projects()
    out = []
    try:
        for a in people:
            fm = a["fm"]
            names = {_fold(a["stem"]), _fold(fm.get("company"))} - {""}
            totals: dict[str, float] = {}
            for i in inv:
                v = _fold(i["vendor"])
                if v and any(n in v or v in n for n in names):
                    totals[i["currency"]] = round(totals.get(i["currency"], 0) + i["amount"], 2)
            open_jobs = []
            for p in projects:
                ref = _fold(p["fm"].get("client") or p["fm"].get("musteri") or "")
                if ref and any(n in ref or ref in n for n in names) and _fold(p["fm"].get("status")) not in DONE_STATUS:
                    open_jobs.append({"title": p["stem"], "status": p["fm"].get("status"), "path": p["rel"]})
            if fm.get("musteri") is not True and not open_jobs:      # şirket alanı tek başına müşteri yapmaz (LinkedIn bağlantıları)
                continue
            out.append({"name": a["stem"], "company": fm.get("company"), "path": a["rel"],
                        "last_contact": _last_contact(con, _emails(fm)), "open_jobs": open_jobs, "invoice_total": totals})
    finally:
        if con is not None:
            con.close()
    return sorted(out, key=lambda r: r["last_contact"] or "", reverse=True)


# ---------------------------------------------------------------- 205 teklif
def write_quote(client: str, items: list[dict], currency: str = "TRY", today: date | None = None) -> dict:
    client = (client or "").strip()
    if not client:
        raise ValueError("client gerekli")
    if not isinstance(items, list) or not items:
        raise ValueError("items gerekli")
    rows, total = [], 0.0
    for it in items:
        try:
            qty, price = float(it.get("qty", 1)), float(it.get("price", 0))
        except (TypeError, ValueError, AttributeError):
            raise ValueError("items: {desc, qty, price} sayısal olmalı")
        if qty <= 0 or price < 0:
            raise ValueError("qty > 0 ve price >= 0 olmalı")
        line = round(qty * price, 2)
        total += line
        rows.append((str(it.get("desc") or "").replace("|", "/"), qty, price, line))
    total = round(total, 2)
    cur = (currency or "TRY").upper()[:5]
    d = _today(today).isoformat()
    lines = [f"# Teklif — {client}", "", f"Tarih: {d}", "", "| Kalem | Adet | Birim fiyat | Tutar |", "|---|---|---|---|"]
    lines += [f"| {desc} | {q:g} | {p:.2f} {cur} | {ln:.2f} {cur} |" for desc, q, p, ln in rows]
    lines += ["", f"**Toplam: {total:.2f} {cur}**", "", "> Taslak — gönderilmedi."]
    rel = _unique(f"{CAREER}/Teklifler", f"{d} {client}")
    _write_note(rel, {"type": "teklif", "status": "taslak", "client": client, "total": total, "currency": cur, "date": d},
                "\n".join(lines) + "\n", f"teklif taslağı: {client}")
    return {"path": rel, "total": total, "currency": cur, "lines": len(rows)}


# ---------------------------------------------------------------- 206 saat takibi
def timelog_path() -> Path:
    return Path(config.DATA) / "timelog.jsonl"


def log_time(project: str, minutes, note: str = "", today: date | None = None) -> dict:
    project = (project or "").strip()
    try:
        minutes = int(float(minutes))
    except (TypeError, ValueError):
        raise ValueError("minutes sayı olmalı")
    if not project or not 0 < minutes <= 1440:
        raise ValueError("project gerekli, minutes 1-1440 arası olmalı")
    rec = {"date": _today(today).isoformat(), "project": project, "minutes": minutes, "note": str(note or "")[:300]}
    p = timelog_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def time_records() -> list[dict]:
    out = []
    try:
        for line in timelog_path().read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                if isinstance(r, dict) and r.get("project") and isinstance(r.get("minutes"), (int, float)):
                    out.append(r)
            except ValueError:
                continue
    except OSError:
        pass
    return out


def time_report(project: str = "", month: str = "") -> dict:
    if month and not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("month YYYY-AA olmalı")
    rows = [r for r in time_records() if (not project or _fold(r["project"]) == _fold(project))
            and (not month or str(r.get("date", "")).startswith(month))]
    by: dict[str, int] = {}
    for r in rows:
        by[r["project"]] = by.get(r["project"], 0) + int(r["minutes"])
    total = sum(by.values())
    lines = [f"Saat raporu{' — ' + project if project else ''}{' · ' + month if month else ''}", ""]
    for r in rows:
        lines.append(f"- {r.get('date')} · {r['project']} · {r['minutes'] / 60:.2f} sa" + (f" — {r['note']}" if r.get("note") else ""))
    lines += ["", f"Toplam: {total / 60:.2f} saat ({total} dk)"]
    return {"minutes": total, "hours": round(total / 60, 2), "by_project": by, "entries": len(rows), "text": "\n".join(lines)}


# ---------------------------------------------------------------- 207 başvuru panosu
def board() -> dict:
    cols: dict[str, list] = {c: [] for c in BOARD_COLS}
    for a in academic.applications():
        st = _fold(a["status"]) or "hazirlaniyor"
        cols.setdefault(st, []).append({k: a[k] for k in ("title", "kind", "organizer", "due", "path")})
    return {"columns": [{"status": k, "items": v} for k, v in cols.items()]}


# ---------------------------------------------------------------- 208-211 model taslakları
def _skill_text() -> str:
    p = _vault() / "40-Kaynaklar" / "Analiz" / "Yetenek profili.md"
    try:
        return p.read_text(encoding="utf-8")[:3000]
    except OSError:
        return ""


def _linkedin_text(limit: int = 3000) -> str:
    out, size = [], 0
    for p in sorted(_vault().glob("**/*.md")):
        if "linkedin" in p.name.lower() and not {".obsidian", "_system"} & set(p.parts):
            t = _read(p)[1][:1500]
            out.append(t)
            size += len(t)
            if size > limit:
                break
    return "\n".join(out)[:limit]


def _first_line(body: str) -> str:
    for line in body.splitlines():
        line = line.strip().lstrip("# ").strip()
        if line:
            return line[:160]
    return ""


def _project_digest(n: int = 12) -> str:
    return "\n".join(f"- {p['stem']}: {_first_line(p['body'])}" for p in _projects()[:n])


def _course_digest() -> str:
    return ", ".join(d.name for d in academic.course_dirs()[:25])


def make_cv(target: str, lang: str = "tr") -> dict:
    target = (target or "").strip()
    if not target:
        raise ValueError("target gerekli")
    lang = "en" if str(lang).lower().startswith("en") else "tr"
    prompt = (f"Aşağıdaki gerçek verilerle '{target}' hedefi için {'İngilizce' if lang == 'en' else 'Türkçe'} bir CV ve kısa ön yazı taslağı yaz. "
              "Veride olmayan hiçbir deneyim/başarı uydurma.\n\n"
              f"LinkedIn:\n{_linkedin_text()}\n\nProjeler:\n{_project_digest()}\n\nDersler: {_course_digest()}\n\nYetenek profili:\n{_skill_text()}")
    text, via = _ask("career_cv", prompt)
    rel = _unique(f"{CAREER}/CV", target)
    _write_note(rel, {"type": "cv", "status": "taslak", "target": target, "lang": lang, "date": _today().isoformat()},
                f"# CV — {target}\n\n{text}\n", f"CV taslağı: {target}")
    return {"path": rel, "text": text, "model": via}


def make_interview(role: str, company: str = "") -> dict:
    role = (role or "").strip()
    if not role:
        raise ValueError("role gerekli")
    prompt = (f"'{company}' şirketinde '{role}' mülakatına hazırlık: 10 olası soru listele, ardından aşağıdaki projelerden "
              f"STAR (Durum, Görev, Eylem, Sonuç) biçiminde 3 cevap taslağı yaz. Uydurma ayrıntı ekleme.\n\nProjeler:\n{_project_digest()}\n\n"
              f"Yetenekler:\n{_skill_text()}")
    text, via = _ask("career_interview", prompt)
    questions = [re.sub(r"^\s*(?:\d+[.)]|[-*])\s*", "", ln).strip() for ln in text.splitlines() if ln.strip().endswith("?")]
    return {"questions": questions[:20], "text": text, "model": via}


def portfolio() -> dict:
    parts = ["# Portfolyo", "", f"_Güncelleme: {_today().isoformat()}_", ""]
    n = 0
    for p in _projects():
        if _fold(p["fm"].get("visibility")) == "private":
            continue
        n += 1
        stat = p["fm"].get("status")
        parts += [f"## {p['stem']}", (_first_line(p["body"]) or "—") + (f" _(durum: {stat})_" if stat else ""), ""]
    if not n:
        parts.append("_Henüz proje notu yok._")
    rel = f"{CAREER}/Portfolyo.md"
    _write_note(rel, {"type": "portfolyo", "status": "taslak"}, "\n".join(parts) + "\n", "portfolyo")
    return {"path": rel, "projects": n}


def linkedin_post(topic: str) -> dict:
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("topic gerekli")
    text, via = _ask("career_post", f"'{topic}' konusunda samimi ve abartısız bir LinkedIn gönderisi taslağı yaz (en çok 150 kelime, Türkçe).\n\n"
                                    f"Bağlam:\n{_project_digest(6)}")
    d = _today().isoformat()
    rel = _unique(f"{CAREER}/LinkedIn", f"{d} {topic}")
    _write_note(rel, {"type": "gonderi", "status": "taslak", "topic": topic, "date": d}, f"# {topic}\n\n{text}\n\n> Taslak — paylaşılmadı.\n",
                f"LinkedIn taslağı: {topic[:40]}")
    return {"path": rel, "text": text, "model": via}


# ---------------------------------------------------------------- 212 pazar
def pazar_path() -> Path:
    return config.SYSTEM / "config" / "pazar.yaml"


def _pazar() -> dict:
    try:
        d = yaml.safe_load(pazar_path().read_text(encoding="utf-8")) or {}
        return d if isinstance(d, dict) else {}
    except (OSError, yaml.YAMLError):
        return {}


def _keywords() -> list[str]:
    return [str(k).strip() for k in (_pazar().get("anahtar_kelimeler") or []) if str(k).strip()]


def _saved_text() -> str:
    try:
        from . import search
        return (_vault() / search.SAVED_NOTE).read_text(encoding="utf-8")
    except Exception:                                            # noqa: BLE001
        return ""


def market() -> dict:
    kws = _keywords()
    saved = _saved_text()
    news, con = [], _mail()
    if con is not None:
        try:
            for r in con.execute("SELECT date_ms, title, url, body FROM items WHERE source='rss' ORDER BY date_ms DESC LIMIT 400"):
                hay = _fold(f"{r['title']} {r['body']}")
                hit = [k for k in kws if _fold(k) in hay]
                if hit:
                    news.append({"title": r["title"], "url": r["url"], "keywords": hit,
                                 "date": datetime.fromtimestamp(r["date_ms"] / 1000).date().isoformat() if r["date_ms"] else None})
        except sqlite3.Error:
            pass
        finally:
            con.close()
    return {"keywords": [{"keyword": k, "saved": k in saved} for k in kws], "rss": _pazar().get("rss") or [], "news": news[:50]}


def market_sync() -> dict:
    from . import search
    saved, added = _saved_text(), []
    for k in _keywords():
        if k not in saved:
            search.add_saved(k)
            added.append(k)
    return {"added": added}


# ---------------------------------------------------------------- 213 sözleşme
BITIS_RE = re.compile(r"(?:biti[sş]|sona erme|expir\w*|end date)[^0-9]{0,25}(\d{4}-\d{2}-\d{2}|\d{1,2}\.\d{1,2}\.\d{4})", re.I)


def _date_in(text: str) -> str | None:
    m = BITIS_RE.search(text or "")
    if not m:
        return None
    s = m.group(1)
    if "." in s:
        d, mo, y = s.split(".")
        s = f"{y}-{int(mo):02d}-{int(d):02d}"
    try:
        date.fromisoformat(s)
    except ValueError:
        return None
    return s


def contracts(today: date | None = None, warn_days: int = 30) -> list[dict]:
    t = _today(today)
    rows: list[dict] = []
    for a in academic._scan({"sozlesme"}):
        rows.append({"title": a["stem"], "source": "not", "path": a["rel"], "end": _iso(a["fm"].get("bitis"))})
    try:
        from . import analysis
        mcon = analysis._mconn(None)
        for r in analysis.classify_docs(mcon=mcon):
            if r.get("cls") != "sözleşme":
                continue
            end = None
            if mcon is not None and str(r["doc_id"]).startswith("file:"):
                try:
                    row = mcon.execute("SELECT text FROM file_text WHERE path = ?", (r["doc_id"][5:],)).fetchone()
                    end = _date_in(row[0]) if row else None
                except sqlite3.Error:
                    pass
            rows.append({"title": r["ad"], "source": "belge", "path": r["doc_id"], "end": end})
    except Exception:                                            # noqa: BLE001 — indeks yoksa yalnız notlar
        pass
    for r in rows:
        try:
            r["days_left"] = (date.fromisoformat(r["end"]) - t).days if r["end"] else None
        except ValueError:
            r["days_left"] = None
        r["warn"] = r["days_left"] is not None and r["days_left"] <= warn_days
    return sorted(rows, key=lambda r: (r["days_left"] is None, r["days_left"] or 0))


# ---------------------------------------------------------------- 214 finans
def _next_dates(t: date) -> list[dict]:
    out = []
    for k in range(14):
        yy, mm = t.year + (t.month - 1 + k) // 12, (t.month - 1 + k) % 12 + 1
        out.append((date(yy, mm, 26), "KDV"))
        if mm in (2, 5, 8, 11):
            out.append((date(yy, mm, 17), "geçici vergi"))
    return [{"date": d.isoformat(), "kind": kind, "days_left": (d - t).days} for d, kind in sorted(out) if d >= t][:6]


def finance(today: date | None = None) -> dict:
    t = _today(today)
    con = _mail()
    months: dict[str, dict[str, float]] = {}
    try:
        for i in _invoices(con):
            if not i["date_ms"]:
                continue
            ym = datetime.fromtimestamp(i["date_ms"] / 1000).strftime("%Y-%m")
            cur = months.setdefault(ym, {})
            cur[i["currency"]] = round(cur.get(i["currency"], 0) + i["amount"], 2)
    finally:
        if con is not None:
            con.close()
    return {"months": [{"month": k, "totals": v} for k, v in sorted(months.items())], "month_count": len(months),
            "reminders": _next_dates(t), "note": "Mailden çıkarılan faturalar (gelen)."}


# ---------------------------------------------------------------- 193 ders notu / 195 öğretici
def _course_text(code: str, source_path: str = "") -> tuple[Path, str]:
    d = academic.find_course(code)
    if d is None:
        raise KeyError(code)
    parts = []
    if source_path:
        parts.append(_read(_inside(source_path))[1][:6000])
    else:
        for p in sorted(d.glob("*.md"))[:6]:
            parts.append(f"## {p.stem}\n{_read(p)[1][:2000]}")
        nb = _vault() / "40-Kaynaklar" / "NotebookLM"
        if nb.is_dir():
            for p in sorted(nb.glob("*.md")):
                if _fold(code) in _fold(p.name):
                    parts.append(f"## {p.stem}\n{_read(p)[1][:2000]}")
    return d, "\n\n".join(parts)[:9000]


def course_notes(code: str, source_path: str = "") -> dict:
    d, src = _course_text(code, source_path)
    if not src.strip():
        raise ValueError("özetlenecek ders metni bulunamadı")
    text, via = _ask("study_notes", f"{code} dersi için kaynaklardan başlıklı, kısa maddeli bir çalışma özeti yaz. Kaynakta olmayanı ekleme.\n\n{src}")
    rel = _unique(d.relative_to(_vault()).as_posix(), f"{code} Özet notu {_today().isoformat()}")
    _write_note(rel, {"type": "ders-notu", "course": code, "status": "taslak", "date": _today().isoformat()}, f"# {code} özet\n\n{text}\n",
                f"ders notu: {code}")
    return {"path": rel, "text": text, "model": via}


TUTOR_SYSTEM = ("SİSTEM: Sen bir öğreticisin. Ödevin ya da sorunun doğrudan cevabını, çözümünü, kodunu ve nihai sayısal sonucunu ASLA verme. "
                "Yalnız ipuçları, ilgili kavramlar ve adım adım yönlendirici sorular ver; öğrenci kendisi çözsün.")


def tutor(code: str, question: str) -> dict:
    question = (question or "").strip()
    if not question:
        raise ValueError("question gerekli")
    _, src = _course_text(code)
    text, via = _ask("tutor", f"{TUTOR_SYSTEM}\n\nDers: {code}\nDers materyali:\n{src[:4000]}\n\nÖğrenci sorusu: {question}")
    return {"hint": text, "model": via}


# ---------------------------------------------------------------- 196 kaynakça
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+")


def _fmt_bib(m: dict, style: str) -> str:
    au = ", ".join(m.get("authors") or []) or "Anon."
    year, title, venue = m.get("year") or "t.y.", m.get("title") or "", m.get("venue") or ""
    if style == "ieee":
        return f"{au}, \"{title},\" {venue + ', ' if venue else ''}{year}."
    return f"{au} ({year}). {title}. {venue}".strip().rstrip(".") + "." + (f" https://doi.org/{m['doi']}" if m.get("doi") else "")


def _fetch_doi(doi: str) -> dict:
    import urllib.request
    req = urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi), headers={"User-Agent": "secondbrain/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:                # noqa: S310 — yalnız crossref
        w = json.loads(r.read().decode("utf-8"))["message"]
    au = [f"{a.get('family', '')}, {(a.get('given') or '')[:1]}." for a in w.get("author", [])][:8]
    year = ((w.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    return {"authors": au, "year": year, "title": (w.get("title") or [""])[0], "venue": (w.get("container-title") or [""])[0], "doi": doi}


def bib(text: str = "", doi: str = "", url: str = "", style: str = "apa") -> dict:
    src = (doi or url or text or "").strip()
    if not src:
        raise ValueError("text, doi ya da url gerekli")
    m = DOI_RE.search(src)
    if m:
        meta = _fetch_doi(m.group(0).rstrip(".,;)"))
        apa, ieee = _fmt_bib(meta, "apa"), _fmt_bib(meta, "ieee")
    elif src.lower().startswith(("http://", "https://")):
        host = urllib.parse.urlparse(src).netloc
        apa = f"{host}. ({_today().year}). {src}"
        ieee = f"{host}, \"{src},\" erişim: {_today().isoformat()}."
    else:
        apa = ieee = src
    entry = ieee if str(style).lower() == "ieee" else apa
    rel = "40-Kaynaklar/Kaynakça.md"
    p = _vault() / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    old = p.read_text(encoding="utf-8") if p.exists() else "---\ntype: kaynakca\nstatus: aktif\n---\n# Kaynakça\n"
    p.write_text(old.rstrip("\n") + f"\n- {entry}\n", encoding="utf-8")
    _commit(rel, "kaynakça")
    return {"apa": apa, "ieee": ieee, "added": entry, "path": rel}


# ---------------------------------------------------------------- 197 yazım
def writing(path: str, task: str) -> dict:
    if task not in ("outline", "review", "expand"):
        raise ValueError("task: outline | review | expand")
    body = _read(_inside(path))[1][:9000]
    what = {"outline": "Bu metin için bir ana hat (başlıklar ve kısa açıklamalar) öner.",
            "review": "Metni eleştirel incele: yapı, açıklık, eksik argüman, dil hataları; maddeler halinde öneri ver.",
            "expand": "Metindeki en zayıf 3 bölümü nasıl genişletebileceğini somut önerilerle yaz."}[task]
    text, via = _ask("writing", f"{what} Dosyayı yeniden yazma, yalnız öneri ver.\n\n{body}")
    return {"suggestion": text, "model": via}      # dosya değiştirilmez


# ---------------------------------------------------------------- 201 grup projesi
def group(project: str) -> dict:
    pr = next((p for p in _projects() if _fold(p["stem"]) == _fold(project)), None)
    if pr is None:
        raise KeyError(project)
    team = pr["fm"].get("ekip") or []
    team = [team] if isinstance(team, str) else [str(x) for x in team]
    people = {a["stem"]: a for a in academic._scan({"kisi"})}
    try:
        from . import tasks as _t
        tasks_text = _t.listing()
    except Exception:                                            # noqa: BLE001
        tasks_text = ""
    con = _mail()
    out = []
    try:
        for name in team:
            clean = re.sub(r"\[\[|\]\]", "", name).split("|")[0].strip()
            a = people.get(clean)
            out.append({"name": clean, "path": a["rel"] if a else None,
                        "last_contact": _last_contact(con, _emails(a["fm"])) if a else None,
                        "tasks": tasks_text.count(clean) if clean else 0})
    finally:
        if con is not None:
            con.close()
    return {"project": pr["stem"], "members": out}
