"""Sabah özeti / uyarı maili: şirket SMTP'si üzerinden, SADECE `accounts.yaml → notify.to` adreslerine.

Gmail hesaplarına gönderme izni verilmez (onlar salt okunur kalır). Şifre keyring'de (`imap-<hesap>`).
Önce SSL 465, olmazsa STARTTLS 587 denenir. Alıcı doğrulaması burada da yapılır: listede olmayan adrese gönderilemez.
"""
from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

import keyring

from .config import KEYRING_SERVICE, accounts
from .redact import redact


def settings() -> dict:
    cfg = accounts().get("notify") or {}
    if not cfg.get("to"):
        raise SystemExit("accounts.yaml içinde notify.to yok")
    smtp = cfg["smtp"]
    acc = accounts()["imap"][smtp["account"]]
    return {"to": list(cfg["to"]), "host": smtp["host"], "user": acc["email"], "alias": smtp["account"]}


def build(subject: str, body: str, to: list[str], sender: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = f"Second Brain <{sender}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1])
    msg["X-Second-Brain"] = "bildirim"
    msg.set_content(redact(body))
    return msg


def send(subject: str, body: str, to: list[str] | None = None) -> str:
    cfg = settings()
    recipients = to or cfg["to"]
    outside = [r for r in recipients if r.lower() not in {a.lower() for a in cfg["to"]}]
    if outside:
        raise PermissionError(f"İzinli alıcı listesinde olmayan adres: {outside}")
    password = keyring.get_password(KEYRING_SERVICE, f"imap-{cfg['alias']}")
    if not password:
        raise SystemExit(f"{cfg['alias']} şifresi yok: sb set-secret imap-{cfg['alias']}")
    msg = build(subject, body, recipients, cfg["user"])
    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(cfg["host"], 465, context=ctx, timeout=30) as s:
            s.login(cfg["user"], password)
            s.send_message(msg, to_addrs=recipients)
        return "465/SSL"
    except (OSError, smtplib.SMTPException) as first:
        try:
            with smtplib.SMTP(cfg["host"], 587, timeout=30) as s:
                s.starttls(context=ctx)
                s.login(cfg["user"], password)
                s.send_message(msg, to_addrs=recipients)
            return "587/STARTTLS"
        except (OSError, smtplib.SMTPException) as second:
            raise RuntimeError(f"Mail gönderilemedi (465: {first}; 587: {second})")
