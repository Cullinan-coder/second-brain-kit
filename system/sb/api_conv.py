"""Faz 2 API: sohbet, geçmiş, ekler, bildirimler, eğik çizgi komutları (Paket A). Sözleşme: docs/faz2-sartname.md."""
from __future__ import annotations

import re
from datetime import date

from . import config, convstore, vault_ops
from .convstore import fold, valid_sid
from .redact import redact
from .webroutes import ApiError, Ctx, route

ATT_CHARS = 6000
TEXT_EXT = {"txt", "md", "markdown", "csv", "tsv", "json", "yaml", "yml", "log", "ini", "toml", "xml", "html", "htm", "py", "js", "ts",
            "tsx", "jsx", "php", "c", "cpp", "h", "java", "go", "rs", "sql", "sh", "bat", "ps1", "css", "tex", "ipynb", "rtf"}
OFFICE_EXT = {"docx", "xlsx", "pptx"}
IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
AUDIO_EXT = {"wav", "mp3", "m4a", "ogg", "webm", "flac", "opus", "aac"}


def _sid(ctx: Ctx) -> str:
    sid = str(ctx.arg("sid") or ctx.sid or "")
    if not valid_sid(sid):
        raise ApiError(400, "geçersiz sohbet kimliği")
    return sid


def _need_respond(ctx: Ctx) -> None:
    if ctx.respond is None:
        raise ApiError(503, "model kullanılamıyor")


def _prime(ctx: Ctx, history: list[dict], conv: dict | None = None) -> None:
    """Sunucu oturumunun model geçmişini sohbet kaydındaki geçmişle eşitler. Sohbetin TEK giriş noktası burası (D-30): model geçmişi
    her turda sohbet kaydından kurulur (araç çıktıları turdan tura taşınmaz) ve kirlilik bayrakları sohbet kaydında kalıcıdır —
    sunucu yeniden başlasa ya da eski sohbet açılsa da dış içerik görmüş sohbet "kirli" kalır (yalnız yeni sohbette sıfırlanır)."""
    s = ctx.session
    if s is not None:
        s.messages[:] = [dict(m) for m in history]
        if conv is not None:
            s.tainted = bool(getattr(s, "tainted", False) or conv.get("tainted"))
            s.external = bool(getattr(s, "external", False) or conv.get("external"))


def _keep_flags(ctx: Ctx, conv: dict) -> None:
    s = ctx.session
    if s is not None:
        conv["tainted"], conv["external"] = bool(getattr(s, "tainted", False)), bool(getattr(s, "external", False))


# ---------------------------------------------------------------- ekler
def _att_block(att_id: str) -> str:
    meta = convstore.att_meta(att_id)
    if not meta:
        return ""
    try:
        text = (convstore.att_dir(att_id) / "text.txt").read_text(encoding="utf-8")
    except OSError:
        text = ""
    return f"[EK: {meta.get('name', 'dosya')}]\n{text[:ATT_CHARS]}".rstrip()


def _att_blocks(user_msg: dict) -> list[str]:
    return [b for b in (_att_block(a["id"]) for a in user_msg.get("attachments") or []) if b]


def _full_text(user_msg: dict) -> str:
    blocks = _att_blocks(user_msg)
    return user_msg["text"] + ("\n\n" + "\n\n".join(blocks) if blocks else "")


def _atts_for(ids) -> list[dict]:
    out = []
    for a in ids or []:
        meta = convstore.att_meta(str(a))
        if meta:
            out.append({"id": meta["att_id"], "name": meta["name"], "kind": meta.get("kind", "other")})
    return out


# ---------------------------------------------------------------- sohbet turu
def _turn(ctx: Ctx, conv: dict, user_msg: dict, reuse: dict | None = None) -> dict:
    """Kullanıcı mesajını cevaplatır. `reuse`: yeniden üretimde yerinde güncellenecek asistan mesajı."""
    _need_respond(ctx)
    idx = convstore.find_msg(conv, user_msg["id"])[0]
    _prime(ctx, convstore.model_history(conv, upto=idx), conv)
    blocks = _att_blocks(user_msg)
    if blocks and ctx.session is not None:                   # ek metni kullanıcının sözü değil dış içeriktir (D-06b)
        ctx.session.external = True
        ctx.session.attachment_text = "\n\n".join(blocks)
    out = ctx.respond(_full_text(user_msg)) or {}
    _keep_flags(ctx, conv)
    reply_text = str(out.get("reply", ""))
    sources = convstore.search_sources(user_msg["text"], 5)
    trace = [str(t) for t in out.get("trace") or []]
    if reuse is not None:
        reuse.setdefault("alternatives", []).append({"text": reuse.get("text", ""), "ts": reuse.get("ts", ""),
                                                      "sources": reuse.get("sources", [])})
        reuse.update({"text": reply_text, "ts": convstore.now(), "sources": sources, "trace": trace})
        reuse.pop("reaction", None)
        reuse.pop("model", None)
        if out.get("model"):
            reuse["model"] = out["model"]
        reply = reuse
    else:
        reply = convstore.add_message(conv, "assistant", reply_text)
        reply.update({"sources": sources, "trace": trace})     # boş olsalar da alan hep bulunur
        if out.get("model"):                                    # gerçekte hangi model cevapladı (+ neden yerele düştüyse)
            reply["model"] = out["model"]
    convstore.save(conv)
    return {"conv": {"sid": conv["sid"], "title": conv.get("title", "")}, "user": user_msg, "reply": reply,
            "proposals": out.get("proposals") or []}


@route("POST", "/api/v2/chat", model=True)
def chat(ctx: Ctx) -> dict:
    sid = _sid(ctx)
    text = str(ctx.arg("text") or "").strip()
    if not text:
        raise ApiError(400, "boş mesaj")
    _need_respond(ctx)
    conv = convstore.ensure(sid)
    atts = _atts_for(ctx.arg("attachments"))
    user = convstore.add_message(conv, "user", text[:4000], attachments=atts)
    return _turn(ctx, conv, user)


@route("POST", "/api/v2/msg/edit", model=True)
def msg_edit(ctx: Ctx) -> dict:
    sid, mid = _sid(ctx), str(ctx.arg("id") or "")
    text = str(ctx.arg("text") or "").strip()
    conv = convstore.load(sid)
    hit = convstore.find_msg(conv, mid) if conv else None
    if not hit or hit[1].get("role") != "user":
        raise ApiError(404, "kullanıcı mesajı bulunamadı")
    if not text:
        raise ApiError(400, "boş mesaj")
    i, msg = hit
    conv["messages"] = conv["messages"][: i + 1]            # sonrakiler atılır (kayıt dışı: sohbet dalı yeniden başlar)
    msg.update({"text": text[:4000], "edited": True, "edited_at": convstore.now()})
    if i == 0:
        conv["title"] = " ".join(text.split())[:60]
    return _turn(ctx, conv, msg)


@route("POST", "/api/v2/msg/regen", model=True)
def msg_regen(ctx: Ctx) -> dict:
    sid, mid = _sid(ctx), str(ctx.arg("id") or "")
    conv = convstore.load(sid)
    hit = convstore.find_msg(conv, mid) if conv else None
    if not hit or hit[1].get("role") != "assistant":
        raise ApiError(404, "asistan mesajı bulunamadı")
    i, msg = hit
    prev = next((m for m in reversed(conv["messages"][:i]) if m.get("role") == "user"), None)
    if prev is None:
        raise ApiError(400, "yanıtlanan soru yok")
    conv["messages"] = conv["messages"][: i + 1]
    return _turn(ctx, conv, prev, reuse=msg)


# ---------------------------------------------------------------- geçmiş
@route("GET", "/api/v2/convs")
def convs(ctx: Ctx) -> list:
    def flag(name):
        v = str(ctx.arg(name, "") or "")
        return None if v == "" else v in ("1", "true")
    try:
        limit = max(1, min(500, int(ctx.arg("limit", 50))))
    except (TypeError, ValueError):
        limit = 50
    return convstore.list_convs(str(ctx.arg("q", "") or ""), flag("pinned"), bool(flag("archived")), limit)


@route("GET", "/api/v2/conv")
def conv_get(ctx: Ctx) -> dict:
    sid = _sid(ctx)
    c = convstore.load(sid)
    if c is None:
        raise ApiError(404, "sohbet yok")
    _prime(ctx, convstore.model_history(c), c)              # açılan eski sohbet modelin bağlamı olur (kirlilik bayrağıyla)
    return c


@route("POST", "/api/v2/conv/update")
def conv_update(ctx: Ctx) -> dict:
    sid = _sid(ctx)
    c = convstore.load(sid)
    if c is None:
        raise ApiError(404, "sohbet yok")
    if ctx.arg("title") is not None:
        c["title"] = " ".join(str(ctx.arg("title")).split())[:120] or c.get("title", "")
    for k in ("pinned", "archived"):
        if ctx.arg(k) is not None:
            c[k] = bool(ctx.arg(k))
    return convstore.save(c)


@route("POST", "/api/v2/conv/delete")
def conv_delete(ctx: Ctx) -> dict:
    """Silmez: arşive taşır."""
    sid = _sid(ctx)
    c = convstore.load(sid)
    if c is None:
        raise ApiError(404, "sohbet yok")
    c["archived"] = True
    return convstore.save(c)


def _reset_session(ctx: Ctx) -> None:
    s = ctx.session
    if s is not None:
        s.messages.clear()
        s.proposals.clear()
        s.tainted = False                                   # kirlilik yalnız yeni sohbette sıfırlanır (D-06)
        s.external = False
        s.attachment_text = ""
        s.vision_reply = ""


@route("POST", "/api/v2/conv/new")
def conv_new(ctx: Ctx) -> dict:
    _reset_session(ctx)
    return {"ok": True, "sid": convstore.new_sid()}


@route("POST", "/api/v2/conv/reset")
def conv_reset(ctx: Ctx) -> dict:
    """Aynı kimlikle baştan başla (eski /api/reset ucunun karşılığı): eski içerik arşivlenmiş ayrı bir sohbete taşınır (kirlilik
    bayrağıyla birlikte), bu kimlik boş ve temiz başlar; bekleyen kartları iptal edilir."""
    sid = _sid(ctx)
    _reset_session(ctx)
    c = convstore.load(sid)
    if c is not None and c.get("messages"):
        convstore.save(dict(c, sid=convstore.new_sid(), archived=True))
        convstore.save(dict(c, messages=[], title="", tainted=False, external=False))
    return {"ok": True, "sid": sid}


# ---------------------------------------------------------------- mesajdan not / tepki
def _note_title(text: str) -> str:
    for line in text.splitlines():
        line = re.sub(r"[#*_`>\[\]]", "", line).strip()
        if line:
            return line[:60]
    return "Sohbet notu"


def _safe_folder(folder: str) -> str:
    f = str(folder or "00-Inbox").strip().replace("\\", "/").strip("/")
    parts = f.split("/")
    if not f or f.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", f) or any(p in ("", ".", "..") for p in parts) or ":" in f:
        raise ApiError(400, "geçersiz klasör")
    if parts[0] not in vault_ops.WRITABLE:
        raise ApiError(400, "bu klasöre yazılamaz")
    return f


@route("POST", "/api/v2/msg/to-note")
def msg_to_note(ctx: Ctx) -> dict:
    from .notes import dump_note, safe_filename
    sid, mid = _sid(ctx), str(ctx.arg("id") or "")
    c = convstore.load(sid)
    hit = convstore.find_msg(c, mid) if c else None
    if not hit:
        raise ApiError(404, "mesaj bulunamadı")
    msg = hit[1]
    folder = _safe_folder(ctx.arg("folder") or "00-Inbox")
    title = redact(" ".join(str(ctx.arg("title") or "").split()) or _note_title(msg.get("text", "")))[:80]
    name = safe_filename(title) or "Sohbet notu"
    vault = vault_ops.VAULT.resolve()
    dest = (vault / folder / f"{name}.md").resolve()
    if vault not in dest.parents:
        raise ApiError(400, "kasa dışına yazılamaz")
    n = 2
    while dest.exists():
        dest = dest.with_name(f"{name} ({n}).md")
        n += 1
    src_lines = []
    for s in msg.get("sources") or []:
        if s.get("path"):
            src_lines.append(f"- [[{s['path'][:-3] if s['path'].endswith('.md') else s['path']}|{s.get('title', '')}]]")
        else:
            src_lines.append(f"- {s.get('kind', '')}: {s.get('title', '')}")
    body = f"# {title}\n\n{redact(msg.get('text', ''))}\n"
    if src_lines:
        body += "\n## Kaynaklar\n" + "\n".join(redact(x) for x in src_lines) + "\n"
    today = date.today()
    fm = {"type": "kaynak", "status": "aktif", "tags": ["not", "sohbet"], "source": "asistan",
          "source_id": f"sohbet:{sid}:{mid}", "created": today, "updated": today}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(dump_note(fm, body), encoding="utf-8")
    rel = dest.relative_to(vault).as_posix()
    sha = vault_ops.commit([rel], f"sohbetten not: {title[:50]}")
    vault_ops.log("asistan", "sohbetten not", rel, title[:120], sha)
    return {"path": rel}


@route("POST", "/api/v2/msg/react")
def msg_react(ctx: Ctx) -> dict:
    sid, mid = _sid(ctx), str(ctx.arg("id") or "")
    reaction = ctx.arg("reaction")
    if reaction not in (None, "up", "down", "copy", "pin"):
        raise ApiError(400, "geçersiz tepki")
    c = convstore.load(sid)
    hit = convstore.find_msg(c, mid) if c else None
    if not hit:
        raise ApiError(404, "mesaj bulunamadı")
    i, msg = hit
    if reaction is None:
        msg.pop("reaction", None)
    else:
        msg["reaction"] = reaction
    comment = str(ctx.arg("comment") or "")[:500]
    if comment:
        msg["comment"] = comment
    convstore.save(c)
    if reaction in ("up", "down"):
        prev = next((m for m in reversed(c["messages"][:i]) if m.get("role") == "user"), {})
        convstore.add_feedback({"ts": convstore.now(), "sid": sid, "msg_id": mid, "reaction": reaction, "comment": comment,
                                "question": redact(prev.get("text", ""))[:300], "answer": redact(msg.get("text", ""))[:600]})
    return {"ok": True}


# ---------------------------------------------------------------- yükleme
def _kind(ext: str) -> str:
    if ext in TEXT_EXT or ext in OFFICE_EXT:
        return "text"
    return "pdf" if ext == "pdf" else "image" if ext in IMAGE_EXT else "audio" if ext in AUDIO_EXT else "other"


def _extract(path, kind: str, ext: str, raw: bytes, ctype: str) -> str:
    try:
        if ext in OFFICE_EXT or ext == "pdf":
            from . import content
            return content.extract(path)
        if kind == "text":
            from . import content
            return content._plain(path)
        if kind == "image":
            from . import vision                              # Paket C; yoksa yalnız ad
            return str(vision.describe(raw))
        if kind == "audio":
            from . import voice
            return str(voice.transcribe(raw, ctype, language=None).get("text", ""))
    except Exception:                                         # noqa: BLE001 — çıkarılamayan ek sohbeti durdurmaz
        return ""
    return ""


@route("POST", "/api/v2/upload", upload=True)
def upload(ctx: Ctx) -> dict:
    import json
    import uuid
    if not ctx.raw:
        raise ApiError(400, "boş dosya")
    name = convstore.safe_name(ctx.arg("name") or "dosya")
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    att_id = uuid.uuid4().hex[:12]
    d = convstore.att_dir(att_id)
    d.mkdir(parents=True, exist_ok=True)
    target = (d / name).resolve()
    if d.resolve() not in target.parents:
        raise ApiError(400, "geçersiz dosya adı")
    target.write_bytes(ctx.raw)
    kind = _kind(ext)
    text = redact(_extract(target, kind, ext, ctx.raw, ctx.ctype))
    (d / "text.txt").write_text(text[:60000], encoding="utf-8")
    meta = {"att_id": att_id, "name": name, "kind": kind, "chars": len(text), "ts": convstore.now(),
            "sid": str(ctx.arg("sid") or ctx.sid or "")[:40], "size": len(ctx.raw)}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return {"att_id": att_id, "name": name, "kind": kind, "chars": len(text), "preview": " ".join(text.split())[:200]}


# ---------------------------------------------------------------- bildirimler
@route("GET", "/api/v2/notifications")
def notifications(ctx: Ctx) -> list:
    return convstore.notifications(unread=str(ctx.arg("unread", "")) in ("1", "true"))


@route("POST", "/api/v2/notifications/read")
def notifications_read(ctx: Ctx) -> dict:
    ids = ctx.arg("ids")
    if ids != "all" and not isinstance(ids, list):
        raise ApiError(400, "ids liste ya da 'all' olmalı")
    return {"ok": True, "n": convstore.mark_read(ids if ids == "all" else [str(i) for i in ids])}


# ---------------------------------------------------------------- eğik çizgi komutları
COMMANDS = [
    {"cmd": "/yeni", "desc": "Yeni sohbet başlat"},
    {"cmd": "/ara", "desc": "Kasada ve arşivde ara", "args": "<metin>"},
    {"cmd": "/not", "desc": "Gelen kutusuna hızlı not", "args": "<metin>"},
    {"cmd": "/gorev", "desc": "Yeni görev ekle", "args": "<metin>"},
    {"cmd": "/ozet", "desc": "Bu sohbeti özetle"},
    {"cmd": "/hatirla", "desc": "Kalıcı bilgi hatırla", "args": "<bilgi>"},
    {"cmd": "/unut", "desc": "Bir konuyu unut (onaylı)", "args": "<konu>"},
    {"cmd": "/bugun", "desc": "Yaklaşan tarihler"},
    {"cmd": "/kisi", "desc": "Kişi görünümünü aç", "args": "<ad>"},
    {"cmd": "/proje", "desc": "Proje görünümünü aç", "args": "<ad>"},
    {"cmd": "/kart", "desc": "Bilgi kartı tekrar oturumu"},
]


@route("GET", "/api/v2/commands")
def commands(ctx: Ctx) -> list:
    return COMMANDS


def _call_route(ctx: Ctx, path: str, data: dict) -> dict | None:
    """Başka modülün (Paket B) ucunu işlev olarak çağırır; modül yoksa None."""
    try:
        from . import api_memory                              # noqa: F401 — uçları kaydeder
    except Exception:                                         # noqa: BLE001
        return None
    from . import webroutes
    r = webroutes.ROUTES.get(("POST", path))
    if r is None:
        return None
    sub = Ctx("POST", path, dict(data), {}, b"", "", ctx.sid, ctx.remote, ctx.session, ctx.respond, ctx.calendar)
    return r.fn(sub)


def _pending(ctx: Ctx) -> list:
    if ctx.session is None:
        return []
    from . import chat
    return chat.pending(ctx.session)


@route("POST", "/api/v2/command", model=True)
def command(ctx: Ctx) -> dict:
    cmd = fold(str(ctx.arg("cmd") or "").strip()).lstrip("/")
    args = str(ctx.arg("args") or "").strip()
    if cmd not in {c["cmd"][1:] for c in COMMANDS}:
        raise ApiError(400, f"bilinmeyen komut: /{cmd}")
    if cmd in ("ara", "not", "gorev", "hatirla", "unut", "kisi", "proje") and not args:
        raise ApiError(400, f"/{cmd} için metin gerekli")
    if cmd == "yeni":
        _reset_session(ctx)
        return {"reply": "Yeni sohbet açıldı.", "open": {"view": "chat", "params": {"sid": convstore.new_sid()}}}
    if cmd == "ara":
        src = convstore.search_sources(args, 8, smart=True)
        lines = [f"{i}. [{s['kind']}] {s['title']}" + (f" — {s['snippet'][:100]}" if s["snippet"] else "") for i, s in enumerate(src, 1)]
        return {"reply": "\n".join(lines) or "Eşleşme bulunamadı.", "sources": src}
    if cmd == "not":
        from . import inbox
        return {"reply": inbox.add(redact(args), source="komut")}
    if cmd == "gorev":
        from . import tasks
        return {"reply": tasks.add(redact(args)[:120], owner=config.USER, actor="asistan")}
    if cmd == "ozet":
        return {"reply": _summarize(ctx)}
    if cmd in ("hatirla", "unut"):
        path, data = ("/api/v2/memory/add", {"scope": "hafiza", "text": redact(args)}) if cmd == "hatirla" else \
                     ("/api/v2/forget", {"sid": ctx.sid, "topic": args})
        try:
            out = _call_route(ctx, path, data)
        except ApiError as e:
            return {"reply": e.message}
        if out is None:
            return {"reply": "Hafıza modülü şu an hazır değil; biraz sonra tekrar dene."}
        if cmd == "hatirla":
            return {"reply": f"Hatırlayacağım: {redact(args)[:200]}"}
        f = out.get("found") or {}
        total = sum(len(v) if isinstance(v, (list, tuple)) else int(v or 0) for v in f.values())
        return {"reply": f"'{args[:60]}' için {total} eşleşme bulundu; silmek için onay kartını onayla." if total
                else "Bu konuyla eşleşen bir şey bulunamadı.", "proposals": _pending(ctx)}
    if cmd == "bugun":
        from . import mcp_server
        return {"reply": mcp_server.brain_today()}
    if cmd == "kisi":
        return {"open": {"view": "person", "params": {"name": args}}}
    if cmd == "proje":
        return {"open": {"view": "project", "params": {"name": args}}}
    return {"open": {"view": "cards", "params": {}}}          # /kart


def _summarize(ctx: Ctx) -> str:
    c = convstore.load(_sid(ctx))
    if not c or not c.get("messages"):
        return "Özetlenecek sohbet yok."
    dialog = "\n".join(f"{'Ben' if m['role'] == 'user' else 'Asistan'}: {m.get('text', '')[:800]}"
                       for m in c["messages"][-30:] if m.get("role") in ("user", "assistant"))
    prompt = ("Aşağıdaki sohbeti Türkçe, 5 maddede özetle (konu, kararlar, açık işler). Uydurma ekleme.\n\n" + redact(dialog)[:8000])
    try:
        from . import llm
        text, _ = llm.complete("answer", prompt, private=True)
        return llm.strip_think(text).strip() or "(boş özet)"
    except Exception as e:                                    # noqa: BLE001
        return f"Özet çıkarılamadı: {type(e).__name__}"
