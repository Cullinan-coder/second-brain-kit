"""LinkedIn veri arşivi → kasa. Kaynak: 00-Inbox/_imports altındaki LinkedIn zip'i (git'e girmez).

Kasaya giren: profil (başlık, özet, deneyim, eğitim, beceri, yayın/sertifika → ilgili proje bağlantısı, takip edilen şirketler,
iş tercihi), 153 bağlantı (mevcut kişi notuna 'LinkedIn' bölümü ya da yeni kişi notu), mesajlar (yalnız mail.db'ye, aranabilir).
Kasaya GİRMEYEN: doğum tarihi, adres, telefon, reklam hedefleme, faturalar, kimlik doğrulama, kayıt IP'si.
Tekrar çalıştırılabilir: notlar source+source_id ile güncellenir, mesajlar kimlikle tekilleşir.
"""
from __future__ import annotations

import csv
import hashlib
import re
import sqlite3
import zipfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from .config import DATA, VAULT
from .notes import NoteSpec, Vault, dump_note, replace_auto, split_note
from .redact import redact

IMPORTS = VAULT / "00-Inbox" / "_imports"
PEOPLE = "60-Kişiler"
PROFILE_TITLE = "LinkedIn profili"
# Yayın/sertifika başlığındaki anahtar kelime → kasadaki proje notu
PROJECT_HINTS = {"akreditasyon": "yok-accreditation-model", "akts": "course-credits-system", "kredi hesaplama": "course-credits-system"}


def _fold(s: str) -> str:
    return " ".join(s.lower().translate(str.maketrans("ıİğüşöçâî", "iigusocai")).split())


def find_export() -> Path | None:
    zips = sorted([p for p in IMPORTS.glob("*.zip") if "linkedin" in p.name.lower()], key=lambda p: p.stat().st_mtime)
    return zips[-1] if zips else None


def extract(zpath: Path) -> Path:
    dest = DATA / "imports" / zpath.stem
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            if info.filename.lower().endswith(".csv"):
                z.extract(info, dest)                    # zipfile yolları kökün dışına çıkarmaz
    return dest


def read(folder: Path, name: str, first_col: str | None = None) -> list[dict]:
    p = folder / name
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8-sig").splitlines()
    if first_col:                                        # Connections.csv başında açıklama satırları var
        lines = lines[next((i for i, l in enumerate(lines) if l.startswith(first_col)), 0):]
    return [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(lines)]


def _project_link(title: str) -> str:
    t = _fold(title)
    for key, proj in PROJECT_HINTS.items():
        if key in t and (VAULT / "20-Projeler" / f"{proj}.md").exists():
            return f" → [[{proj}]]"
    return ""


def profile_spec(d: Path) -> NoteSpec:
    prof = (read(d, "Profile.csv") or [{}])[0]
    pos = read(d, "Positions.csv")
    edu = read(d, "Education.csv")
    skills = [r["Name"].strip() for r in read(d, "Skills.csv") if r.get("Name")]
    pubs = read(d, "Publications.csv")
    certs = read(d, "Certifications.csv")
    langs = read(d, "Languages.csv")
    follows = [r["Organization"] for r in read(d, "Company Follows.csv") if r.get("Organization")]
    jobs = (read(d, "Jobs/Job Seeker Preferences.csv") or [{}])[0]
    media = read(d, "Rich_Media.csv")
    summary = re.sub(r"(?<=[.!?])(?=[A-ZÇĞİÖŞÜ•])", "\n\n", prof.get("Summary", "")).replace("•", "\n- ")
    auto = {
        "profil": f"**{prof.get('Headline', '')}**\n\n{prof.get('Industry', '')} · {prof.get('Geo Location', '')}\n\n{redact(summary)}",
        "deneyim": "\n".join(f"- **{r['Title']}** — {r['Company Name']} ({r['Started On']} – {r['Finished On'] or 'devam'})"
                             f"{' · ' + r['Location'] if r.get('Location') else ''}" for r in pos) or "-",
        "egitim": "\n".join(f"- {r['School Name']} {('· ' + r['Degree Name']) if r.get('Degree Name') else ''} "
                            f"({r['Start Date']} – {r['End Date']})" for r in edu) or "-",
        "beceriler": ", ".join(skills) + ("\n\nDiller: " + ", ".join(f"{r['Name']} ({r['Proficiency']})" for r in langs) if langs else ""),
        "yayinlar": "\n".join([f"- Yayın: **{r['Name']}** — {r['Publisher']}{_project_link(r['Name'])}" for r in pubs] +
                              [f"- Sertifika/sunum: **{r['Name']}** — {r['Authority']} ({r['Started On']}){_project_link(r['Name'])}"
                               for r in certs]) or "-",
        "is-tercihi": "\n".join(f"- {k}: {jobs[k]}" for k in ("Job Titles", "Locations", "Preferred Job Types", "Open To Recruiters")
                                if jobs.get(k)) or "-",
        "takip": ", ".join(follows) or "-",
        "paylasimlar": (f"{len(media)} medya paylaşımı; aylara göre: " +
                        ", ".join(f"{m} ({n})" for m, n in sorted(Counter(_media_month(r.get('Date/Time', '')) for r in media).items()))
                        if media else "-"),
    }
    sections = [("Profil", "profil"), ("Deneyim", "deneyim"), ("Eğitim", "egitim"), ("Beceriler", "beceriler"),
                ("Yayınlar ve sunumlar", "yayinlar"), ("İş arama tercihleri", "is-tercihi"), ("Takip edilen şirketler", "takip"),
                ("Paylaşımlar", "paylasimlar")]
    body = f"# {PROFILE_TITLE}\n\n" + "".join(f"## {h}\n<!-- sb:auto:{k}:start -->\n<!-- sb:auto:{k}:end -->\n\n" for h, k in sections)
    return NoteSpec(folder="30-Kariyer", title=PROFILE_TITLE, owned=(), body=body, auto=auto, frontmatter={
        "type": "kaynak", "status": "aktif", "tags": ["kariyer", "linkedin"], "source": "linkedin", "source_id": "linkedin:profile",
        "due": None})


def _media_month(s: str) -> str:
    m = re.search(r"on (\w+) \d+, (\d{4})", s)
    return f"{m.group(2)}-{datetime.strptime(m.group(1), '%B').month:02d}" if m else "?"


def _people_index() -> dict[str, Path]:
    idx = {}
    for p in (VAULT / PEOPLE).glob("*.md"):
        idx.setdefault(_fold(p.stem), p)
    return idx


def _linkedin_block(r: dict, last_msg: str) -> str:
    lines = [f"Kaynak: [[{PROFILE_TITLE}]] · bağlantı tarihi {r.get('Connected On', '?')}"]
    if r.get("Position") or r.get("Company"):
        lines.append(f"- {r.get('Position') or '?'} — {r.get('Company') or '?'}")
    if r.get("URL"):
        lines.append(f"- Profil: {r['URL']}")
    if last_msg:
        lines.append(f"- Son LinkedIn mesajı: {last_msg}")
    return "\n".join(lines)


def _last_messages(msgs: list[dict], me: str) -> dict[str, str]:
    """Kişi adı (katlanmış) → 'tarih — ilk 80 karakter' (en yeni)."""
    out: dict[str, tuple[str, str]] = {}
    for m in msgs:
        other = m["TO"] if _fold(m["FROM"]) == me else m["FROM"]
        key = _fold(other)
        if key and (key not in out or m["DATE"] > out[key][0]):
            out[key] = (m["DATE"], redact(" ".join(m.get("CONTENT", "").split()))[:80])
    return {k: f"{d[:10]} — {t}" for k, (d, t) in out.items()}


def connections(d: Path, msgs: list[dict], me: str, dry_run: bool = False) -> tuple[list[NoteSpec], int]:
    """Var olan kişi notuna 'linkedin' bölümü yazar (rehber alanlarına dokunmadan); olmayanlar için not şablonu döndürür."""
    idx = _people_index()
    last = _last_messages(msgs, me)
    specs, enriched = [], 0
    for r in read(d, "Connections.csv", first_col="First Name"):
        name = f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip()
        if not name:
            continue
        block = _linkedin_block(r, last.get(_fold(name), ""))
        existing = idx.get(_fold(name))
        if existing and split_note(existing.read_text(encoding="utf-8"))[0].get("source") != "linkedin":
            if not dry_run:
                text = existing.read_text(encoding="utf-8")
                new = replace_auto(text, "linkedin", block) if "sb:auto:linkedin:start" in text else \
                    text.rstrip() + f"\n\n## LinkedIn\n<!-- sb:auto:linkedin:start -->\n{block}\n<!-- sb:auto:linkedin:end -->\n"
                if new != text:
                    existing.write_text(new, encoding="utf-8")
            enriched += 1
            continue
        slug = (r.get("URL", "").rstrip("/").rsplit("/", 1)[-1] or hashlib.sha1(name.encode()).hexdigest()[:12])
        specs.append(NoteSpec(folder=PEOPLE, title=name, owned=("company", "role", "linkedin"), auto={"linkedin": block},
                              body=f"# {name}\n\n## Bağlam\n\n## LinkedIn\n<!-- sb:auto:linkedin:start -->\n<!-- sb:auto:linkedin:end -->\n",
                              frontmatter={"type": "kisi", "status": "aktif", "tags": ["kisi", "linkedin"], "source": "linkedin",
                                           "source_id": f"linkedin:{slug}", "due": None, "company": r.get("Company") or None,
                                           "role": r.get("Position") or None, "relation": "LinkedIn bağlantısı",
                                           "email": [r["Email Address"]] if r.get("Email Address") else None, "phone": None,
                                           "linkedin": r.get("URL") or None}))
    return specs, enriched


def messages_to_db(con: sqlite3.Connection, msgs: list[dict]) -> int:
    from .maildb import insert, known_ids
    known = known_ids(con, "linkedin")
    n = 0
    for m in msgs:
        mid = hashlib.sha1(f"{m['CONVERSATION ID']}|{m['DATE']}|{m['FROM']}".encode()).hexdigest()[:24]
        if mid in known:
            continue
        try:
            ts = datetime.strptime(m["DATE"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        body = m.get("CONTENT", "")
        insert(con, {"account": "linkedin", "id": mid, "thread_id": m["CONVERSATION ID"], "date_ms": int(ts.timestamp() * 1000),
                     "from_addr": m.get("SENDER PROFILE URL"), "from_name": m.get("FROM"), "to_addrs": m.get("TO"),
                     "subject": m.get("SUBJECT") or m.get("CONVERSATION TITLE") or f"LinkedIn: {m.get('FROM')}",
                     "snippet": " ".join(body.split())[:200], "body": body, "labels": [m.get("FOLDER", "")],
                     "attachments": [], "category": "linkedin", "category_src": "rule"})
        n += 1
    con.commit()
    return n


def run(dry_run: bool = False, log=print) -> dict:
    from .maildb import connect
    zp = find_export()
    if not zp:
        raise SystemExit("00-Inbox/_imports altında LinkedIn zip'i yok.")
    d = extract(zp)
    prof = (read(d, "Profile.csv") or [{}])[0]
    me = _fold(f"{prof.get('First Name', '')} {prof.get('Last Name', '')}")
    msgs = read(d, "messages.csv")
    vault = Vault(VAULT, dry_run=dry_run)
    today = date.today()
    vault.upsert(profile_spec(d), today)
    specs, enriched = connections(d, msgs, me, dry_run)
    for s in specs:
        vault.upsert(s, today)
    n_msg = 0 if dry_run else messages_to_db(connect(DATA / "mail.db"), msgs)
    res = {"arşiv": zp.name, "profil": "hazır", "mevcut kişiye eklenen": enriched, "yeni/güncel kişi notu": len(specs),
           "not istatistiği": dict(vault.stats), "yeni mesaj (mail.db)": n_msg}
    log(res)
    return res
