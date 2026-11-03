"""Testler kişisel ayarlardan bağımsız: sabit mail kuralları ve sabit GitHub kullanıcısı."""
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _no_real_system_changes(monkeypatch):
    """Kurulum motoru testte gerçek komut çalıştıramaz (2026-11-03: bir kaldırma testi gerçek zamanlanmış görevleri sildi).
    Komut gereken test _run_capture/_run_stream'i kendisi taklit eder; taklit edilmezse test yüksek sesle kırılır."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from setup import engine
    except Exception:                                           # noqa: BLE001 — kitte setup yoksa koruma gereksiz
        return

    def _blocked(cmd, *a, **k):
        raise RuntimeError(f"testte gerçek komut yok — taklit et: {' '.join(map(str, cmd))[:120]}")
    monkeypatch.setattr(engine, "_run_capture", _blocked)
    monkeypatch.setattr(engine, "_run_stream", _blocked)
    monkeypatch.setattr(engine, "_keyring", lambda: (_ for _ in ()).throw(RuntimeError("testte gerçek şifre kasası yok")))


@pytest.fixture(autouse=True)
def _private_state(monkeypatch, tmp_path):
    """Testler gerçek ~/.secondbrain kayıtlarına (kullanım, performans, çökme, önbellek) yazmasın."""
    from sb import brain, config, gcal_api, router, telemetry, usage
    (tmp_path / "data").mkdir(exist_ok=True)

    def _no_real_calendar(*a, **k):                                 # CI'da giriş yok: testler gerçek Google'a gitmesin
        raise RuntimeError("testte gerçek Google Takvim yok — sahte takvim ver")
    monkeypatch.setattr(gcal_api, "Calendar", _no_real_calendar)
    monkeypatch.setattr(config, "DATA", tmp_path / "data")       # Faz 2 modülleri config.DATA'yı işlev içinde okur
    monkeypatch.setattr(brain, "DB", tmp_path / "brain.db")
    monkeypatch.setattr(brain, "VEC_NPY", tmp_path / "vecs.npy")
    monkeypatch.setattr(brain, "IDS_NPY", tmp_path / "vec_ids.npy")
    monkeypatch.setattr(usage, "FILE", tmp_path / "usage.jsonl")
    monkeypatch.setattr(usage, "WARN_FILE", tmp_path / "usage_warn.json")
    monkeypatch.setattr(telemetry, "DATA", tmp_path)
    monkeypatch.setattr(router, "CACHE_DIR", tmp_path / "llm_cache")


@pytest.fixture(autouse=True)
def _fixed_config(monkeypatch):
    from sb import categorize, projects, sessions
    monkeypatch.setattr(categorize, "RULES_FILE", Path(__file__).parent / "fixtures" / "mail_rules.yaml")
    categorize.rules.cache_clear()
    monkeypatch.setattr(projects, "OWNER", "testuser")
    monkeypatch.setattr(sessions, "GITHUB_USER", "testuser")
    yield
    categorize.rules.cache_clear()
