"""Paket A: görünüm uçları (pano, grafik, zaman çizelgesi, kişi, proje, arama, palet) — geçici kasada, sahte arama."""
import json
import time
from datetime import date, timedelta

import pytest

from sb import api_views, brain, chat, convstore, vault_ops, webroutes
from sb.webroutes import Ctx

TODAY = date.today()


def call(path, query=None, session=None, calendar=None, method="GET"):
    r = webroutes.find(method, path)
    assert r is not None, path
    code, body, _, _ = webroutes.call(r, Ctx(method, path, {}, query or {}, session=session or chat.Session(), calendar=calendar))
    return code, json.loads(body)


def note(vault, rel, fm="", body=""):
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{fm.strip()}\n---\n{body}" if fm else body, encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def vault(monkeypatch, tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(brain, "find", lambda q, k=10, **kw: [
        {"doc_id": "note:20-Projeler/Atlas.md", "kind": "note", "title": "Atlas", "ref": "20-Projeler/Atlas.md", "score": 0.03,
         "date": "2026-09-15", "text": "Atlas toplantı notu"},
        {"doc_id": "mail:main:7", "kind": "mail", "title": "Atlas teklifi", "ref": "7", "score": 0.02, "date": "2026-10-20", "text": "teklif"}][:k])
    monkeypatch.setattr(api_views, "_db_counts", lambda: {"mails": 12, "chunks": 340})
    api_views.reset_cache()
    due = (TODAY + timedelta(days=3)).isoformat()
    note(v, "20-Projeler/Atlas.md", "type: proje\nstatus: aktif\ndue: " + due + "\nupdated: 2026-10-30\nlocal_path: ~/x", """# Atlas

## Özet
Atlas bir deneme projesi. [[Ayşe Yılmaz]] ile yürütülür; bkz [[Kavram A]].

## Oturum günlüğü
<!-- sb:auto:oturumlar:start -->
#### 2026-10-29 — Kurulum
**Kararlar ve gerekçeleri:**
- SQLite seçildi çünkü hafif.

**Sorunlar:**
- yok
<!-- sb:auto:oturumlar:end -->

## Kararlar
- Python 3.12 kullanılacak

## Yapılacaklar
- [ ] Test yaz
- [ ]
""")
    note(v, "60-Kişiler/Ayşe Yılmaz.md", "type: kisi\nstatus: aktif\nphone: [0532 111 22 33]\nemail: ayse@example.com\ncompany: Acme\nrole: Mühendis\naliases: [Ayşe Hoca]", """# Ayşe Yılmaz
## Beyan
- 2026-10-01 (kullanıcı): Atlas'ta çalışıyor
- ~~yanlış~~ (reddedildi 2026-10-02)
## Çıkarım (onay bekliyor)
- 2026-10-03 (çıkarım): kahve sever
<!-- sb:auto:telefon:start -->
Toplam 0 SMS, 3 arama.
- 2026-10-30 19:41 arama (giden, 9 dk)
- 2026-10-25 15:53 arama (gelen, 0 dk)
<!-- sb:auto:telefon:end -->
<!-- sb:auto:mailler:start -->
- 2026-10-28 Teklif hakkında
<!-- sb:auto:mailler:end -->
""")
    note(v, "40-Kaynaklar/Kavramlar/Kavram A.md", "type: kavram\nupdated: 2026-10-10", "Kavram [[Atlas]] için")
    note(v, "90-Arşiv/60-Kişiler/Eski.md", "type: kisi", "[[Atlas]]")
    note(v, "_system/gizli.md", "type: x", "[[Atlas]]")
    note(v, "25-Görevler/Rapor yaz.md", f"type: gorev\nstatus: aktif\ndue: {TODAY.isoformat()}\nowner: Ayşe", "# Rapor yaz")
    note(v, "25-Görevler/Bitti.md", "type: gorev\nstatus: tamamlandi", "# Bitti")
    note(v, "00-Inbox/onay-bekleyenler.md", "type: inbox", "- [ ] [SINAV] Final | 2026-11-20 | kaynak: x\n- [x] eski\n")
    note(v, "00-Inbox/Dump/2026-10-31 10.md", "type: inbox", "hızlı not")
    note(v, f"50-Günlük/{TODAY.isoformat()}.md", "type: gunluk", "# gün\n## Yansıma\nİyi bir gündü.\n## Başka\nx")
    note(v, "40-Kaynaklar/Gizli.md", "type: kaynak\nvisibility: private", "[[Atlas]]")
    return v


def test_dashboard_sections():
    code, d = call("/api/v2/dashboard")
    assert code == 200
    assert set(d) >= {"greeting", "today", "due", "tasks", "recent", "inbox_count", "approvals", "stats", "suggestions", "reflection"}
    assert d["greeting"].endswith(("Ayşe", "kullanıcı")) or d["greeting"].split()[-1]
    assert [r["title"] for r in d["due"]][:2] == ["Rapor yaz", "Atlas"] and d["due"][0]["path"] == "25-Görevler/Rapor yaz.md"
    assert d["today"] == [{"time": "", "title": "Rapor yaz", "kind": "gorev"}]
    assert d["tasks"] == [{"text": "Rapor yaz", "path": "25-Görevler/Rapor yaz.md", "due": TODAY.isoformat()}]
    assert d["inbox_count"] == 1 and d["approvals"][0]["title"].startswith("[SINAV] Final")
    assert d["stats"]["notes"] >= 8 and d["stats"]["people"] == 1 and d["stats"]["projects"] == 1 and d["stats"]["chunks"] == 340
    assert d["reflection"] == {"text": "İyi bir gündü.", "date": TODAY.isoformat()}
    assert "path" in d["recent"][0] and "updated" in d["recent"][0] and d["suggestions"]


def test_dashboard_calendar_session_proposals_and_section_failure(monkeypatch):
    class Cal:
        def list_events(self, a, b):
            return [{"summary": "Toplantı", "start": {"dateTime": "2026-11-01T14:30:00+03:00"}}]
    s = chat.Session()
    chat.add_proposal(s, "unut", "Unut", "detay", lambda: "ok")
    d = call("/api/v2/dashboard", session=s, calendar=Cal())[1]
    assert {"time": "14:30", "title": "Toplantı", "kind": "takvim"} in d["today"]
    assert any(a.get("kind") == "unut" for a in d["approvals"])
    monkeypatch.setattr(api_views, "_dash_tasks", lambda e: 1 / 0)
    d = call("/api/v2/dashboard")[1]
    assert d["tasks"] == [] and d["due"]                    # bozuk bölüm boş, diğerleri sağlam


def test_graph_nodes_edges_and_exclusions():
    code, g = call("/api/v2/graph")
    ids = {n["id"] for n in g["nodes"]}
    assert code == 200 and "20-Projeler/Atlas.md" in ids and "60-Kişiler/Ayşe Yılmaz.md" in ids
    assert not any(i.startswith(("90-Arşiv", "_system")) for i in ids)
    n = {x["id"]: x for x in g["nodes"]}
    assert n["20-Projeler/Atlas.md"]["kind"] == "proje" and n["60-Kişiler/Ayşe Yılmaz.md"]["kind"] == "kisi" and n["20-Projeler/Atlas.md"]["size"] >= 2
    assert {"s", "t", "w"} == set(g["edges"][0]) and all(e["s"] in ids and e["t"] in ids for e in g["edges"])
    g = call("/api/v2/graph", {"center": "60-Kişiler/Ayşe Yılmaz.md", "depth": "1"})[1]
    assert {x["id"] for x in g["nodes"]} == {"60-Kişiler/Ayşe Yılmaz.md", "20-Projeler/Atlas.md"}
    g2 = call("/api/v2/graph", {"center": "60-Kişiler/Ayşe Yılmaz.md", "depth": "2"})[1]
    assert "40-Kaynaklar/Kavramlar/Kavram A.md" in {x["id"] for x in g2["nodes"]}
    g3 = call("/api/v2/graph", {"kinds": "kisi,proje"})[1]
    assert {x["kind"] for x in g3["nodes"]} == {"kisi", "proje"}
    assert len(call("/api/v2/graph", {"limit": "2"})[1]["nodes"]) == 2
    assert call("/api/v2/graph", {"center": "../x.md"})[0] == 404
    assert call("/api/v2/graph", {"limit": "abc"})[0] == 400


def test_timeline_merges_search_and_notes():
    code, rows = call("/api/v2/timeline", {"q": "atlas"})
    assert code == 200 and rows == sorted(rows, key=lambda r: r["date"], reverse=True)
    assert {"date", "title", "kind", "snippet"} <= set(rows[0])
    kinds = {r["kind"] for r in rows}
    assert "mail" in kinds and any(r.get("path") == "20-Projeler/Atlas.md" for r in rows)
    assert sum(r.get("path") == "20-Projeler/Atlas.md" for r in rows) == 1                 # aynı not iki kez yok
    assert all(r["date"] >= "2026-10-01" for r in call("/api/v2/timeline", {"q": "atlas", "from": "2026-10-01"})[1])
    assert {r["kind"] for r in call("/api/v2/timeline", {"q": "atlas", "kinds": "mail"})[1]} == {"mail"}
    assert call("/api/v2/timeline")[0] == 200                                              # q'suz: not tarihleri


def test_person_view():
    code, p = call("/api/v2/person", {"name": "Ayşe Hoca"})              # takma adla bulunur
    assert code == 200 and p["name"] == "Ayşe Yılmaz" and p["path"] == "60-Kişiler/Ayşe Yılmaz.md"
    assert p["aliases"] == ["Ayşe Hoca"] and p["company"] == "Acme" and p["role"] == "Mühendis"
    assert p["phones"] == ["0532 111 22 33"] and p["emails"] == ["ayse@example.com"] and p["linkedin"] == ""
    assert p["last_contact"] == "2026-10-30 19:41" and p["chats"][0] == {"date": "2026-10-30 19:41", "snippet": "arama (giden, 9 dk)"}
    assert p["mail"] == ["2026-10-28 Teklif hakkında"]
    assert p["projects"] == [{"name": "Atlas", "path": "20-Projeler/Atlas.md"}]
    assert p["facts"] == {"declared": ["2026-10-01 (kullanıcı): Atlas'ta çalışıyor"], "inferred": ["2026-10-03 (çıkarım): kahve sever"]}
    assert call("/api/v2/person", {"name": "Yok Kişi"})[0] == 404


def test_project_view():
    code, p = call("/api/v2/project", {"name": "atlas"})
    assert code == 200 and p["name"] == "Atlas" and p["status"] == "aktif" and p["path"] == "20-Projeler/Atlas.md"
    assert p["summary"].startswith("Atlas bir deneme")
    assert "Python 3.12 kullanılacak" in p["decisions"] and any("SQLite" in d for d in p["decisions"])
    assert p["open"] == ["Test yaz"]
    assert p["people"] == [{"name": "Ayşe Yılmaz", "path": "60-Kişiler/Ayşe Yılmaz.md"}]
    assert p["sessions"] == [{"date": "2026-10-29", "title": "Kurulum"}]
    assert {"files", "timeline"} <= set(p)
    assert call("/api/v2/project", {"name": "yok"})[0] == 404


def test_search_returns_sources():
    code, rows = call("/api/v2/search", {"q": "atlas", "k": "1"})
    assert code == 200 and len(rows) == 1 and rows[0]["kind"] == "note" and rows[0]["url"].startswith("obsidian://open?vault=SecondBrain")
    assert call("/api/v2/search", {"q": ""})[1] == []


def test_palette():
    convstore.save({**convstore.ensure("pc"), "title": "Atlas planlama sohbeti", "messages": []})
    code, rows = call("/api/v2/palette", {"q": "atlas"})
    assert code == 200 and len(rows) <= 20 and all({"type", "label", "action"} <= set(r) for r in rows)
    by = {r["type"]: r for r in rows}
    assert by["project"]["action"] == {"view": "project", "params": {"name": "Atlas"}}
    assert by["conv"]["action"] == {"sid": "pc"}
    pr = call("/api/v2/palette", {"q": "ayse hoca"})[1]                          # takma ad + aksan duyarsız
    assert pr[0]["type"] == "person" and pr[0]["action"]["params"]["name"] == "Ayşe Yılmaz"
    cm = call("/api/v2/palette", {"q": "/not"})[1]
    assert cm[0] == {"type": "command", "label": "/not", "sub": "Gelen kutusuna hızlı not", "action": {"cmd": "/not"}}
    assert any(r["type"] == "note" and r["action"] == {"path": "40-Kaynaklar/Kavramlar/Kavram A.md"} for r in call("/api/v2/palette", {"q": "kavram"})[1])
    empty = call("/api/v2/palette")[1]
    assert 0 < len(empty) <= 20 and {r["type"] for r in empty} >= {"command", "conv"}


def test_index_cache_detects_changes_and_is_fast(vault):
    for i in range(300):
        note(vault, f"40-Kaynaklar/Notlar/n{i}.md", "type: kaynak\nupdated: 2026-10-01", f"[[Atlas]] {i}")
    api_views.reset_cache()
    call("/api/v2/dashboard")
    t = time.time()
    call("/api/v2/dashboard")
    call("/api/v2/palette", {"q": "n1"})
    call("/api/v2/graph")
    assert time.time() - t < 1.0
    note(vault, "20-Projeler/Yeni.md", "type: proje\nstatus: aktif", "# Yeni")
    api_views.reset_cache()                                                      # TTL'yi beklemeden
    assert any(r["label"] == "Yeni" for r in call("/api/v2/palette", {"q": "yeni"})[1])
    # disk önbelleği: bellek sıfırlanınca da değişmeyen dosyalar yeniden okunmaz
    reads = []
    orig = api_views._read_entry
    api_views._read_entry = lambda *a, **k: (reads.append(a[1]) or orig(*a, **k))
    try:
        api_views.reset_cache()
        call("/api/v2/palette", {"q": "n1"})
    finally:
        api_views._read_entry = orig
    assert reads == []
