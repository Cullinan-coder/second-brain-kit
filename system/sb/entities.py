"""Faz 1.4: kişi birleştirme (120), varlık bağlantıları (119), kümeleme (121), bağlantı önerisi (123).

Hepsi ÖNERİ → ONAY düzeniyle çalışır; kasada toplu değişiklik yalnız kullanıcı `[x]` işaretleyince yapılır:
- `00-Inbox/Birleştirme önerileri.md`: aynı kişinin iki notu (ad aksansız aynı / aynı telefon / aynı e-posta). `[x]` → zengin olan
  not kalır, diğeri 90-Arşiv'e taşınır (kaynak kimliği arşivde kaldığı için rehber eşitlemesi onu yeniden açmaz), takma ad ve ek
  bilgiler kalana eklenir.
- `00-Inbox/Bağlantı önerileri.md`: anlamca çok yakın ama birbirine bağlı olmayan not çiftleri. `[x]` → gerekçeli bağlantı notu.
- Varlık bağlantıları: kişi notlarının adı/takma adı geçen notlar ve mesajlar beyin dizininden bulunur; kişi notuna otomatik
  "Bahsedildiği yerler" bölümü yazılır (model gerekmez, kural tabanlı).
- Kümeleme: not gömmeleri k-means ile kümelenir, her küme yerel modelle adlandırılır → `40-Kaynaklar/Kümeler/<ad>.md`.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from . import vault_ops
from .notes import dump_note, replace_auto, safe_filename, split_note

PEOPLE = "60-Kişiler"
MERGE_NOTE = "00-Inbox/Birleştirme önerileri.md"
LINK_NOTE = "00-Inbox/Bağlantı önerileri.md"
CLUSTERS = "40-Kaynaklar/Kümeler"
LINK_RE = re.compile(r"\[\[([^\]|#]+)")


def _fold(s: str) -> str:
    s = s.lower().translate(str.maketrans("ıİğüşöçâîû", "iigusocaiu"))
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def _vals(v) -> list[str]:
    if v in (None, ""):
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def _phone_key(p: str) -> str:
    d = re.sub(r"\D", "", p)
    return d[-10:] if len(d) >= 10 else ""


def people(vault: Path | None = None) -> list[tuple[Path, dict]]:
    root = (vault or vault_ops.VAULT) / PEOPLE
    out = []
    for p in sorted(root.glob("*.md")) if root.exists() else []:
        fm, _ = split_note(p.read_text(encoding="utf-8"))
        out.append((p, fm))
    return out


# ---------------------------------------------------------------- kişi birleştirme (120)
def merge_candidates(vault: Path | None = None) -> list[tuple[Path, Path, str]]:
    plist = people(vault)
    groups: dict[str, list[int]] = defaultdict(list)
    for i, (p, fm) in enumerate(plist):
        name = _fold(re.sub(r"\(\d+\)$", "", p.stem))
        if len(name) >= 5 and " " in name:
            groups[f"ad:{name}"].append(i)
        for ph in _vals(fm.get("phone")):
            if (k := _phone_key(ph)):
                groups[f"tel:{k}"].append(i)
        for em in _vals(fm.get("email")):
            groups[f"mail:{em.lower().strip()}"].append(i)
    pairs: dict[tuple[int, int], list[str]] = defaultdict(list)
    for key, idx in groups.items():
        idx = sorted(set(idx))
        if 1 < len(idx) <= 4:                                  # aynı numarayı paylaşan çok kişi (şirket hattı) aday değil
            for a in range(len(idx)):
                for b in range(a + 1, len(idx)):
                    pairs[(idx[a], idx[b])].append({"ad": "aynı ad", "tel": "aynı telefon", "mail": "aynı e-posta"}[key.split(":")[0]])
    return [(plist[a][0], plist[b][0], ", ".join(sorted(set(why)))) for (a, b), why in sorted(pairs.items())]


def _richness(fm: dict) -> int:
    return sum(1 for k in ("company", "role", "email", "phone", "linkedin", "relation") if fm.get(k)) + (2 if fm.get("source") == "contacts" else 0)


def write_merge_proposals(vault: Path | None = None) -> str:
    vault = vault or vault_ops.VAULT
    cands = merge_candidates(vault)
    p = vault / MERGE_NOTE
    done = set()
    if p.exists():                                            # daha önce reddedilen/işlenen çiftler yeniden önerilmez
        done = {l for l in p.read_text(encoding="utf-8").splitlines() if l.startswith(("- [x]", "- [-]"))}
    lines = [f"- [ ] [[{a.stem}]] ⇄ [[{b.stem}]] — {why}" for a, b, why in cands]
    lines = [l for l in lines if not any(l[6:] in d for d in done)]
    body = ("# Birleştirme önerileri\n\nAynı kişiye ait görünen not çiftleri. Birleştirmek istediğinin kutusunu `[x]` yap, istemediğini "
            "`[-]` yap; `sb merge-people --apply` (ya da günlük çalışma) işler. Zengin olan not kalır, diğeri arşive gider.\n\n"
            + "\n".join(sorted(done) + lines) + "\n")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_note({"type": "inbox", "tags": ["inbox", "oneri"]}, body), encoding="utf-8")
    return f"{len(lines)} yeni birleştirme önerisi ({len(cands)} aday) → {MERGE_NOTE}"


def merge_pair(keep: Path, drop: Path, actor: str = "kullanici") -> str:
    kfm, kbody = split_note(keep.read_text(encoding="utf-8"))
    dfm, dbody = split_note(drop.read_text(encoding="utf-8"))
    aliases = set(_vals(kfm.get("aliases"))) | {drop.stem} | set(_vals(dfm.get("aliases")))
    kfm["aliases"] = sorted(a for a in aliases if a != keep.stem)
    extra = []
    for k in ("company", "role", "relation", "linkedin", "email", "phone"):
        new = [v for v in _vals(dfm.get(k)) if v not in _vals(kfm.get(k))]
        if new and not kfm.get(k) and k not in ("email", "phone"):
            kfm[k] = dfm[k]
        elif new:
            extra.append(f"- {k}: {', '.join(new)}")
    kept_sections = re.sub(r"<!-- sb:auto:.*?:end -->", "", re.sub(r"^#\s.*\n", "", dbody), flags=re.S).strip()
    note = f"\n\n## Birleştirilen: {drop.stem} ({date.today()})\n" + "\n".join(extra)
    if len(kept_sections) > 40:
        note += f"\n\n{kept_sections[:3000]}"
    kfm["updated"] = date.today()
    keep.write_text(dump_note(kfm, kbody.rstrip() + note + "\n"), encoding="utf-8")
    rel = vault_ops._rel(keep)
    vault_ops.commit([rel], f"kişi birleştirildi: {drop.stem} → {keep.stem}")
    return vault_ops.archive(vault_ops._rel(drop), f"{keep.stem} ile birleştirildi", actor=actor)


GENERIC = ROLE_WORDS_MERGE = {"abla", "abi", "abim", "hoca", "hocasi", "hocam", "kuzen", "teyze", "dayi", "dayim", "amca", "hala",
                              "babam", "annem", "kardesim", "ikizler", "yenge", "enistem", "tekno", "teknobil", "is", "ev", "numara",
                              "eski", "yeni", "2", "3", "kimya", "fizik", "matematik", "ogretmen", "ogretmeni", "sahibi", "apart"}


def _core(name: str) -> list[str]:
    """Parantez dışındaki ad sözcükleri (aksansız, ≥2 harf)."""
    return [w for w in _fold(re.sub(r"\(.*?\)", " ", name)).split() if len(w) >= 2]


def merge_decision(a: str, b: str, why: str) -> tuple[bool, str]:
    """Otomatik karar: aynı ad → birleştir; ortak numara/e-posta + ortak ad sözcüğü ya da bir taraf genel/rol adı → birleştir;
    iki ayrı tam ad (ortak sözcük yok) aynı numarayı paylaşıyorsa → ayrı kişiler (ev/iş hattı)."""
    if "aynı ad" in why:
        return True, "aynı ad"
    ca, cb = _core(a), _core(b)
    if set(w for w in ca if len(w) >= 3) & set(w for w in cb if len(w) >= 3):
        return True, "ortak ad + aynı iletişim"
    generic = lambda c: len([w for w in c if w not in GENERIC]) <= 1 or any(w in GENERIC for w in c)
    if generic(ca) or generic(cb):
        return True, "takma/rol adı + aynı iletişim"
    return False, "farklı tam adlar, ortak numara"


def auto_decide(vault: Path | None = None) -> tuple[int, int]:
    """Bekleyen önerileri kurala göre [x] ya da [-] yapar (kullanıcı otomatik birleştirmeye izin verdi)."""
    vault = vault or vault_ops.VAULT
    p = vault / MERGE_NOTE
    if not p.exists():
        return 0, 0
    text, yes, no = p.read_text(encoding="utf-8"), 0, 0
    for line in [l for l in text.splitlines() if l.startswith("- [ ]")]:
        names = LINK_RE.findall(line)
        if len(names) < 2:
            continue
        ok, why = merge_decision(names[0], names[1], line.rsplit("—", 1)[-1])
        text = text.replace(line, line.replace("- [ ]", "- [x]" if ok else "- [-]", 1) + f" (otomatik: {why})", 1)
        yes, no = yes + ok, no + (not ok)
    p.write_text(text, encoding="utf-8")
    return yes, no


def auto_merge(vault: Path | None = None) -> str:
    """Öneri yaz → kurala göre karar → birleştir (kullanıcı 2026-11-01'de sormadan birleştirmeye izin verdi)."""
    w = write_merge_proposals(vault)
    yes, no = auto_decide(vault)
    done = apply_merges(vault)
    return f"{w}\notomatik karar: {yes} birleştir, {no} ayrı kalsın → {len(done)} birleştirme yapıldı"


def _resolve_person(vault: Path, name: str) -> Path | None:
    p = vault / PEOPLE / f"{name}.md"
    if p.exists():
        return p
    for q, fm in people(vault):                                # daha önce birleştirildiyse: takma adı taşıyan not
        if name in _vals(fm.get("aliases")):
            return q
    return None


def apply_merges(vault: Path | None = None) -> list[str]:
    vault = vault or vault_ops.VAULT
    p = vault / MERGE_NOTE
    if not p.exists():
        return []
    text, out = p.read_text(encoding="utf-8"), []
    for line in [l for l in text.splitlines() if l.startswith("- [x]") and "işlendi" not in l]:
        names = LINK_RE.findall(line)
        paths = [_resolve_person(vault, n) for n in names[:2]]
        if len(paths) < 2 or not all(paths) or paths[0] == paths[1]:
            text = text.replace(line, line + (" (zaten birleşik)" if len(paths) == 2 and paths[0] and paths[0] == paths[1]
                                              else " (atlandı: not yok)"))
            continue
        fms = [split_note(x.read_text(encoding="utf-8"))[0] for x in paths]
        score = lambda i: (_richness(fms[i]), len(_core(paths[i].stem)), not re.search(r"\(\d+\)$", paths[i].stem))
        keep, drop = (paths[0], paths[1]) if score(0) >= score(1) else (paths[1], paths[0])
        out.append(merge_pair(keep, drop))
        text = text.replace(line, line + f" (işlendi {date.today()}: {keep.stem} kaldı)")
    p.write_text(text, encoding="utf-8")
    if out:
        vault_ops.commit([MERGE_NOTE], f"birleştirme önerileri işlendi ({len(out)})")
    return out


# ---------------------------------------------------------------- varlık bağlantıları (119)
ROLE_WORDS = {"abla", "abi", "hoca", "hocasi", "hocam", "kuzen", "teyze", "dayi", "amca", "hala", "sinif", "okul", "grup", "kurs",
              "tekno", "teknobil", "sirket", "is", "ev", "ofis", "kargo", "taksi", "usta", "bey", "hanim", "anne", "baba", "yeni", "eski"}


def _real_name(n: str) -> bool:
    """Ad soyad gibi görünen ad: rakam yok, en az iki harf kelimesi (≥2 harf), en az biri ≥3 harf, rol/ilişki sözcüğü yok."""
    if re.search(r"\d", n):
        return False
    words = _fold(n).split()
    return len(words) >= 2 and all(len(w) >= 2 for w in words) and any(len(w) >= 3 for w in words) \
        and not any(w in ROLE_WORDS for w in words)
def mentions(con=None, limit_per_person: int = 12, vault: Path | None = None) -> dict[str, list[dict]]:
    """Her kişi için adının/takma adının geçtiği belgeler (beyin dizini, tam ad ya da takma ad eşleşmesi)."""
    from . import brain
    con = con or brain.connect()
    out: dict[str, list[dict]] = {}
    for p, fm in people(vault):
        names = [n for n in [p.stem] + _vals(fm.get("aliases")) if _real_name(n)]   # "11. Sınıf", "Burcu abla" gibi adlar gürültü
        hits, seen = [], {f"note:{PEOPLE}/{p.name}"}
        for n in names:
            q = " ".join(f'"{w}"' for w in re.findall(r"\w+", n.lower()))
            want = re.compile(r"(?<!\w)" + r"\W{1,3}".join(map(re.escape, _fold(n).split())) + r"(?!\w)")
            try:
                rows = con.execute("SELECT c.doc_id, c.text, d.kind, d.title, d.date_ms, d.ref FROM chunks_fts f JOIN chunks c ON c.id = f.rowid "
                                   "JOIN docs d ON d.doc_id = c.doc_id WHERE chunks_fts MATCH ? ORDER BY d.date_ms DESC LIMIT 60",
                                   (f"NEAR({q}, 1)",)).fetchall()
            except Exception:
                rows = []
            for r in rows:
                if r["doc_id"] in seen or not want.search(_fold(r["text"])):   # tam ad sırasıyla geçmiyorsa sayılmaz
                    continue
                seen.add(r["doc_id"])
                hits.append({k: r[k] for k in ("doc_id", "kind", "title", "date_ms", "ref")})
        if hits:
            out[str(p)] = hits[:limit_per_person]
    return out


def write_mentions(con=None, vault: Path | None = None) -> str:
    from datetime import datetime
    found = mentions(con, vault=vault)
    changed = []
    for p, _ in people(vault):                                 # artık eşleşmesi kalmayan eski bölüm kaldırılır
        if str(p) not in found:
            fm, body = split_note(p.read_text(encoding="utf-8"))
            new = re.sub(r"\n*<!-- sb:auto:bahsedilen:start -->.*?<!-- sb:auto:bahsedilen:end -->\n?", "\n", body, flags=re.S)
            if new != body:
                p.write_text(dump_note(fm, new), encoding="utf-8")
                changed.append(vault_ops._rel(p))
    for path, hits in found.items():
        p = Path(path)
        fm, body = split_note(p.read_text(encoding="utf-8"))
        lines = []
        for h in hits:
            when = datetime.fromtimestamp(h["date_ms"] / 1000).strftime("%Y-%m-%d") if h["date_ms"] else ""
            ref = f"[[{Path(h['ref']).with_suffix('').as_posix()}]]" if h["kind"] == "note" else f"{h['kind']}: {h['title']}"
            lines.append(f"- {when} {ref}")
        new = replace_auto(body, "bahsedilen", "Bahsedildiği yerler (beyin dizini, otomatik):\n" + "\n".join(lines))
        if new != body:
            p.write_text(dump_note(fm, new), encoding="utf-8")
            changed.append(vault_ops._rel(p))
    if changed:
        vault_ops.commit(changed, f"kişi bağlantıları: {len(changed)} kişi notu")
    return f"{len(found)} kişinin adı başka yerlerde geçiyor; {len(changed)} kişi notu güncellendi."


# ---------------------------------------------------------------- sohbet bağlantıları (WhatsApp/Telegram → kişi/proje notu)
CHAT_MAP = "config/sohbet_eslesme.yaml"     # elle düzeltme: {"Sohbet adı": "20-Projeler/Sirketim"} (yoksa otomatik eşleşir)


def _chat_threads(mcon) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in mcon.execute("SELECT account, thread_id, COUNT(*) n, MIN(date_ms) a, MAX(date_ms) b FROM messages "
                          "WHERE account IN ('whatsapp','telegram') GROUP BY account, thread_id"):
        last = mcon.execute("SELECT date_ms, from_name, from_addr, body FROM messages WHERE account=? AND thread_id=? "
                            "ORDER BY date_ms DESC LIMIT 4", (r["account"], r["thread_id"])).fetchall()
        who = [x[0] for x in mcon.execute("SELECT from_name, COUNT(*) c FROM messages WHERE account=? AND thread_id=? AND "
                                           "from_addr != 'me' GROUP BY from_name ORDER BY c DESC LIMIT 8", (r["account"], r["thread_id"]))]
        out[r["thread_id"]] = {"account": r["account"], "n": r["n"], "first": r["a"], "last": r["b"], "recent": last, "people": who}
    return out


def _chat_target(name: str, vault: Path, manual: dict) -> Path | None:
    """Sohbet adı → kişi notu (ad/takma ad tam eşleşmesi) ya da proje notu (proje adı sohbet adında geçiyorsa)."""
    if name in manual:
        p = vault / f"{manual[name]}.md"
        return p if p.exists() else None
    key = _fold(name)
    for p, fm in people(vault):
        if key in {_fold(p.stem), *(_fold(a) for a in _vals(fm.get("aliases")))}:
            return p
    for p in sorted((vault / "20-Projeler").glob("*.md")):
        pk = _fold(p.stem.replace("-", " "))
        if len(pk) >= 3 and (pk in key or key in pk or re.sub(r"\s", "", pk) in re.sub(r"\s", "", key)):
            return p
    return None


def _chat_note(name: str, t: dict, vault: Path) -> Path | None:
    """Eşleşmeyen sohbete not açar: grup (birden çok katılımcı) → 40-Kaynaklar/Gruplar, birebir → 60-Kişiler."""
    group = len([p for p in t["people"] if p]) > 1
    folder = vault / ("40-Kaynaklar/Gruplar" if group else PEOPLE)
    folder.mkdir(parents=True, exist_ok=True)
    title = safe_filename(name).strip(" .") or "Sohbet"
    p = folder / f"{title}.md"
    if p.exists():
        return p
    today = date.today()
    fm = ({"type": "kaynak", "status": "aktif", "tags": ["grup", t["account"]], "source": "derived"} if group else
          {"type": "kisi", "status": "aktif", "tags": ["kisi", t["account"]], "source": "derived", "relation": None, "phone": None})
    fm.update({"source_id": f"{t['account']}:{name}", "created": today, "updated": today, "due": None})
    body = f"# {title}\n\n## Bağlam\n" + ("" if not group else f"{t['account']} grubu.\n")
    p.write_text(dump_note(fm, body), encoding="utf-8")
    return p


def write_chat_links(mcon=None, vault: Path | None = None) -> str:
    from datetime import datetime
    import yaml
    from . import maildb
    from .config import MAIL_DB, SYSTEM
    vault = vault or vault_ops.VAULT
    mcon = mcon or maildb.connect(MAIL_DB)
    mp = SYSTEM / CHAT_MAP
    manual = (yaml.safe_load(mp.read_text(encoding="utf-8")) or {}) if mp.exists() else {}
    fmt = lambda ms: datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")
    by_note: dict[Path, list[str]] = defaultdict(list)
    unmatched = []
    for name, t in sorted(_chat_threads(mcon).items(), key=lambda kv: -kv[1]["last"]):
        target = _chat_target(name, vault, manual) or _chat_note(name, t, vault)
        if not target:
            unmatched.append(name)
            continue
        recent = "\n".join(f"  - {fmt(m['date_ms'])} {'Ben' if m['from_addr'] == 'me' else m['from_name']}: "
                           f"{' '.join((m['body'] or '').split())[:120]}" for m in reversed(t["recent"]))
        group = f" · katılımcılar: {', '.join(p for p in t['people'] if p)}" if len(t["people"]) > 1 else ""
        by_note[target].append(f"- **{name}** ({t['account']}): {t['n']} mesaj, {fmt(t['first'])} – {fmt(t['last'])}{group}\n{recent}")
    changed = []
    for p, blocks in by_note.items():
        fm, body = split_note(p.read_text(encoding="utf-8"))
        new = replace_auto(body, "sohbetler", "Sohbetler (WhatsApp/Telegram dışa aktarımı, otomatik):\n" + "\n".join(blocks))
        if new != body:
            p.write_text(dump_note(fm, new), encoding="utf-8")
            changed.append(vault_ops._rel(p))
    if changed:
        vault_ops.commit(changed, f"sohbet bağlantıları: {len(changed)} not")
    out = f"{sum(len(b) for b in by_note.values())} sohbet {len(by_note)} nota bağlandı."
    if unmatched:
        out += f" Eşleşmeyen {len(unmatched)}: " + "; ".join(unmatched[:20]) + f" (elle eşlemek için _system/{CHAT_MAP})"
    return out
def note_vectors(con=None, prefix_skip: tuple[str, ...] = ("60-Kişiler/", "50-Günlük/", "00-Inbox/", "40-Kaynaklar/Mail/",
                                                            "40-Kaynaklar/Bilgisayar/", "40-Kaynaklar/Kümeler/",
                                                            "40-Kaynaklar/Teknolojiler/", "40-Kaynaklar/Konular/",
                                                            "40-Kaynaklar/Drive/", "40-Kaynaklar/Analiz/")):
    """Not başına gömme (parça gömmelerinin ortalaması). Kişi, günlük, kutu, otomatik aynalar hariç."""
    import numpy as np
    from . import brain
    con = con or brain.connect()
    m, ids = brain._matrix()
    if m is None:
        return [], None
    pos = {int(c): i for i, c in enumerate(ids)}
    by: dict[str, list[int]] = defaultdict(list)
    titles = {}
    for r in con.execute("SELECT c.id, d.doc_id, d.title, d.ref FROM chunks c JOIN docs d ON d.doc_id = c.doc_id WHERE d.kind = 'note'"):
        if r["ref"].startswith(prefix_skip) or r["id"] not in pos:
            continue
        by[r["ref"]].append(pos[r["id"]])
        titles[r["ref"]] = r["title"]
    refs = sorted(by)
    if not refs:
        return [], None
    vecs = np.vstack([m[by[r]].mean(axis=0) for r in refs])
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    return [(r, titles[r]) for r in refs], vecs


def kmeans(x, k: int, iters: int = 40, seed: int = 7):
    import numpy as np
    rng = np.random.default_rng(seed)
    cent = x[rng.choice(len(x), size=k, replace=False)].copy()
    for _ in range(iters):
        lab = np.argmax(x @ cent.T, axis=1)                    # kosinüs (vektörler normalize)
        new = np.vstack([x[lab == j].mean(axis=0) if (lab == j).any() else cent[j] for j in range(k)])
        new /= np.linalg.norm(new, axis=1, keepdims=True) + 1e-9
        if np.allclose(new, cent, atol=1e-5):
            break
        cent = new
    return lab, cent


AUTO_NODES = ("40-Kaynaklar/Teknolojiler/", "40-Kaynaklar/Konular/", "40-Kaynaklar/Drive/", "40-Kaynaklar/Analiz/")


def doc_vectors(kinds: tuple[str, ...] = ("note", "file", "mail", "chat"), con=None, auto_nodes: tuple[str, ...] = AUTO_NODES):
    """Belge başına gömme (parça ortalaması) bütün türlerde: notlar (otomatik düğüm/ayna notlar hariç), belgeler, mailler/mesajlar.
    Dönüş: [(ref, başlık, tür)], matris."""
    import numpy as np
    from . import brain
    con = con or brain.connect()
    m, ids = brain._matrix()
    if m is None:
        return [], None
    pos = {int(c): i for i, c in enumerate(ids)}
    skip = ("60-Kişiler/", "50-Günlük/", "00-Inbox/", "40-Kaynaklar/Mail/", "40-Kaynaklar/Bilgisayar/", "40-Kaynaklar/Kümeler/",
            "90-Arşiv/", "_system/", "_templates/") + auto_nodes
    by: dict[tuple, list[int]] = defaultdict(list)
    marks = ",".join("?" * len(kinds))
    for r in con.execute(f"SELECT c.id, d.kind, d.title, d.ref, d.date_ms FROM chunks c JOIN docs d ON d.doc_id = c.doc_id "
                         f"WHERE d.kind IN ({marks})", kinds):
        if r["id"] not in pos or (r["kind"] == "note" and r["ref"].startswith(skip)):
            continue
        by[(r["ref"], r["title"] or "", r["kind"], r["date_ms"] or 0)].append(pos[r["id"]])
    keys = sorted(by)
    if not keys:
        return [], None
    vecs = np.vstack([m[by[k]].mean(axis=0) for k in keys])
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    return keys, vecs


def _member_line(ref: str, title: str, kind: str, date_ms: int) -> str:
    from datetime import datetime
    when = datetime.fromtimestamp(date_ms / 1000).strftime("%Y-%m-%d") if date_ms else ""
    if kind == "note":
        return f"- [[{Path(ref).with_suffix('').as_posix()}|{title}]]"
    icon = {"file": "📄", "mail": "✉️", "item": "🔗"}.get(kind, "•")
    return f"- {icon} {when} {title}" + (f" — `{ref}`" if kind == "file" else "")


NOTE_CLUSTER_SKIP = ("40-Kaynaklar/Teknolojiler/", "40-Kaynaklar/Konular/", "40-Kaynaklar/Analiz/")
DOC_CLUSTERS = "40-Kaynaklar/Analiz/Belge kümeleri"


def clusters(k: int | None = None, con=None, namer=None, kinds: tuple[str, ...] = ("note",), folder: str = CLUSTERS) -> str:
    """Beyni yeniden gruplar (madde 121). Varsayılan: kasa notları konu kümelerine ayrılır; küme notu bütün üyelerine bağlanır
    ve üyelerin `kume` özelliği yazılır (grafikte küme başına renk). kinds başka türler içerirse (belge/mail) kümeler `folder`'a
    yalnız özet olarak yazılır. Her küme yerel modelle adlandırılır; eski küme notları silinmez, arşive taşınır."""
    import numpy as np
    from collections import Counter
    from . import llm
    notes_only = tuple(kinds) == ("note",)
    keys, vecs = doc_vectors(kinds, con, NOTE_CLUSTER_SKIP if notes_only else AUTO_NODES)
    if vecs is None or len(keys) < 12:
        return "Kümeleme için yeterli gömme yok (önce sb index)."
    k = k or (max(8, min(30, round(len(keys) / 12))) if notes_only else max(6, min(40, int(round((len(keys) / 8) ** 0.5)))))
    lab, cent = kmeans(vecs, k)
    rel_folder, folder = folder, vault_ops.VAULT / folder
    folder.mkdir(parents=True, exist_ok=True)
    written, membership = [], {}
    for j in range(k):
        idx = np.where(lab == j)[0]
        if len(idx) < 3:
            continue
        order = idx[np.argsort(-(vecs[idx] @ cent[j]))]
        core = [keys[i] for i in order[:15]]
        if namer:
            name = namer([t for _, t, _, _ in core])
        else:
            lines = [f"- [{_folder_of(r) if kd == 'note' else kd}] {t}" + (f": {_snippet(r)}" if kd == "note" else "")
                     for r, t, kd, _ in core]
            prompt = ("Aşağıdakiler (kişisel bilgi kasasından notlar/belgeler) anlamca aynı kümede. Ortak KONUYU bul ve kümeye 2-4 kelimelik "
                      "Türkçe bir konu adı ver (ör. 'Veri Yapıları ve Algoritmalar', 'Staj ve İş Başvuruları'). 'Notlar', 'Başlıklar', "
                      "'Belgeler' gibi genel adlar YASAK. Kümenin ne hakkında olduğunu tek cümleyle yaz. JSON: {\"ad\": ..., \"aciklama\": ...}\n\n"
                      + "\n".join(lines))
            raw, _ = llm.complete("cluster", prompt, schema={"type": "object", "required": ["ad", "aciklama"], "properties": {
                "ad": {"type": "string"}, "aciklama": {"type": "string"}}}, timeout=300, private=True)
            import json
            name = json.loads(raw)
        title = safe_filename(f"Küme - {name['ad']}")[:80]
        while vault_ops._rel(folder / f"{title}.md") in written:
            title += " +"
        p = folder / f"{title}.md"
        counts = Counter(keys[i][2] for i in idx)
        shown = order if notes_only else order[:40]
        top = "\n".join(_member_line(*keys[i]) for i in shown)
        if notes_only:
            membership.update({keys[i][0]: title for i in idx})
        fm = {"type": "kaynak", "status": "aktif", "tags": ["kume"], "source": "derived", "source_id": f"kume:{title}",
              "created": date.today(), "updated": date.today(), "due": None}
        names = {"note": "not", "file": "belge", "mail": "mail/mesaj", "item": "kayıt"}
        summary = ", ".join(f"{n} {names.get(kd, kd)}" for kd, n in counts.most_common())
        body = (f"# {title}\n\n{name['aciklama']}\n\n<!-- sb:auto:kume:start -->\n{len(idx)} öğe ({summary}). "
                + ("Üyeler (merkeze yakınlığa göre)" if notes_only else f"Merkeze en yakın {min(40, len(idx))}")
                + f":\n{top}\n<!-- sb:auto:kume:end -->\n")
        p.write_text(dump_note(fm, body), encoding="utf-8")
        written.append(vault_ops._rel(p))
    import shutil
    for old in folder.glob("*.md"):                           # bu çalışmada üretilmeyen eski kümeler arşive (silinmez)
        if vault_ops._rel(old) not in written:
            dest = vault_ops.VAULT / vault_ops.ARCHIVE / vault_ops._rel(old)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old), str(dest))
            written += [vault_ops._rel(old), vault_ops._rel(dest)]
    if notes_only:
        written += _write_membership(membership)
    vault_ops.commit(written, f"kümeleme: {k} küme, {len(keys)} öğe")
    return f"{len(keys)} öğe ({', '.join(kinds)}) {k} kümeye ayrıldı → {rel_folder}"


def _folder_of(ref: str) -> str:
    parts = Path(ref).parts
    return "/".join(parts[1:2] if parts and parts[0] == "40-Kaynaklar" and len(parts) > 2 else parts[:1])


def _snippet(ref: str, n: int = 160) -> str:
    """Notun gövdesinden ilk anlamlı satırlar (adlandırma için; otomatik bölüm işaretleri ve başlık atlanır)."""
    try:
        _, body = split_note((vault_ops.VAULT / ref).read_text(encoding="utf-8"))
    except OSError:
        return ""
    text = " ".join(l for l in body.splitlines() if l.strip() and not l.startswith(("#", "<!--", "---")))
    return " ".join(text.split())[:n]


def _write_membership(membership: dict[str, str]) -> list[str]:
    """Notların `kume` özelliği: grafik renk grupları bununla küme başına renklenir. Kümeden çıkan notta özellik kalkar."""
    changed = []
    for p in vault_ops.VAULT.rglob("*.md"):
        rel = vault_ops._rel(p)
        if rel.startswith(("_system/", "90-Arşiv/", "_templates/", ".")):
            continue
        want = membership.get(rel)
        text = p.read_text(encoding="utf-8")
        if not want and "\nkume:" not in text:
            continue
        fm, body = split_note(text)
        if not fm or fm.get("kume") == want:
            continue
        if want:
            fm["kume"] = want
        else:
            fm.pop("kume", None)
        p.write_text(dump_note(fm, body), encoding="utf-8")
        changed.append(rel)
    return changed


def _linked(vault: Path) -> set[tuple[str, str]]:
    pairs = set()
    for p in vault.rglob("*.md"):
        if ".obsidian" in p.parts or "_system" in p.parts:
            continue
        try:
            for t in LINK_RE.findall(p.read_text(encoding="utf-8")):
                a, b = p.stem.lower(), Path(t.strip()).name.lower()
                pairs |= {(a, b), (b, a)}
        except OSError:
            continue
    return pairs


def suggest_links(threshold: float = 0.83, top: int = 40, con=None) -> str:
    import numpy as np
    vault = vault_ops.VAULT
    refs, vecs = note_vectors(con)
    if vecs is None:
        return "Bağlantı önerisi için not gömmesi yok (önce sb index)."
    sims = vecs @ vecs.T
    np.fill_diagonal(sims, 0)
    linked = _linked(vault)
    cands = []
    for i, j in zip(*np.where(np.triu(sims) >= threshold)):
        a, b = refs[i], refs[j]
        if (Path(a[0]).stem.lower(), Path(b[0]).stem.lower()) in linked:
            continue
        cands.append((float(sims[i, j]), a, b))
    cands.sort(reverse=True)
    p = vault / LINK_NOTE
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    kept = [l for l in old.splitlines() if l.startswith(("- [x]", "- [-]"))]
    lines = [f"- [ ] [[{Path(a[0]).with_suffix('').as_posix()}|{a[1]}]] ↔ [[{Path(b[0]).with_suffix('').as_posix()}|{b[1]}]] — anlam yakınlığı {s:.2f}"
             for s, a, b in cands[:top]]
    lines = [l for l in lines if not any(l[6:].split(" — ")[0] in k for k in kept)]
    body = ("# Bağlantı önerileri\n\nAnlamca çok yakın ama birbirine bağlı olmayan notlar. Gerçekten ilişkiliyse `[x]`, değilse `[-]` yap; "
            "`sb suggest-links --apply` gerekçeli bağlantı notu açar.\n\n" + "\n".join(kept + lines) + "\n")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_note({"type": "inbox", "tags": ["inbox", "oneri"]}, body), encoding="utf-8")
    vault_ops.commit([LINK_NOTE], f"bağlantı önerileri: {len(lines)}")
    return f"{len(lines)} bağlantı önerisi → {LINK_NOTE}"


def apply_links() -> list[str]:
    from . import memory
    p = vault_ops.VAULT / LINK_NOTE
    if not p.exists():
        return []
    text, out = p.read_text(encoding="utf-8"), []
    for line in [l for l in text.splitlines() if l.startswith("- [x]") and "işlendi" not in l]:
        targets = LINK_RE.findall(line)
        if len(targets) >= 2:
            score = line.rsplit("yakınlığı", 1)[-1].strip()
            out.append(memory.connect(targets[0], targets[1], f"Kullanıcı onayladı: anlamca yakın notlar (benzerlik {score}).",
                                      actor="kullanici"))
            text = text.replace(line, line + f" (işlendi {date.today()})")
    p.write_text(text, encoding="utf-8")
    if out:
        vault_ops.commit([LINK_NOTE], f"bağlantı önerileri işlendi ({len(out)})")
    return out


def _series(title: str) -> str:
    """Aynı serinin parçaları aynı kökü verir: 'Gemini 2026-03' / 'Gemini 2026-05', 'Adsız doküman(1)' / 'Adsız doküman', '10.500'."""
    return re.sub(r"[\d\W_]+", " ", _fold(Path(title).name)).strip()


def auto_links() -> str:
    """Bağlantı önerilerine kurala göre karar verir ve uygular (kullanıcı 2026-11-01'de sormadan düzenlemeye izin verdi):
    aynı serinin parçaları (ay notları, numaralı kopyalar, adsız belgeler) bağlanmaz; diğer anlam yakın çiftler bağlanır."""
    p = vault_ops.VAULT / LINK_NOTE
    if not p.exists():
        return "Bağlantı önerisi yok."
    text, yes, no = p.read_text(encoding="utf-8"), 0, 0
    for line in [l for l in text.splitlines() if l.startswith("- [ ]")]:
        t = LINK_RE.findall(line)
        if len(t) < 2:
            continue
        a, b = _series(t[0]), _series(t[1])
        if not a or not b or a == b or "adsiz" in (a + b):
            text = text.replace(line, "- [-]" + line[5:] + " (otomatik: aynı seri / anlamsız ad)")
            no += 1
        else:
            text = text.replace(line, "- [x]" + line[5:] + " (otomatik: anlam yakın, farklı konu)")
            yes += 1
    p.write_text(text, encoding="utf-8")
    done = apply_links()
    return f"bağlantı önerileri: {yes} bağlandı, {no} reddedildi (aynı seri) → {len(done)} bağlantı notu"


GRAPH_HIDE_DIRS = ("90-Arşiv", "_system", "_templates", "00-Inbox", "50-Günlük", "40-Kaynaklar/Analiz")
GRAPH_HIDE_FILES = ("AGENTS", "CLAUDE", "Açık konular", "Son oturum", "Araçlar ve erişimler", "Asistan", "Asistan kuralları",
                    "Asistan hafızası", "Asistan kimliği", "Dashboard")
GRAPH_GROUPS = [            # (ad, sorgu, renk) — küme renklerinden sonra uygulanır
    ("Kişiler", 'path:"60-Kişiler"', "#f59e0b"),
    ("Projeler", 'path:"20-Projeler"', "#ef4444"),
    ("Dersler", 'path:"10-Dersler"', "#22c55e"),
    ("Kariyer", 'path:"30-Kariyer"', "#0ea5e9"),
    ("Teknolojiler", 'path:"40-Kaynaklar/Teknolojiler"', "#8b5cf6"),
    ("Konular ve kavramlar", 'path:"40-Kaynaklar/Konular" OR path:"40-Kaynaklar/Kavramlar"', "#ec4899"),
    ("Yapay zeka sohbetleri", 'path:"40-Kaynaklar/Sohbet geçmişi" OR path:"40-Kaynaklar/Claude" OR path:"40-Kaynaklar/NotebookLM"', "#14b8a6"),
    ("Bilgisayar", 'path:"40-Kaynaklar/Bilgisayar"', "#64748b"),
    ("Belgeler ve Drive", 'path:"40-Kaynaklar/Belgeler" OR path:"40-Kaynaklar/Drive" OR path:"40-Kaynaklar/Keep"', "#a3a3a3"),
    ("Gruplar", 'path:"40-Kaynaklar/Gruplar"', "#eab308"),
    ("Bağlantılar", 'path:"40-Kaynaklar/Bağlantılar"', "#94a3b8"),
]


def _rgb(hex_color: str) -> int:
    return int(hex_color.lstrip("#"), 16)


def _cluster_colors(n: int) -> list[int]:
    """Birbirinden ayrık n renk (altın oran ile ton, iki parlaklık katmanı)."""
    import colorsys
    out = []
    for i in range(n):
        h = (0.11 + i * 0.618033988749895) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.62 if i % 2 else 0.78, 0.95 if i % 2 else 0.82)
        out.append((int(r * 255) << 16) | (int(g * 255) << 8) | int(b * 255))
    return out


def graph_style(vault: Path | None = None, hide: bool = False) -> str:
    """Obsidian grafiği renkleri: her konu kümesi (küme notu + üyeleri) kendi renginde; kümede olmayanlar kategori renginde.
    Görünürlük ayarlarına (filtre, etiket, ek, bağlantısız) dokunmaz — Ayşe 2026-11-01'de her şeyin görünmesini sabitledi.
    `hide=True`: teknik notlar, etiketler, ekler ve bağlantısız düğümler gizlenir. Diğer ayarlar (kuvvetler, yakınlaştırma) korunur."""
    import json
    v = vault or vault_ops.VAULT
    gp = v / ".obsidian" / "graph.json"
    try:
        cfg = json.loads(gp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {}
    names = sorted(f.stem for f in (v / CLUSTERS).glob("*.md")) if (v / CLUSTERS).is_dir() else []
    groups = [{"query": f'[kume:"{n}"] OR path:"{CLUSTERS}/{n}.md"', "color": {"a": 1, "rgb": c}}
              for n, c in zip(names, _cluster_colors(len(names)))]
    groups += [{"query": q, "color": {"a": 1, "rgb": _rgb(c)}} for _, q, c in GRAPH_GROUPS]
    cfg.update({"colorGroups": groups, "collapse-color-groups": True})
    if hide:
        search = " ".join([f'-path:"{d}"' for d in GRAPH_HIDE_DIRS] + [f'-file:"{f}"' for f in GRAPH_HIDE_FILES])
        cfg.update({"search": search, "showTags": False, "showAttachments": False, "hideUnresolved": True, "showOrphans": False})
    gp.parent.mkdir(parents=True, exist_ok=True)
    gp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    shown = (f"gizli: {len(GRAPH_HIDE_DIRS)} klasör, etiketler, ekler, bağlantısızlar" if hide
             else "görünürlük ayarlarına dokunulmadı")
    return f"graf: {len(names)} küme rengi + {len(GRAPH_GROUPS)} kategori rengi; {shown}"
