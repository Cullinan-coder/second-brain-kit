"""Google OAuth: hesap başına ayrı yenileme token'ı, Windows Kimlik Yöneticisi'nde.

Keyring'e sadece refresh_token + kapsamlar yazılır (WinVault boyut sınırı); istemci
kimliği `secrets/client_secret.json` dosyasından okunur.
"""
from __future__ import annotations

import json

import keyring
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import CLIENT_SECRET, KEYRING_SERVICE, google_account

# Mail için SADECE okuma kapsamı. Gönderme/silme/etiketleme kapsamı asla istenmez.
SCOPES = {
    "gmail": "https://www.googleapis.com/auth/gmail.readonly",
    "calendar": "https://www.googleapis.com/auth/calendar.events",
    "contacts": "https://www.googleapis.com/auth/contacts.readonly",
    "drive": "https://www.googleapis.com/auth/drive.readonly",
}
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _key(alias: str) -> str:
    return f"google:{alias}"


def _client() -> dict:
    if not CLIENT_SECRET.exists():
        raise SystemExit(f"İstemci dosyası yok: {CLIENT_SECRET}\nRehber: _system/docs/google-cloud-kurulum.md")
    data = json.loads(CLIENT_SECRET.read_text(encoding="utf-8"))
    return data.get("installed") or data["web"]


def scopes_for(alias: str) -> list[str]:
    return [SCOPES[s] for s in google_account(alias)["scopes"]]


def login(alias: str) -> Credentials:
    """Tarayıcıda izin akışı; doğru hesapla girildiğini doğrular ve token'ı saklar."""
    acc = google_account(alias)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), scopes=scopes_for(alias))
    creds = flow.run_local_server(
        port=0, access_type="offline", prompt="consent", login_hint=acc["email"],
        authorization_prompt_message="Tarayıcıda {url} açılıyor...",
        success_message="Second Brain yetkilendirmesi tamam, bu sekmeyi kapatabilirsin.",
    )
    if "gmail" in acc["scopes"]:
        email = build("gmail", "v1", credentials=creds, cache_discovery=False).users().getProfile(userId="me").execute()["emailAddress"]
        if email.lower() != acc["email"].lower():
            raise SystemExit(f"Yanlış hesap: {email} ile giriş yapıldı, beklenen {acc['email']}. Token kaydedilmedi.")
    keyring.set_password(KEYRING_SERVICE, _key(alias), json.dumps({"refresh_token": creds.refresh_token, "scopes": list(creds.scopes or [])}))
    return creds


def credentials(alias: str) -> Credentials:
    raw = keyring.get_password(KEYRING_SERVICE, _key(alias))
    if not raw:
        raise SystemExit(f"{alias} için giriş yok. Çalıştır: uv run python -m sb login {alias}")
    stored = json.loads(raw)
    client = _client()
    creds = Credentials(
        token=None, refresh_token=stored["refresh_token"], token_uri=TOKEN_URI,
        client_id=client["client_id"], client_secret=client["client_secret"], scopes=stored["scopes"],
    )
    creds.refresh(Request())  # token düşmüşse burada google.auth.exceptions.RefreshError verir
    return creds


def service(alias: str, api: str, version: str):
    return build(api, version, credentials=credentials(alias), cache_discovery=False)
