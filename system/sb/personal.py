"""Faz 4a Paket P: kişisel işler (harcama, abonelik, garanti, sağlık, liste, yemek, bakım, hediye, ruh hali, seyahat).
Kart/hesap/TC/IBAN kaydedilmez (redact). Takvime yalnız onay kartıyla; mail salt okunur."""
from __future__ import annotations

import calendar
import json
import re
import sqlite3
import statistics
from datetime import date, datetime, time, timedelta
from pathlib import Path

import yaml

from . import academic, config
from .career import _ask, _commit, _fold, _mail, _read, _today, _unique, _vault, _write_note
from .derived import find_amount
from .notes import dump_note, split_note
from .redact import redact

SAGLIK = "40-Kaynaklar/Sağlık"
LISTE = "40-Kaynaklar/Liste.md"
TARIFLER = "40-Kaynaklar/Tarifler"
PLANLAR = "40-Kaynaklar/Yemek Planları"
SEYAHAT = "40-Kaynaklar/Seyahatler"
GUNLUK = "50-Günlük"

CATEGORIES = {
    "market": ["migros", "bim", "a101", "şok", "sok", "carrefour", "macro", "getir", "market"],
    "yeme-icme": ["yemeksepeti", "restoran", "cafe", "kafe", "starbucks", "burger", "pizza", "lokanta"],
    "ulasim": ["uber", "bitaksi", "taksi", "opet", "shell", "petrol", "akbil", "istanbulkart", "thy", "pegasus", "otobüs"],
    "abonelik": ["netflix", "spotify", "youtube", "icloud", "google one", "disney", "exxen", "amazon prime", "chatgpt", "openai", "turkcell", "vodafone"],
    "alisveris": ["trendyol", "hepsiburada", "n11", "amazon", "teknosa", "mediamarkt", "vatan", "zara", "lc waikiki"],
    "fatura": ["enerjisa", "igdaş", "iski", "turk telekom", "türk telekom", "elektrik", "doğalgaz", "su faturası"],
}
PRODUCT_RE = re.compile(r"teknosa|mediamarkt|vatan|incehesap|apple|samsung|arçelik|arcelik|bosch|beko|vestel|"
                        r"telefon|bilgisayar|laptop|televizyon|buzdolabı|çamaşır|ürün|garanti", re.I)
BANK_RE = re.compile(r"harcama|alışveriş|alisveris|işlem|islem|çekildi|provizyon|ödeme|odeme|kartınızla|kartinizla", re.I)
SKIP_SMS_RE = re.compile(r"iade|kod|şifre|sifre|otp|doğrulama", re.I)
VENDOR_RE = re.compile(r"([A-Za-zÇĞİÖŞÜçğıöşü0-9][\w .&*'-]{2,32}?)\s+(?:işyerinde|isyerinde|işyerinden|isyerinden)\b", re.I)


# ---------------------------------------------------------------- yardımcılar
def _cfg(name: str):
    p = Path(config.SYSTEM) / "config" / name
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}


def _day(ms) -> date | None:
    return datetime.fromtimestamp(ms / 1000).date() if ms else None


def _d(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _category(vendor: str, extra: dict | None = None) -> str:
    v = _fold(vendor)
    maps = {k: list(w) for k, w in CATEGORIES.items()}
    for k, words in (extra or {}).items():
        maps[str(k)] = list(words or []) + maps.get(str(k), [])
    for cat, words in maps.items():
        if any(_fold(w) in v for w in words):
            return cat
    return "diger"


def _items(con, source: str) -> list:
    if con is None:
        return []
    try:
        return con.execute("SELECT id, date_ms, kind, title, url, body, meta FROM items WHERE source=? ORDER BY date_ms", (source,)).fetchall()
    except sqlite3.Error:
        return []


def _meta(r) -> dict:
    try:
        return json.loads(r["meta"] or "{}")
    except ValueError:
        return {}


def _bank_sms(con) -> list[dict]:
    if con is None:
        return []
    try:
        rows = con.execute("SELECT date_ms, from_addr, from_name, body FROM messages WHERE account='sms' AND from_addr != 'me' "
                           "AND body IS NOT NULL ORDER BY date_ms").fetchall()
    except sqlite3.Error:
        return []
    out = []
    for r in rows:
        body = r["body"] or ""
        if not BANK_RE.search(body) or SKIP_SMS_RE.search(body):
            continue
        amt = find_amount(body)
        if not amt:
            continue
        m = VENDOR_RE.search(body)
        vendor = (m.group(1).strip() if m else (r["from_name"] or r["from_addr"] or "banka"))[:60]
        out.append({"date_ms": r["date_ms"], "vendor": redact(vendor), "amount": amt[0], "currency": amt[1],
                    "source": "sms", "title": "", "body": ""})
    return out


def expenses() -> list[dict]:
    """Fatura + banka SMS harcamaları (kart/hesap numarası taşımaz)."""
    con = _mail()
    try:
        out = []
        for r in _items(con, "invoice"):
            m = _meta(r)
            if m.get("amount") is not None:
                out.append({"date_ms": r["date_ms"], "vendor": str(m.get("vendor") or ""), "amount": float(m["amount"]),
                            "currency": str(m.get("currency") or "TRY"), "source": "invoice",
                            "title": r["title"] or "", "body": r["body"] or ""})
        return out + _bank_sms(con)
    finally:
        if con is not None:
            con.close()


# ---------------------------------------------------------------- 229 harcama
def spending(month: str = "", today: date | None = None) -> dict:
    t = _today(today)
    month = (month or t.strftime("%Y-%m")).strip()
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("month YYYY-AA biçiminde olmalı")
    cfg = _cfg("butce.yaml")
    limits = {str(k): float(v) for k, v in (cfg.get("limitler") or {}).items() if isinstance(v, (int, float))}
    cmap = cfg.get("kategoriler") if isinstance(cfg.get("kategoriler"), dict) else None
    cats: dict[str, dict[str, float]] = {}
    count = 0
    for e in expenses():
        d = _day(e["date_ms"])
        if not d or d.strftime("%Y-%m") != month:
            continue
        count += 1
        c = cats.setdefault(_category(e["vendor"], cmap), {})
        c[e["currency"]] = round(c.get(e["currency"], 0) + e["amount"], 2)
    rows = []
    for cat, tot in sorted(cats.items(), key=lambda kv: -sum(kv[1].values())):
        lim = limits.get(cat)
        spent = tot.get("TRY", 0)
        rows.append({"category": cat, "totals": tot, "limit": lim, "over": bool(lim and spent > lim),
                     "ratio": round(spent / lim, 2) if lim else None})
    total: dict[str, float] = {}
    for tot in cats.values():
        for k, v in tot.items():
            total[k] = round(total.get(k, 0) + v, 2)
    return {"month": month, "categories": rows, "total": total, "count": count,
            "note": "Fatura mailleri + banka SMS tutarları; kart/hesap numarası saklanmaz."}


# ---------------------------------------------------------------- 230 abonelik
def subscriptions(today: date | None = None) -> list[dict]:
    t = _today(today)
    groups: dict[tuple, list[date]] = {}
    names: dict[tuple, str] = {}
    for e in expenses():
        d, v = _day(e["date_ms"]), _fold(e["vendor"])
        if not d or not v:
            continue
        key = (v, round(e["amount"]), e["currency"])
        groups.setdefault(key, []).append(d)
        names[key] = e["vendor"]
    out = []
    for key, ds in groups.items():
        ds = sorted(set(ds))
        if len(ds) < 3:
            continue
        gaps = [(b - a).days for a, b in zip(ds, ds[1:])]
        med = statistics.median(gaps)
        if not 25 <= med <= 35 or sum(1 for g in gaps if 20 <= g <= 40) < len(gaps) * 0.7:
            continue
        nxt = ds[-1] + timedelta(days=round(med))
        out.append({"vendor": names[key], "amount": float(key[1]), "currency": key[2], "last": ds[-1].isoformat(),
                    "next": nxt.isoformat(), "days_left": (nxt - t).days, "count": len(ds)})
    return sorted(out, key=lambda r: r["next"])


# ---------------------------------------------------------------- 232 garanti
def warranties(today: date | None = None) -> list[dict]:
    t = _today(today)
    try:
        months = int(_cfg("butce.yaml").get("garanti_ay") or 24)
    except (TypeError, ValueError):
        months = 24
    out = []
    for e in expenses():
        if e["source"] != "invoice":
            continue
        d = _day(e["date_ms"])
        if not d or not PRODUCT_RE.search(f"{e['vendor']} {e['title']} {e['body']}"):
            continue
        end = _add_months(d, months)
        left = (end - t).days
        out.append({"vendor": e["vendor"], "title": e["title"], "amount": e["amount"], "currency": e["currency"],
                    "purchased": d.isoformat(), "ends": end.isoformat(), "days_left": left, "expired": left < 0,
                    "warn": 0 <= left <= 30})
    return sorted(out, key=lambda r: r["ends"])


# ---------------------------------------------------------------- 233 sağlık
def _med_times(m: dict) -> list[str]:
    ts = m.get("saatler") or m.get("saat") or []
    ts = [ts] if isinstance(ts, str) else list(ts or [])
    return [str(x).zfill(5) for x in ts if re.fullmatch(r"\d{1,2}:\d{2}", str(x))]


def health(today: date | None = None, now: datetime | None = None) -> dict:
    t = _today(today)
    now = now or datetime.now()
    raw = _cfg("ilaclar.yaml")
    meds = raw.get("ilaclar") if isinstance(raw, dict) else raw
    out_meds = []
    for m in meds or []:
        if not isinstance(m, dict) or not m.get("ad"):
            continue
        s, e = _d(m.get("baslangic")), _d(m.get("bitis"))
        if (s and t < s) or (e and t > e):
            continue
        times = _med_times(m)
        nxt = next((x for x in sorted(times) if datetime.combine(t, time.fromisoformat(x)) >= now), None)
        out_meds.append({"name": str(m["ad"]), "dose": str(m.get("doz") or ""), "times": times, "next": nxt,
                         "ends": e.isoformat() if e else None})
    appts = []
    d = _vault() / SAGLIK
    if d.is_dir():
        for p in sorted(d.glob("*.md")):
            fm, _ = _read(p)
            when = _d(fm.get("randevu") or fm.get("tarih"))
            if when and when >= t:
                appts.append({"title": p.stem, "date": when.isoformat(), "time": str(fm.get("saat") or ""),
                              "days_left": (when - t).days, "path": f"{SAGLIK}/{p.name}", "visibility": "private"})
    return {"meds": out_meds, "appointments": sorted(appts, key=lambda a: a["date"])}


def health_event(kind: str, name: str, today: date | None = None, now: datetime | None = None) -> dict:
    """Takvime eklenecek tek etkinlik taslağı (yalnız onay kartı sonrası eklenir)."""
    t = _today(today)
    h = health(t, now)
    if kind == "med":
        m = next((x for x in h["meds"] if _fold(x["name"]) == _fold(name)), None)
        if m is None or not m["times"]:
            raise KeyError(name)
        day = t if m["next"] else t + timedelta(days=1)
        at = time.fromisoformat(m["next"] or sorted(m["times"])[0])
        return {"title": f"İlaç: {m['name']}" + (f" ({m['dose']})" if m["dose"] else ""), "day": day, "at": at,
                "minutes": 15, "reminders": (0, 10)}
    if kind == "appt":
        a = next((x for x in h["appointments"] if _fold(x["title"]) == _fold(name)), None)
        if a is None:
            raise KeyError(name)
        try:
            at = time.fromisoformat(a["time"].zfill(5)) if a["time"] else time(9, 0)
        except ValueError:
            at = time(9, 0)
        return {"title": f"Randevu: {a['title']}", "day": date.fromisoformat(a["date"]), "at": at, "minutes": 60,
                "reminders": (60, 1440)}
    raise ValueError("kind med ya da appt olmalı")


# ---------------------------------------------------------------- 234 okuma/izleme listesi
LIST_HEADS = {"okunacak": "## Okunacak", "izlenecek": "## İzlenecek"}


def _parse_list(text: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"okunacak": [], "izlenecek": []}
    cur = None
    for line in text.splitlines():
        if line.startswith("## "):
            f = _fold(line[3:])
            cur = "okunacak" if f.startswith("okunacak") else "izlenecek" if "zlenecek" in f else None
            continue
        m = re.match(r"\s*- \[( |x|X)\] (.+)", line)
        if cur and m:
            out[cur].append({"title": m.group(2).strip(), "done": m.group(1) != " "})
    return out


def reading_list(suggest: bool = True) -> dict:
    p = _vault() / LISTE
    lists = _parse_list(p.read_text(encoding="utf-8")) if p.exists() else {"okunacak": [], "izlenecek": []}
    sug = []
    if suggest:
        con = _mail()
        try:
            have = {_fold(i["title"]) for v in lists.values() for i in v}
            for r in reversed(_items(con, "youtube")):
                blob = _fold(json.dumps(_meta(r), ensure_ascii=False))
                if r["title"] and re.search(r"sonra|later", blob) and _fold(r["title"]) not in have:
                    sug.append({"title": r["title"], "source": "youtube", "url": r["url"]})
            plays = [r for r in reversed(_items(con, "spotify")) if r["title"]][:5]
            sug += [{"title": r["title"], "source": "spotify", "url": r["url"]} for r in plays if _fold(r["title"]) not in have]
        finally:
            if con is not None:
                con.close()
    return {**lists, "suggestions": sug[:10]}


def add_reading(title: str, kind: str = "okunacak") -> dict:
    title = " ".join(redact(title or "").split())[:200]
    kind = _fold(kind)
    if kind not in LIST_HEADS:
        raise ValueError("kind okunacak ya da izlenecek olmalı")
    if not title:
        raise ValueError("title gerekli")
    p = _vault() / LISTE
    lines = (p.read_text(encoding="utf-8") if p.exists() else "---\ntype: kaynak\n---\n# Liste\n").splitlines()
    head = LIST_HEADS[kind]
    idx = next((i for i, l in enumerate(lines) if l.startswith("## ") and (kind == "okunacak" and _fold(l[3:]).startswith("okunacak") or kind == "izlenecek" and "zlenecek" in _fold(l[3:]))), None)
    if idx is None:
        lines += ["", head, f"- [ ] {title}"]
    else:
        j = idx + 1
        while j < len(lines) and not lines[j].startswith("## "):
            j += 1
        while j > idx + 1 and not lines[j - 1].strip():
            j -= 1
        lines.insert(j, f"- [ ] {title}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _commit(LISTE, f"liste: {title[:40]}")
    return {"ok": True, "path": LISTE, "kind": kind, "title": title}


# ---------------------------------------------------------------- 235 yemek planı
def meal_plan(days: int = 7, today: date | None = None) -> dict:
    try:
        days = int(days)
    except (TypeError, ValueError):
        raise ValueError("days sayı olmalı")
    if not 1 <= days <= 14:
        raise ValueError("days 1-14 arası olmalı")
    t = _today(today)
    d = _vault() / TARIFLER
    recipes = []
    if d.is_dir():
        for p in sorted(d.glob("*.md"))[:40]:
            fm, body = _read(p)
            if str(fm.get("visibility") or "") != "private":
                recipes.append(f"### {p.stem}\n{body[:500]}")
    prompt = (f"{days} günlük yemek planı yap (kahvaltı/öğle/akşam), mümkünse aşağıdaki tariflerden seç. Sonunda "
              f"'## Alışveriş listesi' başlığıyla madde madde liste ver. Türkçe, kısa.\n\n"
              + ("\n\n".join(recipes) or "(kayıtlı tarif yok; genel öneri ver)"))
    text, via = _ask("meal_plan", prompt)
    if not text:
        raise ValueError("model boş yanıt verdi")
    text = redact(text)
    rel = _unique(PLANLAR, f"Yemek planı {t.isoformat()}")
    _write_note(rel, {"type": "kaynak", "tags": ["yemek-plani"], "date": t.isoformat(), "generated_by": via},
                f"# Yemek planı {t.isoformat()}\n\n{text}\n", f"yemek planı {t.isoformat()}")
    return {"ok": True, "path": rel, "days": days, "text": text, "model": via}


# ---------------------------------------------------------------- 236 bakım
def maintenance(today: date | None = None) -> list[dict]:
    t = _today(today)
    raw = _cfg("bakim.yaml")
    items = raw.get("bakimlar") if isinstance(raw, dict) else raw
    out = []
    for m in items or []:
        if not isinstance(m, dict) or not m.get("ad"):
            continue
        last = _d(m.get("son_tarih"))
        row = {"name": str(m["ad"]), "last": last.isoformat() if last else None, "due": None, "days_left": None,
               "km_left": None, "soon": False}
        try:
            months = int(m.get("periyot_ay") or 0)
        except (TypeError, ValueError):
            months = 0
        if last and months > 0:
            due = _add_months(last, months)
            row["due"], row["days_left"] = due.isoformat(), (due - t).days
        try:
            per, son, cur = (float(m[k]) for k in ("periyot_km", "son_km", "km"))
            row["km_left"] = round(son + per - cur)
        except (KeyError, TypeError, ValueError):
            pass
        row["soon"] = (row["days_left"] is not None and row["days_left"] <= 30) or \
                      (row["km_left"] is not None and row["km_left"] <= 500)
        out.append(row)
    return sorted(out, key=lambda r: (r["days_left"] is None, r["days_left"] or 0))


# ---------------------------------------------------------------- 237 hediye
def _person(name: str) -> dict | None:
    f = _fold(name)
    return next((a for a in academic._scan({"kisi"}) if f and _fold(a["stem"]) == f), None)


def _ideas(body: str) -> list[str]:
    m = re.search(r"^## Hediye fikirleri[ \t]*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return [l.strip()[2:].strip() for l in (m.group(1).splitlines() if m else []) if l.strip().startswith("- ")]


def _append_section(text: str, head: str, line: str) -> str:
    """`## head` bölümünün sonuna satır ekler; yoksa bölümü sona açar."""
    m = re.search(rf"^## {re.escape(head)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return text.rstrip("\n") + f"\n\n## {head}\n{line}\n"
    body = m.group(1).rstrip("\n")
    tail = "\n\n" if m.end() < len(text) else "\n"
    return text[:m.start(1)] + (body + "\n" if body else "") + line + tail + text[m.end():]


def add_gift(person: str, idea: str) -> dict:
    idea = " ".join(redact(idea or "").split())[:200]
    if not idea:
        raise ValueError("idea gerekli")
    a = _person(person)
    if a is None:
        raise KeyError(person)
    p = _vault() / a["rel"]
    text = _append_section(p.read_text(encoding="utf-8"), "Hediye fikirleri", f"- {idea}")
    p.write_text(text, encoding="utf-8")
    _commit(a["rel"], f"hediye fikri: {a['stem']}")
    return {"ok": True, "person": a["stem"], "ideas": _ideas(split_note(text)[1])}


def gifts(person: str = "", today: date | None = None) -> list[dict]:
    t = _today(today)
    out = []
    for a in academic._scan({"kisi"}):
        if person and _fold(a["stem"]) != _fold(person):
            continue
        ideas = _ideas(split_note((_vault() / a["rel"]).read_text(encoding="utf-8"))[1])
        if not ideas:
            continue
        b = _d(a["fm"].get("dogum") or a["fm"].get("birthday") or a["fm"].get("dogum_gunu"))
        left = None
        if b:
            nb = date(t.year, b.month, min(b.day, calendar.monthrange(t.year, b.month)[1]))
            if nb < t:
                nb = date(t.year + 1, b.month, min(b.day, calendar.monthrange(t.year + 1, b.month)[1]))
            left = (nb - t).days
        out.append({"person": a["stem"], "ideas": ideas, "birthday": b.strftime("%m-%d") if b else None, "days_left": left})
    return sorted(out, key=lambda r: (r["days_left"] is None, r["days_left"] or 0))


# ---------------------------------------------------------------- 238 ruh hali
MOOD_RE = re.compile(r"^- ([1-5])(?: ·.*)?$", re.M)


def _daily(d: date) -> Path:
    return _vault() / GUNLUK / f"{d.isoformat()}.md"


def add_mood(level, note: str = "", today: date | None = None) -> dict:
    try:
        lv = int(level)
    except (TypeError, ValueError):
        raise ValueError("level 1-5 arası olmalı")
    if not 1 <= lv <= 5:
        raise ValueError("level 1-5 arası olmalı")
    t = _today(today)
    note = " ".join(redact(note or "").split())[:200]
    line = f"- {lv} · {note}" if note else f"- {lv}"
    p = _daily(t)
    if p.exists():
        text = _append_section(p.read_text(encoding="utf-8"), "Ruh hali", line)
    else:
        text = dump_note({"type": "gunluk", "date": t.isoformat()}, f"# {t.isoformat()}\n\n## Ruh hali\n{line}\n")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    _commit(f"{GUNLUK}/{p.name}", f"ruh hali {t.isoformat()}")
    return {"ok": True, "date": t.isoformat(), "level": lv}


def mood(days: int = 30, today: date | None = None) -> dict:
    try:
        days = max(1, min(int(days), 365))
    except (TypeError, ValueError):
        raise ValueError("days sayı olmalı")
    t = _today(today)
    series = []
    for i in range(days - 1, -1, -1):
        d = t - timedelta(days=i)
        p = _daily(d)
        if not p.exists():
            continue
        m = re.search(r"^## Ruh hali[ \t]*\n(.*?)(?=^## |\Z)", p.read_text(encoding="utf-8"), re.S | re.M)
        vals = [int(x.group(1)) for x in MOOD_RE.finditer(m.group(1))] if m else []
        if vals:
            series.append({"date": d.isoformat(), "level": round(sum(vals) / len(vals), 1)})
    avg = round(sum(s["level"] for s in series) / len(series), 2) if series else None
    return {"days": days, "series": series, "average": avg, "count": len(series)}


# ---------------------------------------------------------------- 231 seyahat
def trip(destination: str, start: str, end: str) -> dict:
    destination = " ".join((destination or "").split())[:80]
    s, e = _d(start), _d(end)
    if not destination or not s or not e or e < s or (e - s).days > 60:
        raise ValueError("destination, start, end (YYYY-AA-GG, en çok 60 gün) gerekli")
    found: list[str] = []
    con = _mail()
    try:
        if con is not None:
            since = int((datetime.combine(s, time()) - timedelta(days=180)).timestamp() * 1000)
            try:
                rows = con.execute(
                    "SELECT subject, date_ms FROM messages WHERE account != 'sms' AND date_ms >= ? AND "
                    "(lower(subject) LIKE '%bilet%' OR lower(subject) LIKE '%rezervasyon%' OR lower(subject) LIKE '%uçuş%' "
                    "OR lower(subject) LIKE '%booking%' OR lower(subject) LIKE '%flight%' OR lower(subject) LIKE '%otel%') "
                    "ORDER BY date_ms DESC LIMIT 12", (since,)).fetchall()
                found = [f"{_day(r['date_ms'])}: {redact(r['subject'] or '')[:100]}" for r in rows]
            except sqlite3.Error:
                found = []
    finally:
        if con is not None:
            con.close()
    n = (e - s).days + 1
    prompt = (f"{destination} için {s.isoformat()} – {e.isoformat()} ({n} gün) gün gün gezi planı yaz; Türkçe, kısa, madde madde. "
              f"Mevcut rezervasyon mailleri:\n" + ("\n".join(found) or "(yok)"))
    text, via = _ask("trip_plan", prompt)
    if not text:
        raise ValueError("model boş yanıt verdi")
    text = redact(text)
    rel = _unique(SEYAHAT, f"{destination} {s.isoformat()}")
    fm = {"type": "kaynak", "tags": ["seyahat"], "destination": destination, "start": s.isoformat(), "end": e.isoformat(),
          "generated_by": via}
    body = (f"# {destination} ({s} – {e})\n\n## Rezervasyonlar (mailden)\n"
            + ("\n".join(f"- {x}" for x in found) or "- bulunamadı") + f"\n\n## Gün planı\n{text}\n")
    _write_note(rel, fm, body, f"seyahat: {destination}")
    return {"ok": True, "path": rel, "bookings": found, "text": text, "model": via}
