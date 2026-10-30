"""Keyring'deki gizlilerin VAR/YOK durumunu gösterir (değerleri asla yazdırmaz).

Kullanım: uv run --directory _system python tools/secrets_status.py [--delete <ad>]
"""
import os
import sys

import keyring

SERVICE = "second-brain"
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from sb.config import accounts  # noqa: E402
_acc = accounts()
NAMES = [f"google:{a}" for a in (_acc.get("google") or {})] + [f"imap-{a}" for a in (_acc.get("imap") or {})] + \
        ["spotify-refresh", "telegram-bot", "claude-oauth"]

if len(sys.argv) == 3 and sys.argv[1] == "--delete":
    keyring.delete_password(SERVICE, sys.argv[2])
    print(f"{sys.argv[2]} silindi")
for n in NAMES:
    print(f"{n:14} {'VAR' if keyring.get_password(SERVICE, n) else 'yok'}")
print(f"CLAUDE_CODE_OAUTH_TOKEN ortam değişkeni: {'VAR' if os.environ.get('CLAUDE_CODE_OAUTH_TOKEN') else 'yok'}")
