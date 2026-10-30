"""Testler kişisel ayarlardan bağımsız: sabit mail kuralları ve sabit GitHub kullanıcısı."""
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _fixed_config(monkeypatch):
    from sb import categorize, projects, sessions
    monkeypatch.setattr(categorize, "RULES_FILE", Path(__file__).parent / "fixtures" / "mail_rules.yaml")
    categorize.rules.cache_clear()
    monkeypatch.setattr(projects, "OWNER", "testuser")
    monkeypatch.setattr(sessions, "GITHUB_USER", "testuser")
    yield
    categorize.rules.cache_clear()
