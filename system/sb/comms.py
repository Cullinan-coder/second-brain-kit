"""Faz 3b Paket C — iletişim: mail taslağı/özeti, cevap bekleyenler, takip, ilişki sağlığı, önemli tarihler, bülten önerisi,
mail→görev, toplantı hazırlık/sonrası.

MAİL SALT OKUNUR: gönderme/silme/cevap/etiket kodu YOK. Taslaklar yalnız kasada not (`00-Inbox/Taslaklar`); WhatsApp için yeni gönderim
yolu yok, mevcut onay kartı akışı (`chat._whatsapp`) kullanılır. Mail verisi `maildb` (salt okunur). Kasaya yazılan metin `redact`'tan geçer.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

from . import config, llm, maildb, tasks, vault_ops
from .notes import dump_note, safe_filename, split_note
from .redact import redact

MAIL_DB = config.MAIL_DB
OWNER = "Ayşe"
NOREPLY = re.compile(r"no[-_.]?reply|donotreply|do-not-reply|mailer-daemon|notifications?@", re.I)
DAY_MS = 86400000
NOT_CHAT = "account NOT IN ('sms','whatsapp')"


def _fold(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "").replace("İ", "i").replace("ı", "i").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _con():
    return maildb.connect(MAIL_DB)


def own_addrs() -> set[str]:
    a = config.accounts()
    out = {str(v.get("email", "")).lower() for sec in ("google", "imap") for v in (a.get(sec) or {}).values()}
    return {x for x in out if x}


def _now_ms() -> int:
    return int(datetime.now().timestamp() * 1000)


def _addrs(s) -> list[str]:
    return [m.lower() for m in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", str(s or ""))]


def _commit(p: Path, msg: str, detail: str = "") -> None:
    rel = vault_ops._rel(p)
    sha = vault_ops.commit([rel], msg)
    vault_ops.log("claude", msg.split(":")[0], rel, detail[:160], sha)


def _json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except ValueError:
        d = {}
    return d if isinstance(d, dict) else {}


def _write_note(folder: str, name: str, fm: dict, body: str) -> Path:
    base = safe_filename(name)[:100] or "not"
    p = vault_ops.VAULT / folder / f"{base}.md"
    n = 2
    while p.exists():
        p = vault_ops.VAULT / folder / f"{base} ({n}).md"
        n += 1
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_note(fm, redact(body)), encoding="utf-8")
    _commit(p, f"iletişim: {name}", body)
    return p


def _task_ok(msg: str) -> str:
    if not msg.startswith("Görev oluşturuldu"):
        raise ValueError(msg)
    return msg.split(": ", 1)[1].strip()


# ---------------------------------------------------------------- kişiler
def _list(v) -> list[str]:
    if v in (None, ""):
        return []
    return [str(x) for x in (v if isinstance(v, list) else [v]) if x]


def people() -> list[dict]:
    out = []
    for p in sorted((vault_ops.VAULT / "60-Kişiler").glob("*.md")):
        try:
            fm = split_note(p.read_text(encoding="utf-8"))[0]
        except OSError:
            continue
        digits = [re.sub(r"\D", "", x) for x in _list(fm.get("phone"))]
        out.append({"name": p.stem, "path": vault_ops._rel(p), "fm": fm, "emails": [e.lower() for e in _list(fm.get("email"))],
                    "phones": [d[-10:] for d in digits if len(d) >= 10]})
    return out


def find_person(q: str) -> dict | None:
    q = str(q or "").strip()
    if not q:
        return None
    ql, qf = q.lower(), _fold(q)
    ps = people()
    for p in ps:
        if ql in p["emails"] or _fold(p["name"]) == qf:
            return p
    hits = [p for p in ps if qf in _fold(p["name"])]
    return hits[0] if len(hits) == 1 else None


def infer_tone(addr: str, con=None) -> str:
    """Geçmişte bu adrese yazılan maillerden hitap çıkarımı."""
    addr = (addr or "").lower()
    if not addr:
        return ""
    con = con or _con()
    rows = con.execute("SELECT body FROM messages WHERE labels LIKE '%SENT%' AND lower(to_addrs) LIKE ? ORDER BY date_ms DESC LIMIT 8",
                       (f"%{addr}%",)).fetchall()
    text = _fold(" ".join((r[0] or "")[:300] for r in rows))
    if re.search(r"\bsayin\b|saygilarimla", text):
        return "resmi (Sayın ... / saygılarımla)"
    if re.search(r"\bhocam\b", text):
        return "saygılı ama samimi (hocam)"
    if re.search(r"\babi\b|\bkanka\b", text):
        return "samimi (abi/kanka)"
    return ""


def tone_for(to: str, con=None) -> str:
    p = find_person(to)
    if p and p["fm"].get("ton"):
        return str(p["fm"]["ton"])
    addr = (_addrs(to) or (p["emails"] if p else []) or [""])[0]
    try:
        return infer_tone(addr, con)
    except Exception:
        return ""


# ---------------------------------------------------------------- 180 taslak / 185 ton / 191 çeviri
def draft(to: str = "", subject: str = "", context: str = "", tone: str = "", lang: str = "tr") -> dict:
    context = str(context or "").strip()
    if not context:
        raise ValueError("bağlam boş")
    tone = " ".join(str(tone or "").split())[:80] or tone_for(to)
    prompt = (f"{OWNER} adına bir e-posta TASLAĞI yaz (gönderilmeyecek). Dil: {lang}. Ton: {tone or 'nazik, kısa, net'}.\n"
              f"Alıcı: {to or '-'}\nKonu: {subject or '(uygun bir konu öner)'}\nBağlam:\n{redact(context)[:4000]}\n"
              "Yalnız mail metnini yaz; uydurma bilgi ekleme.")
    text, _ = llm.complete("answer", prompt, private=True)
    text = (text or "").strip()
    if not text:
        raise ValueError("model boş yanıt verdi")
    title = subject or "Mail taslağı"
    p = _write_note("00-Inbox/Taslaklar", f"{date.today()} {title}",
                    {"type": "taslak", "status": "taslak", "tags": ["taslak"], "to": to or None, "subject": subject or None,
                     "ton": tone or None, "created": date.today()}, f"# {title}\n\n{text}\n")
    return {"path": vault_ops._rel(p), "text": text, "tone": tone}


def translate(text: str, to: str = "tr") -> dict:
    text = str(text or "").strip()
    if not text:
        raise ValueError("metin boş")
    out, _ = llm.complete("answer", f"Aşağıdaki metni {to} diline çevir. Yalnız çeviriyi yaz.\n\n{redact(text)[:6000]}", private=True)
    return {"text": (out or "").strip(), "to": to}


# ---------------------------------------------------------------- 181 zincir özeti
def thread_messages(thread_id: str, con=None) -> list[dict]:
    con = con or _con()
    cur = con.execute("SELECT account,id,date_ms,from_addr,from_name,subject,body,snippet FROM messages WHERE thread_id=? ORDER BY date_ms",
                      (thread_id,))
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def thread_summary(thread_id: str) -> dict:
    thread_id = str(thread_id or "").strip()
    if not thread_id:
        raise ValueError("thread_id boş")
    msgs = thread_messages(thread_id)
    if not msgs:
        raise LookupError("zincir bulunamadı")
    flat = "\n\n".join(f"[{datetime.fromtimestamp(m['date_ms'] / 1000):%Y-%m-%d}] {m['from_name'] or m['from_addr']}: "
                       f"{(m['body'] or m['snippet'] or '')[:1200]}" for m in msgs[-12:])
    prompt = ('Mail zincirini özetle. YALNIZ JSON döndür: {"summary": "...", "decisions": ["..."], "asks": ["Ayşe\'ten istenenler"]}\n\n'
              + redact(flat)[:12000])
    raw, _ = llm.complete("answer", prompt, private=True)
    d = _json(raw)
    return {"thread_id": thread_id, "count": len(msgs), "subject": msgs[0]["subject"], "summary": str(d.get("summary") or raw or "").strip(),
            "decisions": [str(x) for x in d.get("decisions") or []], "asks": [str(x) for x in d.get("asks") or []]}


# ---------------------------------------------------------------- 182 bekleyenler / 183 takip
def awaiting(days: int = 3, window: int = 60, con=None) -> list[dict]:
    con = con or _con()
    me = own_addrs()
    now = _now_ms()
    rows = con.execute(
        f"SELECT account,id,COALESCE(thread_id,id),date_ms,to_addrs,subject FROM messages WHERE labels LIKE '%SENT%' "
        f"AND {NOT_CHAT} AND date_ms BETWEEN ? AND ? ORDER BY date_ms DESC",
        (now - window * DAY_MS, now - int(days) * DAY_MS)).fetchall()
    seen, out = set(), []
    for acc, mid, tid, dms, to, subj in rows:
        if tid in seen:
            continue
        seen.add(tid)
        rcpt = [a for a in _addrs(to) if a not in me and not NOREPLY.search(a)]
        if not rcpt:
            continue
        later = con.execute("SELECT from_addr FROM messages WHERE COALESCE(thread_id,id)=? AND date_ms>?", (tid, dms)).fetchall()
        if any(_addrs(r[0]) and _addrs(r[0])[0] not in me for r in later):
            continue                                    # karşı taraf cevap vermiş
        out.append({"id": tid, "to": rcpt[0], "subject": subj or "", "sent": datetime.fromtimestamp(dms / 1000).strftime("%Y-%m-%d"),
                    "days": (now - dms) // DAY_MS})
    return out


def followup(tid: str, days=3) -> dict:
    try:
        days = max(0, min(int(days), 90))
    except (TypeError, ValueError):
        raise ValueError("days sayı olmalı")
    tid = str(tid or "").strip()
    msgs = thread_messages(tid) if tid else []
    if not msgs:
        raise LookupError("zincir bulunamadı")
    me = own_addrs()
    sent = [m for m in msgs if (_addrs(m["from_addr"]) or [""])[0] in me] or msgs
    r = _con().execute("SELECT to_addrs FROM messages WHERE account=? AND id=?", (sent[-1]["account"], sent[-1]["id"])).fetchone()
    cand = [a for a in _addrs(r[0] if r else "") if a not in me]
    to = cand[0] if cand else (sent[-1]["from_name"] or "")
    p = find_person(to)
    who = p["name"] if p else (to or "alıcı")
    due = (date.today() + timedelta(days=days)).isoformat()
    msg = tasks.add(f"{who}'e takip et - {msgs[0]['subject'] or 'mail'}"[:100], f"Mail zinciri: {tid}", OWNER, "", due, "", "inbox", "claude")
    return {"ok": True, "task": _task_ok(msg), "due": due}


# ---------------------------------------------------------------- 171 mail→görev
def mail_to_task(message_id: str) -> dict:
    mid = str(message_id or "").strip()
    row = _con().execute("SELECT account,id,COALESCE(thread_id,id),from_name,from_addr,subject,date_ms FROM messages WHERE id=? LIMIT 1", (mid,)).fetchone()
    if not row:
        raise LookupError("mail bulunamadı")
    acc, _, tid, fname, faddr, subj, dms = row
    link = f"https://mail.google.com/mail/u/0/#all/{tid}" if acc in ("main", "side") else f"(arşiv: {acc}/{mid})"
    msg = tasks.add(f"Mail: {subj or faddr}"[:100],
                    f"Gönderen: {fname or faddr} <{faddr}>\nTarih: {datetime.fromtimestamp(dms / 1000):%Y-%m-%d}\nBağlantı: {link}",
                    OWNER, "", None, "", "inbox", "claude")
    return {"ok": True, "task": _task_ok(msg), "link": link}


# ---------------------------------------------------------------- 186 tarihler
def _as_date(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v or "").strip().lstrip("-")
    m = re.match(r"(?:(\d{4})-)?(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, mo, d = m.groups()
    else:
        m = re.match(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?$", s)
        if not m:
            return None
        d, mo, y = m.groups()
    try:
        return date(int(y or 2000), int(mo), int(d))
    except ValueError:
        return None


def _next_occurrence(d: date, today: date) -> date:
    def at(y):
        try:
            return d.replace(year=y)
        except ValueError:
            return date(y, 3, 1)                        # 29 Şubat
    n = at(today.year)
    return n if n >= today else at(today.year + 1)


def upcoming_dates(days: int = 30, today: date | None = None) -> list[dict]:
    today = today or date.today()
    out = []
    for p in people():
        for key, label in (("dogum_gunu", "Doğum günü"), ("birthday", "Doğum günü"), ("onemli_tarih", "Önemli tarih")):
            d = _as_date(p["fm"].get(key))
            if not d:
                continue
            nxt = _next_occurrence(d, today)
            left = (nxt - today).days
            if left <= days:
                out.append({"name": p["name"], "kind": label, "date": nxt.isoformat(), "in_days": left})
    return sorted(out, key=lambda r: r["in_days"])


# ---------------------------------------------------------------- 187 ilişki sağlığı
def last_contacts(con=None) -> dict[str, tuple[int, str]]:
    """anahtar (e-posta, 10 haneli telefon, katlanmış ad) -> (son ms, kanal)."""
    con = con or _con()
    best: dict[str, tuple[int, str]] = {}

    def put(k, ms, ch):
        if k and ms and ms > best.get(k, (0, ""))[0]:
            best[k] = (ms, ch)
    for a, ms in con.execute(f"SELECT lower(from_addr),max(date_ms) FROM messages WHERE {NOT_CHAT} GROUP BY 1"):
        for e in _addrs(a):
            put(e, ms, "mail")
    for to, ms in con.execute(f"SELECT to_addrs,date_ms FROM messages WHERE labels LIKE '%SENT%' AND {NOT_CHAT}"):
        for e in _addrs(to):
            put(e, ms, "mail")
    for acc, tid, ms in con.execute("SELECT account,thread_id,max(date_ms) FROM messages WHERE account IN ('sms','whatsapp') GROUP BY 1,2"):
        put(re.sub(r"\D", "", tid or "")[-10:] if acc == "sms" else _fold(tid), ms, acc)
    for k, ms in con.execute("SELECT phone_key,max(date_ms) FROM calls GROUP BY 1"):
        put(re.sub(r"\D", "", k or "")[-10:], ms, "arama")
    return best


def relationships(days: int = 90, limit: int = 50, con=None) -> list[dict]:
    best = last_contacts(con)
    now = _now_ms()
    out = []
    for p in people():
        hits = [best[k] for k in p["emails"] + p["phones"] + [_fold(p["name"])] if k in best]
        if not hits:
            continue
        ms, ch = max(hits)
        d = (now - ms) // DAY_MS
        if days <= d <= 1095:
            out.append({"name": p["name"], "path": p["path"], "last": datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d"), "days": d, "channel": ch})
    return sorted(out, key=lambda r: r["days"])[:limit]


# ---------------------------------------------------------------- 189 bülten / 190 aramalar
def newsletters(days: int = 90, min_count: int = 5, con=None) -> list[dict]:
    con = con or _con()
    since = _now_ms() - days * DAY_MS
    rows = con.execute(
        f"SELECT lower(from_addr),max(from_name),count(*),sum(labels LIKE '%UNREAD%') FROM messages WHERE category='reklam' "
        f"AND {NOT_CHAT} AND date_ms>=? GROUP BY 1 HAVING count(*)>=? ORDER BY 3 DESC LIMIT 40", (since, min_count)).fetchall()
    return [{"sender": a, "name": n or "", "count": c, "unread": u or 0, "unread_ratio": round((u or 0) / c, 2),
             "suggest": "abonelikten çıkmayı düşün" if (u or 0) / c >= 0.8 else "filtrelemeyi düşün"} for a, n, c, u in rows]


def recent_calls(hours: int = 24, con=None) -> list[dict]:
    con = con or _con()
    since = _now_ms() - hours * 3600000
    kinds = {1: "gelen", 2: "giden", 3: "cevapsız", 5: "reddedilen"}
    rows = con.execute("SELECT id,number,date_ms,type,duration,contact_name FROM calls WHERE date_ms>=? ORDER BY date_ms DESC LIMIT 50", (since,))
    return [{"id": i, "number": n, "name": c or "", "time": datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M"),
             "type": kinds.get(t, str(t)), "duration": d or 0} for i, n, ms, t, d, c in rows]


# ---------------------------------------------------------------- 188 toplu taslak
def bulk_draft(names: list, template: str, channel: str = "mail", whatsapp=None) -> list[dict]:
    template = str(template or "").strip()
    if not template:
        raise ValueError("şablon boş")
    if not isinstance(names, list) or not names:
        raise ValueError("names liste olmalı")
    if channel not in ("mail", "whatsapp"):
        raise ValueError("channel mail|whatsapp")
    out = []
    for n in names[:30]:
        p = find_person(n)
        if not p:
            out.append({"name": str(n), "ok": False, "error": "kişi bulunamadı ya da belirsiz"})
            continue
        text = template.replace("{ad}", p["name"].split()[0])
        if channel == "whatsapp":
            res = whatsapp(p["name"], text) if whatsapp else "onay kartı yok"
            out.append({"name": p["name"], "ok": True, "channel": "whatsapp", "result": res, "text": text})
        else:
            note = _write_note("00-Inbox/Taslaklar", f"{date.today()} {p['name']}",
                               {"type": "taslak", "status": "taslak", "tags": ["taslak"], "to": (p["emails"] or [None])[0],
                                "created": date.today()}, f"# {p['name']}\n\n{text}\n")
            out.append({"name": p["name"], "ok": True, "channel": "mail", "path": vault_ops._rel(note), "text": text})
    return out


# ---------------------------------------------------------------- 172 / 173 toplantı
def meeting_prep(title: str = "", people_names=None, event=None) -> dict:
    title = " ".join(str(title or (event or {}).get("summary") or "").split())
    names = [str(x) for x in (people_names or []) if x]
    if not title and not names:
        raise ValueError("başlık ya da katılımcı gerekli")
    con = _con()
    ctx = []
    for n in names[:10]:
        p = find_person(n)
        if not p:
            ctx.append(f"## {n}\n(kişi notu yok)")
            continue
        body = split_note((vault_ops.VAULT / p["path"]).read_text(encoding="utf-8"))[1][:600]
        mails = []
        for e in p["emails"][:2]:
            q = con.execute("SELECT date_ms,subject FROM messages WHERE lower(from_addr) LIKE ? OR lower(to_addrs) LIKE ? "
                            "ORDER BY date_ms DESC LIMIT 5", (f"%{e}%", f"%{e}%"))
            mails += [f"- {datetime.fromtimestamp(d / 1000):%Y-%m-%d} {s}" for d, s in q]
        ctx.append(f"## {p['name']}\n{body}\nSon yazışmalar:\n" + ("\n".join(mails[:6]) or "-"))
    open_tasks = [t for t in tasks.listing().splitlines() if t.strip()][:15]
    prompt = (f"Toplantı hazırlık notu yaz: '{title}'. Gündem önerisi, her katılımcı için hatırlanacaklar, sorulacak sorular. Kısa, Türkçe.\n\n"
              + redact("\n\n".join(ctx))[:8000] + "\n\nAçık görevler:\n" + redact("\n".join(open_tasks)))
    text, _ = llm.complete("answer", prompt, private=True)
    p = _write_note("00-Inbox/Toplantı hazırlık", f"{date.today()} {title or 'Toplantı'}",
                    {"type": "toplanti-hazirlik", "status": "taslak", "tags": ["toplanti"], "created": date.today()},
                    f"# {title or 'Toplantı'}\n\n{(text or '').strip()}\n\n---\n" + "\n\n".join(ctx) + "\n")
    return {"path": vault_ops._rel(p), "text": (text or "").strip()}


def meeting_after(text: str, title: str = "") -> dict:
    text = str(text or "").strip()
    if not text:
        raise ValueError("metin boş")
    prompt = ('Toplantı notundan çıkar. YALNIZ JSON: {"summary":"...","decisions":["..."],"tasks":[{"title":"...","due":"YYYY-AA-GG veya boş"}]}\n\n'
              + redact(text)[:10000])
    raw, _ = llm.complete("answer", prompt, private=True)
    d = _json(raw)
    made = []
    for t in (d.get("tasks") or [])[:15]:
        t = t if isinstance(t, dict) else {"title": str(t)}
        ttl = " ".join(str(t.get("title") or "").split())[:100]
        due = str(t.get("due") or "")
        try:
            date.fromisoformat(due)
        except ValueError:
            due = ""
        if ttl:
            m = tasks.add(redact(ttl), f"Toplantı: {title}", OWNER, "", due or None, "", "inbox", "claude")
            made.append({"title": ttl, "ok": m.startswith("Görev oluşturuldu"), "msg": m})
    decisions = [str(x) for x in d.get("decisions") or []]
    p = _write_note("00-Inbox/Toplantı notları", f"{date.today()} {title or 'Toplantı'}",
                    {"type": "toplanti", "status": "taslak", "tags": ["toplanti"], "created": date.today()},
                    f"# {title or 'Toplantı'}\n\n{d.get('summary') or ''}\n\n## Kararlar\n" + "".join(f"- {x}\n" for x in decisions)
                    + "\n## Görevler\n" + "".join(f"- {m['title']}\n" for m in made))
    return {"path": vault_ops._rel(p), "summary": str(d.get("summary") or ""), "decisions": decisions, "tasks": made}
