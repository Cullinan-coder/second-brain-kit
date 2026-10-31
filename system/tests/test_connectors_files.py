"""Dosya tabanlı bağlayıcılar: ayrıştırma, kopyasız yeniden içe aktarma, süzgeçler, detect, CLI."""
import json
import sqlite3
import time
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from sb import maildb
from sb.connectors import academic, browser, detect, kindle, rss, spotify, telegram, whatsapp, youtube
from sb import connectors

FX = Path(__file__).parent / "fixtures" / "connectors"
DAY = 86_400_000


@pytest.fixture
def con(tmp_path):
    c = maildb.connect(tmp_path / "mail.db")
    yield c
    c.close()


def count(con, table):
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def twice(run, path, con, **kw):
    a = run(path, con, **kw)
    b = run(path, con, **kw)
    return a, b


# ---- WhatsApp
def test_whatsapp_android():
    rows = whatsapp.parse(FX / "WhatsApp Chat with Deniz.txt", me="Ayşe")
    assert {r["thread_id"] for r in rows} == {"Deniz"}
    bodies = [r["body"] for r in rows]
    assert not any("şifrelidir" in b or "grup oluşturdu" in b for b in bodies)
    multi = next(r for r in rows if r["from_name"] == "Ayşe")
    assert multi["from_addr"] == "me" and multi["body"] == "Evet, saat 10:00\nsatır iki burada\nve satır üç"
    assert sum(1 for r in rows if r["body"] == "ok") == 2  # aynı dakikadaki aynı mesaj kopya sayılmaz
    assert len({r["id"] for r in rows}) == len(rows)
    media = [r for r in rows if r["attachments"]]
    assert len(media) == 2 and all(m["body"] == "" for m in media)
    assert "IMG-20261031-WA0001.jpg" in media[1]["attachments"]
    assert any("gizlendi" in b for b in bodies)  # IBAN maskelendi


def test_whatsapp_ios_ve_12_saat():
    rows = whatsapp.parse(FX / "WhatsApp Sohbeti - Kerem.txt")
    assert rows[0]["thread_id"] == "Kerem" and rows[1]["body"] == "Nasılsın?\nİyi misin"
    assert rows[2]["attachments"] == ["00000012-PHOTO-2026-10-31.jpg"] and rows[0]["from_addr"] == "Kerem"
    rows = whatsapp.parse(FX / "WhatsApp Chat with Mina.txt")
    from datetime import datetime
    assert datetime.fromtimestamp(rows[0]["date_ms"] / 1000) == datetime(2026, 10, 31, 14, 5)
    assert datetime.fromtimestamp(rows[2]["date_ms"] / 1000) == datetime(2026, 11, 1, 0, 30)
    assert rows[2]["attachments"] == ["Media omitted"] and rows[2]["body"] == "late night"


def test_whatsapp_zip_ve_tekrar(tmp_path, con):
    z = tmp_path / "WhatsApp Chat - Zeynep.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("_chat.txt", "31.10.2026 14:05 - Zeynep: selam\n")
    assert whatsapp.parse(z)[0]["thread_id"] == "Zeynep"
    a, b = twice(whatsapp.run, FX / "WhatsApp Chat with Deniz.txt", con)
    assert a["yeni"] == a["okunan"] > 0 and b["yeni"] == 0 and b["okunan"] == a["okunan"]
    assert count(con, "messages") == a["okunan"]


def test_whatsapp_dry_run_yazmaz(con):
    r = whatsapp.run(FX / "WhatsApp Chat with Deniz.txt", con, dry_run=True)
    assert r["yeni"] > 0 and r["ornek"] == ["Deniz"] and r["tarih_min"] == "2026-10-31" and count(con, "messages") == 0


# ---- Telegram
def test_telegram(con):
    rows = telegram.parse(FX / "telegram_result.json")
    assert len(rows) == 4  # servis mesajı atlanır
    link = next(r for r in rows if r["from_name"] == "Ayşe")
    assert link["body"] == "Bak şu linke https://example.com ve önemli" and link["from_addr"] == "me"
    assert rows[2]["attachments"] == ["photos/photo_1.jpg"]
    assert {r["thread_id"] for r in rows} == {"Arda", "Grup"} and {r["account"] for r in rows} == {"telegram"}
    a, b = twice(telegram.run, FX / "telegram_result.json", con)
    assert a["yeni"] == 4 and b["yeni"] == 0


def test_telegram_tek_sohbet(tmp_path):
    p = tmp_path / "result.json"
    p.write_text(json.dumps({"name": "X", "id": 1, "messages": [
        {"id": 1, "type": "message", "date": "2026-10-30T10:01:00", "from": "A", "from_id": "user1", "text": "m"}]}))
    assert len(telegram.parse(p)) == 1 and detect(p) == "telegram"


# ---- Kindle
def test_kindle(con):
    rows = kindle.parse(FX / "My Clippings.txt")
    assert [r["kind"] for r in rows] == ["highlight", "note", "bookmark", "highlight", "note"]
    h = rows[0]
    assert h["title"] == "Yapay Zeka" and h["meta"] == {"author": "Stuart Russell", "location": "100-102", "page": "12"}
    assert h["body"] == "Amaçlar insanlardan gelmeli."
    tr = rows[3]
    assert tr["meta"]["location"] == "200-203" and tr["title"] == "Sefiller" and tr["meta"]["author"] == "Victor Hugo"
    assert rows[4]["meta"]["page"] == "15"
    from datetime import datetime
    assert datetime.fromtimestamp(tr["date_ms"] / 1000) == datetime(2026, 10, 31, 14, 5)
    assert datetime.fromtimestamp(h["date_ms"] / 1000) == datetime(2026, 10, 31, 14, 5)
    a, b = twice(kindle.run, FX / "My Clippings.txt", con)
    assert a["yeni"] == 5 and b["yeni"] == 0


# ---- YouTube
def test_youtube(con):
    rows = youtube.parse(FX / "watch-history.json")
    assert [r["title"] for r in rows] == ["Python Tutorial", "Türkçe Video"]  # silinmiş video atlanır
    assert rows[0]["meta"] == {"channel": "Kanal A"} and rows[0]["kind"] == "watch"
    h = youtube.parse(FX / "watch-history.html")
    assert h[0]["title"] == "HTML & Video" and h[0]["meta"]["channel"] == "Kanal H" and h[0]["url"].endswith("v=h1")
    from datetime import datetime, timezone
    assert h[0]["date_ms"] == int(datetime(2026, 10, 31, 11, 5, tzinfo=timezone.utc).timestamp() * 1000)
    subs = youtube.parse(FX / "subscriptions.csv")
    assert [s["title"] for s in subs] == ["Kanal A", "Kanal B"] and subs[0]["kind"] == "subscription"
    a, b = twice(youtube.run, FX / "subscriptions.csv", con)
    assert a["yeni"] == 2 and b["yeni"] == 0


# ---- Spotify
def test_spotify(con):
    rows = spotify.parse(FX / "Streaming_History_Audio_2026_0.json")
    assert len(rows) == 1  # 5 sn ve parçasız kayıt atlanır
    assert rows[0]["meta"] == {"artist": "Sanatçı X", "album": "Albüm Y", "ms": 200000}
    assert rows[0]["url"] == "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC"
    short = spotify.parse(FX / "StreamingHistory0.json")
    assert [r["title"] for r in short] == ["Kısa Biçim"]  # 29.999 ms atlanır
    assert len(spotify.parse(FX)) == 2  # klasör
    a, b = twice(spotify.run, FX / "StreamingHistory0.json", con)
    assert a["yeni"] == 1 and b["yeni"] == 0


# ---- Tarayıcı
def now_chromium_us(days_ago=0):
    return (int(time.time() * 1000) - days_ago * DAY + browser.CHROMIUM_EPOCH_MS) * 1000


def make_chromium(path, entries):
    db = sqlite3.connect(path)
    db.executescript("CREATE TABLE urls(id INTEGER PRIMARY KEY, url TEXT, title TEXT, visit_count INT, last_visit_time INT);"
                     "CREATE TABLE visits(id INTEGER PRIMARY KEY, url INT, visit_time INT);")
    ids = {}
    for url, title, ago in entries:
        if url not in ids:
            ids[url] = len(ids) + 1
            db.execute("INSERT INTO urls VALUES (?,?,?,1,?)", (ids[url], url, title, now_chromium_us(ago)))
        db.execute("INSERT INTO visits(url, visit_time) VALUES (?,?)", (ids[url], now_chromium_us(ago)))
    db.commit()
    db.close()


ENTRIES = [
    ("https://docs.python.org/3/", "Python docs", 1),
    ("https://docs.python.org/3/", "Python docs", 2),  # ikinci satır: aynı URL tek item olmalı
    ("https://example.com/a?q=1", "Örnek", 3),
    ("https://example.com/cb?access_token=abc", "Token", 1),
    ("https://example.com/login?sessionid=1", "Oturum", 1),
    ("https://example.com/o?code=xyz", "Kod", 1),
    ("https://example.com/#access_token=zzz", "Parça", 1),
    ("chrome://settings", "Ayarlar", 1),
    ("edge://history", "Geçmiş", 1),
    ("about:blank", "Boş", 1),
    ("file:///C:/x.txt", "Dosya", 1),
    ("https://www.garantibbva.com.tr/x", "Banka", 1),
    ("https://online.isbank.com.tr/", "Banka2", 1),
    ("https://giris.turkiye.gov.tr/", "eDevlet", 1),
    ("https://www.somebank.com/", "Banka3", 1),
    ("https://old.example.org/", "Eski", 400),
]


def test_url_suzgeci():
    assert browser.keep_url("https://example.com/?page=2&zipcode=34")
    assert not browser.keep_url("https://example.com/?password=1")
    assert not browser.keep_url("https://enpara.com/")


def test_chromium_gecmis(tmp_path, con):
    h = tmp_path / "Edge" / "History"
    h.parent.mkdir()
    make_chromium(h, ENTRIES)
    rows = browser.parse(h, days=30)
    assert sorted(r["title"] for r in rows) == ["Python docs", "Örnek"]
    py = next(r for r in rows if r["title"] == "Python docs")
    assert py["meta"]["visits"] == 2 and py["meta"]["browser"] == "edge"
    assert abs(py["date_ms"] - (time.time() * 1000 - DAY)) < 60_000  # en son ziyaret
    assert len(browser.parse(h, days=1000)) == 3
    r = browser.run(h, con, dry_run=True, days=30)
    assert r["okunan"] == 2 and count(con, "items") == 0
    a, b = twice(browser.run, h, con, days=30)
    assert a["yeni"] == 2 and b["yeni"] == 0 and count(con, "items") == 2


def test_chromium_bookmarks(tmp_path):
    p = tmp_path / "Bookmarks"
    p.write_text(json.dumps({"roots": {"bookmark_bar": {"type": "folder", "name": "Bar", "children": [
        {"type": "url", "name": "İyi", "url": "https://example.com/ok", "date_added": "13400000000000000"},
        {"type": "folder", "name": "Alt", "children": [
            {"type": "url", "name": "Banka", "url": "https://www.akbank.com/", "date_added": "1"},
            {"type": "url", "name": "Derin", "url": "https://example.com/d", "date_added": "1"}]}]}}}))
    rows = browser.parse(p)
    assert [(r["title"], r["kind"]) for r in rows] == [("İyi", "bookmark"), ("Derin", "bookmark")]
    assert rows[1]["meta"]["folder"] == "Bar/Alt" and detect(p) == "browser"


def test_firefox(tmp_path):
    p = tmp_path / "places.sqlite"
    db = sqlite3.connect(p)
    now_us = int(time.time() * 1000) * 1000
    db.executescript("CREATE TABLE moz_places(id INTEGER PRIMARY KEY, url TEXT, title TEXT, visit_count INT, last_visit_date INT);"
                     "CREATE TABLE moz_historyvisits(id INTEGER PRIMARY KEY, place_id INT, visit_date INT);"
                     "CREATE TABLE moz_bookmarks(id INTEGER PRIMARY KEY, type INT, fk INT, title TEXT, dateAdded INT);")
    db.execute("INSERT INTO moz_places VALUES (1,'https://mozilla.org/','Mozilla',1,?)", (now_us,))
    db.execute("INSERT INTO moz_places VALUES (2,'https://x.com/?token=1','Gizli',1,?)", (now_us,))
    db.execute("INSERT INTO moz_historyvisits(place_id, visit_date) VALUES (1,?),(1,?),(2,?)", (now_us, now_us, now_us))
    db.execute("INSERT INTO moz_bookmarks VALUES (1,1,1,'Yer imi',?)", (now_us,))
    db.commit()
    db.close()
    rows = browser.parse(p, days=7)
    assert sorted((r["kind"], r["title"]) for r in rows) == [("bookmark", "Yer imi"), ("visit", "Mozilla")]
    assert next(r for r in rows if r["kind"] == "visit")["meta"] == {"browser": "firefox", "visits": 2}
    assert detect(p) == "browser"


def test_discover_bos_ortam(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "L"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "R"))
    assert browser.discover() == []
    prof = tmp_path / "L" / "Microsoft" / "Edge" / "User Data" / "Default"
    prof.mkdir(parents=True)
    (prof / "History").write_bytes(b"x")
    found = browser.discover()
    assert [(d["tarayici"], d["profil"], d["tur"]) for d in found] == [("edge", "Default", "gecmis")]


# ---- RSS / arXiv
def test_rss_ve_atom(tmp_path, monkeypatch, con):
    cfg = tmp_path / "rss.yaml"
    cfg.write_text("feeds:\n  - {name: Blog, url: http://f/rss}\n  - http://f/atom\n")
    monkeypatch.setattr(rss, "CONFIG", cfg)
    pages = {"http://f/rss": (FX / "feed_rss.xml").read_bytes(), "http://f/atom": (FX / "feed_atom.xml").read_bytes()}
    monkeypatch.setattr(rss, "_fetch", lambda u: pages[u])
    rows = rss.parse()
    assert [r["title"] for r in rows] == ["Yazı Bir", "Yazı İki", "Atom Yazı"]
    assert rows[0]["body"] == "Özet bir" and rows[0]["meta"] == {"feed": "Blog"} and rows[2]["url"] == "https://atom.example/a1"
    assert rows[0]["date_ms"] > rows[1]["date_ms"] > 0
    a, b = twice(rss.run, None, con)
    assert a["yeni"] == 3 and b["yeni"] == 0


def test_rss_akis_yok(tmp_path, monkeypatch, con):
    monkeypatch.setattr(rss, "CONFIG", tmp_path / "yok.yaml")
    monkeypatch.setattr(rss, "_fetch", lambda u: pytest.fail("ağa çıkmamalı"))
    r = rss.run(None, con)
    assert r["okunan"] == 0 and "akış yok" in r["not"] and not (tmp_path / "yok.yaml").exists()


def test_arxiv(tmp_path, monkeypatch, con):
    cfg = tmp_path / "rss.yaml"
    cfg.write_text("arxiv:\n  - 'cat:cs.AI AND ti:attention'\n")
    monkeypatch.setattr(rss, "CONFIG", cfg)
    seen = []
    monkeypatch.setattr(rss, "_fetch", lambda u: seen.append(u) or (FX / "arxiv_feed.xml").read_bytes())
    rows = academic.parse_arxiv_config()
    assert seen[0].startswith("http://export.arxiv.org/api/query?search_query=cat%3Acs.AI")
    assert rows[0]["id"] == "2610.01234" and rows[0]["title"] == "Dikkat Mekanizmaları Üzerine"
    assert rows[0]["meta"]["authors"] == ["Ada Lovelace", "Alan Turing"] and rows[0]["body"] == "Bir özet metni."
    a, b = twice(academic.run_arxiv, None, con)
    assert a["yeni"] == 1 and b["yeni"] == 0


# ---- Zotero / BibTeX
def test_bibtex(con):
    rows = academic.parse_bibtex(FX / "refs.bib")
    assert [r["title"] for r in rows] == ["Notes on the Analytical Engine", "The Art of Computer Programming"]
    assert rows[0]["meta"]["authors"] == ["Lovelace, Ada", "Babbage, Charles"] and rows[0]["url"] == "https://doi.org/10.1000/xyz"
    assert rows[0]["body"] == "Bir özet, virgüllü." and rows[1]["source"] == "bibtex"
    a, b = twice(academic.run, FX / "refs.bib", con)
    assert a["yeni"] == 2 and b["yeni"] == 0


def test_zotero(tmp_path, con):
    p = tmp_path / "zotero.sqlite"
    db = sqlite3.connect(p)
    db.executescript("""
    CREATE TABLE itemTypes(itemTypeID INTEGER PRIMARY KEY, typeName TEXT);
    CREATE TABLE items(itemID INTEGER PRIMARY KEY, itemTypeID INT, key TEXT);
    CREATE TABLE fields(fieldID INTEGER PRIMARY KEY, fieldName TEXT);
    CREATE TABLE itemDataValues(valueID INTEGER PRIMARY KEY, value TEXT);
    CREATE TABLE itemData(itemID INT, fieldID INT, valueID INT);
    CREATE TABLE creators(creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT);
    CREATE TABLE itemCreators(itemID INT, creatorID INT, creatorTypeID INT, orderIndex INT);
    CREATE TABLE deletedItems(itemID INTEGER PRIMARY KEY);
    INSERT INTO itemTypes VALUES (1,'journalArticle'),(2,'attachment');
    INSERT INTO fields VALUES (1,'title'),(2,'url'),(3,'date'),(4,'abstractNote');
    INSERT INTO items VALUES (1,1,'KEY1'),(2,2,'KEY2'),(3,1,'KEY3');
    INSERT INTO itemDataValues VALUES (1,'Makale Bir'),(2,'https://p.example/1'),(3,'2025-03-04 3/4/2025'),(4,'Özet'),(5,'Silinmiş');
    INSERT INTO itemData VALUES (1,1,1),(1,2,2),(1,3,3),(1,4,4),(2,1,1),(3,1,5);
    INSERT INTO creators VALUES (1,'Ada','Lovelace');
    INSERT INTO itemCreators VALUES (1,1,1,0);
    INSERT INTO deletedItems VALUES (3);
    """)
    db.commit()
    db.close()
    rows = academic.parse(p)
    assert len(rows) == 1
    r = rows[0]
    assert (r["id"], r["title"], r["url"], r["body"], r["source"]) == ("KEY1", "Makale Bir", "https://p.example/1", "Özet", "zotero")
    assert r["meta"]["authors"] == ["Ada Lovelace"] and r["date_ms"] > 0
    assert detect(p) == "zotero"
    a, b = twice(academic.run, p, con)
    assert a["yeni"] == 1 and b["yeni"] == 0


# ---- detect + CLI
def test_detect(tmp_path):
    cases = {"WhatsApp Chat with Deniz.txt": "whatsapp", "WhatsApp Sohbeti - Kerem.txt": "whatsapp", "My Clippings.txt": "kindle",
             "watch-history.json": "youtube", "watch-history.html": "youtube", "subscriptions.csv": "youtube",
             "Streaming_History_Audio_2026_0.json": "spotify", "StreamingHistory0.json": "spotify",
             "telegram_result.json": "telegram", "refs.bib": "bibtex"}
    for name, want in cases.items():
        assert detect(FX / name) == want, name
    assert detect(FX) == "spotify" and detect(tmp_path / "yok.txt") is None
    other = tmp_path / "notlar.txt"
    other.write_text("sıradan metin", encoding="utf-8")
    assert detect(other) is None
    z = tmp_path / "x.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("_chat.txt", "a")
    assert detect(z) == "whatsapp"


def cli_args(**kw):
    base = dict(source="auto", path=None, me=None, days=365, dry_run=False, discover=False)
    return SimpleNamespace(**{**base, **kw})


def test_cli_dry_run(tmp_path, monkeypatch, capsys):
    import sb.config
    db = tmp_path / "mail.db"
    monkeypatch.setattr(sb.config, "MAIL_DB", db)
    assert connectors.cli(cli_args(path=str(FX / "My Clippings.txt"), dry_run=True)) == 0
    out = capsys.readouterr().out
    assert "algılanan kaynak: kindle" in out and "okunan 5" in out and "yeni olacak 5" in out
    assert "2026-10-31" in out and "Yapay Zeka" in out and "Amaçlar insanlardan" not in out and "dry-run" in out
    con = maildb.connect(db)
    assert count(con, "items") == 0
    con.close()
    assert connectors.cli(cli_args(source="kindle", path=str(FX / "My Clippings.txt"))) == 0
    assert "yeni 5" in capsys.readouterr().out
    assert connectors.cli(cli_args(source="kindle")) == 1
    assert connectors.cli(cli_args(source="nope", path="x")) == 1


def test_cli_alt_komut(tmp_path, monkeypatch, capsys):
    import sb.config
    from sb.__main__ import main
    monkeypatch.setattr(sb.config, "MAIL_DB", tmp_path / "mail.db")
    assert main(["import", "auto", str(FX / "refs.bib"), "--dry-run"]) == 0
    assert "bibtex: okunan 2" in capsys.readouterr().out


def test_browser_drops_login_and_token_urls():
    from sb.connectors.browser import keep_url
    bad = ["https://accounts.google.com/o/oauth2/auth?client_id=1&state=x",
           "https://www.netflix.com/tr-en/login?serverState=abc",
           "https://www.google.com/url?q=https://site.com/reset_password?nick%3Dx%26token%3Dabc",
           "https://business.facebook.com/business/loginpage/?next=https%3A%2F%2Fx%2F%3Ftoken%3Dy",
           "https://photoshop.adobe.com/#old_hash=&from_ims=true?client_id=PS&api=logout",
           "https://huggingface.co/settings/tokens/new",
           "https://myaccount.google.com/verification/selfie/precollection?next=x"]
    good = ["https://www.youtube.com/watch?v=abc", "https://github.com/user/repo", "https://www.google.com/search?q=laravel+queue"]
    assert not any(keep_url(u) for u in bad) and all(keep_url(u) for u in good)


def test_takeout_activity_gemini_keep(tmp_path):
    import json
    import zipfile
    from sb.connectors import takeout
    cell = ('<div class="outer-cell mdl-cell"><div class="mdl-grid"><div class="header-cell"><p class="mdl-typography--title">{p}<br></p></div>'
            '<div class="content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1">{b}</div><div class="content-cell x"></div></div></div>')
    gem = cell.format(p="Gemini Uygulamaları", b="Docker LLM arayüzü adı neydi sorgusuna yanıt istendi<br>31 Eki 2026 02:30:22 GMT+03:00<br><p>Open WebUI</p><br>")
    yt = cell.format(p="YouTube", b='<a href="https://www.youtube.com/channel/X">Kanal</a> abonesi oldunuz<br>30 Tem 2024 22:40:22 GMT+03:00<br>')
    login = cell.format(p="Chrome", b='<a href="https://accounts.google.com/o/oauth2/auth?client_id=1">Giriş</a> sayfasını ziyaret ettiniz<br>1 Eki 2026 10:00:00 GMT+03:00<br>')
    z = tmp_path / "takeout-1.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("Takeout/Etkinliğim/Gemini Uygulamaları/Etkinliğim.html", f"<html><body>{gem}</body></html>")
        f.writestr("Takeout/Etkinliğim/YouTube/Etkinliğim.html", f"<html><body>{yt}</body></html>")
        f.writestr("Takeout/Etkinliğim/Chrome/Etkinliğim.html", f"<html><body>{login}</body></html>")
        f.writestr("Takeout/Keep/a.json", json.dumps({"title": "Alışveriş", "textContent": "süt", "isTrashed": False,
                                                       "userEditedTimestampUsec": 1767225600000000, "labels": [{"name": "Ev"}]}))
        f.writestr("Takeout/Keep/b.json", json.dumps({"title": "Çöp", "textContent": "x", "isTrashed": True}))
        f.writestr("Takeout/Chrome/Tarih.json", json.dumps({"Browser History": [
            {"title": "Laravel", "url": "https://laravel.com/docs", "time_usec": 1767225600000000},
            {"title": "Giriş", "url": "https://site.com/login?token=x", "time_usec": 1767225600000000}]}))
    g = takeout.gemini_convs(zipfile.ZipFile(z).read("Takeout/Etkinliğim/Gemini Uygulamaları/Etkinliğim.html").decode())
    assert g[0]["turns"] == [("user", "Docker LLM arayüzü adı neydi"), ("assistant", "Open WebUI")]
    out = takeout.run([str(z)], None, account="side", dry_run=True)
    assert out["gemini"] == 1 and out["keep"] == 1 and out["browser"] == 1 and out["activity"] == 1   # giriş adresi ve çöp alınmadı
