"""Yollar, kişi profili ve hesap ayarları. Gizli bilgi burada değil, keyring'de."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

VAULT = Path(os.environ.get("SB_VAULT") or Path(__file__).resolve().parents[2])
SYSTEM = VAULT / "_system"
# %LOCALAPPDATA% kullanılmıyor: Claude Code yalıtımı onu sanal bir kopyaya yönlendiriyor.
DATA = Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain")
SECRETS = DATA / "secrets"
CLIENT_SECRET = SECRETS / "client_secret.json"
MAIL_DB = DATA / "mail.db"
KEYRING_SERVICE = "second-brain"


def _load_profile() -> dict:
    for name in ("profile.yaml", "profile.example.yaml"):
        p = SYSTEM / "config" / name
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {}


PROFILE = _load_profile()
USER = str(PROFILE.get("name") or "kullanıcı")                 # asistan istemlerinde hitap
FULL_NAME = str(PROFILE.get("full_name") or USER)
BIO = str(PROFILE.get("bio") or "")
TIMEZONE = str(PROFILE.get("timezone") or "Europe/Istanbul")
GITHUB_USER = str(PROFILE.get("github_user") or "")
WORKSPACE = Path(os.path.expanduser(str(PROFILE.get("workspace") or "~/Workspace/projects")))
IMPORTANT_CATEGORIES = tuple(PROFILE.get("important_mail_categories") or ("okul", "basvuru-yarisma", "kariyer", "kisisel", "finans"))
LMS = PROFILE.get("lms") or {}


def accounts() -> dict:
    return yaml.safe_load((SYSTEM / "config" / "accounts.yaml").read_text(encoding="utf-8"))


def google_account(alias: str) -> dict:
    acc = accounts()["google"].get(alias)
    if not acc:
        raise SystemExit(f"Bilinmeyen Google hesabı: {alias} (accounts.yaml)")
    return acc
