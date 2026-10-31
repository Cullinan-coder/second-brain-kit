"""Kasa denetleyicisi: frontmatter şeması, tekil source_id ve hassas veri kontrolü.

Kullanım: uv run --project _system python _system/tools/lint.py [kasa_yolu]
Çıkış kodu: hata varsa 1, yoksa 0.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import yaml

REQUIRED = ("type", "status", "tags", "source", "source_id", "created", "updated", "due")

STATUSES = {
    "ders": {"aktif", "tamamlandi", "tekrar"},
    "teslim": {"acik", "tamamlandi", "iptal"},
    "proje": {"fikir", "aktif", "beklemede", "tamamlandi", "arsiv"},
    "kisi": {"aktif", "pasif"},
    "basvuru": {"planlandi", "hazirlaniyor", "gonderildi", "sonuc-bekleniyor", "kabul", "red", "vazgecildi"},
    "gorusme": {"planlandi", "yapildi", "iptal"},
    "gunluk": {"acik"},
    "akademik": {"aktif", "arsiv"},
    "kaynak": {"aktif", "arsiv"},
    "gorev": {"inbox", "aktif", "bekliyor", "engelli", "tamamlandi", "iptal"},
}
# Şemanın dışında kalan, ortak alan zorunluluğu olmayan yardımcı notlar.
FREE_TYPES = {"dashboard", "inbox"}

SOURCES = {
    "manual", "gcal", "gmail-main", "gmail-side", "gdrive",
    "github", "workspace", "contacts", "sms", "linkedin", "obs", "telegram", "mail", "derived", "web",
}

SKIP_DIRS = {".obsidian", ".git", ".trash", "_system", ".venv", "node_modules"}
DATE_FIELDS = ("created", "updated", "due")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
TEMPLATE_VAR_RE = re.compile(r"\{\{\s*(date|time|title)[^}]*\}\}")

TCKN_RE = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")
# Harf/rakam/"/" ile bitişik sayılar kimliktir (ör. people/c123..., takvim id), kart sayılmaz.
CARD_RE = re.compile(r"(?<![\w/])(?:\d[ -]?){13,19}(?![\w/])")
IBAN_RE = re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.I)


def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def tckn_ok(s: str) -> bool:
    d = [int(c) for c in s]
    if (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]


URL_RE = re.compile(r"(?:https?|file)://\S+")


def sensitive_hits(text: str) -> list[str]:
    text = URL_RE.sub(" ", text)  # linklerdeki kimlikler (ör. Gmail thread id) kart no sanılmasın
    hits = []
    for m in TCKN_RE.finditer(text):
        if tckn_ok(m.group()):
            hits.append(f"TCKN olabilir: {m.group()[:3]}***")
    for m in CARD_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            hits.append(f"kart no olabilir: ****{digits[-4:]}")
    for m in IBAN_RE.finditer(text):
        hits.append(f"IBAN olabilir: {m.group()[:4]}***")
    return hits


def check_date(value, field: str, is_template: bool) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return None
    if is_template and isinstance(value, str) and value == "TEMPLATE_DATE":
        return None
    return f"{field} YYYY-MM-DD olmalı, bulunan: {value!r}"


def lint_file(path: Path, vault: Path, seen: dict[tuple[str, str], Path]) -> list[str]:
    rel = path.relative_to(vault).as_posix()
    text = path.read_text(encoding="utf-8")
    is_template = rel.startswith("_templates/")
    errors = [f"{rel}: {h}" for h in sensitive_hits(text)]

    m = FRONTMATTER_RE.match(text)
    if not m:
        if rel in ("CLAUDE.md", "AGENTS.md") or rel.startswith("_") or rel.startswith("00-Inbox/"):   # kutu: ham, düzensiz not serbest
            return errors
        return errors + [f"{rel}: frontmatter yok"]

    raw = m.group(1)
    if is_template:
        raw = TEMPLATE_VAR_RE.sub("TEMPLATE_DATE", raw)
    try:
        fm = yaml.safe_load(raw) or {}
    except yaml.YAMLError as e:
        return errors + [f"{rel}: YAML okunamadı: {e}"]

    ntype = fm.get("type")
    if ntype in FREE_TYPES:
        return errors
    if ntype not in STATUSES:
        return errors + [f"{rel}: bilinmeyen type {ntype!r}"]

    for key in REQUIRED:
        if key not in fm:
            errors.append(f"{rel}: zorunlu alan eksik: {key}")
    status = fm.get("status")
    if status not in STATUSES[ntype]:
        errors.append(f"{rel}: {ntype} için geçersiz status {status!r}")
    if not isinstance(fm.get("tags"), list):
        errors.append(f"{rel}: tags liste olmalı")
    source = fm.get("source")
    if source not in SOURCES and not str(source).startswith("imap-"):   # imap-<takma ad> hesaba göre değişir
        errors.append(f"{rel}: bilinmeyen source {source!r}")
    for field in DATE_FIELDS:
        err = check_date(fm.get(field), field, is_template)
        if err:
            errors.append(f"{rel}: {err}")
    due_time = fm.get("due_time")
    if due_time not in (None, "") and not TIME_RE.match(str(due_time)):
        errors.append(f"{rel}: due_time HH:MM olmalı, bulunan: {due_time!r}")
    if fm.get("visibility") not in (None, "internal", "private"):
        errors.append(f"{rel}: visibility internal ya da private olmalı, bulunan: {fm.get('visibility')!r}")
    if ntype == "gorev":
        if not fm.get("owner"):
            errors.append(f"{rel}: görevin sorumlusu (owner) yok")
        if status == "tamamlandi" and fm.get("completion_criterion"):
            ev = fm.get("evidence") or []
            if not ev:
                errors.append(f"{rel}: bitiş ölçütü olan görev kanıtsız tamamlanmış")
            for e in ev:
                if not (vault / str(e)).exists():
                    errors.append(f"{rel}: kanıt dosyası yok: {e}")

    sid = fm.get("source_id")
    if sid not in (None, "") and not is_template:
        key = (str(source), str(sid))
        if key in seen:
            errors.append(f"{rel}: source_id tekrarı, ilk not: {seen[key].relative_to(vault).as_posix()}")
        else:
            seen[key] = path
    return errors


def iter_notes(vault: Path):
    for p in sorted(vault.rglob("*.md")):
        parts = p.relative_to(vault).parts
        if any(part in SKIP_DIRS for part in parts[:-1]):
            continue
        yield p


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    vault = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[2]
    seen: dict[tuple[str, str], Path] = {}
    errors: list[str] = []
    count = 0
    for note in iter_notes(vault):
        count += 1
        errors.extend(lint_file(note, vault, seen))
    for e in errors:
        print(f"HATA  {e}")
    print(f"{count} not tarandı, {len(errors)} hata.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
