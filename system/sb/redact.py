"""Kasaya yazılmadan önce hassas veriyi maskeler (TCKN, kart no, IBAN, doğrulama kodları)."""
from __future__ import annotations

import re

TCKN_RE = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")
# Harf/rakam/"/" ile bitişik sayılar kimliktir (ör. people/c123..., takvim id), kart sayılmaz.
CARD_RE = re.compile(r"(?<![\w/])(?:\d[ -]?){13,19}(?![\w/])")
IBAN_RE = re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.I)
OTP_CONTEXT_RE = re.compile(
    r"(kod|code|şifre|sifre|password|otp|pin|doğrulama|verification)[^\d\n]{0,40}(\d{4,8})(?!\d)", re.I)
# Bilinen API anahtarı biçimleri ve ortam değişkeni atamaları (SMTP_PASSWORD=..., API_KEY: ...).
KEY_RE = re.compile(r"\b(?:AIza[0-9A-Za-z_-]{30,}|sk-(?:ant-|proj-)?[0-9A-Za-z_-]{20,}|gh[pousr]_[0-9A-Za-z]{30,}"
                    r"|xox[abp]-[0-9A-Za-z-]{20,}|AKIA[0-9A-Z]{16})")
ASSIGN_RE = re.compile(r"\b([A-Z][A-Z0-9_]*(?:PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|APIKEY)[A-Z0-9_]*\s*[=:]\s*)"
                       r"(?![\s'\"`$\[{(<]|\.\.\.)(\S{4,})")


def _luhn(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch) * (2 if i % 2 else 1)
        total += n - 9 if n > 9 else n
    return total % 10 == 0


def _tckn(s: str) -> bool:
    d = [int(c) for c in s]
    return (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10 == d[9] and sum(d[:10]) % 10 == d[10]


def redact(text: str) -> str:
    text = KEY_RE.sub("[gizli-anahtar]", text)
    text = ASSIGN_RE.sub(lambda m: m.group(1) + "[gizlendi]", text)
    text = IBAN_RE.sub("TR** **** [IBAN gizlendi]", text)

    def card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group())
        return f"**** {digits[-4:]}" if 13 <= len(digits) <= 19 and _luhn(digits) else m.group()

    text = CARD_RE.sub(card, text)
    text = TCKN_RE.sub(lambda m: "[TCKN gizlendi]" if _tckn(m.group()) else m.group(), text)
    return OTP_CONTEXT_RE.sub(lambda m: m.group(0)[: -len(m.group(2))] + "••••", text)
