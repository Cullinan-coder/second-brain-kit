"""m0002 — ortak ön bilgi alanları: `type` taşıyan notlarda eksik `source` / `source_id` alanlarını ekler.

Neden bu göç: kasa şeması (CLAUDE.md) `source` ve `source_id`'yi her notta zorunlu sayar (tekilleştirme anahtarı `source + source_id`),
ama elle yazılmış/sistem notlarının (Asistan.md, Açık konular.md, Makbuzlar, Inbox önerileri ...) çoğunda yoktu. Zararsızdır:
yalnız iki satır eklenir (`source: manual`, `source_id: ""`), var olan hiçbir değer değişmez, okuyan kod eksik alanı zaten "manual" sayar
(geri uyumluluk için okuyucu değişikliği gerekmedi).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

VERSION = 2
DESCRIPTION = "Ortak ön bilgi: eksik source/source_id alanlarını ekle (source: manual, source_id: \"\")"

SKIP_TOP = {"_system", ".git", ".obsidian", "_templates", "_attachments", "node_modules"}
DEFAULTS = (("source", "manual"), ("source_id", '""'))


def _tracked_notes(vault: Path) -> list[str]:
    r = subprocess.run(["git", "-C", str(vault), "ls-files", "-z", "--", "*.md"], capture_output=True)
    if r.returncode:
        raise RuntimeError("git ls-files başarısız: " + r.stderr.decode("utf-8", "replace").strip()[:200])
    return [p for p in r.stdout.decode("utf-8", "surrogateescape").split("\0") if p and p.split("/")[0] not in SKIP_TOP]


def _fix(text: str) -> tuple[str, list[str]]:
    """(yeni metin, eklenen alanlar). Ön bilgi yoksa ya da `type` yoksa dokunmaz."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return text, []
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"), None)
    if end is None:
        return text, []
    keys = {ln.split(":", 1)[0].strip() for ln in lines[1:end] if ":" in ln and not ln[:1].isspace() and not ln.lstrip().startswith("#")}
    if "type" not in keys:
        return text, []
    nl = "\r\n" if lines[0].endswith("\r\n") else "\n"
    add = [(k, v) for k, v in DEFAULTS if k not in keys]
    if not add:
        return text, []
    if not lines[end - 1].endswith(("\n", "\r")):
        lines[end - 1] += nl
    new = [f"{k}: {v}{nl}" for k, v in add]
    return "".join(lines[:end] + new + lines[end:]), [k for k, _ in add]


def up(vault: Path, dry_run: bool) -> list[str]:
    out: list[str] = []
    for rel in _tracked_notes(vault):
        p = vault / rel
        try:
            text = p.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new, added = _fix(text)
        if not added:
            continue
        out.append(f"{rel}: + {', '.join(added)}")
        if not dry_run:
            tmp = p.with_name(p.name + ".sbmig")
            tmp.write_bytes(new.encode("utf-8"))
            os.replace(tmp, p)
    return out
