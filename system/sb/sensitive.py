"""Hassas veri ve gizli not kalıplarının TEK kaynağı (D-30).

Eskiden dört ayrı kopya vardı (`vault_ops.SENSITIVE_RE`, `router.SENSITIVE_RE`, `redact.py`, `agents.PRIVATE_RE`) ve aralarında
fark vardı (`pin kodu` yalnız birinde). Hepsi artık buradan okur; eski adlar takma ad olarak kaldı.

İki düzey:
- `SECRET_RE` / `has_secret()`: metin bir sırrın DEĞERİNİ taşıyor mu ("şifre: X", "şifrem 1234", "parola=…", "pin kodu 4321",
  kart/TCKN/IBAN biçimi, API anahtarı). Kasaya, makbuza, hafızaya, kurala, ajana yazmadan önce bakılır. Değer yoksa hassas
  DEĞİLDİR: "şifreli yedek", "şifreleme anahtarını yedekle", "pin kodu değişti" geçer.
- `TOPIC_RE` / `is_sensitive(strict=True)`: bulut süzgeci (router). Değer taşıyan her şey + sır KONUSU sözcükleri ("şifrem şu",
  "IBAN'ım", "tc kimlik"): böyle istem bilgisayardan çıkmaz, yerel modele gider. "şifreli/şifreleme" burada da konu sayılmaz.

Kelime anlamı: "şifre" kökü, ardından "li/lı" (şifreli) ya da "le…" (şifrele, şifreleme, şifrelenmiş) gelirse ŞİFRELEME demektir;
"şifreler" (çoğul) yine paroladır.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------- yapı taşları
# "şifre"/"sifre" kökü; şifreli/şifrele-/şifrelenmiş (encrypted) HARİÇ, şifreler (çoğul) dahil.
PW_STEM = r"(?<!\w)(?:şifre|sifre)(?!l[iı]|le(?!r))"
PW_WORDS = rf"(?:{PW_STEM}|(?<!\w)(?:parola|password|passwd|passcode|pwd)(?!\w*(?:-?protected|less)))"
# Yer tutucu değerler (belgelerde "password: ...", "şifre: <senin şifren>", "$PASS") değer sayılmaz.
_NOT_PLACEHOLDER = r"(?![\s'\"`$\[{(<]|\.\.\.)"
_SUFFIX = r"\w{0,6}"                                   # şifrem, şifresi, parolamız, şifreyi…

TCKN_RE = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")
# Harf/rakam/"/" ile bitişik sayılar kimliktir (ör. people/c123..., takvim id), kart sayılmaz.
CARD_RE = re.compile(r"(?<![\w/])(?:\d[ -]?){13,19}(?![\w/])")
IBAN_RE = re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.I)
# Anahtar sözcük kendi başına geçmeli ("Autoencoder", "spinning" içindeki code/pin sayılmaz); tarihin parçası olan sayı
# ("kod video · son etkinlik 2026-11-03", "03.11.2026") kod değildir.
OTP_CONTEXT_RE = re.compile(
    rf"(?<!\w)(kod|code|{PW_STEM}|password|otp|pin|doğrulama|verification)[^\d\n]{{0,40}}(?<![\d./-])(\d{{4,8}})(?!\d)"
    r"(?![-./]\d{1,2}[-./]\d)", re.I)
# Bilinen API anahtarı biçimleri ve ortam değişkeni atamaları (SMTP_PASSWORD=..., API_KEY: ...).
KEY_RE = re.compile(r"\b(?:AIza[0-9A-Za-z_-]{30,}|sk-(?:ant-|proj-)?[0-9A-Za-z_-]{20,}|gh[pousr]_[0-9A-Za-z]{30,}"
                    r"|xox[abp]-[0-9A-Za-z-]{20,}|AKIA[0-9A-Z]{16})")
ASSIGN_RE = re.compile(r"\b([A-Z][A-Z0-9_]*(?:PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|APIKEY)[A-Z0-9_]*\s*[=:]\s*)"
                       rf"{_NOT_PLACEHOLDER}(\S{{4,}})")
PEM_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
# "parola: hunter2", "token=abcd", "api key: x" — açık ayraçlı değer (bağlayıcılar böyle kaydı atlar).
PLAIN_PASS_RE = re.compile(rf"(?:{PW_WORDS}|(?<!\w)(?:api[_ -]?key|secret|token|gizli anahtar|şifreleme anahtar\w*)){_SUFFIX}"
                           rf"\s*[:=]\s*{_NOT_PLACEHOLDER}\S{{3,}}", re.I)

# ---------------------------------------------------------------- değer taşıyan biçimler (kasaya yazma süzgeci)
_SECRET_PARTS = [
    PLAIN_PASS_RE.pattern,                                                           # şifre: X · parola=… · password: hunter2
    rf"{PW_WORDS}{_SUFFIX}\s+(?:(?:şu|olarak|is|ise)\s*:?\s*)?(?=\S*\d)\S{{3,}}",       # şifrem 1234 · şifre 1234 · password is hunter2
    r"(?<!\w)pin(?:\s*kod\w*)?(?:\s*(?:no|numara\w*))?\s*[:=]?\s*\d{4,8}(?!\d)",       # pin kodu 1234 · pin: 4321
    r"(?<!\w)(?:cvv2?|cvc)\w*\s*[:=]?\s*\d{3,4}(?!\d)",                               # cvv 123
    r"(?<!\w)iban\w*\s*[:=]?\s*[A-Z]{2}\d{2}[\dA-Z ]{10,}",                           # iban: TR..
    IBAN_RE.pattern,
    r"(?<!\w)(?:tc|t\.c\.)\s*kimlik\w*(?:\s*no\w*)?\s*[:=]?\s*\d{11}(?!\d)",          # tc kimlik no 1...
    TCKN_RE.pattern,                                                                 # 11 hane, 0 ile başlamaz (telefon değil)
    r"(?<![\w/.])(?!\d{4}-\d{2}-\d{2})(?:\d[ -]?){12,18}\d(?![\w/])",                  # kart (13-19 hane; tarih dizisi değil)
    rf"(?-i:{KEY_RE.pattern})",
    rf"(?-i:{ASSIGN_RE.pattern})",
    PEM_RE.pattern,
    # redact() izleri: metin önce maskelenip sonra denetlenirse ("kart **** 1111", "şifre ••••") sır vardı demektir.
    r"\*{4} \d{4}(?!\d)|••••|\[(?:gizli-anahtar|gizlendi|TCKN gizlendi)\]|TR\*\* \*{4} \[IBAN gizlendi\]",
]
SECRET_RE = re.compile("|".join(f"(?:{p})" for p in _SECRET_PARTS), re.I)

# ---------------------------------------------------------------- konu sözcükleri (bulut süzgeci, daha sıkı)
TOPIC_RE = re.compile(SECRET_RE.pattern + "|" + "|".join(f"(?:{p})" for p in [
    PW_WORDS, r"(?<!\w)pin\s*kod", r"(?<!\w)cvv", r"(?<!\w)iban", r"kart\s*numara", r"(?<!\w)(?:tc|t\.c\.)\s*kimlik",
]), re.I)


def has_secret(text: str | None) -> bool:
    """Metin bir sırrın değerini taşıyor mu (kasaya/makbuza/hafızaya yazılmaz)."""
    return bool(text) and bool(SECRET_RE.search(text))


def is_sensitive(text: str | None, strict: bool = False) -> bool:
    """strict=False: `has_secret`. strict=True (bulut): sır konusu sözcükleri de sayar ve `redact` metni değiştiriyorsa
    (OTP, geçerli kart/TCKN, anahtar) hassastır."""
    text = text or ""
    if not strict:
        return has_secret(text)
    if TOPIC_RE.search(text):
        return True
    from .redact import redact
    try:
        return redact(text) != text
    except Exception:                                           # noqa: BLE001
        return False


def mask(text: str, repl: str = "[gizli]") -> str:
    return SECRET_RE.sub(repl, text or "")


# ---------------------------------------------------------------- gizli not (visibility: private)
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)
# Gevşek yedek desen (YAML ayrıştırılamazsa): büyük/küçük harf, tırnak, satır sonu yorumu (D-11).
PRIVATE_RE = re.compile(r"^[ \t]*visibility[ \t]*:[ \t]*['\"]?[ \t]*private[ \t]*['\"]?[ \t]*(?:#.*)?$", re.M | re.I)


def is_private_text(text: str) -> bool:
    """Not metni `visibility: private` mi. TEK doğruluk kaynağı (notes, agents, kanca). Ön bilgi YAML olarak ayrıştırılır; BOM, tırnak,
    büyük harf (`Private`), satır sonu yorumu ve uzun ön bilgi fark etmez. Ayrıştırılamıyorsa gevşek desenle bakar (gizli yönünde hata)."""
    import yaml
    t = (text or "").lstrip("﻿")
    if not t.startswith("---"):
        return False
    m = FRONTMATTER_RE.match(t)
    block = m.group(1) if m else t[3:]
    try:
        fm = yaml.safe_load(block)
    except yaml.YAMLError:
        fm = None
    if isinstance(fm, dict):
        return str(fm.get("visibility", "")).strip().lower() == "private" or bool(PRIVATE_RE.search(block))
    return bool(PRIVATE_RE.search(block))
