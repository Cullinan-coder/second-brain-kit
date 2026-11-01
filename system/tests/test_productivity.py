"""Paket V: görev panosu, plan, pomodoro, alışkanlık, hedef, haftalık gözden geçirme (taklitli; gerçek takvim/model/ağ yok)."""
import json
from datetime import date, datetime, time, timedelta

import pytest

from sb import api_plan, chat, convstore, productivity as pr, vault_ops, webroutes
from sb.notes import dump_note
from sb.webroutes import Ctx

TODAY = date.today()
NOW = datetime.combine(TODAY, time(8, 0))


def call(method, path, data=None, query=None, session=None, calendar=None):
    r = webroutes.find(method, path)
    assert r is not None, path
    ctx = Ctx(method, path, data or {}, query or {}, b"", "", (data or {}).get("sid", "s1"), False,
              session if session is not None else chat.Session(), None, calendar)
    code, body, _, _ = webroutes.call(r, ctx)
    return code, json.loads(body)


class FakeCal:
    def __init__(self, events=()):
        self.events, self.added = list(events), []

    def list_events(self, start, end):
        return self.events

    def add(self, ev, dry_run=True):
        self.added.append((ev, dry_run))
        return "eklendi", {}


def ev(title, a, b):
    d = TODAY.isoformat()
    return {"summary": title, "start": {"dateTime": f"{d}T{a}:00"}, "end": {"dateTime": f"{d}T{b}:00"}}


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", vault)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "")
    monkeypatch.setattr(convstore, "notify", lambda *a, **k: notes.append(a) or {})
    notes.clear()
    return vault


notes: list = []


def add(text, **kw):
    code, out = call("POST", "/api/v2/tasks/add", {"text": text, **kw})
    assert code == 200, out
    return out["card"]


def cols():
    code, out = call("GET", "/api/v2/tasks/board")
    assert code == 200
    return {c["id"]: [k["id"] for k in c["cards"]] for c in out["columns"]}


def test_board_add_move():
    c = add("Rapor yaz", due=TODAY.isoformat(), project="Atlas", priority=1)
    assert c["priority"] == 1 and c["project"] == "Atlas" and c["due"] == TODAY.isoformat()
    assert cols() == {"todo": ["Rapor yaz"], "doing": [], "done": []}
    assert call("POST", "/api/v2/tasks/move", {"id": "Rapor yaz", "to": "doing"})[0] == 200
    assert cols()["doing"] == ["Rapor yaz"]
    call("POST", "/api/v2/tasks/move", {"id": "Rapor yaz", "to": "done"})
    assert cols()["done"] == ["Rapor yaz"]
    assert call("POST", "/api/v2/tasks/move", {"id": "yok", "to": "done"})[0] == 404
    assert call("POST", "/api/v2/tasks/move", {"id": "../x", "to": "done"})[0] == 400
    assert call("POST", "/api/v2/tasks/move", {"id": "Rapor yaz", "to": "x"})[0] == 400
    assert call("POST", "/api/v2/tasks/add", {"text": ""})[0] == 400
    assert call("POST", "/api/v2/tasks/add", {"text": "a", "repeat": "ayda bir kez"})[0] == 400


def test_repeat_spawns_next_once():
    add("Spor", repeat="daily", due=TODAY.isoformat())
    call("POST", "/api/v2/tasks/move", {"id": "Spor", "to": "done"})
    c = cols()
    nd = TODAY + timedelta(days=1)
    assert c["done"] == ["Spor"] and c["todo"] == [f"Spor ({nd})"]
    call("POST", "/api/v2/tasks/move", {"id": "Spor", "to": "todo"})
    call("POST", "/api/v2/tasks/move", {"id": "Spor", "to": "done"})
    assert len(cols()["todo"]) == 1                              # ikinci kopya açılmaz


def test_next_due_rules():
    base = date(2026, 1, 31)                                       # cumartesi
    assert pr.next_due("weekly", base) == date(2026, 2, 7)
    assert pr.next_due("monthly", base) == date(2026, 2, 28)
    assert pr.next_due("cuma", base) == date(2026, 2, 6)
    assert pr.next_due("Cuma", date(2026, 2, 6)) == date(2026, 2, 13)
    assert pr.next_due("saçma", base) is None


def test_dependency_blocks_until_done():
    add("Taslak")
    b = add("Son hali", after="Taslak")
    assert b["blocked"] is True
    code, out = call("POST", "/api/v2/tasks/move", {"id": "Son hali", "to": "doing"})
    assert code == 409 and "Taslak" in out["error"]
    assert [x["id"] for x in pr.candidates()] == ["Taslak"]
    call("POST", "/api/v2/tasks/move", {"id": "Taslak", "to": "done"})
    assert call("POST", "/api/v2/tasks/move", {"id": "Son hali", "to": "doing"})[0] == 200
    assert call("POST", "/api/v2/tasks/add", {"text": "x", "after": "Yok"})[0] == 404


def test_today_ranking_and_plan_gaps():
    add("Rutin", priority=3)
    add("Yarın teslim", due=(TODAY + timedelta(days=1)).isoformat(), priority=3)
    add("Önemli", priority=1)
    cal = FakeCal([ev("Ders", "09:00", "11:00")])
    out = pr.plan_today(cal, NOW)
    assert [t["text"] for t in out["top3"]] == ["Yarın teslim", "Önemli", "Rutin"]
    kinds = [(p["start"], p["kind"]) for p in out["plan"]]
    assert ("09:00", "etkinlik") in kinds
    tasks_ = [p for p in out["plan"] if p["kind"] == "görev"]
    assert tasks_ and all(p["start"] >= "11:00" for p in tasks_)
    assert any(p["kind"] == "mola" for p in out["plan"])
    code, api = call("GET", "/api/v2/plan/today", calendar=cal)
    assert code == 200 and set(api) >= {"top3", "plan", "warnings"}


def test_conflict_and_calendar_failure():
    cal = FakeCal([ev("A", "10:00", "11:00"), ev("B", "10:30", "11:30")])
    assert any("Çakışma" in w for w in pr.plan_today(cal, NOW)["warnings"])

    class Bad:
        def list_events(self, *a):
            raise RuntimeError("ağ")
    out = pr.plan_today(Bad(), NOW)
    assert any("Takvim okunamadı" in w for w in out["warnings"])


def test_low_mood_shortens_and_defers_hard():
    add("Zor iş", priority=1)
    add("Kolay iş", priority=2)
    normal = pr.plan_today(FakeCal(), NOW)["plan"]
    assert normal[0]["title"] == "Zor iş" and normal[0]["end"] == "09:50"
    assert call("POST", "/api/v2/plan/mood", {"level": 2})[0] == 200
    assert call("POST", "/api/v2/plan/mood", {"level": 9})[0] == 400
    low = pr.plan_today(FakeCal(), NOW)
    assert low["mood"] == 2
    work = [p for p in low["plan"] if p["kind"] == "görev"]
    assert work[0]["title"] == "Kolay iş" and work[0]["end"] == "09:25"
    assert "seviye 2" in pr.daily_path().read_text(encoding="utf-8")


def test_time_block_is_proposal_only():
    cal, s = FakeCal(), chat.Session()
    d = TODAY.isoformat()
    code, out = call("POST", "/api/v2/plan/block", {"sid": "s1", "title": "Rapor", "start": f"{d}T10:00", "end": f"{d}T10:50"},
                     session=s, calendar=cal)
    assert code == 200 and len(out["proposals"]) == 1 and cal.added == []
    assert call("POST", "/api/v2/plan/block", {"sid": "s1", "title": "", "start": f"{d}T10:00", "end": f"{d}T10:50"}, session=s)[0] == 400
    assert call("POST", "/api/v2/plan/block", {"sid": "s1", "title": "x", "start": f"{d}T12:00", "end": f"{d}T10:50"}, session=s)[0] == 400
    pid = next(iter(s.proposals))
    s.proposals[pid]["_run"]()                                    # onaylanınca eklenir
    assert len(cal.added) == 1 and cal.added[0][1] is False


def test_pomodoro_writes_focus_line():
    add("Odak işi")
    code, out = call("POST", "/api/v2/plan/pomodoro", {"task_id": "Odak işi", "minutes": 25})
    assert code == 200 and out["minutes"] == 25
    txt = pr.daily_path().read_text(encoding="utf-8")
    assert "## Odak" in txt and "25 dk" in txt and "[[Odak işi]]" in txt
    call("POST", "/api/v2/plan/pomodoro", {"task_id": "", "minutes": 50})
    assert pr.daily_path().read_text(encoding="utf-8").count("dk") == 2
    assert call("POST", "/api/v2/plan/pomodoro", {"task_id": "", "minutes": 0})[0] == 400


def test_habits_streak():
    assert call("POST", "/api/v2/habits", {"name": "Su iç"})[0] == 200
    assert call("POST", "/api/v2/habits", {"name": "su iç"})[0] == 400
    hid = call("GET", "/api/v2/habits")[1]["habits"][0]["id"]
    out = call("POST", "/api/v2/habits", {"id": hid})[1]["habits"][0]
    assert out["done_today"] and out["streak"] == 1
    hs = pr._hload()
    hs[0]["done"] += [(TODAY - timedelta(days=i)).isoformat() for i in (1, 2, 4)]
    pr._hsave(hs)
    assert call("GET", "/api/v2/habits")[1]["habits"][0]["streak"] == 3
    off = call("POST", "/api/v2/habits", {"id": hid, "done": False})[1]["habits"][0]
    assert not off["done_today"] and off["streak"] == 2
    assert call("POST", "/api/v2/habits", {"id": "yok"})[0] == 404


def test_goals_progress(env):
    d = env / "40-Kaynaklar" / "Hedefler"
    d.mkdir(parents=True)
    (d / "Fit ol.md").write_text("---\ntype: hedef\n---\n# Fit ol\n- [x] 10 km koş\n- [ ] 5 kg ver\n- [x] Uyku düzeni\n- [ ] Su\n", encoding="utf-8")
    g = call("GET", "/api/v2/goals")[1]["goals"]
    assert g[0]["title"] == "Fit ol" and g[0]["progress"] == 50 and g[0]["total"] == 4 and g[0]["key_results"][0]["done"] is True


def test_weekly_review(env, monkeypatch):
    add("Biten")
    call("POST", "/api/v2/tasks/move", {"id": "Biten", "to": "done"})
    add("Kalan")
    proj = env / "20-Projeler"
    proj.mkdir()
    (proj / "Sunum.md").write_text(dump_note({"type": "teslim", "due": TODAY + timedelta(days=5)}, "# Sunum\n"), encoding="utf-8")
    from sb import memory
    monkeypatch.setattr(memory, "receipts", lambda since=None, until=None: [{"date": TODAY, "project": "Atlas", "text": "bitti", "id": "1"}])
    code, r = call("GET", "/api/v2/review/week")
    assert code == 200 and [c["id"] for c in r["done"]] == ["Biten"] and [c["id"] for c in r["remaining"]] == ["Kalan"]
    assert r["receipts"][0]["project"] == "Atlas" and r["next_week"][0]["title"] == "Sunum"
    code, out = call("POST", "/api/v2/review/week", {"answers": {"Ne iyi gitti?": "Odak", "Takıldı": ""}})
    assert code == 200 and out["path"].startswith("50-Günlük/Haftalık/")
    assert "Odak" in (env / out["path"]).read_text(encoding="utf-8")
    assert call("POST", "/api/v2/review/week", {"answers": {}})[0] == 400


def test_deadline_risk_warning_and_notify_once(env):
    proj = env / "20-Projeler"
    proj.mkdir()
    (proj / "Rapor.md").write_text(dump_note({"type": "teslim", "due": TODAY + timedelta(days=2)}, "# Rapor\n"), encoding="utf-8")
    (proj / "Uzak.md").write_text(dump_note({"type": "teslim", "due": TODAY + timedelta(days=20)}, "# Uzak\n"), encoding="utf-8")
    out = pr.plan_today(FakeCal(), NOW)
    assert any("Rapor" in w and "Teslim riski" in w for w in out["warnings"]) and not any("Uzak" in w for w in out["warnings"])
    assert len(pr.check_risks()) == 1 and len(notes) == 1
    assert pr.check_risks() == []                                  # aynı gün tekrar bildirmez
    add("Rapor taslağı")                                            # ilgili görev todo → hâlâ uyarı
    call("POST", "/api/v2/tasks/move", {"id": "Rapor taslağı", "to": "doing"})
    assert not any("«Rapor»" in w["text"] for w in pr.risk_warnings())   # üzerinde çalışılıyor → uyarı yok


def test_morning_text_and_cli(capsys):
    add("Sabah işi", priority=1)
    t = pr.morning_text(FakeCal([ev("Toplantı", "13:00", "14:00")]))
    assert "Sabah işi" in t and "Toplantı" in t
    assert pr.main(["board"]) == 0 and "Yapılacak (1)" in capsys.readouterr().out
    assert pr.main(["plan"]) == 0
