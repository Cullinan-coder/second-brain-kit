import json
from datetime import date

import pytest
import yaml

from sb import api_career, career, config, llm, vault_ops, webroutes
from sb.webroutes import ApiError, Ctx

TODAY = date(2026, 11, 1)


def _ctx(method="GET", **kw):
    data = kw.pop("data", {})
    return Ctx(method=method, path="/x", data=data, query={k: str(v) for k, v in kw.items()})


@pytest.fixture
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    (v / "20-Projeler").mkdir(parents=True)
    (v / "30-Kariyer").mkdir()
    (v / "60-Kişiler").mkdir()
    d = v / "10-Dersler" / "YPZ201 Veri Yapıları"
    d.mkdir(parents=True)
    (d / "YPZ201 Veri Yapıları.md").write_text("---\ntype: ders\ncode: YPZ201\n---\n# YPZ201\n\nDiziler ve listeler.\n", encoding="utf-8")
    (v / "20-Projeler" / "Site Acme.md").write_text(
        "---\ntype: proje\nstatus: aktif\nclient: Acme\nekip: ['[[Ali Veli]]', Ayşe]\n---\n# Acme sitesi\n", encoding="utf-8")
    (v / "20-Projeler" / "Gizli.md").write_text("---\ntype: proje\nvisibility: private\n---\n# Gizli iş\n", encoding="utf-8")
    (v / "60-Kişiler" / "Can Acme.md").write_text("---\ntype: kisi\nmusteri: true\ncompany: Acme\nemail: can@acme.com\n---\n# Can\n", encoding="utf-8")
    (v / "60-Kişiler" / "Ali Veli.md").write_text("---\ntype: kisi\nemail: ali@x.com\n---\n# Ali\n", encoding="utf-8")
    (v / "60-Kişiler" / "Rastgele.md").write_text("---\ntype: kisi\n---\n# R\n", encoding="utf-8")
    (v / "30-Kariyer" / "Burs.md").write_text("---\ntype: basvuru\nstatus: mulakat\ndue: 2026-12-01\n---\n# Burs\n", encoding="utf-8")
    (v / "30-Kariyer" / "Sözleşme Acme.md").write_text("---\ntype: sozlesme\nbitis: 2026-11-20\n---\n# S\n", encoding="utf-8")
    (v / "30-Kariyer" / "Sözleşme Uzun.md").write_text("---\ntype: sozlesme\nbitis: 2027-06-01\n---\n# S2\n", encoding="utf-8")
    sysdir = v / "_system"
    (sysdir / "config").mkdir(parents=True)
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(config, "SYSTEM", sysdir)
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    monkeypatch.setattr(config, "MAIL_DB", tmp_path / "yok.db")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "")
    return v


def _maildb(tmp_path, monkeypatch):
    from sb import maildb
    db = tmp_path / "mail.db"
    con = maildb.connect(db)
    ms = lambda y, m, d: int(__import__("datetime").datetime(y, m, d, 12).timestamp() * 1000)
    con.execute("INSERT INTO messages (account,id,date_ms,from_addr,to_addrs,subject) VALUES ('main','1',?,'can@acme.com','me@x.com','Merhaba')", (ms(2026, 10, 20),))
    for i, (d, amt) in enumerate([((2026, 9, 5), 100.0), ((2026, 9, 20), 50.5), ((2026, 10, 2), 200.0)]):
        maildb.insert_item(con, {"source": "invoice", "id": f"i{i}", "date_ms": ms(*d), "kind": "invoice", "title": "f",
                                 "meta": {"vendor": "Acme", "amount": amt, "currency": "TRY"}})
    con.commit()
    con.close()
    monkeypatch.setattr(config, "MAIL_DB", db)


def test_crm_and_finance(vault, tmp_path, monkeypatch):
    assert [r["name"] for r in career.crm()] == ["Can Acme"]        # mail.db yok: hata yok
    _maildb(tmp_path, monkeypatch)
    r = career.crm()[0]
    assert r["last_contact"] == "2026-10-20" and r["invoice_total"] == {"TRY": 350.5}
    assert r["open_jobs"][0]["title"] == "Site Acme"
    f = career.finance(TODAY)
    assert [m["month"] for m in f["months"]] == ["2026-09", "2026-10"] and f["months"][0]["totals"] == {"TRY": 150.5}
    assert f["reminders"][0] == {"date": "2026-11-17", "kind": "geçici vergi", "days_left": 16}
    assert {"2026-11-26", "2026-12-26"} <= {x["date"] for x in f["reminders"]}
    assert api_career._crm(_ctx())[0]["name"] == "Can Acme"


def test_quote_and_time(vault):
    r = career.write_quote("Acme A.Ş.", [{"desc": "Site | tasarım", "qty": 2, "price": 100}, {"desc": "Bakım", "qty": 1, "price": 50.5}], "try", TODAY)
    assert r["total"] == 250.5 and r["path"].startswith("30-Kariyer/Teklifler/2026-11-01")
    txt = (vault / r["path"]).read_text(encoding="utf-8")
    assert "250.50 TRY" in txt and "gönderilmedi" in txt and "status: taslak" in txt
    r2 = career.write_quote("Acme A.Ş.", [{"desc": "x", "qty": 1, "price": 1}], today=TODAY)
    assert r2["path"] != r["path"]                                  # üzerine yazmaz
    with pytest.raises(ApiError) as e:
        api_career._quote(_ctx("POST", data={"client": "X", "items": [{"desc": "a", "qty": 0, "price": 1}]}))
    assert e.value.code == 400
    api_career._time(_ctx("POST", data={"project": "Acme", "minutes": 90, "note": "tasarım"}))
    api_career._time(_ctx("POST", data={"project": "Acme", "minutes": 30}))
    api_career._time(_ctx("POST", data={"project": "Diğer", "minutes": 60}))
    rep = api_career._time_report(_ctx(project="acme"))
    assert rep["minutes"] == 120 and rep["hours"] == 2.0 and "tasarım" in rep["text"]
    assert career.time_report(month=date.today().strftime("%Y-%m"))["minutes"] == 180
    assert career.time_report(month="2000-01")["minutes"] == 0
    with pytest.raises(ApiError):
        api_career._time_report(_ctx(month="x"))
    with pytest.raises(ApiError):
        api_career._time(_ctx("POST", data={"project": "A", "minutes": "abc"}))
    assert len((config.DATA / "timelog.jsonl").read_text(encoding="utf-8").splitlines()) == 3


def test_board_contracts_portfolio_group(vault):
    cols = {c["status"]: c["items"] for c in career.board()["columns"]}
    assert cols["mulakat"][0]["title"] == "Burs" and cols["hazirlaniyor"] == []
    cs = career.contracts(TODAY)
    assert cs[0]["title"] == "Sözleşme Acme" and cs[0]["days_left"] == 19 and cs[0]["warn"] is True
    assert cs[1]["warn"] is False
    assert career._date_in("Sözleşme bitiş tarihi: 15.03.2027") == "2027-03-15"
    p = career.portfolio()
    txt = (vault / p["path"]).read_text(encoding="utf-8")
    assert p["projects"] == 1 and "Acme sitesi" in txt and "Gizli" not in txt
    g = career.group("site acme")
    assert [m["name"] for m in g["members"]] == ["Ali Veli", "Ayşe"] and g["members"][0]["path"] and g["members"][1]["path"] is None
    with pytest.raises(ApiError) as e:
        api_career._group(_ctx(project="yok"))
    assert e.value.code == 404


def test_model_features(vault, monkeypatch):
    seen = []

    def fake(task, prompt, **kw):
        seen.append((task, prompt, kw))
        return "<think>x</think>1. Kendini tanıt?\n2. Neden biz?\nSTAR cevabı", "yerel"
    monkeypatch.setattr(llm, "complete", fake)
    cv = career.make_cv("Backend Stajyeri", "en")
    assert cv["path"] == "30-Kariyer/CV/Backend Stajyeri.md" and "think" not in cv["text"]
    assert seen[0][2].get("private") is True and "Acme sitesi" in seen[0][1] and "YPZ201" in seen[0][1]
    iv = career.make_interview("Dev", "Acme")
    assert iv["questions"] == ["Kendini tanıt?", "Neden biz?"]
    lp = career.linkedin_post("Yeni proje")
    assert "paylaşılmadı" in (vault / lp["path"]).read_text(encoding="utf-8")
    n = career.course_notes("YPZ201")
    assert (vault / n["path"]).exists() and n["path"].startswith("10-Dersler/YPZ201")
    t = career.tutor("YPZ201", "Bağlı liste nasıl tersine çevrilir?")
    assert "ASLA" in seen[-1][1] and "Bağlı liste" in seen[-1][1] and t["hint"]
    src = vault / "10-Dersler" / "tez.md"
    src.write_text("# Tez\n\nGiriş metni.\n", encoding="utf-8")
    before = src.read_text(encoding="utf-8")
    w = career.writing("10-Dersler/tez.md", "review")
    assert w["suggestion"] and src.read_text(encoding="utf-8") == before      # dosya değişmez
    with pytest.raises(ValueError):
        career.writing("../x.md", "review")
    with pytest.raises(ValueError):
        career.writing("10-Dersler/tez.md", "sil")
    with pytest.raises(ApiError) as e:
        api_career._tutor(_ctx("POST", data={"code": "YOK1", "question": "?"}))
    assert e.value.code == 404


def test_bib_and_market(vault, monkeypatch):
    r = career.bib(text="Knuth, D. (1968). The Art of Computer Programming.")
    assert r["path"] == "40-Kaynaklar/Kaynakça.md"
    r = career.bib(url="https://example.com/x")
    assert "example.com" in (vault / r["path"]).read_text(encoding="utf-8").splitlines()[-1]
    monkeypatch.setattr(career, "_fetch_doi", lambda doi: {"authors": ["Doe, J."], "year": 2020, "title": "T", "venue": "J", "doi": doi})
    r = career.bib(doi="10.1000/xyz", style="ieee")
    assert r["apa"].startswith("Doe, J. (2020). T. J.") and r["added"] == r["ieee"] and r["ieee"].startswith("Doe, J., \"T,\"")
    assert len((vault / r["path"]).read_text(encoding="utf-8").splitlines()) >= 5
    with pytest.raises(ApiError):
        api_career._bib(_ctx("POST", data={}))
    (config.SYSTEM / "config" / "pazar.yaml").write_text(yaml.safe_dump({"anahtar_kelimeler": ["forklift", "ikinci el"]}, allow_unicode=True), encoding="utf-8")
    added = []
    from sb import search
    monkeypatch.setattr(search, "add_saved", lambda q, alert=False: added.append(q) or "x")
    assert career.market()["keywords"] == [{"keyword": "forklift", "saved": False}, {"keyword": "ikinci el", "saved": False}]
    assert added == []                                              # GET yan etkisiz
    assert career.market_sync()["added"] == ["forklift", "ikinci el"] and added == ["forklift", "ikinci el"]


def test_routes_registered():
    routes = webroutes.ROUTES                                       # api_career içe aktarıldığında kayıtlı
    for m, p in [("GET", "/api/v2/crm"), ("POST", "/api/v2/quote"), ("GET", "/api/v2/finance"), ("GET", "/api/v2/applications/board"),
                 ("POST", "/api/v2/cv"), ("GET", "/api/v2/contracts"), ("POST", "/api/v2/tutor")]:
        assert (m, p) in routes
    assert routes[("POST", "/api/v2/cv")].model is True
    assert routes[("GET", "/api/v2/crm")].model is False
