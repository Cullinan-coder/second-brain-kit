"""Sohbet geçmişi, bildirimler ve ekler için dosya deposu (Faz 2, Paket A).

`DATA/convs/<sid>.json` = {sid, title, created, updated, pinned, archived, messages:[...]}; `DATA/notifications.jsonl` (son 500);
`DATA/feedback.jsonl` (👍/👎); `DATA/uploads/<att_id>/<ad>`. DATA yolları her çağrıda `config.DATA`'dan okunur (testler yönlendirir).
Hiçbir şey kalıcı silinmez: sohbet "arşivlendi" işaretlenir.
"""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from . import config

SID_RE = re.compile(r"^[\w-]{1,40}$")
ATT_RE = re.compile(r"^[0-9a-f]{12}$")
NOTIF_MAX = 500
_lock = threading.RLock()
_TR = str.maketrans("İIıĞğÜüŞşÖöÇç", "iiigguussoocc")


def fold(s: str) -> str:
    """Büyük/küçük ve Türkçe aksan duyarsız karşılaştırma anahtarı."""
    return (s or "").translate(_TR).lower()


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def valid_sid(sid: str) -> bool:
    return bool(SID_RE.match(str(sid or "")))


def new_sid() -> str:
    return "c" + uuid.uuid4().hex[:12]


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def _dir(name: str) -> Path:
    d = config.DATA / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_json(p: Path, obj) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, p)


# ---------------------------------------------------------------- sohbetler
def _conv_path(sid: str) -> Path:
    if not valid_sid(sid):
        raise ValueError("geçersiz sohbet kimliği")
    return _dir("convs") / f"{sid}.json"


def load(sid: str) -> dict | None:
    p = _conv_path(sid)
    if not p.is_file():
        return None
    try:
        c = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return c if isinstance(c, dict) else None


def save(conv: dict) -> dict:
    conv["updated"] = now()
    with _lock:
        _write_json(_conv_path(conv["sid"]), conv)
    _cache.pop(conv["sid"], None)
    return conv


def ensure(sid: str) -> dict:
    """Kayıt varsa yükler, yoksa boş kayıt döndürür (ilk mesajda diske yazılır)."""
    c = load(sid)
    if c is None:
        t = now()
        c = {"sid": sid, "title": "", "created": t, "updated": t, "pinned": False, "archived": False, "messages": []}
    return c


def add_message(conv: dict, role: str, text: str, **extra) -> dict:
    m = {"id": new_id(), "role": role, "text": text, "ts": now()}
    m.update({k: v for k, v in extra.items() if v not in (None, "", [])})
    conv["messages"].append(m)
    if not conv.get("title") and role == "user":
        conv["title"] = " ".join(text.split())[:60]
    return m


def find_msg(conv: dict, mid: str) -> tuple[int, dict] | None:
    for i, m in enumerate(conv.get("messages", [])):
        if m.get("id") == mid:
            return i, m
    return None


def model_history(conv: dict, upto: int | None = None, n: int = 12) -> list[dict]:
    """Modele verilecek geçmiş: user/assistant, son n mesaj (upto dizinine kadar, o hariç)."""
    msgs = conv.get("messages", [])[: upto if upto is not None else None]
    return [{"role": m["role"], "content": m.get("text", "")} for m in msgs if m.get("role") in ("user", "assistant")][-n:]


_cache: dict[str, tuple[float, dict]] = {}   # sid -> (mtime, özet satırı)


def _summary(p: Path) -> dict | None:
    sid = p.stem
    try:
        mt = p.stat().st_mtime
    except OSError:
        return None
    hit = _cache.get(sid)
    if hit and hit[0] == mt:
        return hit[1]
    try:
        c = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    msgs = c.get("messages") or []
    last = next((m for m in reversed(msgs) if m.get("role") in ("user", "assistant")), None)
    row = {"sid": c.get("sid", sid), "title": c.get("title") or "(başlıksız)", "updated": c.get("updated", ""),
           "pinned": bool(c.get("pinned")), "archived": bool(c.get("archived")), "count": len(msgs),
           "preview": " ".join((last or {}).get("text", "").split())[:120],
           "_hay": fold((c.get("title") or "") + " " + " ".join(m.get("text", "") for m in msgs))}
    _cache[sid] = (mt, row)
    return row


def list_convs(q: str = "", pinned: bool | None = None, archived: bool = False, limit: int = 50) -> list[dict]:
    d = config.DATA / "convs"
    rows = []
    for p in d.glob("*.json") if d.is_dir() else []:
        r = _summary(p)
        if not r or r["archived"] != archived or (pinned is not None and r["pinned"] != pinned):
            continue
        rows.append(r)
    fq = fold(q.strip())
    if fq:
        rows = [r for r in rows if all(w in r["_hay"] for w in fq.split())]
    rows.sort(key=lambda r: r["updated"], reverse=True)
    rows.sort(key=lambda r: not r["pinned"])
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows[: max(1, limit)]]


# ---------------------------------------------------------------- bildirimler
def _notif_path() -> Path:
    return config.DATA / "notifications.jsonl"


def _read_notifs() -> list[dict]:
    p = _notif_path()
    out = []
    for line in p.read_text(encoding="utf-8").splitlines() if p.is_file() else []:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _write_notifs(rows: list[dict]) -> None:
    p = _notif_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows[-NOTIF_MAX:]), encoding="utf-8")


def notify(title: str, body: str = "", kind: str = "info", link: str = "") -> dict:
    """Bildirim merkezine yazar (diğer modüller çağırır). kind: info|reminder|approval|error|done."""
    if kind not in ("info", "reminder", "approval", "error", "done"):
        kind = "info"
    row = {"id": new_id(), "ts": now(), "title": str(title)[:200], "body": str(body)[:1000], "kind": kind, "read": False}
    if link:
        row["link"] = str(link)[:500]
    with _lock:
        _write_notifs(_read_notifs() + [row])
    try:                                                       # telefona anlık bildirim (abonelik + pywebpush varsa)
        from . import mobile
        mobile.on_notify(row)
    except Exception:                                          # noqa: BLE001 — bildirim gönderilemezse merkezde yine durur
        pass
    return row


def notifications(unread: bool = False, limit: int = 100) -> list[dict]:
    rows = _read_notifs()
    if unread:
        rows = [r for r in rows if not r.get("read")]
    return list(reversed(rows))[:limit]


def mark_read(ids) -> int:
    with _lock:
        rows = _read_notifs()
        n = 0
        for r in rows:
            if (ids == "all" or r.get("id") in ids) and not r.get("read"):
                r["read"] = True
                n += 1
        _write_notifs(rows)
    return n


# ---------------------------------------------------------------- geri bildirim
def add_feedback(entry: dict) -> None:
    p = config.DATA / "feedback.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with _lock, p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- ekler
def safe_name(name: str) -> str:
    """Yükleme dosya adı: yalnız son bileşen, tehlikeli karakterler ve nokta öneki yok, ≤80 karakter."""
    base = re.split(r"[\\/]", str(name or ""))[-1]
    base = re.sub(r"[^\w.\- ()çğıöşüÇĞİÖŞÜ]", "_", base).strip(" .")
    base = base.lstrip(".") or "dosya"
    stem, ext = os.path.splitext(base)
    return (stem[: 80 - len(ext)] + ext) or "dosya"


def uploads_dir() -> Path:
    return _dir("uploads")


def att_dir(att_id: str) -> Path:
    if not ATT_RE.match(str(att_id or "")):
        raise ValueError("geçersiz ek kimliği")
    return uploads_dir() / att_id


def att_meta(att_id: str) -> dict | None:
    try:
        p = att_dir(att_id) / "meta.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except (ValueError, OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------- kaynaklar (beyin araması)
KIND_MAP = {"note": "note", "mail": "mail", "file": "file", "chat": "chat", "item": "item"}


def obsidian_url(rel: str) -> str:
    rel = rel[:-3] if rel.lower().endswith(".md") else rel
    return f"obsidian://open?vault=SecondBrain&file={quote(rel, safe='')}"


def to_source(h: dict) -> dict:
    """brain.find sonucu → Source."""
    from .redact import redact
    doc_id = str(h.get("doc_id", ""))
    kind = KIND_MAP.get(str(h.get("kind", "")), "item")
    if kind == "item" and doc_id.startswith("chat:"):
        kind = "chat"
    text = " ".join(str(h.get("text", "")).split())
    src = {"kind": kind, "title": h.get("title") or doc_id, "doc_id": doc_id, "snippet": redact(text)[:240],
           "date": h.get("date") or "", "score": h.get("score", 0)}
    if kind == "note":
        rel = str(h.get("ref") or doc_id.removeprefix("note:"))
        src["path"] = rel
        src["url"] = obsidian_url(rel)
    return src


def search_sources(q: str, k: int = 5, smart: bool = False, **kw) -> list[dict]:
    """Beyin dizininde ara → [Source]. Dizin yoksa/bozuksa boş liste (sohbeti durdurmaz)."""
    if not q.strip():
        return []
    try:
        from . import brain
        try:
            from . import search
            hits = search.smart_find(q, k=k, log=False, **kw) if smart else brain.find(q, k=k, **kw)
        except (ImportError, AttributeError):
            hits = brain.find(q, k=k, **kw)
        return [to_source(h) for h in hits]
    except Exception:                                        # noqa: BLE001
        return []
