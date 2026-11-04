import json
import sys
import zipfile
from datetime import datetime, timedelta

import pytest

from sb import telemetry


@pytest.fixture(autouse=True)
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setattr(telemetry, "DATA", tmp_path)
    monkeypatch.setenv("SB_SECRET_TEST", "cok-gizli-deger")
    return tmp_path


def rows(d):
    return [json.loads(l) for l in (d / "perf.jsonl").read_text(encoding="utf-8").splitlines()]


def test_timed_kaydi_ve_hata(tmp_data):
    with telemetry.timed("hook", "a"):
        pass
    with pytest.raises(ValueError):
        with telemetry.timed("hook", "b"):
            raise ValueError("x")
    r = rows(tmp_data)
    assert [(x["name"], x["ok"]) for x in r] == [("a", True), ("b", False)]
    assert {"ts", "kind", "name", "ms", "ok"} <= set(r[0])


def test_5mb_budama(tmp_data):
    p = tmp_data / "perf.jsonl"
    line = json.dumps({"ts": "2026-01-01T00:00:00", "kind": "k", "name": "n" * 900, "ms": 1, "ok": True}) + "\n"
    p.write_text(line * 6000, encoding="utf-8")                 # ~5.4 MB
    telemetry.record("k", "yeni", 5)
    assert p.stat().st_size < telemetry.MAX_PERF_BYTES
    assert rows(tmp_data)[-1]["name"] == "yeni"


def test_perf_summary_p95(tmp_data):
    for ms in range(1, 101):
        telemetry.record("daily_step", "mail", ms, ms != 100)
    out = telemetry.perf_summary(7)
    assert "mail" in out and "95" in out and "En yavaş 5" in out
    assert "1" in out.splitlines()[3].split()[-1]               # hata %1
    assert telemetry.perf_summary(1).startswith("Performans")
    (tmp_data / "perf.jsonl").unlink()
    assert "ölçüm yok" in telemetry.perf_summary()


def test_perf_eski_kayit_dislanir(tmp_data):
    old = (datetime.now() - timedelta(days=30)).isoformat(timespec="seconds")
    (tmp_data / "perf.jsonl").write_text(json.dumps({"ts": old, "kind": "k", "name": "n", "ms": 1, "ok": True}) + "\n")
    assert "ölçüm yok" in telemetry.perf_summary(7)


def test_crash_maskeler_ve_env_yok(tmp_data):
    try:
        raise RuntimeError("ali@example.com bağlantı koptu")
    except RuntimeError as e:
        p = telemetry.crash(e, "ask ali@example.com +90 532 123 45 67")
    t = p.read_text(encoding="utf-8")
    assert "ali@example.com" not in t and "532 123" not in t
    assert "cok-gizli-deger" not in t and "SB_SECRET_TEST" not in t
    assert "Traceback" in t and "Python:" in t and "Sürüm:" in t
    assert telemetry.crash_list() == [p]
    assert "Traceback" in telemetry.logs(kind="crash")


def test_bundle(tmp_data, monkeypatch):
    from sb import doctor
    monkeypatch.setattr(doctor, "run", lambda: print("doktor çıktısı") or 0)
    telemetry.crash(RuntimeError("a"), "x")
    z = telemetry.crash_bundle()
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        assert "doctor.txt" in names and any(n.startswith("crashes/") for n in names)
        assert "doktor çıktısı" in zf.read("doctor.txt").decode("utf-8")


def test_logs_son_n(tmp_data):
    d = tmp_data / "logs"
    d.mkdir()
    (d / "daily-20260101-0100.log").write_text("\n".join(f"s{i}" for i in range(100)), encoding="utf-8")
    out = telemetry.logs(3)
    assert out.splitlines()[-1] == "s99" and "s96" not in out
    assert "yok" in telemetry.logs(kind="weekly")


def test_main_sarmalayici(tmp_data, monkeypatch, capsys):
    from sb import __main__ as m

    def boom(a):
        raise RuntimeError("patladı")
    monkeypatch.setattr(m, "cmd_notify_test", boom)
    assert m.main(["notify-test"]) == 1
    assert "sb logs --bundle" in capsys.readouterr().err
    assert len(telemetry.crash_list()) == 1

    monkeypatch.setattr(m, "cmd_notify_test", lambda a: (_ for _ in ()).throw(KeyboardInterrupt()))
    assert m.main(["notify-test"]) == 130
    monkeypatch.setattr(m, "cmd_notify_test", lambda a: sys.exit(7))
    with pytest.raises(SystemExit):
        m.main(["notify-test"])


def test_whatsnew(tmp_data, monkeypatch, tmp_path):
    cl = tmp_path / "CHANGELOG.md"
    cl.write_text("# Değişiklikler\n\n## 0.3.1 — x\n- c\n\n## 0.3.0 — y\n- b\n\n## 0.2.0 — z\n- a\n", encoding="utf-8")
    monkeypatch.setattr(telemetry, "_changelog", lambda: cl)
    monkeypatch.setattr("sb.update.version", lambda root=None: "0.3.1")
    (tmp_data / "seen_version").write_text("0.2.0", encoding="utf-8")
    out = telemetry.whatsnew()
    assert "0.3.1" in out and "0.3.0" in out and "0.2.0" not in out
    assert (tmp_data / "seen_version").read_text() == "0.3.1"
    assert "Yeni bir şey yok" in telemetry.whatsnew()
    assert "0.2.0" in telemetry.whatsnew(show_all=True)
    (tmp_data / "seen_version").unlink()
    first = telemetry.whatsnew()
    assert "0.3.1" in first and "0.3.0" not in first


def test_crash_reports_never_overwrite_each_other(monkeypatch):
    """Aynı mikro saniyede (Windows saat çözünürlüğü) iki çökme iki ayrı rapor olmalı."""
    from datetime import datetime as real
    from sb import telemetry

    class Frozen(real):
        @classmethod
        def now(cls, tz=None):
            return real(2026, 11, 4, 12, 0, 0, 123456)
    monkeypatch.setattr(telemetry, "datetime", Frozen)
    try:
        raise ValueError("x")
    except ValueError as e:
        a, b = telemetry.crash(e, "daily"), telemetry.crash(e, "daily")
    assert a != b and a.exists() and b.exists()
