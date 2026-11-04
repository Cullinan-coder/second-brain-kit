"""Faz 4b Paket A: otomasyon motoru. Kurallar `config/otomasyon.yaml`; tetik -> koşul -> eylem.

Güvenlik: gorev_ekle/bildirim/not_ekle/ozet doğrudan; takvim_oner ve whatsapp_taslak ASLA doğrudan yürütülmez,
yalnız `pending_approvals.jsonl`'a "bekliyor" kaydı yazılır; kullanıcı `decide` ile onaylayınca yürür.
Zamanlanmış görev kaydı YOK: `tick(now)` mevcut runner'dan çağrılır. Mail salt okunur (yalnız maildb SELECT).
"""
from __future__ import annotations

import hmac
import json
import re
import uuid
from datetime import datetime
from pathlib import Path

import yaml

from . import config, filelock

DATA = config.DATA
RULES_FILE = config.SYSTEM / "config" / "otomasyon.yaml"
TRIGGERS = ("yeni_mail", "teslim_yaklasti", "zaman", "not_degisti", "webhook")
SAFE = ("gorev_ekle", "bildirim", "not_ekle", "ozet")
EXTERNAL = ("takvim_oner", "whatsapp_taslak")
ACTIONS = SAFE + EXTERNAL
DAYS = ["pazartesi", "salı", "çarşamba", "perşembe", "cuma", "cumartesi", "pazar"]
_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def _state_path() -> Path:
    return DATA / "automation_state.json"


def _pending_path() -> Path:
    return DATA / "pending_approvals.jsonl"


# ---- kurallar
def load_rules() -> list[dict]:
    if not RULES_FILE.exists():
        return []
    data = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")) or []
    if isinstance(data, dict):
        data = data.get("kurallar") or []
    return [r for r in data if isinstance(r, dict) and r.get("id")]


def _save_rules(rules: list[dict]) -> None:
    filelock.atomic_write(RULES_FILE, yaml.safe_dump(rules, allow_unicode=True, sort_keys=False))


def validate(rule: dict) -> dict:
    ad = " ".join(str(rule.get("ad") or "").split())[:80]
    tetik, eylem = rule.get("tetik") or {}, rule.get("eylem") or {}
    if not ad:
        raise ValueError("kural adı boş")
    if tetik.get("tur") not in TRIGGERS:
        raise ValueError("tetik.tur: " + "|".join(TRIGGERS))
    if eylem.get("tur") not in ACTIONS:
        raise ValueError("eylem.tur: " + "|".join(ACTIONS))
    if tetik["tur"] == "webhook" and not re.fullmatch(r"[a-z0-9_-]{1,40}", str(tetik.get("ad") or "")):
        raise ValueError("webhook tetiği için tetik.ad (a-z0-9_-) gerekli")
    if tetik["tur"] == "zaman" and not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", str(tetik.get("saat") or "")):
        raise ValueError("zaman tetiği için tetik.saat SS:DD gerekli")
    rid = re.sub(r"[^a-z0-9]+", "-", str(rule.get("id") or ad).translate(_TR).lower()).strip("-")[:40] or uuid.uuid4().hex[:8]
    kosul = rule.get("kosul") or {}
    return {"id": rid, "ad": ad, "tetik": dict(tetik), "kosul": {"alan": str(kosul.get("alan") or ""), "iceren": str(kosul.get("iceren") or "")},
            "eylem": dict(eylem), "acik": bool(rule.get("acik", True))}


def add_rule(rule: dict) -> dict:
    r = validate(rule)
    with filelock.locked(RULES_FILE):                       # oku-değiştir-yaz süreçler arası kilitli (D-20)
        rules = load_rules()
        if any(x["id"] == r["id"] for x in rules):
            r["id"] += "-" + uuid.uuid4().hex[:4]
        _save_rules(rules + [r])
    return r


def set_enabled(rid: str, on: bool) -> dict:
    with filelock.locked(RULES_FILE):
        rules = load_rules()
        for r in rules:
            if r["id"] == rid:
                r["acik"] = bool(on)
                _save_rules(rules)
                return r
    raise LookupError("kural bulunamadı")


# ---- durum
def _state() -> dict:
    try:
        return json.loads(_state_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(st: dict) -> None:
    filelock.atomic_write(_state_path(), json.dumps(st, ensure_ascii=False))


# ---- tetik toplama: her olay bir bağlam sözlüğü
def _mail_events(since_ms: int) -> list[dict]:
    from . import maildb
    if not config.MAIL_DB.exists():
        return []
    con = maildb.connect(config.MAIL_DB)
    try:
        rows = con.execute("SELECT subject, from_addr, from_name, snippet, date_ms FROM messages WHERE date_ms > ? ORDER BY date_ms LIMIT 200",
                           (since_ms,)).fetchall()
    finally:
        con.close()
    return [{"konu": r[0] or "", "gonderen": f"{r[2] or ''} <{r[1] or ''}>", "ozet": r[3] or "", "_ms": r[4]} for r in rows]


def _due_events(days: int, seen: list[str], now: datetime) -> list[dict]:
    from . import productivity as pr
    out = []
    for r in pr.load_tasks():
        d = r.get("due")
        if not d or r.get("col") == "done" or r["id"] in seen:
            continue
        if 0 <= (d - now.date()).days <= days:
            out.append({"konu": r["text"], "baslik": r["text"], "bitis": d.isoformat(), "_key": r["id"]})
    return out


def _note_events(sub: str, since: float) -> list[dict]:
    from . import vault_ops
    out = []
    for p in vault_ops.VAULT.rglob("*.md"):
        parts = p.relative_to(vault_ops.VAULT).parts
        if parts[0].startswith((".", "_")) or sub.lower() not in "/".join(parts).lower():
            continue
        if p.stat().st_mtime > since:
            out.append({"konu": p.stem, "baslik": p.stem, "yol": "/".join(parts), "_mt": p.stat().st_mtime})
    return out


def _zaman_due(t: dict, now: datetime, last: str | None) -> bool:
    if t.get("gun") and DAYS[now.weekday()] != str(t["gun"]).lower():
        return False
    h, m = map(int, str(t["saat"]).split(":"))
    slot = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return now >= slot and (not last or datetime.fromisoformat(last) < slot)


def _match(kosul: dict, ctx: dict) -> bool:
    need = str(kosul.get("iceren") or "").lower()
    if not need:
        return True
    alan = kosul.get("alan") or ""
    hay = str(ctx.get(alan, "")) if alan else " ".join(str(v) for k, v in ctx.items() if not k.startswith("_"))
    return need in hay.lower()


class _Safe(dict):
    def __missing__(self, k):
        return ""


def _fmt(s, ctx: dict) -> str:
    return str(s or "").format_map(_Safe({k: v for k, v in ctx.items() if not k.startswith("_")}))


# ---- eylemler
def _queue(rule: dict, kind: str, title: str, detail: str, payload: dict) -> dict:
    rec = {"id": uuid.uuid4().hex[:8], "kural": rule["id"], "tur": kind, "baslik": title, "ayrinti": detail, "payload": payload,
           "durum": "bekliyor", "zaman": datetime.now().isoformat(timespec="seconds")}
    filelock.append_line(_pending_path(), json.dumps(rec, ensure_ascii=False))     # D-20: süreçler arası kilitli ekleme
    from . import convstore
    convstore.notify(f"Onay bekliyor: {title}", detail[:200], "onay")
    return rec


def describe(rule: dict, ctx: dict) -> str:
    e = rule["eylem"]
    t = e["tur"]
    if t == "gorev_ekle":
        return f"Görev eklerdi: {_fmt(e.get('metin'), ctx)}"
    if t == "bildirim":
        return f"Bildirim gösterirdi: {_fmt(e.get('baslik') or rule['ad'], ctx)}"
    if t == "not_ekle":
        return f"Kutuya not eklerdi: {_fmt(e.get('metin'), ctx)}"
    if t == "ozet":
        return "Yerel modelle özet üretip kutuya not eklerdi"
    if t == "takvim_oner":
        return f"ONAY İSTERDİ (takvim): {_fmt(e.get('baslik'), ctx)} {e.get('gun', '')} {e.get('saat', '')}"
    return f"ONAY İSTERDİ (WhatsApp → {e.get('kisi', '')}): {_fmt(e.get('metin'), ctx)}"


def apply(rule: dict, ctx: dict) -> str:
    e, t = rule["eylem"], rule["eylem"]["tur"]
    if t == "gorev_ekle":
        from . import productivity as pr
        c = pr.add_task(_fmt(e.get("metin"), ctx), str(e.get("bitis") or ""), str(e.get("proje") or ""), e.get("oncelik"))
        return f"görev: {c['id']}"
    if t == "bildirim":
        from . import convstore
        convstore.notify(_fmt(e.get("baslik") or rule["ad"], ctx), _fmt(e.get("govde"), ctx), "otomasyon")
        return "bildirim"
    if t == "not_ekle":
        from . import inbox
        return inbox.add(_fmt(e.get("metin"), ctx), "otomasyon")
    if t == "ozet":
        from . import inbox, llm
        text, _ = llm.complete("automation", _fmt(e.get("istem") or rule["ad"], ctx), private=True)
        return inbox.add(f"{_fmt(e.get('baslik') or rule['ad'], ctx)}\n\n{text}", "otomasyon")
    if t == "takvim_oner":
        title = _fmt(e.get("baslik"), ctx)
        gun = str(e.get("gun") or ctx.get("bitis") or "")
        rec = _queue(rule, t, f"Takvim: {title}", f"{gun} {e.get('saat', '')}",
                     {"baslik": title, "gun": gun, "saat": str(e.get("saat") or ""), "dakika": int(e.get("dakika") or 60)})
        return f"onay bekliyor: {rec['id']}"
    if t == "whatsapp_taslak":
        rec = _queue(rule, t, f"WhatsApp → {e.get('kisi', '')}", _fmt(e.get("metin"), ctx),
                     {"kisi": str(e.get("kisi") or ""), "metin": _fmt(e.get("metin"), ctx)})
        return f"onay bekliyor: {rec['id']}"
    raise ValueError("bilinmeyen eylem")


def _events(rule: dict, now: datetime, st: dict, hook: tuple[str, dict] | None) -> tuple[list[dict], dict]:
    """(olaylar, bu kurala ait yeni durum)."""
    t, rs = rule["tetik"], dict(st.get(rule["id"]) or {})
    k = t["tur"]
    if k == "webhook":
        return ([dict(hook[1] or {}, ad=hook[0])] if hook and hook[0] == t.get("ad") else []), rs
    if hook:
        return [], rs
    if k == "yeni_mail":
        since = rs.get("ms")
        if since is None:                                   # ilk çalışma: eski postaya yağmur yağdırma
            return [], {"ms": int(now.timestamp() * 1000)}
        ev = _mail_events(int(since))
        return ev, {"ms": max([e["_ms"] for e in ev] + [int(since)])}
    if k == "teslim_yaklasti":
        ev = _due_events(int(t.get("gun") or 2), rs.get("seen", []), now)
        return ev, {"seen": (rs.get("seen", []) + [e["_key"] for e in ev])[-500:]}
    if k == "not_degisti":
        since = rs.get("mt")
        if since is None:
            return [], {"mt": now.timestamp()}
        ev = _note_events(str(t.get("yol") or ""), float(since))
        return ev, {"mt": max([e["_mt"] for e in ev] + [float(since)])}
    if k == "zaman":
        if _zaman_due(t, now, rs.get("last")):
            return [{"baslik": rule["ad"], "tarih": now.date().isoformat()}], {"last": now.isoformat(timespec="seconds")}
        return [], rs
    return [], rs


def tick(now: datetime | None = None, hook: tuple[str, dict] | None = None) -> list[dict]:
    """Açık kuralları değerlendirir; her uygulanan eylem için {kural, eylem, sonuc}. Runner periyodik çağırır."""
    now = now or datetime.now()
    st, out = _state(), []
    for rule in load_rules():
        if not rule.get("acik", True):
            continue
        try:
            events, new = _events(rule, now, st, hook)
            for ctx in events:
                if not _match(rule.get("kosul") or {}, ctx):
                    continue
                out.append({"kural": rule["id"], "eylem": rule["eylem"]["tur"], "sonuc": apply(rule, ctx)})
            st[rule["id"]] = new
        except Exception as e:                              # noqa: BLE001 — bir kural diğerlerini durdurmasın
            out.append({"kural": rule["id"], "eylem": rule["eylem"].get("tur"), "hata": f"{type(e).__name__}: {str(e)[:150]}"})
    if not hook:
        _save_state(st)
    return out


def test_run(rid: str, sample: dict | None = None) -> dict:
    """Kuru çalıştırma: hiçbir şey yürütmez, ne yapacağını söyler."""
    rule = next((r for r in load_rules() if r["id"] == rid), None)
    if not rule:
        raise LookupError("kural bulunamadı")
    ctx = dict({"konu": "(örnek konu)", "gonderen": "ornek@ornek.com", "ozet": "", "baslik": rule["ad"], "bitis": ""}, **(sample or {}))
    return {"id": rid, "eslesir": _match(rule.get("kosul") or {}, ctx), "yapardi": describe(rule, ctx),
            "onay_gerekir": rule["eylem"]["tur"] in EXTERNAL}


# ---- webhook
def fire_webhook(name: str, token: str, data: dict | None = None) -> list[dict]:
    if not re.fullmatch(r"[a-z0-9_-]{1,40}", str(name or "")):
        raise ValueError("geçersiz webhook adı")
    import keyring
    secret = keyring.get_password(config.KEYRING_SERVICE, f"hook-{name}")
    if not secret or not hmac.compare_digest(str(secret).encode(), str(token or "").encode()):
        raise PermissionError("token geçersiz")
    return tick(hook=(name, data if isinstance(data, dict) else {}))


# ---- onaylar
def _read_pending() -> list[dict]:
    p = _pending_path()
    rows = []
    for ln in (p.read_text(encoding="utf-8").splitlines() if p.exists() else []):
        try:
            rows.append(json.loads(ln))
        except ValueError:
            pass
    return rows


def _write_pending(rows: list[dict]) -> None:
    filelock.atomic_write(_pending_path(), "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def approvals(only_pending: bool = True) -> list[dict]:
    return [r for r in _read_pending() if not only_pending or r.get("durum") == "bekliyor"]


def decide(aid: str, ok: bool, calendar=None) -> dict:
    with filelock.locked(_pending_path()):                  # başka süreç araya kayıt eklerken satır kaybolmasın (D-20)
        rows = _read_pending()
        rec = next((r for r in rows if r.get("id") == aid), None)
        if not rec:
            raise LookupError("onay kaydı bulunamadı")
        if rec["durum"] != "bekliyor":
            raise PermissionError("zaten sonuçlandı")
        rec["durum"] = "onaylandi" if ok else "reddedildi"   # önce işaretle: çift yürütme olmasın
        _write_pending(rows)
    msg = _execute(rec, calendar) if ok else "reddedildi"   # yürütme (ağ çağrısı) kilit dışında
    with filelock.locked(_pending_path()):
        rows = _read_pending()
        cur = next((r for r in rows if r.get("id") == aid), None)
        if cur is not None:
            cur["sonuc"] = msg
            _write_pending(rows)
    rec["sonuc"] = msg
    return {"ok": True, "durum": rec["durum"], "sonuc": msg}


def _execute(rec: dict, calendar=None) -> str:
    pl = rec["payload"]
    if rec["tur"] == "takvim_oner":
        from datetime import date, time
        from .gcal_api import Calendar, NewEvent
        day = date.fromisoformat(pl["gun"])
        at = time.fromisoformat(pl["saat"]) if pl.get("saat") else None
        ev = NewEvent("HATIRLATMA", pl["baslik"], day, at, int(pl.get("dakika") or 60), description="Otomasyon önerisi (onaylandı)")
        status, _ = (calendar or Calendar("main")).add(ev, dry_run=False)
        return f"takvim: {status}"
    if rec["tur"] == "whatsapp_taslak":
        from . import actions, vault_ops
        found = actions.find_contacts(pl["kisi"], vault_ops.VAULT)
        if len(found) != 1:
            return f"WhatsApp gönderilmedi: '{pl['kisi']}' için {len(found)} eşleşme"
        who, phone = found[0]
        vault_ops.log("onay", "whatsapp gönder", "", f"{who}: {pl['metin'][:80]}", "")
        return str(actions.whatsapp_send(phone, pl["metin"]))
    raise ValueError("bilinmeyen onay türü")
