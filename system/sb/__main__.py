"""sb — second brain komut satırı. `_system` klasöründen çalıştır: `uv run python -m sb <komut>`

  login <hesap>                     Google izni (tarayıcı); token keyring'e
  mail-fetch <hesap> [--full] [--limit N]
                                    Gmail → mail.db (salt okunur)
  mail-ics-backfill <hesap>         Eski maillerdeki .ics eklerini okuyup tarih çıkarmaya yeniden aç
  contacts-sync [--dry-run]         Google Contacts → 60-Kişiler (salt okunur)
  drive-sync                        Drive dosya listesi (+ son 120 gün Docs metni) → mail.db (salt okunur)
  drive-index [--dry-run]           mail.db → 40-Kaynaklar/Drive üst klasör indeks notları
  course-deep <KOD>|--all [--force] Ders dosyalarının metninden Claude ile "Ders dosyası" derle
  sessions-sync                     Claude Code oturumlarını özetle → proje notunda "Oturum günlüğü"
  links [--dry-run]                 Teknoloji/konu bağlantı notları (derlenmiş projelerden)
  content-sync [--limit N]          Belgelerin metnini çıkar (PDF/Word/PPT/Excel/ipynb/metin) → aranabilir arşiv
  search <sorgu>                    Belgeler, mailler, SMS ve Drive içinde ara
  local-files [--dry-run]           Bu bilgisayardaki dosyalar → 40-Kaynaklar/Bilgisayar (link, kopya yok)
  project-deep <klasör>|--all [--force]  Claude (salt okunur) projeyi inceler → notta "Proje dosyası"
  projects-sync [--dry-run]         ~/Workspace/projects + GitHub → 20-Projeler (son çalışmalar, özet)
  course-files [--dry-run]          Bilgisayardaki ders dosyalarını ders notlarına link olarak bağla
  obs-import [--dry-run]            _system/data/obs.yaml (ÖBS, elle) → Akademik Durum + ders not geçmişi
  sms-sync                          Drive'daki SMS Backup & Restore yedekleri → mail.db (sonra contacts-sync)
  mail-categorize [--all]           Kurallarla yeniden kategorile
  mail-index                        40-Kaynaklar/Mail indeks notlarını güncelle
  sync-gcal [--dry-run]             Takvim API → ders/teslim/akademik notları
  import-gcal <events.json>         Takvim JSON anlık görüntüsünden aynı aktarım
  extract-dates [--days N] [--apply]
                                    Maillerden tarih çıkar; --apply olmadan takvime/ dosyaya yazmaz
  approve [--apply]                 onay-bekleyenler.md'de [x] işaretlileri takvime ekle
  set-secret <ad>                   Gizli değeri (ör. claude-oauth) gizli girişle keyring'e kaydet
  daily / weekly                    Otomatik günlük güncelleme + sabah özeti (mail) / haftalık denetim
  notify-test                       Deneme maili (şirket SMTP → sadece kullanıcının adresi)
  telegram setup|pull|send          (İsteğe bağlı) Telegram: bağla / bota yazılanları 00-Inbox'a çek / deneme
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from . import gcal
from .config import DATA, MAIL_DB, VAULT, WORKSPACE, accounts
from .notes import Vault


def _today(args) -> date:
    return date.fromisoformat(args.today) if getattr(args, "today", None) else date.today()


def _import_events(events: list[dict], args) -> None:
    today = _today(args)
    vault = Vault(Path(args.vault) if getattr(args, "vault", None) else VAULT, dry_run=args.dry_run)
    for spec in gcal.build_specs(events, today):
        vault.upsert(spec, today)
    s = vault.stats
    print(f"gcal: {s['created']} yeni, {s['updated']} güncellendi, {s['unchanged']} değişmedi")


def cmd_import_gcal(args) -> int:
    _import_events(json.loads(Path(args.file).read_text(encoding="utf-8"))["events"], args)
    return 0


def cmd_sync_gcal(args) -> int:
    from .gcal_api import Calendar
    now = datetime.now().astimezone()
    events = Calendar("main").list_events(now - timedelta(days=30), now + timedelta(days=365))
    snap = DATA / "raw" / "gcal" / f"snapshot-{now:%Y-%m-%d}.json"
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps({"events": events}, ensure_ascii=False), encoding="utf-8")
    print(f"takvim: {len(events)} etkinlik okundu → {snap}")
    _import_events(events, args)
    return 0


def cmd_login(args) -> int:
    from .google_auth import login
    login(args.account)
    print(f"{args.account}: giriş tamam, token Windows Kimlik Yöneticisi'nde (second-brain).")
    return 0


def cmd_mail_fetch(args) -> int:
    from . import gmail, imap, maildb
    con = maildb.connect(MAIL_DB)
    if args.account in accounts()["imap"]:
        imap.fetch(args.account, con, limit=args.limit)
    else:
        gmail.fetch(args.account, con, full=args.full, limit=args.limit)
    return 0


def cmd_mail_ics_backfill(args) -> int:
    from . import gmail, maildb
    gmail.backfill_ics(args.account, maildb.connect(MAIL_DB))
    return 0


def cmd_courses(args) -> int:
    from . import academic
    for c in academic.courses():
        nd = c.get('next_due') or {}
        print(f"{c.get('code', ''):8} {c.get('name', '')[:40]:40} " + (f"{nd.get('date')} {nd.get('title')}" if isinstance(nd, dict) and nd else '—'))
    return 0


def cmd_gpa(args) -> int:
    from . import academic
    changes = [{"code": k.strip(), "grade": v.strip().upper()} for k, _, v in (w.partition("=") for w in args.what_if) if v]
    out = academic.compute_gpa(academic.load_grades().get("entries", []) if isinstance(academic.load_grades(), dict)
                               else academic.load_grades(), changes or None)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    return 0


def cmd_voice(args) -> int:
    from . import voice
    if args.transcribe:
        p = Path(args.transcribe)
        out = voice.transcribe(p.read_bytes(), "audio/" + p.suffix.lstrip("."), args.lang or None)
        print(out.get("text") or out.get("hint") or out)
        return 0 if out.get("text") is not None else 1
    st = voice.status() if hasattr(voice, "status") else {}
    print(json.dumps(st, ensure_ascii=False, indent=1) if st else "voice modülü yüklü; durum bilgisi yok")
    return 0


def cmd_contacts_sync(args) -> int:
    from . import contacts, maildb
    people = contacts.fetch_all("main")
    specs = contacts.build_specs(people, maildb.connect(MAIL_DB))
    with_mail = sum(1 for s in specs if s.frontmatter["email"])
    with_phone = sum(1 for s in specs if s.frontmatter["phone"])
    print(f"rehber: {len(people)} kişi, {len(specs)} not adayı ({with_mail} mailli, {with_phone} telefonlu)")
    vault = Vault(VAULT, dry_run=args.dry_run)
    today = date.today()
    for spec in specs:
        vault.upsert(spec, today)
    s = vault.stats
    relinked = vault.relink()
    if args.dry_run:
        print(f"DENEME: {s['created']} not oluşturulacak, {s['updated']} güncellenecek, {s['renamed']} yeniden adlandırılacak "
              "(hiçbir şey yazılmadı)")
    else:
        print(f"kişiler: {s['created']} yeni, {s['updated']} güncellendi, {s['renamed']} yeniden adlandırıldı "
              f"({len(relinked)} notta bağlantı güncellendi), {s['unchanged']} değişmedi")
    for old, new in vault.renamed[:40]:
        print(f"  {old} → {new}")
    return 0


def cmd_sms_sync(args) -> int:
    from . import maildb, sms
    con = maildb.connect(MAIL_DB)
    if args.sms:  # test: yerel dosyalar
        print(f"SMS: {sms.import_sms(Path(args.sms), con)} yeni")
        if args.calls:
            print(f"arama: {sms.import_calls(Path(args.calls), con)} yeni")
        return 0
    n_sms, n_calls = sms.sync_from_drive(con, "main")
    print(f"toplam: {n_sms} yeni SMS, {n_calls} yeni arama")
    return 0


def cmd_obs_import(args) -> int:
    from . import obs
    vault = Vault(VAULT, dry_run=args.dry_run)
    today = date.today()
    for spec in obs.build_specs(obs.load()):
        vault.upsert(spec, today)
    s = vault.stats
    print(f"ÖBS: {s['created']} yeni, {s['updated']} güncellendi, {s['unchanged']} değişmedi")
    return 0


def cmd_course_files(args) -> int:
    from . import course_files, maildb
    vault = Vault(VAULT, dry_run=args.dry_run)
    specs, missing = course_files.build_specs(vault, course_files.load(), con=maildb.connect(MAIL_DB))
    today = date.today()
    for spec in specs:
        vault.upsert(spec, today)
    s = vault.stats
    print(f"ders dosyaları: {s['updated']} not güncellendi, {s['unchanged']} değişmedi")
    if missing:
        print(f"notu olmayan ders kodları (atlandı): {', '.join(missing)}")
    return 0


def cmd_projects_sync(args) -> int:
    from . import projects
    today = date.today()
    found = projects.scan(WORKSPACE, today)
    specs = projects.build_specs(found, projects.github_repos(), today)
    vault = Vault(VAULT, dry_run=args.dry_run)
    from .notes import split_note
    for spec in specs:
        existing = vault.index.get(spec.key)
        if existing and split_note(existing.read_text(encoding="utf-8"))[0].get("deep_analyzed"):
            spec.auto.pop("ozet", None)   # derlenmiş özet README'den gelenle ezilmesin
        vault.upsert(spec, today)
    s = vault.stats
    print(f"projeler: {len(specs)} not ({s['created']} yeni, {s['updated']} güncellendi, {s['unchanged']} değişmedi)")
    return 0


def cmd_drive_sync(args) -> int:
    from . import drive, maildb
    drive.sync(maildb.connect(MAIL_DB), "main")
    return 0


def cmd_drive_index(args) -> int:
    from . import drive, maildb
    vault = Vault(VAULT, dry_run=args.dry_run)
    today = date.today()
    for spec in drive.build_specs(maildb.connect(MAIL_DB)):
        vault.upsert(spec, today)
    s = vault.stats
    print(f"drive indeksi: {s['created']} yeni, {s['updated']} güncellendi, {s['unchanged']} değişmedi")
    return 0


def cmd_local_files(args) -> int:
    from . import local_files, maildb
    cfg = local_files.load()
    con = maildb.connect(MAIL_DB)
    local_files.sync(con, cfg)
    vault = Vault(VAULT, dry_run=args.dry_run)
    today = date.today()
    specs = local_files.build_specs(con, cfg)
    for spec in specs:
        vault.upsert(spec, today)
    s = vault.stats
    print(f"bilgisayar indeksi: {len(specs)} klasör notu ({s['created']} yeni, {s['updated']} güncellendi, {s['unchanged']} değişmedi)")
    # Eski kök notları ("local-index:*") ve artık olmayan klasörlerin notları silinmez, 90-Arşiv'e taşınır.
    current = {("workspace", sp.frontmatter["source_id"]) for sp in specs}
    stale = [p for k, p in vault.index.items()
             if k[0] == "workspace" and k[1].startswith(("local-index:", "local-folder:")) and k not in current
             and "90-Arşiv" not in p.relative_to(VAULT).parts]
    if stale and not args.dry_run:
        dest = VAULT / "90-Arşiv" / "Bilgisayar indeksi (eski)"
        dest.mkdir(parents=True, exist_ok=True)
        for p in stale:
            target, n = dest / p.name, 2
            while target.exists():
                target, n = dest / f"{p.stem} ({n}){p.suffix}", n + 1
            p.replace(target)
    print(f"arşive taşınan eski bilgisayar notu: {len(stale)}")
    return 0


def cmd_project_deep(args) -> int:
    base = WORKSPACE
    if args.all:
        failed = []
        for folder in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")):
            try:
                _project_deep(folder, args.force, False)
            except Exception as e:  # bir projenin hatası (ör. abonelik sınırı) diğerlerini durdurmasın
                print(f"{folder.name}: HATA {e}")
                failed.append(folder.name)
                if "limit" in str(e).lower() or "usage" in str(e).lower():
                    print("Abonelik kullanım sınırına takıldı; kalan projeler bir sonraki çalıştırmada derlenir.")
                    break
        print(f"bitti; hatalı: {', '.join(failed) or 'yok'}")
        return 1 if failed else 0
    fold = lambda t: t.lower().translate(str.maketrans("ıığşçöüİ", "iigscoui"))
    match = [p for p in base.iterdir() if p.is_dir() and fold(p.name) == fold(args.folder or "")]  # ASCII yazım da olur
    if not match:
        print(f"klasör yok: {base / (args.folder or '')}")
        return 1
    return _project_deep(match[0], args.force, args.show_prompt)


def _project_deep(folder: Path, force: bool, show_prompt: bool) -> int:
    from . import deep
    from .notes import split_note
    name = folder.name
    vault = Vault(VAULT)
    path = vault.index.get(("workspace", f"projects/{name}"))
    if not path:
        print(f"{name}: proje notu yok; önce `sb projects-sync` çalıştır.")
        return 1
    courses = sorted(p.stem for p in (VAULT / "10-Dersler").rglob("*.md") if split_note(p.read_text(encoding="utf-8"))[0].get("type") == "ders")
    projects = sorted(p.stem for p in (VAULT / "20-Projeler").glob("*.md"))
    fm, body = split_note(path.read_text(encoding="utf-8"))
    fp = deep.fingerprint(folder)
    if fm.get("deep_fingerprint") == fp and not force:
        print(f"{path.stem}: değişiklik yok, derleme atlandı")
        return 0
    prompt = deep.build_prompt(folder, path.stem, courses, projects)
    if show_prompt:
        print(prompt)
        return 0
    print(f"{path.stem}: inceleniyor... ({deep.stamp()})", flush=True)
    raw, label = deep.compile_project(folder, prompt)
    result, meta = deep.parse(raw)
    result = deep.clean_links(deep.fix_tech_links(result), set(courses) | set(projects))
    marker = "<!-- sb:auto:proje-dosyasi:start -->"
    if marker not in body:  # mevcut notlarda bölümü "Amaç"ın üstüne yerleştir
        block = "## Proje dosyası (derlenmiş)\n" + marker + "\n<!-- sb:auto:proje-dosyasi:end -->\n\n"
        body = body.replace("## Amaç", block + "## Amaç", 1) if "## Amaç" in body else body + "\n" + block
        from .notes import dump_note
        path.write_text(dump_note(fm, body), encoding="utf-8", newline="\n")
    from .notes import NoteSpec
    allowed = set(courses) | set(projects)
    related = [x for x in (meta.get("related_courses") or []) + (meta.get("related_projects") or []) if x in allowed]
    from . import llm
    warn = " — YEREL MODEL (dosyalara erişimsiz, hata payı daha yüksek; önemli bilgiyi kaynaktan doğrula)" if llm.is_local(label) else ""
    head = (f"*Derlendi: {deep.stamp()} · model {label if llm.is_local(label) else deep.MODEL} · "
            f"kaynak `~/Workspace/projects/{name}` · parmak izi {fp}{warn}*\n\n")
    auto = {"proje-dosyasi": head + result}
    if deep.summary(result):
        auto["ozet"] = deep.summary(result)
    spec = NoteSpec(folder="", title=path.stem,
                    frontmatter={"source": "workspace", "source_id": f"projects/{name}",
                                 "stack": meta.get("stack") or None, "technologies": deep.technologies(result) or None,
                                 "topics": meta.get("topics") or None,
                                 "related": [f"[[{x}]]" for x in related] or None,
                                 "deep_analyzed": date.today(), "deep_fingerprint": fp},
                    owned=("stack", "technologies", "topics", "related", "deep_analyzed", "deep_fingerprint"),
                    auto=auto)
    Vault(VAULT).upsert(spec, date.today())
    print(f"{path.stem}: proje dosyası yazıldı ({len(result)} karakter, {len(deep.technologies(result))} teknoloji)", flush=True)
    return 0


def cmd_course_deep(args) -> int:
    from . import course_deep, course_files, maildb
    from .notes import NoteSpec, dump_note, split_note
    con = maildb.connect(MAIL_DB)
    files = course_files.files_for(course_files.load())
    notes = {}
    for p in (VAULT / "10-Dersler").rglob("*.md"):
        fm = split_note(p.read_text(encoding="utf-8"))[0]
        if fm.get("type") == "ders" and fm.get("code"):
            notes[str(fm["code"])] = p
    names = sorted({p.stem for p in notes.values()} | {p.stem for p in (VAULT / "20-Projeler").glob("*.md")})
    codes = sorted(notes) if args.all else [args.code]
    failed = []
    for code in codes:
        path, flist = notes.get(code), files.get(code, [])
        if not path or not flist:
            print(f"{code}: {'not yok' if not path else 'bağlı dosya yok'}, atlandı")
            continue
        text = path.read_text(encoding="utf-8")
        fm, body = split_note(text)
        block, fp = course_deep.gather(con, flist)
        if fm.get("deep_fingerprint") == fp and not args.force:
            print(f"{path.stem}: değişiklik yok, atlandı")
            continue
        prompt = course_deep.build_prompt(path.stem, text, block, names)
        if args.show_prompt:
            print(prompt)
            return 0
        print(f"{path.stem}: derleniyor ({len(flist)} dosya, {len(prompt)} karakter) ({course_deep.stamp()})", flush=True)
        try:
            raw, label = course_deep.run(prompt)
            result = course_deep.clean_links(raw, set(names))
        except Exception as e:
            print(f"{path.stem}: HATA {e}")
            failed.append(code)
            if "limit" in str(e).lower() or "usage" in str(e).lower():
                break
            continue
        marker = "<!-- sb:auto:ders-dosyasi:start -->"
        if marker not in body:
            blockmd = "## Ders dosyası (derlenmiş)\n" + marker + "\n<!-- sb:auto:ders-dosyasi:end -->\n\n"
            i = body.find("\n## ")
            body = body[: i + 1] + blockmd + body[i + 1:] if i >= 0 else body + "\n" + blockmd
            path.write_text(dump_note(fm, body), encoding="utf-8", newline="\n")
        src, sid = fm["source"], fm["source_id"]
        Vault(VAULT).upsert(NoteSpec(folder="", title=path.stem, frontmatter={"source": src, "source_id": sid,
                            "deep_analyzed": date.today(), "deep_fingerprint": fp},
                            owned=("deep_analyzed", "deep_fingerprint"),
                            auto={"ders-dosyasi": course_deep.header(fp, len(flist), label) + result}), date.today())
        print(f"{path.stem}: ders dosyası yazıldı ({len(result)} karakter, {label})", flush=True)
    print(f"bitti; hatalı: {', '.join(failed) or 'yok'}")
    return 1 if failed else 0


def cmd_deep_relink(args) -> int:
    """Derlenmiş proje dosyalarını Claude'a sormadan yeniden işler: teknoloji linkleri, link temizliği, listeler."""
    import re as _re
    from . import deep
    from .notes import NoteSpec, split_note
    courses = {p.stem for p in (VAULT / "10-Dersler").rglob("*.md")}
    projects = {p.stem for p in (VAULT / "20-Projeler").glob("*.md")}
    vault = Vault(VAULT)
    for p in sorted((VAULT / "20-Projeler").glob("*.md")):
        fm, body = split_note(p.read_text(encoding="utf-8"))
        m = _re.search(r"<!-- sb:auto:proje-dosyasi:start -->\n(.*?)<!-- sb:auto:proje-dosyasi:end -->", body, _re.S)
        if not m or not fm.get("deep_analyzed"):
            continue
        fixed = deep.clean_links(deep.fix_tech_links(m.group(1)), courses | projects).rstrip()
        auto = {"proje-dosyasi": fixed}
        if deep.summary(fixed):
            auto["ozet"] = deep.summary(fixed)
        vault.upsert(NoteSpec(folder="", title=p.stem, frontmatter={"source": fm["source"], "source_id": fm["source_id"],
                     "technologies": deep.technologies(fixed) or None}, owned=("technologies",), auto=auto), date.today())
    print(f"yeniden bağlandı: {vault.stats}")
    return 0


def cmd_sessions_sync(args) -> int:
    from . import maildb, sessions
    from .notes import NoteSpec, dump_note, split_note
    con = maildb.connect(MAIL_DB)
    folders = [p for p in (WORKSPACE).iterdir() if p.is_dir()]
    if not args.render_only:
        n = sessions.sync(con, folders, include_active=args.include_active)
        print(f"oturumlar: {n} oturum özetlendi")
    vault = Vault(VAULT)
    keys = {r[0] for r in con.execute("SELECT DISTINCT project FROM session_summaries")}
    for key in sorted(keys):
        src, sid = key.split(":", 1)
        path = vault.index.get((src, sid))
        if not path:
            print(f"  {key}: notu yok, atlandı")
            continue
        fm, body = split_note(path.read_text(encoding="utf-8"))
        marker = "<!-- sb:auto:oturumlar:start -->"
        if marker not in body:
            block = "## Oturum günlüğü (Claude Code)\n" + marker + "\n<!-- sb:auto:oturumlar:end -->\n\n"
            body = body.replace("## Son çalışmalar", block + "## Son çalışmalar", 1) if "## Son çalışmalar" in body else body + "\n" + block
            path.write_text(dump_note(fm, body), encoding="utf-8", newline="\n")
        vault.upsert(NoteSpec(folder="", title=path.stem, frontmatter={"source": src, "source_id": sid},
                              owned=(), auto={"oturumlar": sessions.render(con, key)}), date.today())
    print(f"proje notları: {vault.stats}")
    return 0


def cmd_topic_map(args) -> int:
    import yaml
    from . import links
    groups = links.build_topic_map(VAULT)
    links.MAP_FILE.write_text("# Ortak konu başlığı → ona bağlanan serbest ifadeler. Elle düzenlenebilir; sonra `sb links`.\n" +
                              yaml.safe_dump(groups, allow_unicode=True, sort_keys=True, width=1000), encoding="utf-8")
    print(f"{len(groups)} ortak konu başlığı → {links.MAP_FILE}")
    return 0


def cmd_links(args) -> int:
    from . import links
    vault = Vault(VAULT, dry_run=args.dry_run)
    today = date.today()
    specs = links.build_specs(VAULT)
    for spec in specs:
        vault.upsert(spec, today)
    s = vault.stats
    print(f"bağlantı notları: {s['created']} yeni, {s['updated']} güncellendi, {s['unchanged']} değişmedi")
    # Artık hiçbir projede geçmeyen bağlantı notları silinmez, 90-Arşiv'e taşınır (geri alınabilir).
    current = {("derived", sp.frontmatter["source_id"]) for sp in specs}
    stale = [(k, p) for k, p in vault.index.items()
             if k[0] == "derived" and k not in current and "90-Arşiv" not in p.relative_to(VAULT).parts]
    if stale and not args.dry_run:
        dest = VAULT / "90-Arşiv" / "Bağlantı notları (eski)"
        dest.mkdir(parents=True, exist_ok=True)
        for _, p in stale:
            target = dest / p.name
            n = 2
            while target.exists():
                target = dest / f"{p.stem} ({n}){p.suffix}"
                n += 1
            p.replace(target)
    print(f"arşive taşınan eski bağlantı notu: {len(stale)}")
    return 0


def cmd_content_sync(args) -> int:
    from . import content, maildb
    content.sync(maildb.connect(MAIL_DB), limit=args.limit)
    return 0


def cmd_search(args) -> int:
    from . import content, maildb
    hits = content.search(maildb.connect(MAIL_DB), " ".join(args.query), limit=args.limit)
    for kind, line in hits:
        print(f"[{kind}] {line}")
    print(f"{len(hits)} sonuç")
    return 0


def cmd_mail_categorize(args) -> int:
    from . import maildb
    from .categorize import categorize
    con = maildb.connect(MAIL_DB)
    where = "" if args.all else "WHERE category IS NULL"
    rows = con.execute(f"SELECT * FROM messages {where}").fetchall()
    changed = 0
    for r in rows:
        if r["category_src"] == "manual":
            continue
        cat = categorize(dict(r))
        if cat != r["category"]:
            con.execute("UPDATE messages SET category = ?, category_src = 'rule' WHERE account = ? AND id = ?",
                        (cat, r["account"], r["id"]))
            changed += 1
    con.commit()
    print(f"{len(rows)} mesaj tarandı, {changed} kategori değişti")
    for cat, n in con.execute("SELECT category, COUNT(*) FROM messages GROUP BY category ORDER BY 2 DESC"):
        print(f"  {cat:18} {n}")
    return 0


def cmd_mail_index(args) -> int:
    from . import mail_index, maildb
    con = maildb.connect(MAIL_DB)
    vault = Vault(VAULT, dry_run=args.dry_run)
    today = date.today()
    for spec in mail_index.build_specs(con):
        vault.upsert(spec, today)
    s = vault.stats
    print(f"mail indeksi: {s['created']} yeni, {s['updated']} güncellendi, {s['unchanged']} değişmedi")
    return 0


def cmd_extract_dates(args) -> int:
    from . import extract, maildb
    from .gcal_api import Calendar
    con = maildb.connect(MAIL_DB)
    today = _today(args)
    source_of = {k: v["source"] for kind in ("google", "imap") for k, v in accounts()[kind].items()}
    cands = extract.candidates(con, args.days, source_of)
    print(f"{len(cands)} aday mail (son {args.days} gün, tarih ifadesi içeren)")
    if args.limit:
        cands = cands[: args.limit]
    cal = Calendar("main") if args.apply else None
    pending: list[str] = []
    stats = {"calendar": 0, "exists": 0, "pending": 0, "none": 0}
    for i in range(0, len(cands), extract.BATCH):
        batch = cands[i:i + extract.BATCH]
        by_id = {c.id: c for c in batch}
        # Deneme çalıştırmasında görülen sonuç varsa aynısı kullanılır: onaylanan liste ile uygulanan aynı olur.
        fresh = [c for c in batch if c.cached is None]
        items = extract.ask_claude(fresh, today, model=args.model) if fresh else []
        items += [it for c in batch if c.cached for it in c.cached]
        raw: dict[str, list] = {c.id: [] for c in batch}
        for it in items:
            raw.setdefault(it.get("mail_id"), []).append(it)
        decided: dict[str, list] = {c.id: [] for c in batch}
        for item in items:
            ev, err = extract.validate(item, set(by_id), today)
            c = by_id.get(item.get("mail_id"))
            if not ev or not c:
                print(f"  atlandı: {err} {item.get('title', '')!r}")
                continue
            ev.source_id = f"{c.source}:{c.id}"
            ev.description = f"Kaynak mail: {c.subject} ({c.sender}, {c.received})"
            conf = float(item.get("confidence") or 0)
            when = f"{ev.day} {ev.at:%H:%M}" if ev.at else str(ev.day)
            if conf >= extract.THRESHOLD:
                if args.apply:
                    status, _ = cal.add(ev, dry_run=False)
                    stats["exists" if status == "exists" else "calendar"] += 1
                else:
                    status = "takvime eklenecek"
                    stats["calendar"] += 1
                print(f"  [{conf:.2f}] {ev.summary} | {when} → {status}")
                decided[c.id].append({**item, "decision": "calendar"})
            else:
                pending.append(extract.pending_line(ev, ev.source_id, conf, item.get("reason", "")))
                stats["pending"] += 1
                print(f"  [{conf:.2f}] {ev.summary} | {when} → onay bekliyor")
                decided[c.id].append({**item, "decision": "pending"})
        if args.apply:
            for mid, res in decided.items():
                dec = "calendar" if any(r["decision"] == "calendar" for r in res) else ("pending" if res else "none")
                stats["none"] += dec == "none"
                con.execute("INSERT OR REPLACE INTO extractions(account, id, result, decision) VALUES (?, ?, ?, ?)",
                            (by_id[mid].account, mid, json.dumps(res, ensure_ascii=False), dec))
        else:
            for c in fresh:
                con.execute("INSERT OR REPLACE INTO extractions(account, id, result, decision) VALUES (?, ?, ?, 'preview')",
                            (c.account, c.id, json.dumps(raw.get(c.id, []), ensure_ascii=False)))
        con.commit()
    if args.apply and pending:
        added = extract.append_pending(pending)
        print(f"onay-bekleyenler.md: {added} yeni satır")
    print(("UYGULANDI: " if args.apply else "DENEME (hiçbir şey yazılmadı): ") + json.dumps(stats, ensure_ascii=False))
    return 0


def cmd_housekeep(args) -> int:
    from . import vault_ops
    items = vault_ops.housekeep(dry_run=not args.apply)
    if args.apply:
        n = vault_ops.compact_cards()
        if n:
            print(f"eski oturum kartı arşive: {n}")
    print(("arşive taşındı" if args.apply else "arşive taşınacak (deneme)") + f": {len(items)}")
    for x in items:
        print(f"  {x}")
    return 0


def cmd_approve(args) -> int:
    from . import extract
    from .gcal_api import Calendar
    items = extract.approved()
    if not items:
        print("Onaylanmış ([x]) satır yok.")
        return 0
    cal = Calendar("main")
    added = []
    for line, ev in items:
        status, _ = cal.add(ev, dry_run=not args.apply)
        print(f"  {ev.summary} | {ev.day} → {status}")
        if args.apply and status in ("created", "exists"):
            added.append(line)
    if added:
        extract.mark_added(added, date.today().isoformat())
    return 0


def cmd_add_event(args) -> int:
    """Takvime kurallı (etiket/renk/hatırlatma) tek etkinlik ekler; aynısı varsa eklemez. Varsayılan: deneme."""
    from datetime import time as dtime
    from .gcal_api import RULES, Calendar, NewEvent, build_body, match_tag
    tag = match_tag(args.tag)                                                  # ASCII yazım da olur
    if tag is None:
        print(f"Bilinmeyen etiket: {args.tag}. Geçerliler: {', '.join(RULES)}")
        return 1
    try:
        day = date.fromisoformat(args.date)
        at = dtime.fromisoformat(args.time) if args.time else None
    except ValueError:
        print("Tarih YYYY-AA-GG, saat SS:DD olmalı (ör. 2026-11-13 14:00).")
        return 1
    ev = NewEvent(tag=tag, title=args.title, day=day, at=at, minutes=args.minutes, description=args.note or "",
                  source_id=f"manual:{day.isoformat()}:{args.title.casefold()[:60]}")
    body = build_body(ev)
    mins = [r["minutes"] for r in body["reminders"]["overrides"]]
    print(f"{ev.summary} · {day} {at or '(tüm gün)'} · renk {body['colorId']} · hatırlatma (dk önce): {sorted(mins) or 'yok'}")
    status, _ = Calendar("main").add(ev, dry_run=not args.apply)
    print({"exists": "Takvimde zaten var, eklenmedi.", "dry-run": "DENEME: eklenmedi (eklemek için --apply).",
           "created": "Takvime eklendi."}[status])
    return 0


def cmd_chat(args) -> int:
    from . import chat, llm
    llm.ensure_ollama(llm.config())
    chat.serve(args.port)
    return 0


def cmd_daily(args) -> int:
    from . import runner
    return runner.daily(force=args.force)


def cmd_weekly(args) -> int:
    from . import runner
    return runner.weekly()


def cmd_notify_test(args) -> int:
    from . import mailer
    how = mailer.send("Second Brain deneme", "Bu bir deneme mailidir.\n\nBu mail şirket SMTP'sinden gönderildi; Gmail hesapların salt okunur kalmaya devam ediyor.\n"
                      "Sabah özeti ve uyarılar bu adrese böyle gelecek.")
    print(f"deneme maili gönderildi ({how}) → {', '.join(mailer.settings()['to'])}")
    return 0


def cmd_telegram(args) -> int:
    from . import maildb, telegram
    if args.action == "setup":
        print(f"Telegram bağlandı: {telegram.setup()}")
    elif args.action == "pull":
        print(f"{telegram.pull(maildb.connect(MAIL_DB))} yeni not alındı")
    else:
        print(f"{telegram.send('Second Brain deneme mesajı')} mesaj gönderildi")
    return 0


def cmd_set_secret(args) -> int:
    import getpass

    import keyring
    from .config import KEYRING_SERVICE
    value = getpass.getpass(f"{args.name} değerini yapıştır (ekranda görünmez), Enter: ").strip()
    if not value:
        print("Boş değer, kaydedilmedi.")
        return 1
    keyring.set_password(KEYRING_SERVICE, args.name, value)
    print(f"{args.name} Windows Kimlik Yöneticisi'ne kaydedildi (servis: {KEYRING_SERVICE}).")
    return 0


def cmd_ask(args) -> int:
    from . import llm, providers
    cfg = llm.config()
    spec = args.model or cfg["tasks"].get("chat", "ollama")
    if spec == "ollama":
        spec = "ollama:" + cfg["ollama"]["model"]
    messages = [{"role": "user", "content": args.question}]
    try:
        if args.stream:
            for piece in providers.stream_text(spec, messages):
                print(piece, end="", flush=True)
            print()
        else:
            out = providers.chat(spec, messages)
            print(out["content"])
            print(f"[{out['provider']}:{out['model']} · {out['usage']['input']}+{out['usage']['output']} token]", file=sys.stderr)
    except providers.ProviderError as e:
        print(f"Hata: {e}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if stream:                                   # pythonw (kısayol) altında akış yoktur
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="sb", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("import-gcal")
    g.add_argument("file")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--vault", help="test için farklı kasa kökü")
    g.add_argument("--today", help="test için bugünün tarihi (YYYY-MM-DD)")
    g.set_defaults(func=cmd_import_gcal)

    g = sub.add_parser("sync-gcal")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_sync_gcal)

    g = sub.add_parser("login")
    g.add_argument("account", choices=list(accounts()["google"]))
    g.set_defaults(func=cmd_login)

    g = sub.add_parser("mail-fetch")
    g.add_argument("account", choices=list(accounts()["google"]) + list(accounts()["imap"]))
    g.add_argument("--full", action="store_true")
    g.add_argument("--limit", type=int)
    g.set_defaults(func=cmd_mail_fetch)

    g = sub.add_parser("mail-ics-backfill")
    g.add_argument("account", choices=list(accounts()["google"]))
    g.set_defaults(func=cmd_mail_ics_backfill)

    g = sub.add_parser("contacts-sync")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_contacts_sync)

    g = sub.add_parser("sms-sync")
    g.add_argument("--sms", help="test için yerel sms XML")
    g.add_argument("--calls", help="test için yerel calls XML")
    g.set_defaults(func=cmd_sms_sync)

    g = sub.add_parser("obs-import")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_obs_import)

    g = sub.add_parser("course-files")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_course_files)

    g = sub.add_parser("projects-sync")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_projects_sync)

    g = sub.add_parser("drive-sync")
    g.set_defaults(func=cmd_drive_sync)

    g = sub.add_parser("drive-index")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_drive_index)

    g = sub.add_parser("local-files")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_local_files)

    g = sub.add_parser("project-deep")
    g.add_argument("folder", nargs="?", help="~/Workspace/projects altındaki klasör adı")
    g.add_argument("--all", action="store_true", help="tüm projeler (değişmeyenler atlanır)")
    g.add_argument("--force", action="store_true", help="değişiklik olmasa da yeniden derle")
    g.add_argument("--show-prompt", action="store_true", help="Claude'a gidecek metni göster, çalıştırma")
    g.set_defaults(func=cmd_project_deep)

    g = sub.add_parser("course-deep")
    g.add_argument("code", nargs="?", help="ders kodu, ör. YPZ204")
    g.add_argument("--all", action="store_true")
    g.add_argument("--force", action="store_true")
    g.add_argument("--show-prompt", action="store_true")
    g.set_defaults(func=cmd_course_deep)

    g = sub.add_parser("deep-relink")
    g.set_defaults(func=cmd_deep_relink)

    g = sub.add_parser("sessions-sync")
    g.add_argument("--include-active", action="store_true", help="son 60 dk içinde değişen oturumları da özetle")
    g.add_argument("--render-only", action="store_true", help="Claude çağırmadan sadece notları yeniden yaz")
    g.set_defaults(func=cmd_sessions_sync)

    g = sub.add_parser("topic-map")
    g.set_defaults(func=cmd_topic_map)

    g = sub.add_parser("links")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_links)

    g = sub.add_parser("content-sync")
    g.add_argument("--limit", type=int)
    g.set_defaults(func=cmd_content_sync)

    g = sub.add_parser("search")
    g.add_argument("query", nargs="+")
    g.add_argument("--limit", type=int, default=15)
    g.set_defaults(func=cmd_search)

    g = sub.add_parser("mail-categorize")
    g.add_argument("--all", action="store_true")
    g.set_defaults(func=cmd_mail_categorize)

    g = sub.add_parser("mail-index")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=cmd_mail_index)

    g = sub.add_parser("extract-dates")
    g.add_argument("--days", type=int, default=60)
    g.add_argument("--limit", type=int)
    g.add_argument("--model", default="haiku")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--today")
    g.set_defaults(func=cmd_extract_dates)

    g = sub.add_parser("approve")
    g.add_argument("--apply", action="store_true")
    g.set_defaults(func=cmd_approve)

    g = sub.add_parser("add-event", help="takvime kurallı etkinlik ekle")
    g.add_argument("tag", help="SINAV, SUNUM, ÖDEV, BAŞVURU, GÖRÜŞME, YOLCULUK, RANDEVU, HATIRLATMA, AKADEMİK, TATİL")
    g.add_argument("title", help='ör. "İzgaz – Gaz Açım"')
    g.add_argument("date", help="YYYY-AA-GG")
    g.add_argument("time", nargs="?", help="SS:DD (yoksa tüm gün)")
    g.add_argument("--minutes", type=int, default=60, help="süre (dk)")
    g.add_argument("--note", help="açıklama")
    g.add_argument("--apply", action="store_true", help="gerçekten ekle (yoksa deneme)")
    g.set_defaults(func=cmd_add_event)

    g = sub.add_parser("housekeep", help="süresi geçen/biten teslim, görüşme, başvuruları arşive taşı")
    g.add_argument("--apply", action="store_true", help="gerçekten taşı (yoksa sadece listeler)")
    g.set_defaults(func=cmd_housekeep)

    g = sub.add_parser("doctor", help="kurulumu kontrol et (eksikleri ve ne yapılacağını söyler)")
    g.set_defaults(func=lambda a: __import__("sb.doctor", fromlist=["x"]).run())

    g = sub.add_parser("today", help="bugün: teslimler, bekleyen onaylar, önemli okunmamış mail, eskiyen kaynaklar, son başarısız adım")
    g.add_argument("--json", action="store_true", help="arayüz için JSON çıktı")
    g.set_defaults(func=lambda a: __import__("sb.today", fromlist=["x"]).cli(a))

    g = sub.add_parser("freshness", help="kaynak tazeliği: her kaynağın son içe aktarması, yaşı, nasıl güncellenir")
    g.add_argument("action", nargs="?", choices=["status", "seed"], default="status", help="status (varsayılan) | seed: mail.db geçmişinden ilk kaydı yaz")
    g.add_argument("--json", action="store_true")
    g.add_argument("--dry-run", action="store_true", help="hiçbir şey yazma (tohum bellekte hesaplanır)")
    g.set_defaults(func=lambda a: __import__("sb.freshness", fromlist=["x"]).cli(a))

    g = sub.add_parser("import-inbox", help="00-Inbox/İçe aktar klasöründeki yeni dışa aktarma dosyalarını tanı, içe aktar, _işlendi'ye taşı")
    g.add_argument("--assign", nargs=2, metavar=("DOSYA", "KAYNAK"), help="_tanınmadı altındaki dosyayı seçtiğin kaynakla içe aktar")
    g.add_argument("--me", help="--assign: kendi adın (WhatsApp/Telegram)")
    g.add_argument("--no-create", action="store_true", help="klasör yoksa oluşturma")
    g.set_defaults(func=lambda a: __import__("sb.import_inbox", fromlist=["x"]).cli(a))

    g = sub.add_parser("linkedin-import", help="00-Inbox/_imports altındaki LinkedIn arşivini kasaya aktar")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=lambda a: __import__("sb.linkedin", fromlist=["x"]).run(dry_run=a.dry_run) and 0)

    g = sub.add_parser("inbox-process", help="00-Inbox/Dump notlarını yerel modelle ilgili notlara dağıt")
    g.add_argument("--apply", action="store_true", help="gerçekten dağıt (yoksa yalnız kararları listeler)")
    g.set_defaults(func=lambda a: print("\n".join(__import__("sb.inbox", fromlist=["x"]).process(dry_run=not a.apply))
                                        or "kutu boş") or 0)

    g = sub.add_parser("capture", help="Beyne at: panodaki bağlantı/metni kasaya kaydet (Ctrl+Alt+B)")
    g.add_argument("text", nargs="?", help="pano yerine bu metni/bağlantıyı kaydet")
    g.add_argument("--file", default="", help="dosyayı kaydet (Sağ tık › Gönder › Beyne At bunu kullanır)")
    g.set_defaults(func=lambda a: (lambda c: print(c.capture(a.text)) or 0 if a.text else c.run(a.file))(
        __import__("sb.capture", fromlist=["x"])))

    g = sub.add_parser("arsenal", help="kasada 'Araçlar ve erişimler' notunu güncelle")
    g.set_defaults(func=lambda a: print(__import__("sb.arsenal", fromlist=["x"]).build()) or 0)

    g = sub.add_parser("migrate", help="kasa şema göçleri: --check (salt okunur), --dry-run, --yes (yedek alır, tek commit atar)")
    g.add_argument("--check", action="store_true", help="kaç göç bekliyor, ne değişecek (salt okunur; bekleyen varsa çıkış 3)")
    g.add_argument("--dry-run", action="store_true", help="göçleri deneme kipinde çalıştır: hiçbir şey yazılmaz")
    g.add_argument("--yes", action="store_true", help="bekleyen göçleri uygula (önce şifreli yedek, sonra tek git commit'i)")
    g.set_defaults(func=lambda a: __import__("sb.schema", fromlist=["x"]).cli(check_only=a.check, dry_run=a.dry_run, yes=a.yes))

    g = sub.add_parser("update", help="kit kurulumunu son sürüme getir (notlara ve ayarlara dokunmaz)")
    g.add_argument("--check", action="store_true", help="yalnız yeni sürüm var mı bak")
    g.add_argument("--rollback", action="store_true", help="son güncellemeden önceki yedeğe dön")
    g.add_argument("--recover", action="store_true", help="yarım kalan güncellemeyi tamamla (kodu kitten yeniden kur)")
    g.add_argument("--yes", action="store_true", help="gelen değişiklikleri sormadan çek")
    g.add_argument("--tags-only", action="store_true", help="yalnız etiketli (v*) sürümlere güncelle")
    g.set_defaults(func=lambda a: (lambda u: u.rollback() if a.rollback else u.recover() if a.recover else
                                   u.run(check_only=a.check, yes=a.yes, tags_only=a.tags_only))(
        __import__("sb.update", fromlist=["x"])))

    g = sub.add_parser("verify", help="kurulu kodu kitin SHA256SUMS dosyasıyla karşılaştır (yerel değişiklik/eksik/fazla dosyaları listeler)")
    g.set_defaults(func=lambda a: __import__("sb.kitsums", fromlist=["x"]).cli(a))

    g = sub.add_parser("version", help="kurulu sürüm")
    g.set_defaults(func=lambda a: print(__import__("sb.update", fromlist=["x"]).version()) or 0)

    M = lambda: __import__("sb.memory", fromlist=["x"])
    g = sub.add_parser("receipt", help="iş sonucu makbuzu (kaynak bağlantılı tek satır; günlük nota da düşer)")
    g.add_argument("--summary", required=True)
    g.add_argument("--ref", action="append", default=[], help="kasa içi göreli yol (tekrarlanabilir)")
    g.add_argument("--link", action="append", default=[], help="https bağlantı (PR, sayfa)")
    g.add_argument("--learned", default="", help="kalıcı öğrenim (tek cümle); yoksa boş")
    g.add_argument("--project", default="")
    g.add_argument("--session", default="")
    g.add_argument("--event-id", default="")
    g.set_defaults(func=lambda a: print(M().receipt(a.summary, a.ref, a.link, a.learned, a.project, a.session, a.event_id)) or 0)

    g = sub.add_parser("recap", help="son günlerde ne yapıldı (makbuzlardan)")
    g.add_argument("--days", type=int, default=7)
    g.add_argument("--project", default="")
    g.set_defaults(func=lambda a: print(M().recap(a.days, a.project)) or 0)

    g = sub.add_parser("learn", help="öğrenim adayı defteri")
    g.add_argument("candidate", nargs="?")
    g.add_argument("--source", default="")
    g.add_argument("--scope", default="")
    g.add_argument("--list", action="store_true")
    g.set_defaults(func=lambda a: print(M().learn_list() if a.list or not a.candidate else M().learn(a.candidate, a.source, a.scope)) or 0)

    g = sub.add_parser("concept", help="kavram notu oluştur/güncelle (40-Kaynaklar/Kavramlar)")
    g.add_argument("title")
    g.add_argument("--text", required=True)
    g.add_argument("--point", action="append", default=[])
    g.add_argument("--limits", default="")
    g.add_argument("--source", action="append", default=[])
    g.set_defaults(func=lambda a: print(M().concept(a.title, a.text, a.point, a.limits, a.source)) or 0)

    g = sub.add_parser("connect", help="iki not arasında gerekçeli bağlantı notu")
    g.add_argument("a")
    g.add_argument("b")
    g.add_argument("--why", required=True)
    g.set_defaults(func=lambda a: print(M().connect(a.a, a.b, a.why)) or 0)

    g = sub.add_parser("trace", help="dosya değişmeyen anlamlı sohbetin ≤450 karakterlik izi")
    g.add_argument("text")
    g.add_argument("--session", default="")
    g.add_argument("--project", default="")
    g.set_defaults(func=lambda a: print(M().trace(a.text, a.session, a.project)) or 0)

    g = sub.add_parser("error-log", help="hata kataloğu; aynı hata ikinci kez gelince çözüm kural olur")
    g.add_argument("error")
    g.add_argument("--fix", default="")
    g.set_defaults(func=lambda a: print(M().error_log(a.error, a.fix)) or 0)

    g = sub.add_parser("knowledge-index", help="Kavramlar/_Dizin.md'yi yenile")
    g.set_defaults(func=lambda a: print(M().knowledge_index()) or 0)

    g = sub.add_parser("hook-flush", help="(kanca içi) oturum dökümünü yerel modelle özetleyip günlük nota yaz")
    g.add_argument("--transcript", required=True)
    g.add_argument("--session", required=True)
    g.add_argument("--project", default="")
    g.add_argument("--reason", default="end", choices=["end", "precompact"])
    g.set_defaults(func=lambda a: print(__import__("sb.hookwork", fromlist=["x"]).flush(a.transcript, a.session, a.project, a.reason)) or 0)

    T = lambda: __import__("sb.tasks", fromlist=["x"])
    g = sub.add_parser("task", help="görevler (25-Görevler): add | update | list")
    g.add_argument("action", choices=["add", "update", "list"])
    g.add_argument("title", nargs="?", default="")
    g.add_argument("--text", default="")
    g.add_argument("--owner", default="")
    g.add_argument("--project", default="")
    g.add_argument("--due", default=None)
    g.add_argument("--criterion", default="", help="gözlenebilir bitiş ölçütü (verilirse bitirmek için kanıt gerekir)")
    g.add_argument("--status", default="")
    g.add_argument("--evidence", action="append", default=[], help="kanıt dosyası (kasa içi yol)")
    g.add_argument("--note", default="")
    g.add_argument("--expected-revision", type=int, default=None)
    g.set_defaults(func=lambda a: print(
        T().add(a.title, a.text, a.owner, a.project, a.due, a.criterion, a.status or "aktif") if a.action == "add" else
        T().update(a.title, a.status, a.evidence, a.note, a.expected_revision) if a.action == "update" else
        T().listing(a.status)) or 0)

    g = sub.add_parser("person", help="kişi notuna beyan / çıkarım / takma ad (60-Kişiler)")
    g.add_argument("name")
    g.add_argument("fact", nargs="?", default="")
    g.add_argument("--inference", action="store_true", help="modelin tahmini: onay bekleyen çıkarım")
    g.add_argument("--reject", action="store_true", help="bu metni içeren çıkarımı reddet")
    g.add_argument("--alias", default="")
    g.set_defaults(func=lambda a: print(T().person_fact(a.name, a.fact, a.inference, a.reject, a.alias)) or 0)

    g = sub.add_parser("rule", help="kalıcı kural ekle (--scope proje: yalnız o projede yüklenir)")
    g.add_argument("text")
    g.add_argument("--scope", default="")
    g.set_defaults(func=lambda a: print(__import__("sb.vault_ops", fromlist=["x"]).add_rule(
        (f"[kapsam: {a.scope}] " if a.scope else "") + a.text, actor="claude")) or 0)

    g = sub.add_parser("hygiene", help="hafıza hijyeni raporu (tekrar, kopuk bağlantı, bayat, büyüyen dosya)")
    g.set_defaults(func=lambda a: print((lambda h: h.render(h.report()))(__import__("sb.hygiene", fromlist=["x"]))) or 0)

    g = sub.add_parser("mode", help="Claude Code hafıza modu: normal | ekonomik | manuel (config/hafiza.yaml)")
    g.add_argument("profile", nargs="?", choices=["normal", "ekonomik", "manuel"])
    g.set_defaults(func=lambda a: print(__import__("sb.update", fromlist=["x"]).set_mode(a.profile)) or 0)

    g = sub.add_parser("history-import", help="ChatGPT / Claude.ai / Gemini geçmişini içe aktar (önce --apply olmadan dene)")
    g.add_argument("src", help="dışa aktarım zip'i, klasörü ya da conversations.json")
    g.add_argument("--since", default="")
    g.add_argument("--until", default="")
    g.add_argument("--exclude", default="", help="virgülle ayrılmış kelimeler: geçen sohbet alınmaz")
    g.add_argument("--private", action="store_true", help="notları gizli yap (otomatik bağlama girmez)")
    g.add_argument("--apply", action="store_true")
    g.set_defaults(func=lambda a: print(__import__("sb.history", fromlist=["x"]).run(
        a.src, a.since, a.until, a.exclude, a.private, a.apply)) or 0)

    W = lambda: __import__("sb.worker", fromlist=["x"])
    g = sub.add_parser("qwen", help="yerel Qwen'e iş ver (büyük metin/log/belge özeti; Claude limiti harcanmaz)")
    g.add_argument("instruction")
    g.add_argument("--file", action="append", default=[])
    g.add_argument("--text", default="")
    g.set_defaults(func=lambda a: print(W().run(a.instruction, a.file, a.text)) or 0)

    g = sub.add_parser("night", help="gece koşusu: 00-Inbox/Gece işleri.md maddelerini claude -p ile sırayla çalıştır")
    g.add_argument("--plan", action="store_true", help="yalnız ne çalışacağını göster")
    g.add_argument("--run", action="store_true", help="şimdi çalıştır (bu pencerede, sırayla)")
    g.add_argument("--start", action="store_true", help="arka planda başlat (bitince bildirim)")
    g.add_argument("--add", default="", help="listeye iş ekle")
    g.add_argument("--where", default="", help="--add için çalışma klasörü")
    g.set_defaults(func=lambda a: print(W().night_run() if a.run else W().night_start() if a.start else
                                        W().night_add(a.add, a.where) if a.add else (W().ensure_note() and W().night_plan())) or 0)

    F = lambda: __import__("sb.features", fromlist=["x"])
    g = sub.add_parser("features", help="modülleri aç/kapat (config/features.yaml); listesiz çalıştırınca durumu gösterir")
    g.add_argument("--on", action="append", default=[])
    g.add_argument("--off", action="append", default=[])
    g.set_defaults(func=lambda a: print(F().set_modules(a.on, a.off) if a.on or a.off else F().listing()) or 0)

    g = sub.add_parser("roadmap", help="250 maddelik yol haritasının ilerlemesi (features.yaml)")
    g.add_argument("--mark", default="", help="ör. 3,5,23")
    g.add_argument("--status", default="tamamlandi")
    g.set_defaults(func=lambda a: print(F().mark([int(x) for x in a.mark.split(",") if x.strip()], a.status) if a.mark
                                        else F().roadmap()) or 0)

    TEL = lambda: __import__("sb.telemetry", fromlist=["x"])
    g = sub.add_parser("logs", help="son günlük çalışma logu / çökme raporu; --bundle paylaşılabilir paket üretir")
    g.add_argument("--n", type=int, default=40)
    g.add_argument("--crash", action="store_true", help="son çökme raporunu göster")
    g.add_argument("--bundle", action="store_true", help="son 5 rapor + doctor çıktısını tek zip yap (hiçbir yere gönderilmez)")
    g.set_defaults(func=lambda a: print(f"Paket hazır: {TEL().crash_bundle()}\nGitHub issue'ya ekleyebilirsin; kendiliğinden gönderilmez.")
                   or 0 if a.bundle else print(TEL().logs(a.n, "crash" if a.crash else "daily")) or 0)

    g = sub.add_parser("perf", help="performans panosu (perf.jsonl): adım/sohbet süreleri, p95, hata oranı")
    g.add_argument("--days", type=int, default=7)
    g.set_defaults(func=lambda a: print(TEL().perf_summary(a.days)) or 0)

    g = sub.add_parser("whatsnew", help="son görmediğin sürüm yenilikleri")
    g.add_argument("--all", action="store_true", help="tüm sürümleri göster")
    g.set_defaults(func=lambda a: print(TEL().whatsnew(a.all)) or 0)

    g = sub.add_parser("e2e", help="gerçek kasada salt okunur uçtan uca testler; --live çalışan asistanı da dener")
    g.add_argument("--live", action="store_true")
    g.set_defaults(func=lambda a: __import__("sb.telemetry", fromlist=["x"]).run_e2e(a.live))

    g = sub.add_parser("models", help="yerel model yöneticisi: donanım, öneri, profil, indirme/silme, kendi verinle sınav")
    g.add_argument("--apply", default="", help="profili llm.yaml'a uygula: full|medium|small|cloud (--yes olmadan yalnız fark)")
    g.add_argument("--bench", default="", help="virgüllü model listesi, ör. ollama:qwen3:14b,ollama:qwen3:4b")
    g.add_argument("--n", type=int, default=5, help="sınavda not sayısı")
    g.add_argument("--pull", default="", help="Ollama'ya model indir (--yes gerekir)")
    g.add_argument("--rm", default="", help="Ollama'dan model sil (--yes gerekir)")
    g.add_argument("--yes", action="store_true")
    g.set_defaults(func=lambda a: __import__("sb.models", fromlist=["x"]).cli(a))

    g = sub.add_parser("apps", help="hazır uygulamalar (ClipBoardLine, Nashi): list | status [id] | install <id> | start <id> | autostart <id> [login|startup|off] | update <id> [--accept SÜRÜM] | sync <id|all>")
    g.add_argument("action", choices=["list", "status", "install", "start", "autostart", "update", "sync"])
    g.add_argument("id", nargs="?", default="", help="uygulama kimliği (clipboardline, nashi); status/sync için all")
    g.add_argument("mode", nargs="?", default="", choices=["", "login", "startup", "off"], help="autostart: login = bilgisayar açılınca, startup = Çalışmaya başla ile, off = başlamasın")
    g.add_argument("--force", action="store_true", help="install: kuruluysa da yeniden kur")
    g.add_argument("--background", action="store_true", help="start: arka planda (Nashi tepsiye) başlat")
    g.add_argument("--dry-run", action="store_true", help="sync: yazmadan say")
    g.add_argument("--accept", default="", metavar="SÜRÜM", help="update: bildirilen yeni sürümü kabul et (sürüm+özet sabitlenir, sonra kurulur)")
    g.set_defaults(func=lambda a: __import__("sb.apps", fromlist=["x"]).cli(a))

    g = sub.add_parser("usage", help="model kullanımı ve maliyet özeti (bütçeyle birlikte)")
    g.add_argument("--days", type=int, default=30)
    g.set_defaults(func=lambda a: print(__import__("sb.usage", fromlist=["x"]).summary(a.days)) or 0)

    def cmd_embed_test(a):
        from . import llm, providers
        spec = ((llm.config().get("embedding") or {}).get("model")) or ""
        if not spec:
            print("llm.yaml içinde embedding.model tanımlı değil (ör. ollama:nomic-embed-text).")
            return 1
        try:
            v = providers.embed(spec, [a.text])[0]
        except Exception as e:
            print(f"Gömme başarısız ({spec}): {e}")
            return 1
        print(f"{spec}: {len(v)} boyut\nilk 5: {[round(x, 4) for x in v[:5]]}")
        return 0

    g = sub.add_parser("embed-test", help="yapılandırılmış gömme modeliyle tek metni göm (boyut + ilk 5 değer)")
    g.add_argument("text")
    g.set_defaults(func=cmd_embed_test)

    B = lambda: __import__("sb.brain", fromlist=["x"])
    g = sub.add_parser("index", help="beyin dizinini güncelle (notlar, mailler/mesajlar, belgeler, diğer kaynaklar + gömme)")
    g.add_argument("--sources", default="notes,mail,files,items")
    g.add_argument("--days", type=int, default=730, help="mesajlar için geriye kaç gün")
    g.add_argument("--no-embed", action="store_true")
    g.add_argument("--stats", action="store_true")
    g.set_defaults(func=lambda a: print(B().stats() if a.stats else B().index(tuple(a.sources.split(",")), a.days, not a.no_embed)) or 0)

    g = sub.add_parser("find", help="karma arama (kelime + anlam) bütün kaynaklarda")
    g.add_argument("query")
    g.add_argument("-k", type=int, default=10)
    g.add_argument("--kind", action="append", default=None, help="note | mail | chat | file | item")
    g.add_argument("--since", default=None)
    g.add_argument("--until", default=None)
    g.set_defaults(func=lambda a: print("\n".join(
        f"{h['score']:.3f} [{h['kind']}] {h['date']} {h['title']} — {h['ref']}\n    {' '.join(h['text'].split())[:160]}"
        for h in B().find(a.query, a.k, a.kind, a.since, a.until)) or "Sonuç yok.") or 0)

    g = sub.add_parser("answer", help="beyin dizininden kaynak numaralı cevap")
    g.add_argument("question")
    g.add_argument("--kind", action="append", default=None)
    g.set_defaults(func=lambda a: print(B().answer(a.question, kinds=a.kind)) or 0)

    g = sub.add_parser("similar", help="bir belgeye benzeyen belgeler (doc_id: note:<yol> | mail:<hesap>:<id> ...)")
    g.add_argument("doc_id")
    g.set_defaults(func=lambda a: print("\n".join(f"[{h['kind']}] {h['title']} — {h['ref']}" for h in B().similar(a.doc_id)) or "Yok.") or 0)

    g = sub.add_parser("github-deep", help="GitHub repolarında son N gün issue/PR/yorum/commit/release → items")
    g.add_argument("--days", type=int, default=90)
    g.add_argument("--repo", default="", help="tek repo (ad ya da sahip/ad)")
    g.add_argument("--dry-run", action="store_true", help="yalnız say, yazma")
    g.set_defaults(func=lambda a: __import__("sb.github_deep", fromlist=["x"]).cli(a))

    g = sub.add_parser("derive", help="mail/SMS'ten fatura ve kargo çıkar → items (kural tabanlı)")
    g.add_argument("--days", type=int, default=365)
    g.add_argument("--dry-run", action="store_true", help="yalnız say, yazma")
    g.set_defaults(func=lambda a: __import__("sb.derived", fromlist=["x"]).cli(a))

    g = sub.add_parser("caldav-sync", help="iCloud CalDAV/CardDAV (ve Outlook ICS) takvim+kişileri → items")
    g.add_argument("alias", help="accounts.yaml imap takma adı")
    g.set_defaults(func=lambda a: __import__("sb.caldav", fromlist=["x"]).cli(a))

    g = sub.add_parser("import", help="dışa aktarım dosyasından içe aktar (whatsapp, telegram, kindle, youtube, spotify, browser, rss, arxiv, zotero, bibtex, auto)")
    g.add_argument("source")
    g.add_argument("path", nargs="?")
    g.add_argument("--me", help="kendi adın (WhatsApp/Telegram: mesajların from_addr='me' olur)")
    g.add_argument("--days", type=int, default=365, help="tarayıcı geçmişi: kaç gün geriye (varsayılan 365)")
    g.add_argument("--dry-run", action="store_true", help="yazmadan say: kayıt sayısı, tarih aralığı, 3 örnek başlık")
    g.add_argument("--discover", action="store_true", help="browser: bu bilgisayardaki tarayıcı profillerini listele")
    g.set_defaults(func=lambda a: __import__("sb.connectors", fromlist=["x"]).cli(a))

    g = sub.add_parser("plan", help="bugünün planı: en önemli 3 iş, takvim boşluklarına bloklar, uyarılar")
    g.set_defaults(func=lambda a: __import__("sb.productivity", fromlist=["x"]).main(["plan"]))
    g = sub.add_parser("tasks-board", help="görev panosu (yapılacak / yapılıyor / bitti)")
    g.set_defaults(func=lambda a: __import__("sb.productivity", fromlist=["x"]).main(["board"]))
    g = sub.add_parser("courses", help="ders panosu: yaklaşan sınav/teslim, dosya sayısı")
    g.set_defaults(func=cmd_courses)
    g = sub.add_parser("gpa", help="GANO; --what-if KOD=HARF ile senaryo")
    g.add_argument("--what-if", nargs="*", default=[])
    g.set_defaults(func=cmd_gpa)

    g = sub.add_parser("automation-tick", help="otomasyon kurallarını bir kez değerlendir (dış etkili eylemler onaya düşer)")
    g.set_defaults(func=lambda a: print(__import__("sb.automation", fromlist=["x"]).tick()) or 0)

    PV = lambda: __import__("sb.privacy", fromlist=["x"])
    for name, fn, hlp in (("vault-encrypt", "encrypt_cli", "klasörü şifrele (önce yedek; --folder <klasör> --confirm)"),
                          ("encrypt", "encrypt_cli", "vault-encrypt takma adı; geçmişteki düz metin: --purge-history <klasör> --confirm (onaylı, önce tam yedek, ZORLA push gerekir)"),
                          ("vault-decrypt", "decrypt_cli", "şifreli klasörü aç (--folder <klasör> --confirm)"),
                          ("restore", "restore_cli", "yedekten geri yükle (önce mevcut durumun yedeği; <yedek> --confirm)"),
                          ("security-test", "security_test_cli", "istem enjeksiyonu kalkanı: yerel modelle senaryolar")):
        g = sub.add_parser(name, help=hlp)
        g.add_argument("rest", nargs="*")
        g.add_argument("--folder", default="")
        g.add_argument("--confirm", action="store_true")
        g.add_argument("--purge-history", default="", help="(encrypt) klasörün düz metin git geçmişini temizle; --confirm olmadan yalnız anlatır")
        g.set_defaults(func=lambda a, fn=fn: getattr(PV(), fn)(
            a.rest + (["--folder", a.folder] if a.folder else []) + (["--purge-history", a.purge_history] if a.purge_history else [])
            + (["--confirm"] if a.confirm else [])))

    def _backup_cmd(a):
        r = PV().create_backup()
        print(r.get("message") or (", ".join(r["created"]) + chr(10) + r["note"]))
        return 0 if r.get("ok") else 1
    g = sub.add_parser("backup", help="şifreli kasa yedeği al (~/.secondbrain/backups/*.zip.enc); haftalık görev de alır, son 8 kalır")
    g.set_defaults(func=_backup_cmd)

    g = sub.add_parser("vault-key", help="kasa şifreleme anahtarını yedekle: --export <dosya>")
    g.add_argument("--export", default="")
    g.set_defaults(func=lambda a: PV().vault_key_cli(["--export", a.export] if a.export else []))

    P = lambda: __import__("sb.persona", fromlist=["x"])
    g = sub.add_parser("persona", help="asistan kimliği ve hafıza işleri: --reflect (günlük yansıma), --weekly (beni tanı), --prefs (tercih adayları)")
    g.add_argument("--reflect", action="store_true")
    g.add_argument("--weekly", action="store_true")
    g.add_argument("--prefs", action="store_true")
    g.set_defaults(func=lambda a: print("\n".join(
        [P().daily_reflection()] * a.reflect + [P().weekly_profile()] * a.weekly + [P().learn_prefs()] * a.prefs)
        or json.dumps(P().identity(), ensure_ascii=False, indent=1, default=str)) or 0)

    g = sub.add_parser("voice", help="ses: --setup (faster-whisper kurulum durumu), --transcribe <dosya> (yazıya çevir)")
    g.add_argument("--setup", action="store_true")
    g.add_argument("--transcribe", default="")
    g.add_argument("--lang", default="")
    g.set_defaults(func=cmd_voice)

    E = lambda: __import__("sb.entities", fromlist=["x"])
    g = sub.add_parser("merge-people", help="tekrar kişi notları: öneri yaz (--apply: [x] işaretlileri birleştir; --auto: kurala göre karar ver ve birleştir)")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--auto", action="store_true")
    g.set_defaults(func=lambda a: print(E().auto_merge() if a.auto else
                                        "\n".join(E().apply_merges()) or "İşaretli öneri yok." if a.apply
                                        else E().write_merge_proposals()) or 0)

    g = sub.add_parser("mentions", help="kişi notlarına 'Bahsedildiği yerler' bölümü (beyin dizininden)")
    g.set_defaults(func=lambda a: print(E().write_mentions()) or 0)

    g = sub.add_parser("chat-links", help="WhatsApp/Telegram sohbetlerini kişi ve proje notlarına bağla")
    g.set_defaults(func=lambda a: print(E().write_chat_links()) or 0)

    g = sub.add_parser("clusters", help="notları konu kümelerine ayır (40-Kaynaklar/Kümeler; --docs: belge/mail/sohbet kümeleri → Analiz)")
    g.add_argument("-k", type=int, default=None)
    g.add_argument("--docs", action="store_true")
    g.set_defaults(func=lambda a: print(E().clusters(a.k, kinds=("file", "mail", "chat"), folder=E().DOC_CLUSTERS) if a.docs
                                        else E().clusters(a.k)) or 0)

    g = sub.add_parser("graph-style", help="Obsidian grafiği renkleri (küme başına, kategori); görünürlüğe dokunmaz. "
                                           "--hide: teknik/etiket/ek/bağlantısız düğümleri gizle")
    g.add_argument("--hide", action="store_true")
    g.set_defaults(func=lambda a: print(E().graph_style(hide=a.hide)) or 0)

    g = sub.add_parser("suggest-links", help="anlamca yakın ama bağlı olmayan notlar (--apply: [x] işaretlilere bağlantı; "
                                             "--auto: kurala göre karar ver ve bağla)")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--auto", action="store_true")
    g.add_argument("--threshold", type=float, default=0.83)
    g.set_defaults(func=lambda a: print(E().auto_links() if a.auto else
                                        "\n".join(E().apply_links()) or "İşaretli öneri yok." if a.apply
                                        else E().suggest_links(a.threshold)) or 0)

    g = sub.add_parser("analyze", help="beyin analizleri (40-Kaynaklar/Analiz): zaman çizelgesi, proje haritası, sınıflar, tekrarlar...")
    g.add_argument("what", nargs="?", default="all", choices=["all", "timeline", "projects", "classify", "duplicates", "aging", "freshness",
                                                              "conflicts", "skills", "glossary", "tags", "quality", "trust", "map", "pipeline"])
    g.add_argument("topic", nargs="?", help="timeline için konu")
    g.add_argument("--dry-run", action="store_true", help="kasaya yazma, özet bas")
    g.set_defaults(func=lambda a: __import__("sb.analysis", fromlist=["x"]).cli(a.what, a.topic, a.dry_run))

    g = sub.add_parser("search2", help="gelişmiş arama: doğal dil süzgeçleri, kayıtlı aramalar, araştırma, hatırlama, ek/görsel, SSS")
    g.add_argument("query", nargs="?", default=None, help="doğal dil sorgu ('geçen ay hocadan gelen mailler')")
    g.add_argument("--save", action="store_true", help="sonuçları 40-Kaynaklar/Aramalar'a not olarak kaydet")
    g.add_argument("--recall", default=None, help="yarım hatırlanan şeyi bul")
    g.add_argument("--research", default=None, help="çok adımlı araştırma → 40-Kaynaklar/Araştırmalar")
    g.add_argument("--web", action="store_true", help="--research: alt soruları DuckDuckGo'da da ara (kasa içeriği gitmez)")
    g.add_argument("--attachments", default=None, help="mail ekleri + belge içeriği içinde ara")
    g.add_argument("--images", default=None, help="görsellerin OCR metninde ara")
    g.add_argument("--index", action="store_true", help="görsel OCR dizinini güncelle")
    g.add_argument("--saved", action="store_true", help="kayıtlı aramaları kontrol et (yeni eşleşmeler)")
    g.add_argument("--faq", action="store_true", help="soru günlüğünden 40-Kaynaklar/SSS.md üret")
    g.add_argument("--eval", default=None, help="arama kalite testi YAML'ı (hit@5, MRR)")
    g.set_defaults(func=lambda a: __import__("sb.search", fromlist=["x"]).cli(a))

    g = sub.add_parser("takeout", help="Google Takeout zip'lerinden Gemini, Keep, Chrome, YouTube, etkinlik geçmişi, Play")
    g.add_argument("paths", nargs="+", help="zip dosyaları ya da içinde takeout-*.zip olan klasör")
    g.add_argument("--account", default="google", help="hangi hesap (ör. main, side) — Keep notlarının kimliği için")
    g.add_argument("--dry-run", action="store_true")
    g.set_defaults(func=lambda a: (lambda t, m: print(t.run(
        [str(z) for x in a.paths for z in (sorted(__import__("pathlib").Path(x).glob("takeout-*.zip"))
                                         if __import__("pathlib").Path(x).is_dir() else [x])],
        m.connect(__import__("sb.config", fromlist=["x"]).MAIL_DB), a.account, a.dry_run)) or 0)(
        __import__("sb.connectors.takeout", fromlist=["x"]), __import__("sb.maildb", fromlist=["x"])))

    g = sub.add_parser("asistan-undo", help="asistanın son kasa değişikliğini geri al")
    g.set_defaults(func=lambda a: print(__import__("sb.vault_ops", fromlist=["x"]).undo_last(actor="kullanici")) or 0)

    g = sub.add_parser("chat", help="yerel Qwen asistanı (Obsidian'a gömülür)")
    g.add_argument("--port", type=int, default=8765)
    g.set_defaults(func=cmd_chat)

    g = sub.add_parser("daily")
    g.add_argument("--force", action="store_true", help="bugün zaten çalışmış olsa da çalıştır")
    g.set_defaults(func=cmd_daily)

    g = sub.add_parser("weekly")
    g.set_defaults(func=cmd_weekly)

    g = sub.add_parser("notify-test")
    g.set_defaults(func=cmd_notify_test)

    g = sub.add_parser("telegram")
    g.add_argument("action", choices=["setup", "pull", "send"])
    g.set_defaults(func=cmd_telegram)

    g = sub.add_parser("ask", help="tek soru: verilen (ya da tasks.chat) modele sor, ör. --model openai:gpt-5-mini")
    g.add_argument("question")
    g.add_argument("--model", default="", help="<sağlayıcı>:<model>; boşsa tasks.chat")
    g.add_argument("--stream", action="store_true", help="cevabı parça parça yazdır")
    g.set_defaults(func=cmd_ask)

    g = sub.add_parser("set-secret")
    g.add_argument("name", choices=["claude-oauth", "telegram-bot", *[f"imap-{a}" for a in (accounts().get("imap") or {})],
                                    *[f"api-{n}" for n in ("openai", "anthropic", "gemini", "openrouter", "groq", "deepseek", "mistral")]])
    g.set_defaults(func=cmd_set_secret)

    args = p.parse_args(argv)
    if args.cmd not in ("doctor", "version", "migrate", "update", "logs"):    # kasa koddan yeniyse yazmadan önce uyar
        from . import schema
        schema.warn_if_ahead()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:                           # SystemExit Exception değildir: dokunulmadan geçer
        from . import telemetry
        path = telemetry.crash(e, " ".join(sys.argv[1:] if argv is None else argv))
        print(f"Beklenmeyen hata; rapor: {path}. Paylaşmak için: sb logs --bundle", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
