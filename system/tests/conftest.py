"""Testler kişisel ayarlardan bağımsız: sabit mail kuralları ve sabit GitHub kullanıcısı."""
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _private_state(monkeypatch, tmp_path):
    """Testler gerçek ~/.secondbrain kayıtlarına (kullanım, performans, çökme, önbellek) yazmasın."""
    from sb import brain, router, telemetry, usage
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
