"""Paket A: sohbet, geçmiş, ekler, bildirimler, komutlar (sahte model; gerçek ağ/model yok)."""
import json

import pytest

from sb import api_conv, brain, chat, convstore, vault_ops, webroutes
from sb.webroutes import Ctx


def call(method, path, data=None, query=None, session=None, respond=None, raw=b"", sid="", ctype=""):
    r = webroutes.find(method, path)
    assert r is not None, path
    ctx = Ctx(method, path, data or {}, query or {}, raw, ctype, sid or (data or {}).get("sid", "") or (query or {}).get("sid", ""),
              False, session if session is not None else chat.Session(), respond)
    code, body, _, _ = webroutes.call(r, ctx)
    return code, json.loads(body)


class Model:
    """Sahte ctx.respond: oturum geçmişini gerçek respond gibi büyütür."""
    def __init__(self, session, replies=None):
        self.s, self.seen, self.replies = session, [], list(replies or [])

    def __call__(self, text):
        self.seen.append(text)
        self.s.messages.append({"role": "user", "content": text})
        reply = self.replies.pop(0) if self.replies else f"cevap {len(self.seen)}"
        self.s.messages.append({"role": "assistant", "content": reply})
        return {"reply": reply, "trace": ["otomatik getirme: x"], "proposals": []}


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    (vault / "00-Inbox").mkdir(parents=True)
    monkeypatch.setattr(vault_ops, "VAULT", vault)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "")
    monkeypatch.setattr(brain, "find", lambda q, k=10, **kw: [
        {"doc_id": "note:20-Projeler/Atlas.md", "kind": "note", "title": "Atlas", "ref": "20-Projeler/Atlas.md", "score": 0.03,
         "date": "2026-10-01", "text": "Atlas projesi notu  " + "x" * 400},
        {"doc_id": "mail:main:1", "kind": "mail", "title": "Konu", "ref": "1", "score": 0.02, "date": "2026-10-02", "text": "mail"}][:k])
    return vault


def chat_once(sid, text, session=None, **extra):
    s = session or chat.Session()
    m = Model(s)
    code, out = call("POST", "/api/v2/chat", {"sid": sid, "text": text, **extra}, session=s, respond=m)
    return code, out, s, m


def test_chat_sources_title_and_storage():
    code, out, s, m = chat_once("s1", "Atlas projesi ne durumda? " + "u" * 100)
    assert code == 200
    assert out["conv"] == {"sid": "s1", "title": ("Atlas projesi ne durumda? " + "u" * 100)[:60]}
    assert out["user"]["role"] == "user" and out["reply"]["role"] == "assistant" and out["proposals"] == []
    src = out["reply"]["sources"]
    assert src[0]["kind"] == "note" and src[0]["path"] == "20-Projeler/Atlas.md"
    assert src[0]["url"] == "obsidian://open?vault=SecondBrain&file=20-Projeler%2FAtlas"
    assert len(src[0]["snippet"]) <= 240 and src[1]["kind"] == "mail" and "path" not in src[1]
    assert out["reply"]["trace"] == ["otomatik getirme: x"]
    stored = convstore.load("s1")
    assert [x["role"] for x in stored["messages"]] == ["user", "assistant"]


def test_chat_survives_broken_index(monkeypatch):
    monkeypatch.setattr(brain, "find", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("dizin yok")))
    code, out, *_ = chat_once("s2", "merhaba")
    assert code == 200 and out["reply"]["sources"] == []


def test_invalid_sid_and_empty_text():
    assert chat_once("../x", "a")[0] == 400
    assert chat_once("a" * 41, "a")[0] == 400
    assert chat_once("ok", "  ")[0] == 400
    assert call("GET", "/api/v2/conv", query={"sid": "..\\..\\evil"})[0] == 400


def test_convs_list_search_pin_archive():
    chat_once("a1", "Kasadaki ŞİFRE politikası")
    chat_once("a2", "Başka konu")
    code, rows = call("GET", "/api/v2/convs", query={"q": "sifre"})          # aksan/büyük-küçük duyarsız
    assert code == 200 and [r["sid"] for r in rows] == ["a1"]
    assert set(rows[0]) == {"sid", "title", "updated", "pinned", "archived", "count", "preview"} and rows[0]["count"] == 2
    call("POST", "/api/v2/conv/update", {"sid": "a1", "pinned": True, "title": "Yeni ad"})
    rows = call("GET", "/api/v2/convs")[1]
    assert [r["sid"] for r in rows] == ["a1", "a2"] and rows[0]["title"] == "Yeni ad"
    assert [r["sid"] for r in call("GET", "/api/v2/convs", query={"pinned": "1"})[1]] == ["a1"]
    code, rec = call("POST", "/api/v2/conv/delete", {"sid": "a2"})
    assert rec["archived"] is True and convstore.load("a2") is not None          # silinmez
    assert [r["sid"] for r in call("GET", "/api/v2/convs")[1]] == ["a1"]
    assert [r["sid"] for r in call("GET", "/api/v2/convs", query={"archived": "1"})[1]] == ["a2"]
    assert call("POST", "/api/v2/conv/update", {"sid": "yok"})[0] == 404


def test_conv_get_primes_session_with_last_12():
    s = chat.Session()
    m = Model(s)
    for i in range(10):
        call("POST", "/api/v2/chat", {"sid": "g", "text": f"soru {i}"}, session=s, respond=m)
    fresh = chat.Session()
    code, rec = call("GET", "/api/v2/conv", query={"sid": "g"}, session=fresh)
    assert code == 200 and len(rec["messages"]) == 20
    assert len(fresh.messages) == 12 and fresh.messages[-1]["role"] == "assistant"
    assert set(fresh.messages[0]) == {"role", "content"}


def test_conv_new_resets_session():
    s = chat.Session()
    s.messages.append({"role": "user", "content": "x"})
    code, out = call("POST", "/api/v2/conv/new", {}, session=s)
    assert code == 200 and convstore.valid_sid(out["sid"]) and s.messages == []


def test_edit_truncates_and_regen_keeps_alternatives():
    s = chat.Session()
    m = Model(s, ["bir", "iki", "üç", "dört", "beş"])
    _, o1 = call("POST", "/api/v2/chat", {"sid": "e", "text": "ilk"}, session=s, respond=m)
    call("POST", "/api/v2/chat", {"sid": "e", "text": "ikinci"}, session=s, respond=m)
    uid = o1["user"]["id"]
    code, out = call("POST", "/api/v2/msg/edit", {"sid": "e", "id": uid, "text": "ilk düzeltilmiş"}, session=s, respond=m)
    assert code == 200 and out["user"]["edited"] is True and out["reply"]["text"] == "üç"
    rec = convstore.load("e")
    assert [x["text"] for x in rec["messages"]] == ["ilk düzeltilmiş", "üç"]            # sonrakiler atıldı
    assert rec["title"] == "ilk düzeltilmiş"
    assert [x["content"] for x in s.messages] == ["ilk düzeltilmiş", "üç"]              # model geçmişi de tutarlı
    code, out = call("POST", "/api/v2/msg/regen", {"sid": "e", "id": out["reply"]["id"]}, session=s, respond=m)
    assert code == 200 and out["reply"]["text"] == "dört" and out["reply"]["alternatives"][0]["text"] == "üç"
    assert m.seen[-1] == "ilk düzeltilmiş"                                              # aynı soru
    assert call("POST", "/api/v2/msg/edit", {"sid": "e", "id": out["reply"]["id"], "text": "x"}, respond=m)[0] == 404


def test_to_note_redacts_links_sources_and_blocks_escape(env):
    _, out, s, _ = chat_once("n", "soru")
    mid = out["reply"]["id"]
    rec = convstore.load("n")
    rec["messages"][1]["text"] = "# Başlık\nIBAN TR33 0006 1005 1978 6457 8413 26 gizli"
    convstore.save(rec)
    code, r = call("POST", "/api/v2/msg/to-note", {"sid": "n", "id": mid})
    assert code == 200 and r["path"] == "00-Inbox/Başlık.md"
    text = (env / r["path"]).read_text(encoding="utf-8")
    assert "TR33 0006" not in text and "[[20-Projeler/Atlas|Atlas]]" in text and "type: kaynak" in text
    code2, r2 = call("POST", "/api/v2/msg/to-note", {"sid": "n", "id": mid, "title": "Başlık", "folder": "40-Kaynaklar"})
    assert r2["path"] == "40-Kaynaklar/Başlık.md"
    for bad in ("../dışarı", "/etc", "C:/Windows", "00-Inbox/../../x", "_system", "90-Arşiv"):
        assert call("POST", "/api/v2/msg/to-note", {"sid": "n", "id": mid, "folder": bad})[0] == 400, bad
    code, r3 = call("POST", "/api/v2/msg/to-note", {"sid": "n", "id": mid, "title": "../../kaçış"})
    assert (env / r3["path"]).resolve().is_relative_to(env.resolve())


def test_react_writes_feedback():
    import sb.config as config
    _, out, *_ = chat_once("r", "soru bu")
    mid = out["reply"]["id"]
    assert call("POST", "/api/v2/msg/react", {"sid": "r", "id": mid, "reaction": "up", "comment": "iyi"})[1] == {"ok": True}
    assert convstore.load("r")["messages"][1]["reaction"] == "up"
    rows = [json.loads(l) for l in (config.DATA / "feedback.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["reaction"] == "up" and rows[0]["question"] == "soru bu" and rows[0]["comment"] == "iyi"
    call("POST", "/api/v2/msg/react", {"sid": "r", "id": mid, "reaction": "copy"})
    assert len((config.DATA / "feedback.jsonl").read_text(encoding="utf-8").splitlines()) == 1     # copy yazılmaz
    call("POST", "/api/v2/msg/react", {"sid": "r", "id": mid, "reaction": None})
    assert "reaction" not in convstore.load("r")["messages"][1]
    assert call("POST", "/api/v2/msg/react", {"sid": "r", "id": mid, "reaction": "boo"})[0] == 400


def test_upload_text_sanitizes_name_and_feeds_chat():
    import sb.config as config
    code, up = call("POST", "/api/v2/upload", query={"sid": "u", "name": "..\\..\\evil/../not.txt"}, raw="selam dünya ".encode() * 3, ctype="text/plain")
    assert code == 200 and up["kind"] == "text" and up["name"] == "not.txt" and up["chars"] > 0 and up["preview"].startswith("selam")
    d = config.DATA / "uploads" / up["att_id"]
    assert (d / "not.txt").is_file() and not list(config.DATA.glob("evil*"))
    _, up2 = call("POST", "/api/v2/upload", query={"name": "büyük.md"}, raw=("a" * 9000).encode())
    s = chat.Session()
    m = Model(s)
    code, out = call("POST", "/api/v2/chat", {"sid": "u", "text": "özetle", "attachments": [up["att_id"], up2["att_id"], "../x", "yok"]},
                     session=s, respond=m)
    assert code == 200 and m.seen[0].startswith("özetle\n\n[EK: not.txt]\nselam")
    assert "[EK: büyük.md]\n" + "a" * 6000 in m.seen[0] and "a" * 6001 not in m.seen[0]        # ≤6000
    assert [a["name"] for a in out["user"]["attachments"]] == ["not.txt", "büyük.md"]
    assert call("POST", "/api/v2/upload", query={"name": "x"}, raw=b"")[0] == 400


def test_upload_image_and_audio_use_optional_modules(monkeypatch):
    import sys
    import types
    v = types.ModuleType("sb.vision")
    v.describe = lambda b: "bir kedi fotoğrafı"
    vo = types.ModuleType("sb.voice")
    vo.transcribe = lambda b, ct, language=None: {"text": "merhaba dünya"}
    monkeypatch.setitem(sys.modules, "sb.vision", v)
    monkeypatch.setitem(sys.modules, "sb.voice", vo)
    import sb
    monkeypatch.setattr(sb, "vision", v, raising=False)
    monkeypatch.setattr(sb, "voice", vo, raising=False)
    assert call("POST", "/api/v2/upload", query={"name": "k.png"}, raw=b"\x89PNG")[1]["preview"] == "bir kedi fotoğrafı"
    a = call("POST", "/api/v2/upload", query={"name": "s.wav"}, raw=b"RIFF", ctype="audio/wav")[1]
    assert a["kind"] == "audio" and a["preview"] == "merhaba dünya"
    o = call("POST", "/api/v2/upload", query={"name": "x.bin"}, raw=b"\x00\x01")[1]
    assert o["kind"] == "other" and o["chars"] == 0


def test_notifications_roundtrip():
    a = convstore.notify("Başlık", "gövde", kind="reminder", link="/x")
    convstore.notify("İkinci", kind="bilinmeyen")
    code, rows = call("GET", "/api/v2/notifications")
    assert [r["title"] for r in rows] == ["İkinci", "Başlık"] and rows[0]["kind"] == "info" and rows[1]["link"] == "/x"
    assert {"id", "ts", "title", "body", "kind", "read"} <= set(rows[1])
    call("POST", "/api/v2/notifications/read", {"ids": [a["id"]]})
    assert [r["title"] for r in call("GET", "/api/v2/notifications", query={"unread": "1"})[1]] == ["İkinci"]
    call("POST", "/api/v2/notifications/read", {"ids": "all"})
    assert call("GET", "/api/v2/notifications", query={"unread": "1"})[1] == []
    assert call("POST", "/api/v2/notifications/read", {"ids": 5})[0] == 400
    for i in range(520):
        convstore.notify(f"n{i}")
    assert len(convstore._read_notifs()) == convstore.NOTIF_MAX


def test_commands_listing_and_simple_commands():
    code, cmds = call("GET", "/api/v2/commands")
    assert [c["cmd"] for c in cmds] == ["/yeni", "/ara", "/not", "/gorev", "/ozet", "/hatirla", "/unut", "/bugun", "/kisi", "/proje", "/kart"]
    code, out = call("POST", "/api/v2/command", {"sid": "k", "cmd": "/yeni", "args": ""})
    assert out["open"]["view"] == "chat" and convstore.valid_sid(out["open"]["params"]["sid"])
    code, out = call("POST", "/api/v2/command", {"sid": "k", "cmd": "ara", "args": "atlas"})
    assert out["sources"][0]["title"] == "Atlas" and "Atlas" in out["reply"]
    assert call("POST", "/api/v2/command", {"sid": "k", "cmd": "/kisi", "args": "Ali Veli"})[1] == {"open": {"view": "person", "params": {"name": "Ali Veli"}}}
    assert call("POST", "/api/v2/command", {"sid": "k", "cmd": "/proje", "args": "Atlas"})[1]["open"]["view"] == "project"
    assert call("POST", "/api/v2/command", {"sid": "k", "cmd": "/kart"})[1]["open"]["view"] == "cards"
    assert call("POST", "/api/v2/command", {"sid": "k", "cmd": "/yok"})[0] == 400
    assert call("POST", "/api/v2/command", {"sid": "k", "cmd": "/not", "args": ""})[0] == 400


def test_commands_not_gorev_bugun_ozet(monkeypatch):
    from sb import inbox, llm, mcp_server, tasks
    seen = {}
    monkeypatch.setattr(inbox, "add", lambda t, source="asistan": seen.setdefault("not", (t, source)) and "Kutuya not alındı")
    monkeypatch.setattr(tasks, "add", lambda title, **kw: seen.setdefault("gorev", (title, kw)) and "Görev oluşturuldu")
    monkeypatch.setattr(mcp_server, "brain_today", lambda days=14: "Yaklaşan: yok")
    prompts = []
    monkeypatch.setattr(llm, "complete", lambda task, prompt, **kw: (prompts.append((prompt, kw)) or ("<think>x</think>Özet metni", "yerel")))
    assert call("POST", "/api/v2/command", {"sid": "k", "cmd": "/not", "args": "süt al"})[1]["reply"].startswith("Kutuya")
    assert seen["not"] == ("süt al", "komut")
    assert call("POST", "/api/v2/command", {"sid": "k", "cmd": "/gorev", "args": "rapor yaz"})[1]["reply"].startswith("Görev")
    assert seen["gorev"][0] == "rapor yaz" and seen["gorev"][1]["owner"]
    assert call("POST", "/api/v2/command", {"sid": "k", "cmd": "/bugun"})[1]["reply"] == "Yaklaşan: yok"
    assert "Özetlenecek" in call("POST", "/api/v2/command", {"sid": "bos", "cmd": "/ozet"})[1]["reply"]
    chat_once("k", "uzun bir konuşma")
    out = call("POST", "/api/v2/command", {"sid": "k", "cmd": "/ozet"})[1]
    assert out["reply"] == "Özet metni" and prompts[0][1]["private"] is True and "uzun bir konuşma" in prompts[0][0]


def test_commands_memory_optional(monkeypatch):
    monkeypatch.setattr(api_conv, "_call_route", lambda ctx, path, data: None)
    assert "hazır değil" in call("POST", "/api/v2/command", {"sid": "k", "cmd": "/hatirla", "args": "x"})[1]["reply"]
    calls = []
    monkeypatch.setattr(api_conv, "_call_route", lambda ctx, path, data: calls.append((path, data)) or {"found": {"memory": [1], "notes": [], "docs": 2, "convs": []}})
    out = call("POST", "/api/v2/command", {"sid": "k", "cmd": "/unut", "args": "eski proje"})[1]
    assert calls[0] == ("/api/v2/forget", {"sid": "k", "topic": "eski proje"}) and "3 eşleşme" in out["reply"]
    out = call("POST", "/api/v2/command", {"sid": "k", "cmd": "/hatirla", "args": "kahveyi sütsüz içerim"})[1]
    assert calls[1][0] == "/api/v2/memory/add" and "kahveyi" in out["reply"]
