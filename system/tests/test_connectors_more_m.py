"""Paket M: Discord, Slack, Notion, notlar (Keep/Apple/OneNote/Evernote), Instagram + X. Örnekler uydurmadır."""
import json
import zipfile

import pytest

from sb import maildb, vault_ops
from sb.connectors import discord, notes, notion, slack, social


@pytest.fixture
def con(tmp_path):
    c = maildb.connect(tmp_path / "mail.db")
    yield c
    c.close()


@pytest.fixture
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    v.mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "")
    return v


def count(con, table):
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def w(p, text, mode="w"):
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        p.write_bytes(text)
    else:
        p.write_text(text if not isinstance(text, (dict, list)) else json.dumps(text), encoding="utf-8")
    return p


def test_discord(tmp_path, con):
    root = tmp_path / "pkg"
    w(root / "messages/c111/channel.json", {"id": "111", "name": "genel-sohbet"})
    w(root / "messages/c111/messages.json", [
        {"ID": "1", "Timestamp": "2026-10-31 14:05:00+00:00", "Contents": "merhaba", "Attachments": ""},
        {"ID": "2", "Timestamp": "2026-10-31 14:06:00+00:00", "Contents": "", "Attachments": "https://cdn.example/a.png"}])
    w(root / "messages/c222/messages.csv", "ID,Timestamp,Contents,Attachments\n3,2026-11-01T10:00:00+00:00,\"selam, dünya\",\n")
    rows = discord.parse(root)
    assert {r["thread_id"] for r in rows} == {"genel-sohbet", "kanal-222"} and len(rows) == 3
    assert rows[1]["attachments"] == ["https://cdn.example/a.png"] and rows[0]["from_addr"] == "me"
    a = discord.run(root, con)
    b = discord.run(root, con)
    assert (a["yeni"], b["yeni"], count(con, "messages")) == (3, 0, 3)


def test_slack_zip(tmp_path, con):
    z = tmp_path / "ws.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("users.json", json.dumps([{"id": "U1", "real_name": "Ayşe Test"}, {"id": "U2", "name": "bora"}]))
        f.writestr("proje/2026-10-31.json", json.dumps([
            {"type": "message", "user": "U1", "text": "bak <@U2> <https://example.com|site>", "ts": "1793455500.000100"},
            {"type": "message", "subtype": "channel_join", "user": "U2", "text": "joined", "ts": "1793455400.0"},
            {"type": "message", "user": "U2", "text": "tamam", "ts": "1793455600.000200", "files": [{"name": "r.pdf"}]}]))
    rows = slack.parse(z, me="bora")
    assert len(rows) == 2 and rows[0]["thread_id"] == "proje"
    assert "@bora" in rows[0]["body"] and "site (https://example.com)" in rows[0]["body"]
    assert rows[1]["from_addr"] == "me" and rows[1]["attachments"] == ["r.pdf"]
    a, b = slack.run(z, con), slack.run(z, con)
    assert (a["yeni"], b["yeni"]) == (2, 0)


def test_notion(tmp_path, con, vault):
    h1, h2 = "a" * 32, "b" * 32
    root = tmp_path / "export"
    w(root / f"Ana Sayfa {h1}.md", f"# Ana Sayfa\n\nBak: [Alt](Ana%20Sayfa%20{h1}/Alt%20Sayfa%20{h2}.md)\n")
    w(root / f"Ana Sayfa {h1}/Alt Sayfa {h2}.md", "# Alt Sayfa\n\nİçerik")
    w(root / f"Tablo {'c' * 32}.csv", "Ad,Değer\nx,1\n")
    pages = {p["title"]: p for p in notion.parse(root)}
    assert set(pages) == {"Ana Sayfa", "Alt Sayfa", "Tablo"}
    assert "[[Alt Sayfa|Alt]]" in pages["Ana Sayfa"]["body"] and pages["Alt Sayfa"]["sub"] == "Ana Sayfa"
    assert "| Ad | Değer |" in pages["Tablo"]["body"]
    a, b = notion.run(root, con), notion.run(root, con)
    assert (a["yeni"], b["yeni"], count(con, "items")) == (3, 0, 3)
    assert (vault / "40-Kaynaklar/Notion/Ana Sayfa/Alt Sayfa.md").exists()
    assert len(list((vault / "40-Kaynaklar/Notion").rglob("*.md"))) == 3


def test_keep_apple_onenote_evernote(tmp_path, vault):
    keep = tmp_path / "keep"
    w(keep / "n1.json", {"title": "Alışveriş", "textContent": "süt", "userEditedTimestampUsec": 1793455500000000,
                         "labels": [{"name": "ev"}]})
    w(keep / "n2.json", {"title": "çöp", "textContent": "x", "isTrashed": True})
    r = notes.run_keep(keep, None)
    assert r["okunan"] == 1 and r["notlar"] == 1
    assert (vault / "40-Kaynaklar/Notlar/keep/Alışveriş.md").exists()

    ap = tmp_path / "apple"
    w(ap / "Fikir.html", "<html><body><div>Başlık</div><div>gövde&nbsp;metni<br>satır</div></body></html>")
    w(ap / "Düz.txt", "sadece metin")
    assert {n["title"] for n in notes.parse_apple(ap)} == {"Fikir", "Düz"}
    assert notes.run_apple(ap, None)["notlar"] == 2

    one = tmp_path / "one.docx"
    with zipfile.ZipFile(one, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:p><w:r><w:t>Toplantı notu</w:t></w:r></w:p><w:p><w:r><w:t>madde 1</w:t></w:r></w:p></w:document>")
    n = notes.parse_onenote(one)
    assert n[0]["body"] == "Toplantı notu\nmadde 1"

    enex = tmp_path / "a.enex"
    w(enex, '<?xml version="1.0"?><en-export><note><title>Tarif</title>'
            '<content><![CDATA[<en-note><div>un</div><div>şeker</div></en-note>]]></content>'
            '<created>20261031T140500Z</created><tag>mutfak</tag></note></en-export>')
    e = notes.parse_enex(enex)
    assert e[0]["title"] == "Tarif" and e[0]["tags"] == ["mutfak"] and "şeker" in e[0]["body"] and e[0]["date_ms"]
    r1, r2 = notes.run_evernote(enex, None), notes.run_evernote(enex, None)
    assert r1["notlar"] == r2["notlar"] == 1
    assert len(list((vault / "40-Kaynaklar/Notlar/evernote").glob("*.md"))) == 1
    assert notes.run_evernote(enex, None, dry_run=True)["yazıldı"] is False


def test_instagram_ve_x(tmp_path, con):
    ig = tmp_path / "ig"
    bozuk = "Merhaba çay".encode("utf-8").decode("latin-1")
    w(ig / "your_instagram_activity/messages/inbox/ali_123/message_1.json", {
        "title": "ali", "participants": [{"name": "ali"}],
        "messages": [{"sender_name": "ali", "timestamp_ms": 1793455500000, "content": bozuk},
                     {"sender_name": "ben", "timestamp_ms": 1793455600000, "photos": [{"uri": "x/p.jpg"}]}]})
    w(ig / "your_instagram_activity/media/posts_1.json", [
        {"media": [{"title": "Gün batımı", "creation_timestamp": 1793455500}]}])
    msgs, items = social.parse_instagram(ig, me="ben")
    assert msgs[0]["body"] == "Merhaba çay" and msgs[1]["from_addr"] == "me" and msgs[1]["attachments"] == ["p.jpg"]
    assert items[0]["title"] == "Gün batımı"
    a, b = social.run_instagram(ig, con), social.run_instagram(ig, con)
    assert (a["yeni"], b["yeni"]) == (3, 0)

    x = tmp_path / "x"
    tw = [{"tweet": {"id_str": "9", "full_text": "merhaba dünya", "created_at": "Sat Oct 31 14:05:00 +0000 2026"}},
          {"tweet": {"id_str": "10", "full_text": "RT @biri: x", "created_at": "Sun Nov 01 09:00:00 +0000 2026"}}]
    w(x / "data/tweets.js", "window.YTD.tweets.part0 = " + json.dumps(tw))
    its = social.parse_x(x)
    assert [i["kind"] for i in its] == ["tweet", "retweet"] and its[0]["date_ms"]
    a, b = social.run_x(x, con), social.run_x(x, con)
    assert (a["yeni"], b["yeni"]) == (2, 0)
