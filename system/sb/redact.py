"""Kasaya yazılmadan önce hassas veriyi maskeler (TCKN, kart no, IBAN, doğrulama kodları)."""
from __future__ import annotations

import re

# Kalıpların TEK kaynağı sb/sensitive.py (D-30); buradaki adlar geriye uyumluluk için.
from .sensitive import (ASSIGN_RE, CARD_RE, IBAN_RE, KEY_RE, OTP_CONTEXT_RE, PEM_RE, PLAIN_PASS_RE,  # noqa: F401
                        SECRET_RE, TCKN_RE)


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


def contains_secret(text: str | None) -> bool:
    """Metin bir sır içeriyor mu? (parola/anahtar, kart, IBAN, TCKN, tek kullanımlık kod.) Bağlayıcılar böyle kaydı maskelemek yerine ATLAR."""
    if not text:
        return False
    return bool(SECRET_RE.search(text) or redact(text) != text)
