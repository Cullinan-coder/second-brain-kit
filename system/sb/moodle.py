"""Okul Moodle'ı okuyucu (ör. KOÜ e-destek; adres `profile.yaml` → `lms.moodle_url`): mobil uygulama servisi (`moodle_mobile_app`) ile salt okunur erişim.

Giriş: `sb moodle-login` kullanıcı adı + gizli şifre sorar, `login/token.php`'den jeton alır; şifre hiçbir yere yazılmaz,
yalnız jeton keyring'e (`moodle-token`) gider. Bu modül yalnız okuma fonksiyonları çağırır (gönderme/teslim/mesaj yok).
Ders materyalleri telif kapsamında: indirilen dosyalar kasaya değil yerel veri klasörüne (`~/.secondbrain/moodle`) gider
(git'e/telefona girmez); ders notuna yalnız bağlantıları yazılır.

`sb moodle-sync`: her dersin notunda "e-destek" bölümü (hoca, teslimler/seçimler, duyurular, haftalık içerik),
dosyalar yerele; gelecekteki ödev/quiz kapanışları `lms.moodle_calendar: true` ise takvime [ÖDEV] (aynısı varsa eklenmez).
"""
from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request

from .config import KEYRING_SERVICE, LMS

# Okulun Moodle adresi `config/profile.yaml` → `lms.moodle_url` (ör. https://edestek3.kocaeli.edu.tr). Boşsa modül kapalı.
BASE = str((LMS.get("moodle_url") or "")).rstrip("/")
# Kapanış tarihlerini [ÖDEV] olarak takvime doğrudan yaz (`lms.moodle_calendar: true`). Kapalıysa yalnız ders notunda listelenir.
CALENDAR = bool(LMS.get("moodle_calendar", False))
KEY = "moodle-token"
MAX_FILE = 100 * 1024 * 1024
LIVE = ("msteams", "lti", "bigbluebuttonbn")             # canlı ders bağlantıları (haftada tekrarlanır)
ICON = {"resource": "📄", "folder": "📁", "url": "🔗", "page": "📃", "assign": "📝", "quiz": "❓", "choice": "☑",
        "forum": "💬", "label": "🏷", "msteams": "🎥", "lti": "🎥", "bigbluebuttonbn": "🎥"}
# Yalnız okuma: adında `_get_` geçmeyen fonksiyon (teslim, seçim gönderme, mesaj, "view" kaydı...) çağrılmaz.
READ_ONLY = re.compile(r"^[a-z]+_[a-z]+_get_|^core_webservice_get_site_info$")


def _post(path: str, data: dict, timeout: int = 60):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=body, headers={"User-Agent": "MoodleMobile"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _token() -> str | None:
    import keyring
    return keyring.get_password(KEYRING_SERVICE, KEY)


def login() -> int:
    import getpass

    import keyring
    if not BASE:
        print("Önce okulun Moodle adresini yaz: config/profile.yaml → lms.moodle_url (ör. https://edestek3.kocaeli.edu.tr)")
        return 1
    user = input(f"Moodle kullanıcı adı ({BASE}): ").strip()
    pw = getpass.getpass("Şifre (ekranda görünmez): ")
    out = _post("/login/token.php", {"username": user, "password": pw, "service": "moodle_mobile_app"})
    pw = None
    if not out.get("token"):
        print(f"Giriş olmadı: {out.get('error') or out}")
        return 1
    keyring.set_password(KEYRING_SERVICE, KEY, out["token"])
    info = call("core_webservice_get_site_info")
    print(f"Bağlandı: {info.get('fullname')} · {info.get('sitename')} (jeton keyring'de: {KEY})")
    return 0


def _flat(prefix: str, v, out: dict) -> None:
    """Moodle REST dizi/sözlük parametreleri: courseids[0]=5, options[0][name]=x."""
    if isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            _flat(f"{prefix}[{i}]", x, out)
    elif isinstance(v, dict):
        for k, x in v.items():
            _flat(f"{prefix}[{k}]", x, out)
    else:
        out[prefix] = int(v) if isinstance(v, bool) else v


def call(fn: str, **params):
    if not READ_ONLY.match(fn):
        raise PermissionError(f"{fn}: salt okunur modül, yazan fonksiyon çağrılmaz")
    token = _token()
    if not token:
        raise RuntimeError("e-destek jetonu yok: `sb moodle-login`")
    data = {"wstoken": token, "wsfunction": fn, "moodlewsrestformat": "json"}
    for k, v in params.items():
        _flat(k, v, data)
    out = _post("/webservice/rest/server.php", data)
    if isinstance(out, dict) and out.get("exception"):
        raise RuntimeError(f"{fn}: {out.get('errorcode')} {out.get('message')}")
    return out


# ---------------------------------------------------------------- yardımcılar

def text(s: str | None, limit: int = 0) -> str:
    s = re.sub(r"<(br|/p|/li|/div|/h\d)[^>]*>", "\n", s or "", flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = "\n".join(re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in s.splitlines())
    s = re.sub(r"\n{2,}", "\n", s).strip()
    s = re.sub(r"(?m)^(\S{1,12})\n(?=\d)", r"\1 ", s)    # "Chapter\n11: ..." → "Chapter 11: ..."
    return (s[:limit].rstrip() + " …") if limit and len(s) > limit else s


def _one_line(s: str, limit: int) -> str:
    return text(s, limit).replace("\n", " · ")


def _norm(s: str) -> str:
    s = re.sub(r"\([^)]*\)", " ", s)                       # "(UE)", "(Hoca ADI)"
    return re.sub(r"\s+", " ", s).strip().casefold()


def _fmt(ts: int) -> str:
    from datetime import datetime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _safe(s: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", s).strip(" .")[:80]


def _link(p) -> str:
    return "file:///" + urllib.parse.quote(p.as_posix(), safe="/:")


def course_map(vault_root) -> dict[str, tuple[str, object]]:
    """Ders adı (normalize) → (kod, not yolu); bu dönemin ders notlarından (Geçmiş hariç)."""
    from .notes import split_note
    out = {}
    for f in (vault_root / "10-Dersler").glob("*/*.md"):
        if f.parent.name == "Geçmiş":
            continue
        fm, _ = split_note(f.read_text(encoding="utf-8"))
        if fm.get("type") == "ders" and fm.get("code"):
            out[_norm(f.stem)] = (str(fm["code"]), f)
    return out


def _download(url: str, dest, size: int) -> str:
    """Dosyayı indirir (aynı boyutta varsa atlar): 'yeni' | 'var' | 'büyük'."""
    if size and size > MAX_FILE:
        return "büyük"
    if dest.exists() and (not size or dest.stat().st_size == size):
        return "var"
    dest.parent.mkdir(parents=True, exist_ok=True)
    sep = "&" if "?" in url else "?"
    with urllib.request.urlopen(f"{url}{sep}token={_token()}", timeout=300) as r:
        dest.write_bytes(r.read())
    return "yeni"


# ---------------------------------------------------------------- ders bölümü

def _deadlines(cid: int) -> list[dict]:
    out = []
    for a in call("mod_assign_get_assignments", courseids=[cid])["courses"]:
        for x in a["assignments"]:
            if x.get("duedate"):
                out.append({"kind": "ödev", "icon": ICON["assign"], "id": x["id"], "name": x["name"], "ts": x["duedate"],
                            "url": f"{BASE}/mod/assign/view.php?id={x['cmid']}", "intro": _one_line(x.get("intro"), 500)})
    for q in call("mod_quiz_get_quizzes_by_courses", courseids=[cid])["quizzes"]:
        if q.get("timeclose"):
            out.append({"kind": "quiz", "icon": ICON["quiz"], "id": q["id"], "name": q["name"], "ts": q["timeclose"],
                        "url": f"{BASE}/mod/quiz/view.php?id={q['coursemodule']}", "intro": _one_line(q.get("intro"), 300)})
    for ch in call("mod_choice_get_choices_by_courses", courseids=[cid])["choices"]:
        opts = call("mod_choice_get_choice_options", choiceid=ch["id"]).get("options", [])
        mine = [text(o["text"]) for o in opts if o.get("checked")]
        out.append({"kind": "seçim", "icon": ICON["choice"], "id": ch["id"], "name": ch["name"], "ts": ch.get("timeclose") or 0,
                    "url": f"{BASE}/mod/choice/view.php?id={ch['coursemodule']}",
                    "intro": f"Seçimin: **{', '.join(mine)}**" if mine
                    else "⚠ Henüz seçim yapmadın. Seçenekler: " + "; ".join(text(o["text"]) for o in opts)})
    return out


def course_md(c: dict, folder, stats: dict, download: bool) -> tuple[str, list[dict]]:
    """Bir dersin e-destek bölümü (markdown) + teslim/seçim listesi."""
    cid = c["id"]
    m = re.search(r"\(([^()]*)\)\s*$", c["fullname"])
    lines = [f"Hoca: **{m.group(1) if m else '?'}** · [Derse git]({BASE}/course/view.php?id={cid}) · e-destek'ten otomatik (salt okunur)", ""]
    deadlines = _deadlines(cid)
    if deadlines:
        lines.append("**Teslimler / seçimler**")
        for d in sorted(deadlines, key=lambda d: d["ts"] or 9e12):
            when = _fmt(d["ts"]) if d["ts"] else "kapanış yok"
            lines.append(f"- {d['icon']} [{d['name']}]({d['url']}) — **{when}**" + (f" · {d['intro']}" if d["intro"] else ""))
        lines.append("")
    posts = []
    for f in call("mod_forum_get_forums_by_courses", courseids=[cid]):
        if f.get("type") == "news":
            posts += call("mod_forum_get_forum_discussions", forumid=f["id"]).get("discussions", [])
    lines.append(f"**Duyurular** ({len(posts)})")
    lines += [f"- {_fmt(p['created'])[:10]} · **{text(p['name'])}**" + (f" — {_one_line(p['message'], 400)}" if text(p["message"]) else "")
              for p in sorted(posts, key=lambda p: -p["created"])[:15]] or ["- yok"]
    lines += ["", "**Haftalar**"]
    pages = None
    seen = set()
    for s in call("core_course_get_contents", courseid=cid):
        mods = [x for x in s["modules"] if x.get("uservisible", True) and not (x["modname"] == "forum" and x["name"] == "Duyurular")]
        summ = _one_line(s.get("summary"), 600)
        if not mods and not summ:
            continue
        lines.append(f"- **{s['name']}**" + (f" — {summ}" if summ else ""))
        for x in mods:
            if x["modname"] in LIVE:
                if (x["modname"], x["name"]) in seen:
                    continue
                seen.add((x["modname"], x["name"]))
            icon = ICON.get(x["modname"], "•")
            if x["modname"] == "label":
                lines.append(f"    - {icon} {_one_line(x.get('description'), 500)}")
                continue
            item = f"    - {icon} [{text(x['name'])}]({x.get('url') or BASE})"
            if x["modname"] == "url" and x.get("contents"):
                item += f" → <{x['contents'][0].get('fileurl')}>"
            desc = _one_line(x.get("description"), 200)
            if desc and x["modname"] not in ("page", "assign", "choice"):
                item += f" — {desc}"
            files = [f for f in x.get("contents", []) if f.get("type") == "file"] if x["modname"] in ("resource", "folder") else []
            if files and download:
                links = []
                for f in files:
                    sub = [_safe(p) for p in f.get("filepath", "/").strip("/").split("/") if p]
                    dest = folder.joinpath(_safe(s["name"]) or "genel", *sub, _safe(f["filename"]) or "dosya")
                    try:
                        st = _download(f["fileurl"], dest, f.get("filesize") or 0)
                    except Exception as e:
                        st = "hata"
                        print(f"  ! {f['filename']}: {str(e)[:80]}")
                    stats[st] += 1
                    links.append(f"[{f['filename']}]({_link(dest)})" if dest.exists() else f"{f['filename']} ({st})")
                item += " · " + ", ".join(links)
            elif files:
                item += " · " + ", ".join(f["filename"] for f in files)
            lines.append(item)
            if x["modname"] == "page":
                if pages is None:
                    pages = call("mod_page_get_pages_by_courses", courseids=[cid])["pages"]
                pg = next((p for p in pages if p["coursemodule"] == x["id"]), None)
                if pg:
                    lines += [f"        > {ln}" for ln in text(pg["content"], 3000).splitlines()]
    if lines[-1] == "**Haftalar**":
        lines.append("- Hoca henüz içerik yüklememiş.")
    return "\n".join(lines), [dict(d, course=c) for d in deadlines]


SECTION = "## e-destek (ders sitesi)"


def _ensure_section(body: str) -> str:
    """İlk eşitlemede başlık + otomatik aralık "Teslimler ve sınavlar"ın önüne eklenir (yoksa sona)."""
    if "<!-- sb:auto:edestek:start -->" in body:
        return body
    block = f"{SECTION}\n<!-- sb:auto:edestek:start -->\n<!-- sb:auto:edestek:end -->\n\n"
    i = body.find("## Teslimler ve sınavlar")
    return body[:i] + block + body[i:] if i >= 0 else body.rstrip() + "\n\n" + block


# ---------------------------------------------------------------- eşitleme

def sync(apply: bool = False, download: bool = True) -> int:
    from datetime import date, datetime, time as dtime

    from .config import DATA, VAULT
    from .notes import dump_note, replace_auto, split_note
    if not BASE:
        print("Moodle adresi yok (profile.yaml → lms.moodle_url); atlandı.")
        return 0
    if not _token():
        print("e-destek bağlı değil (`sb moodle-login`); atlandı.")
        return 0
    cmap = course_map(VAULT)
    uid = call("core_webservice_get_site_info")["userid"]
    stats = {"yeni": 0, "var": 0, "büyük": 0, "hata": 0}
    deadlines, changed = [], []
    for c in call("core_enrol_get_users_courses", userid=uid):
        hit = cmap.get(_norm(c["fullname"]))
        if not hit:
            print(f"! kasada eşleşen ders notu yok: {c['fullname']}")
            continue
        code, note = hit
        md, dl = course_md(c, DATA / "moodle" / code, stats, download and apply)
        deadlines += dl
        raw = note.read_text(encoding="utf-8")
        fm, body = split_note(raw)
        body = replace_auto(_ensure_section(body), "edestek", md)
        fm["edestek"] = f"{BASE}/course/view.php?id={c['id']}"
        if dump_note(fm, body) != raw:
            fm["updated"] = date.today()
            if apply:
                note.write_text(dump_note(fm, body), encoding="utf-8", newline="\n")
            changed.append(note.stem)
    print(f"e-destek: {len(changed)} ders notu {'güncellendi' if apply else 'güncellenecek (deneme)'}: {', '.join(changed) or '-'}")
    if download and apply:
        print(f"dosyalar: {stats['yeni']} yeni, {stats['var']} vardı, {stats['büyük']} çok büyük, {stats['hata']} hata → {DATA / 'moodle'}")
    # takvim: gelecekteki ödev/quiz/seçim kapanışları → [ÖDEV] (aynı kimlik ya da gün+başlık varsa eklenmez)
    now = datetime.now().timestamp()
    future = [d for d in deadlines if d["ts"] and d["ts"] > now and not (d["kind"] == "seçim" and "Seçimin:" in d["intro"])]
    if future and not CALENDAR:
        print(f"takvim: {len(future)} kapanış ders notlarında; takvime yazmak için profile.yaml → lms.moodle_calendar: true")
    if future and CALENDAR:
        from .gcal_api import Calendar, NewEvent
        cal = Calendar("main")
        for d in future:
            when = datetime.fromtimestamp(d["ts"])
            at = dtime(when.hour, when.minute) if (when.hour, when.minute) != (0, 0) else None
            name = re.sub(r"\s*\([^)]*\)", "", d["course"]["fullname"]).strip()
            ev = NewEvent(tag="ÖDEV", title=f"{name} – {d['name']}", day=when.date(), at=at, minutes=1,
                          description=f"e-destek: {d['url']}\n{d['intro']}".strip(), source_id=f"moodle:{d['kind']}:{d['id']}")
            st, _ = cal.add(ev, dry_run=not apply)
            print(f"takvim: {ev.summary} · {when:%Y-%m-%d %H:%M} → {st}")
    return 0
