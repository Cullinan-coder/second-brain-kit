from datetime import date

import pytest
import yaml

from sb import academic, api_school, config, vault_ops, webroutes
from sb.webroutes import ApiError, Ctx


def _ctx(method="GET", **kw):
    data = kw.pop("data", {})
    return Ctx(method=method, path="/x", data=data, query={k: str(v) for k, v in kw.items()})


@pytest.fixture
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    d = v / "10-Dersler" / "YPZ201 Veri Yapıları"
    d.mkdir(parents=True)
    (v / "10-Dersler" / "Geçmiş").mkdir()
    (d / "YPZ201 Veri Yapıları.md").write_text(
        "---\ntype: ders\nstatus: aktif\ncode: YPZ201\ninstructor: Dr. Ali Veli\nschedule: ['Pzt 13:00']\n---\n# YPZ201\n\n"
        "### Konular\n- **1. Hafta** — Giriş\n- **2. Hafta** — Diziler\n- **3. Hafta** — Listeler\n\nVize: 2026-12-20 saat 10\n", encoding="utf-8")
    (d / "slayt.pdf").write_bytes(b"x")
    (v / "20-Teslimler").mkdir()
    (v / "20-Teslimler" / "YPZ201 Ödev 1.md").write_text(
        "---\ntype: teslim\nstatus: acik\nkind: odev\ncourse: '[[YPZ201 Veri Yapıları]]'\ndue: 2026-11-10\n---\n# Ödev\n", encoding="utf-8")
    (v / "30-Kariyer").mkdir()
    (v / "30-Kariyer" / "Burs X.md").write_text("---\ntype: basvuru\nstatus: hazirlaniyor\nkind: burs\ndue: 2026-11-30\n---\n# Burs X\n", encoding="utf-8")
    (v / "30-Kariyer" / "Eski.md").write_text("---\ntype: basvuru\nstatus: red\ndue: 2026-01-01\n---\n# Eski\n", encoding="utf-8")
    (v / "Ali Veli.md").write_text("---\ntype: kisi\nstatus: aktif\nemail: ali@x.edu\n---\n# Ali Veli\n", encoding="utf-8")
    sysdir = v / "_system"
    (sysdir / "config").mkdir(parents=True)
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(config, "SYSTEM", sysdir)
    monkeypatch.setattr(config, "MAIL_DB", tmp_path / "yok.db")
    return v


def _notlar(vault, rows):
    (vault / "_system" / "config" / "notlar.yaml").write_text(yaml.safe_dump({"dersler": rows}, allow_unicode=True), encoding="utf-8")


ROWS = [{"code": "A1", "kredi": 4, "harf": "AA", "donem": "T1"}, {"code": "A2", "kredi": 6, "harf": "CC", "donem": "T1"},
        {"code": "A3", "kredi": 5, "harf": "FF", "donem": "T2"}]


def test_gpa_and_template(vault):
    assert academic.load_grades()["source"] in ("bos", "obs")      # dosya yok, hata yok
    assert not academic.notlar_path().exists()
    academic.ensure_template()
    assert academic.notlar_path().exists()
    _notlar(vault, ROWS)
    r = api_school._gpa(_ctx())
    assert r["credits"] == 15 and r["gpa"] == round((16 + 12 + 0) / 15, 2) and len(r["terms"]) == 2


def test_gpa_retake_and_whatif(vault):
    _notlar(vault, ROWS + [{"code": "A3", "kredi": 5, "harf": "BB", "donem": "T3"}])
    assert api_school._gpa(_ctx())["gpa"] == round((16 + 12 + 15) / 15, 2)
    r = api_school._what_if(_ctx("POST", data={"changes": [{"code": "A2", "grade": "AA"}]}))
    assert r["gpa"] > r["current"] and r["delta"] > 0
    r = api_school._what_if(_ctx("POST", data={"changes": [{"code": "NEW", "grade": "AA", "credits": 3}]}))
    assert r["credits"] == 18
    for bad in ({}, {"changes": [{"code": "A1", "grade": "ZZ"}]}, {"changes": [{"code": "NEW", "grade": "AA"}]}):
        with pytest.raises(ApiError):
            api_school._what_if(_ctx("POST", data=bad))


def test_courses_and_course(vault):
    _notlar(vault, [{"code": "YPZ201", "kredi": 5, "harf": "CB", "donem": "T"}])
    cs = api_school._courses(_ctx())
    assert len(cs) == 1 and cs[0]["code"] == "YPZ201" and cs[0]["grade"] == "CB" and cs[0]["files_count"] >= 2
    assert cs[0]["exams"][0]["date"] == "2026-12-20"
    d = api_school._course(_ctx(code="ypz201"))
    dates = [e["date"] for e in d["events"]]
    assert "2026-11-10" in dates and "2026-12-20" in dates
    assert d["topics"][0].startswith("1. Hafta")
    with pytest.raises(ApiError):
        api_school._course(_ctx(code="NOPE"))
    with pytest.raises(ApiError):
        api_school._course(_ctx())


def test_study_plan(vault):
    plan = academic.make_plan(["a", "b", "c", "d"], date(2026, 11, 6), 2, today=date(2026, 11, 1))
    assert len(plan) == 5 and plan[-1]["topics"][0].startswith("Genel tekrar")
    assert [t for p in plan[:-1] for t in p["topics"]] == ["a", "b", "c", "d"]
    with pytest.raises(ValueError):
        academic.make_plan(["a"], date(2026, 11, 1), 2, today=date(2026, 11, 1))
    r = api_school._study_plan(_ctx("POST", data={"code": "YPZ201", "exam_date": "2099-01-05", "hours_per_day": 3}))
    assert (vault / r["path"]).exists() and r["topics"] == 3
    assert "Çalışma planı" in (vault / r["path"]).read_text(encoding="utf-8")
    for bad in ({"code": "YPZ201", "exam_date": "zzz"}, {"code": "YPZ201", "exam_date": "2020-01-01"},
                {"code": "YPZ201", "exam_date": "2099-01-05", "hours_per_day": 40}, {"code": "NOPE", "exam_date": "2099-01-05"}):
        with pytest.raises(ApiError):
            api_school._study_plan(_ctx("POST", data=bad))


def test_schedule_applications(vault):
    s = api_school._schedule(_ctx())
    assert s["schedule"][0]["slot"] == "Pzt 13:00" and isinstance(s["announcements"], list)
    apps = api_school._applications(_ctx())
    assert [a["title"] for a in apps] == ["Burs X", "Eski"] and apps[0]["open"] and not apps[1]["open"]


def test_instructor_mails(vault, tmp_path, monkeypatch):
    r = api_school._instructor(_ctx(code="YPZ201"))
    assert r["person"]["name"] == "Ali Veli" and r["mails"] == []
    from sb import maildb
    db = tmp_path / "mail.db"
    con = maildb.connect(db)
    con.execute("INSERT INTO messages (account, id, from_addr, from_name, subject, date_ms) VALUES ('a','1','ali@x.edu','Ali Veli','Vize hk.',1760000000000)")
    con.commit()
    con.close()
    monkeypatch.setattr(config, "MAIL_DB", db)
    r = api_school._instructor(_ctx(code="YPZ201"))
    assert r["mails"][0]["subject"] == "Vize hk."
    with pytest.raises(ApiError):
        api_school._instructor(_ctx(code="NOPE"))


def test_school_docs(vault, monkeypatch):
    from sb import analysis
    monkeypatch.setattr(analysis, "classify_docs", lambda *a, **k: [
        {"doc_id": "1", "ad": "Transkript.pdf", "cls": "rapor", "why": "", "date_ms": 1760000000000},
        {"doc_id": "2", "ad": "dilekce.pdf", "cls": "resmi yazı", "why": "x", "date_ms": None},
        {"doc_id": "3", "ad": "cv.pdf", "cls": "cv", "why": "", "date_ms": None}])
    r = api_school._school_docs(_ctx())
    assert {d["kind"] for d in r} == {"transkript", "resmi yazı"} and len(r) == 2


def test_routes_registered(vault):
    webroutes.MODULES  # noqa: B018
    for m, p in [("GET", "/api/v2/courses"), ("GET", "/api/v2/course"), ("GET", "/api/v2/gpa"), ("POST", "/api/v2/gpa/what-if"),
                 ("POST", "/api/v2/study-plan"), ("GET", "/api/v2/applications"), ("GET", "/api/v2/school-docs")]:
        assert (m, p) in webroutes.ROUTES
