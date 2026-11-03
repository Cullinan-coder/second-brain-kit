"""Paket 4: Çalışmaya başla boru hattı, uçlar ve masaüstü yardımcıları — her şey taklit (gerçek güncelleme/doctor/daily/ollama/pencere yok)."""
import json
import socket

import pytest

from app import desktop
from sb import api_startup, chat, startup, webroutes
from sb.webroutes import Ctx


def call(path, data=None, method="GET"):
    r = webroutes.find(method, path)
    assert r is not None, path
    code, body, _, _ = webroutes.call(r, Ctx(method, path, data or {}, {}, session=chat.Session()))
    return code, json.loads(body)


@pytest.fixture
def fake(monkeypatch, tmp_path):
    calls = {"apply": 0, "daily": 0, "warm": 0}
    monkeypatch.setattr(startup, "SETTINGS", tmp_path / "uygulama.yaml")
    monkeypatch.setattr(startup, "_check_update", lambda: {"ok": True, "available": False, "text": "Güncel"})
    monkeypatch.setattr(startup, "_apply_update", lambda: calls.__setitem__("apply", calls["apply"] + 1) or 0)
    monkeypatch.setattr(startup, "_doctor", lambda: [("✓", "Profil", ""), ("!", "Codex", "npm i -g @openai/codex")])
    monkeypatch.setattr(startup, "_daily_done_today", lambda: False)
    monkeypatch.setattr(startup, "_run_daily", lambda: calls.__setitem__("daily", calls["daily"] + 1) or 0)
    monkeypatch.setattr(startup, "_warm_models", lambda: calls.__setitem__("warm", calls["warm"] + 1) or ["Ollama (x)"])
    with startup._lock:
        startup._state.clear()
        startup._state.update(startup._fresh())
    return calls


def test_pipeline_all_steps(fake):
    assert startup.start(background=False)
    st = startup.status()
    assert [s["id"] for s in st["steps"]] == ["update", "health", "daily", "warm", "ready"]
    by = {s["id"]: s for s in st["steps"]}
    assert by["update"]["status"] == "ok" and by["health"]["status"] == "warn"
    assert "Codex" in by["health"]["fix"] and "npm i -g" in by["health"]["fix"]
    assert by["daily"]["status"] == "ok" and by["warm"]["status"] == "ok" and by["ready"]["status"] == "warn"
    assert all("duration_s" in s and "message" in s for s in st["steps"])
    assert st["done"] and not st["running"] and st["ok"] is True
    assert fake == {"apply": 0, "daily": 1, "warm": 1}


def test_update_only_when_user_setting(fake, monkeypatch, tmp_path):
    monkeypatch.setattr(startup, "_check_update", lambda: {"ok": True, "available": True, "current": "1.0", "new": "1.1", "text": ""})
    startup.start(background=False)                       # ayar yok → yalnız bilgi
    s = startup.status()
    assert fake["apply"] == 0 and s["steps"][0]["status"] == "warn" and s["update"]["new"] == "1.1"
    (tmp_path / "uygulama.yaml").write_text("auto_update: true\n", encoding="utf-8")
    startup.start(background=False)
    assert fake["apply"] == 1 and startup.status()["steps"][0]["status"] == "ok"


def test_request_flag_cannot_enable_update(fake, monkeypatch):
    monkeypatch.setattr(startup, "_check_update", lambda: {"ok": True, "available": True, "current": "1", "new": "2", "text": ""})
    monkeypatch.setattr(startup.threading.Thread, "start", lambda self: self.run())
    code, out = call("/api/v2/startup/run", {"auto_update": True}, "POST")
    assert code == 200 and out["started"] and fake["apply"] == 0


def test_daily_skipped_and_step_error_isolated(fake, monkeypatch):
    monkeypatch.setattr(startup, "_daily_done_today", lambda: True)
    monkeypatch.setattr(startup, "_doctor", lambda: (_ for _ in ()).throw(RuntimeError("bozuk")))
    startup.start(background=False)
    by = {s["id"]: s for s in startup.status()["steps"]}
    assert by["daily"]["status"] == "skipped" and fake["daily"] == 0
    assert by["health"]["status"] == "error" and "bozuk" in by["health"]["message"]
    assert by["warm"]["status"] == "ok" and startup.status()["ok"] is False


def test_single_run_at_a_time(fake):
    with startup._lock:
        startup._state["running"] = True
    assert startup.start(background=False) is False
    with startup._lock:
        startup._state["running"] = False


def test_warm_failure_is_warning(fake, monkeypatch):
    def boom():
        raise RuntimeError("Ollama kurulu değil")
    monkeypatch.setattr(startup, "_warm_models", boom)
    startup.start(background=False)
    w = {s["id"]: s for s in startup.status()["steps"]}["warm"]
    assert w["status"] == "warn" and w["fix"]


def test_status_and_settings_routes(fake, monkeypatch):
    code, out = call("/api/v2/startup/status")
    assert code == 200 and len(out["steps"]) == 5
    made = []

    class Srv:
        url = "http://127.0.0.1:1/?t=abc"

    monkeypatch.setattr(api_startup, "_setup_srv", None)
    monkeypatch.setattr(api_startup, "_make_setup_server", lambda: made.append(1) or Srv())
    assert call("/api/v2/startup/settings-url")[1]["url"].startswith("http://127.0.0.1:1/?t=abc")
    call("/api/v2/startup/settings-url")
    assert made == [1]                                    # tek örnek
    for m, p in (("POST", "/api/v2/startup/run"), ("GET", "/api/v2/startup/status"), ("GET", "/api/v2/startup/settings-url")):
        assert webroutes.find(m, p).local_only


# ------------------------------------------------------------ masaüstü
def test_ensure_server_leaves_existing_alone():
    started = []
    assert desktop.ensure_server(up=lambda: True, popen=lambda *a, **k: started.append(1)) is None
    assert not started


def test_ensure_server_starts_child_and_stops_on_timeout():
    class P:
        terminated = False

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            pass
    p = P()
    state = {"n": 0}

    def up():
        state["n"] += 1
        return state["n"] > 2
    assert desktop.ensure_server(up=up, popen=lambda *a, **k: p, sleep=lambda s: None) is p
    q = P()
    with pytest.raises(RuntimeError):
        desktop.ensure_server(up=lambda: False, popen=lambda *a, **k: q, sleep=lambda s: None, wait=2)
    assert q.terminated


def test_single_instance_brings_first_to_front():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    shown = []
    first = desktop.SingleInstance(port, on_show=lambda: shown.append(1))
    assert first.acquire()
    try:
        assert desktop.SingleInstance(port).acquire() is False
        for _ in range(50):
            if shown:
                break
            import time
            time.sleep(0.05)
        assert shown
    finally:
        first.release()
