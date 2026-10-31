"""Beyin analizleri (Faz 1.5, madde 124-137).

Her analiz: saf hesap fonksiyonu + kasaya yazan `write_*` (`40-Kaynaklar/Analiz/<ad>.md`, tek `sb:auto:analiz` bölümü; elle
yazılan kısım korunur). Hepsi öneri/rapor üretir: arşive taşıma, silme, otomatik etiket/not değişikliği YOK.
`write_*(vault=None, con=None, mcon=None, dry=False)`: dry=True kasaya/dizine yazmaz, yalnız özet döndürür.
`vault=None` gerçek kasa (yazınca git commit); test için geçici kasa verilir.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from . import config, vault_ops
from .notes import SKIP_DIRS, dump_note, is_private, replace_auto, safe_filename, split_note

FOLDER = "40-Kaynaklar/Analiz"
LINK_RE = re.compile(r"\[\[([^\]|#]+)")
AUTO_RE = re.compile(r"<!--\s*sb:auto:.*?:end\s*-->|<!--\s*sb:auto:.*?:start\s*-->", re.S)
# kasadaki otomatik aynalar/kutu notları: kalite, yaşlanma, bağlantı hesaplarında kaynak ya da konu sayılmaz
MIRROR = ("40-Kaynaklar/Mail/", "40-Kaynaklar/Bilgisayar/", "40-Kaynaklar/Drive/", "40-Kaynaklar/Analiz/", "40-Kaynaklar/Kümeler/",
          "00-Inbox/")
SKIP = SKIP_DIRS | {"90-Arşiv"}


# ---------------------------------------------------------------- ortak
class Note:
    __slots__ = ("rel", "stem", "fm", "body", "mtime")

    def __init__(self, rel, fm, body, mtime):
        self.rel, self.stem, self.fm, self.body, self.mtime = rel, Path(rel).stem, fm, body, mtime


def load_notes(vault: Path | None = None) -> list[Note]:
    vault = vault or vault_ops.VAULT
    out = []
    for p in sorted(vault.rglob("*.md")):
        rel = p.relative_to(vault)
        if any(x in SKIP for x in rel.parts[:-1]) or is_private(p):
            continue
        try:
            fm, body = split_note(p.read_text(encoding="utf-8"))
            out.append(Note(rel.as_posix(), fm if isinstance(fm, dict) else {}, body, p.stat().st_mtime))
        except (OSError, Exception):
            continue
    return out


def _d(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(v or ""))
    try:
        return date(*map(int, m.groups())) if m else None
    except ValueError:
        return None


def _note_date(n: Note) -> date:
    return _d(n.fm.get("updated")) or _d(n.fm.get("created")) or date.fromtimestamp(n.mtime)


def _ms(ms) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d") if ms else "—"


def _fold(s: str) -> str:
    return (s or "").translate(str.maketrans("İIıĞğÜüŞşÖöÇç", "iiigguussoocc")).lower()


def _list(v) -> list[str]:
    if v in (None, ""):
        return []
    return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else [str(v).strip()]


def _wl(n: Note) -> str:
    return f"[[{Path(n.rel).with_suffix('').as_posix()}|{n.stem}]]"


def _body(n: Note) -> str:
    return AUTO_RE.sub("", n.body)


def link_graph(notes: list[Note]) -> tuple[dict[str, set], dict[str, set]]:
    """(giden, gelen) bağlantılar; kaynak olarak yalnız insan notları sayılır (analiz/ayna notları değil)."""
    stems = defaultdict(list)
    for n in notes:
        stems[n.stem.lower()].append(n.rel)
    out, inn = defaultdict(set), defaultdict(set)
    for n in notes:
        if n.rel.startswith(MIRROR):
            continue
        for t in LINK_RE.findall(n.body):
            for rel in stems.get(Path(t.strip()).name.lower(), []):
                if rel != n.rel:
                    out[n.rel].add(rel)
                    inn[rel].add(n.rel)
    return out, inn


def _emit(name: str, intro: str, content: str, summary: str, vault: Path | None, dry: bool) -> str:
    """Analiz notunu yazar/yeniler (auto bölümü). Değişmediyse dokunmaz."""
    if dry:
        return f"[dry-run] {name}: {summary}"
    real = vault is None
    root = vault or vault_ops.VAULT
    rel = f"{FOLDER}/{safe_filename(name)}.md"
    p = root / rel
    today = date.today()
    if p.exists():
        text = p.read_text(encoding="utf-8")
        fm, body = split_note(text)
        new_body = replace_auto(body, "analiz", content)
        if new_body == body:
            return f"{name}: değişmedi ({summary})"
        fm["updated"] = today
    else:
        fm = {"type": "kaynak", "status": "aktif", "tags": ["analiz"], "source": "derived", "source_id": f"analiz:{name}",
              "due": None, "created": today, "updated": today}
        new_body = replace_auto(f"# {name}\n\n{intro}\n", "analiz", content)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dump_note(fm, new_body), encoding="utf-8", newline="\n")
    if real:
        vault_ops.commit([rel], f"analiz: {name}")
    return f"{name}: {summary} → {rel}"


def _conn(con):
    from . import brain
    return con or brain.connect()


def _mconn(mcon):
    if mcon is not None:
        return mcon
    from . import maildb
    return maildb.connect(config.MAIL_DB) if config.MAIL_DB.exists() else None


def _phrase(text: str) -> str:
    words = re.findall(r"\w+", text.lower())
    return '"' + " ".join(words) + '"' if words else ""


# ---------------------------------------------------------------- 124 konu zaman çizelgesi
def topic_timeline(query: str, con=None, k: int = 60) -> dict[str, list[dict]]:
    from . import brain
    hits = brain.find(query, k=k, con=_conn(con))
    months: dict[str, list[dict]] = defaultdict(list)
    for h in hits:
        months[h["date"][:7] if h["date"] else "Tarihsiz"].append(h)
    return dict(sorted(months.items(), key=lambda kv: kv[0], reverse=True))


def write_timeline(query: str, *, vault=None, con=None, mcon=None, dry=False) -> str:
    months = topic_timeline(query, con)
    n = sum(len(v) for v in months.values())
    lines = []
    for mon, hs in months.items():
        lines.append(f"### {mon}")
        for h in sorted(hs, key=lambda x: x["date"], reverse=True):
            ref = f"[[{Path(h['ref']).with_suffix('').as_posix()}|{h['title']}]]" if h["kind"] == "note" else f"{h['kind']}: {h['title']}"
            lines.append(f"- {h['date']} · {ref}")
    return _emit(f"Zaman çizelgesi - {query}", f"“{query}” konusunun beyin dizinindeki izleri, aya göre.",
                 "\n".join(lines) or "Eşleşen belge yok.", f"{n} belge, {len(months)} ay", vault, dry)


# ---------------------------------------------------------------- 125 proje ilişki haritası
def project_map(vault: Path | None = None, con=None, limit: int = 300) -> list[dict]:
    from . import entities
    vault = vault or vault_ops.VAULT
    con = _conn(con)
    notes = load_notes(vault)
    tech_stems = {n.stem.lower(): n.stem for n in notes if n.rel.startswith("40-Kaynaklar/Teknolojiler/")}
    people = [(p.stem, _fold(p.stem)) for p, _ in entities.people(vault) if len(p.stem) >= 6 and " " in p.stem.strip()]
    rows = []
    for n in notes:
        if not n.rel.startswith("20-Projeler/"):
            continue
        q = _phrase(n.stem)
        found = []
        if q:
            try:
                found = con.execute("SELECT c.doc_id, d.kind, c.text FROM chunks_fts f JOIN chunks c ON c.id = f.rowid "
                                    "JOIN docs d ON d.doc_id = c.doc_id WHERE chunks_fts MATCH ? AND c.doc_id != ? LIMIT ?",
                                    (q, f"note:{n.rel}", limit)).fetchall()
            except sqlite3.Error:
                found = []
        mails = {r["doc_id"] for r in found if r["kind"] == "mail"}
        ppl = Counter()
        for r in found:
            txt = _fold(r["text"])
            for name, f in people:
                if f in txt:
                    ppl[name] += 1
        techs = {t.lower(): t for t in _list(n.fm.get("technologies"))}
        for t in LINK_RE.findall(n.body):
            if Path(t.strip()).name.lower() in tech_stems:
                techs.setdefault(Path(t.strip()).name.lower(), tech_stems[Path(t.strip()).name.lower()])
        rows.append({"proje": n.stem, "rel": n.rel, "kisiler": ppl.most_common(8), "teknolojiler": sorted(techs.values(), key=str.lower),
                     "mail": len(mails)})
    return sorted(rows, key=lambda r: r["proje"].lower())


def mermaid(rows: list[dict], max_nodes: int = 25) -> str:
    edges = []
    for r in rows:
        edges += [(w, r["proje"], p) for p, w in r["kisiler"]]
        edges += [(1, r["proje"], t) for t in r["teknolojiler"]]
    nodes: dict[str, str] = {}
    keep = []
    for w, a, b in sorted(edges, key=lambda e: (-e[0], e[1], e[2])):
        new = {x for x in (a, b) if x not in nodes}
        if len(nodes) + len(new) > max_nodes:
            continue
        for x in sorted(new):
            nodes[x] = f"n{len(nodes)}"
        keep.append((a, b))
    lab = lambda s: re.sub(r'["\[\]()<>|{}]', "", s)[:30]
    out = ["```mermaid", "graph LR"]
    out += [f'    {i}["{lab(x)}"]' for x, i in nodes.items()]
    out += [f"    {nodes[a]} --- {nodes[b]}" for a, b in keep]
    return "\n".join(out + ["```"])


def write_projects(*, vault=None, con=None, mcon=None, dry=False) -> str:
    rows = project_map(vault, con)
    head = "| Proje | Kişiler | Teknolojiler | Mail |\n|---|---|---|---|"
    body = [head]
    for r in rows:
        ppl = ", ".join(f"[[60-Kişiler/{p}|{p}]]" for p, _ in r["kisiler"]) or "—"
        tech = ", ".join(r["teknolojiler"]) or "—"
        body.append(f"| [[{Path(r['rel']).with_suffix('').as_posix()}|{r['proje']}]] | {ppl} | {tech} | {r['mail']} |")
    content = "\n".join(body) + "\n\n" + mermaid(rows)
    return _emit("Proje ilişki haritası", "Projelerin adının geçtiği kişi, teknoloji ve mail sayısı (beyin dizininden, kural tabanlı).",
                 content, f"{len(rows)} proje", vault, dry)


# ---------------------------------------------------------------- 126 belge sınıflandırma
CLASSES = ["cv", "fatura", "sözleşme", "ödev/teslim", "sunum", "resmi yazı", "rapor", "ders notu"]
NAME_KW = {
    "cv": ["cv", "ozgecmis", "resume", "curriculum"],
    "fatura": ["fatura", "invoice", "makbuz", "receipt", "dekont"],
    "sözleşme": ["sozlesme", "contract", "protokol", "taahhut", "agreement"],
    "ödev/teslim": ["odev", "homework", "assignment", "teslim", "hw1", "hw2", "lab"],
    "sunum": ["sunum", "presentation", "slayt", "slide", "pitch"],
    "resmi yazı": ["dilekce", "resmi yazi", "ogrenci belgesi", "transkript", "onay belgesi", "basvuru formu", "dilekçe"],
    "rapor": ["rapor", "report", "analiz"],
    "ders notu": ["ders notu", "lecture", "hafta", "week", "notlari", "notes", "vize", "final"],
}
TEXT_KW = {
    "cv": ["ozgecmis", "curriculum vitae", "is deneyimi", "work experience", "egitim bilgileri", "yetenekler", "skills"],
    "fatura": ["fatura no", "vergi dairesi", "toplam tutar", "kdv", "invoice no", "odenecek tutar", "vkn"],
    "sözleşme": ["sozlesme", "taraflar", "yukumluluk", "madde 1", "isbu", "feshedilebilir", "agreement"],
    "ödev/teslim": ["teslim tarihi", "odev", "son teslim", "deadline", "due date", "assignment", "submit"],
    "sunum": ["slayt", "slide", "sunum", "presentation", "tesekkurler", "thank you"],
    "resmi yazı": ["sayin", "t.c.", "sayi:", "ilgi:", "rektorlugu", "mudurlugu", "dekanligi", "konu:"],
    "rapor": ["ozet", "abstract", "yontem", "methodology", "sonuc", "bulgular", "results", "conclusion"],
    "ders notu": ["ders notlari", "lecture", "chapter", "teorem", "tanim", "ornek:", "definition", "theorem"],
}


def classify_text(name: str, text: str) -> tuple[str, str]:
    """(sınıf, gerekçe): önce dosya adı, sonra ilk 1500 karakterde ≥2 anahtar kelime; yoksa 'diğer'."""
    n = _fold(name)
    words = set(re.findall(r"[a-z0-9]+", n))
    for cls in CLASSES:
        for kw in NAME_KW[cls]:
            if (kw in words) if len(kw) <= 3 else (kw in n):
                return cls, f"ad:{kw}"
    if n.endswith((".pptx", ".ppt")):
        return "sunum", "uzantı"
    t = _fold((text or "")[:1500])
    best, why = None, 0
    for cls in CLASSES:
        hit = [kw for kw in TEXT_KW[cls] if kw in t]
        if len(hit) >= 2 and len(hit) > why:
            best, why, hits = cls, len(hit), hit
    return (best, "metin:" + ",".join(hits[:3])) if best else ("diğer", "")


def classify_docs(con=None, mcon=None) -> list[dict]:
    """file_text belgeleri + Drive aynı notları. Satır: doc_id, ad, cls, why, date_ms."""
    from . import brain
    con, mcon = _conn(con), _mconn(mcon)
    out = []
    if mcon is not None:
        try:
            rows = mcon.execute("SELECT path, mtime, text FROM file_text WHERE text IS NOT NULL AND length(text) > 50").fetchall()
        except sqlite3.Error:
            rows = []
        for r in rows:
            p = Path(r[0])
            if p.suffix.lower() not in brain.DOC_EXT:
                continue
            cls, why = classify_text(p.name, r[2])
            out.append({"doc_id": f"file:{r[0]}", "ad": p.name, "cls": cls, "why": why, "date_ms": int(r[1] * 1000) if r[1] else None})
    for d in con.execute("SELECT doc_id, title, date_ms FROM docs WHERE kind = 'note' AND ref LIKE '40-Kaynaklar/Drive/%'"):
        first = con.execute("SELECT text FROM chunks WHERE doc_id = ? ORDER BY ord LIMIT 1", (d["doc_id"],)).fetchone()
        cls, why = classify_text(d["title"], first[0] if first else "")
        out.append({"doc_id": d["doc_id"], "ad": d["title"], "cls": cls, "why": why, "date_ms": d["date_ms"]})
    return out


def write_classify(*, vault=None, con=None, mcon=None, dry=False) -> str:
    con = _conn(con)
    rows = classify_docs(con, mcon)
    by = defaultdict(list)
    for r in rows:
        by[r["cls"]].append(r)
    if not dry:
        con.execute("CREATE TABLE IF NOT EXISTS doc_class (doc_id TEXT PRIMARY KEY, cls TEXT, why TEXT)")
        con.executemany("INSERT OR REPLACE INTO doc_class(doc_id, cls, why) VALUES (?,?,?)", [(r["doc_id"], r["cls"], r["why"]) for r in rows])
        con.commit()
    lines = ["| Sınıf | Belge |\n|---|---|"] + [f"| {c} | {len(by[c])} |" for c in CLASSES + ["diğer"] if c in by]
    for c in CLASSES + ["diğer"]:
        if c in by:
            lines.append(f"\n### {c} (en yeni 10)")
            lines += [f"- {_ms(r['date_ms'])} · {r['ad']}" + (f" ({r['why']})" if r["why"] else "")
                      for r in sorted(by[c], key=lambda r: r["date_ms"] or 0, reverse=True)[:10]]
    return _emit("Belge sınıfları", "Bilgisayar ve Drive belgelerinin kural tabanlı sınıfı (dosya adı + ilk 1500 karakter). Sınıflar brain.db `doc_class` tablosunda.",
                 "\n".join(lines), f"{len(rows)} belge, {len(by)} sınıf", vault, dry)


# ---------------------------------------------------------------- 127 tekrar belgeler
def _norm_sha(text: str) -> str:
    return hashlib.sha1(re.sub(r"\s+", " ", (text or "").lower()).strip().encode("utf-8", "replace")).hexdigest()


def duplicate_groups(con=None, mcon=None, sim: float = 0.98, min_chars: int = 200) -> list[dict]:
    """Aynı normalize metin sha'sı ya da dosya gömmesi benzerliği > sim olan dosya grupları (birleşik bileşenler)."""
    import numpy as np
    from . import brain
    con, mcon = _conn(con), _mconn(mcon)
    parent: dict[str, str] = {}
    why: dict[frozenset, str] = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    pairs = defaultdict(set)
    if mcon is not None:
        by = defaultdict(list)
        for path, text in mcon.execute("SELECT path, text FROM file_text WHERE text IS NOT NULL"):
            if Path(path).suffix.lower() in brain.DOC_EXT and len(text) >= min_chars:
                by[_norm_sha(text)].append(path)
        for paths in by.values():
            for p in paths[1:]:
                union(paths[0], p)
                pairs[paths[0]].add("aynı içerik")
    m, ids = brain._matrix()
    if m is not None:
        owner = {int(r[0]): r[1] for r in con.execute("SELECT c.id, d.ref FROM chunks c JOIN docs d ON d.doc_id = c.doc_id WHERE d.kind = 'file'")}
        pos = defaultdict(list)
        for i, cid in enumerate(ids):
            if int(cid) in owner:
                pos[owner[int(cid)]].append(i)
        refs = sorted(pos)
        if len(refs) > 1:
            v = np.vstack([m[pos[r]].mean(axis=0) for r in refs])
            v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
            for s in range(0, len(refs), 1000):
                block = v[s:s + 1000] @ v.T
                for a, b in zip(*np.where(block > sim)):
                    a += s
                    if a < b:
                        union(refs[a], refs[b])
                        pairs[refs[a]].add(f"çok benzer ({float(block[a - s, b]):.3f})")
    groups = defaultdict(list)
    for x in list(parent):
        groups[find(x)].append(x)
    out = []
    for g in groups.values():
        if len(g) > 1:
            reasons = sorted({w for p in g for w in pairs.get(p, ())})
            out.append({"paths": sorted(g), "neden": ", ".join(reasons)})
    return sorted(out, key=lambda x: (-len(x["paths"]), x["paths"][0]))


def write_duplicates(*, vault=None, con=None, mcon=None, dry=False) -> str:
    groups = duplicate_groups(con, mcon)
    lines = []
    for i, g in enumerate(groups[:100], 1):
        lines.append(f"### Grup {i} — {g['neden']}")
        lines += [f"- `{p}`" for p in g["paths"][:10]]
    extra = len(groups) - 100
    if extra > 0:
        lines.append(f"\n… ve {extra} grup daha.")
    return _emit("Tekrar belgeler", "Aynı içerikli ya da çok benzer bilgisayar belgeleri. Yalnız liste: hiçbir dosya silinmez.",
                 "\n".join(lines) or "Tekrar belge bulunamadı.", f"{len(groups)} grup", vault, dry)


# ---------------------------------------------------------------- 128 yaşlanan bilgi
def aging_notes(notes: list[Note], today: date | None = None, days: int = 730) -> list[tuple[Note, int]]:
    today = today or date.today()
    out_l, in_l = link_graph(notes)
    res = []
    for n in notes:
        if n.rel.startswith(MIRROR + ("60-Kişiler/", "50-Günlük/")) or str(n.fm.get("status") or "") == "aktif":
            continue
        age = (today - _note_date(n)).days
        if age > days and not out_l.get(n.rel) and not in_l.get(n.rel):
            res.append((n, age))
    return sorted(res, key=lambda x: -x[1])


def write_aging(*, vault=None, con=None, mcon=None, dry=False, today=None) -> str:
    res = aging_notes(load_notes(vault), today)
    lines = [f"- [ ] {_wl(n)} — son güncelleme {_note_date(n)} ({age // 30} ay)" for n, age in res[:200]]
    return _emit("Yaşlanan notlar", "2 yıldan eski, aktif olmayan, hiçbir yere bağlı olmayan notlar. Kutular yalnız işaret: arşive taşıma elle yapılır.",
                 "\n".join(lines) or "Yaşlanan not yok.", f"{len(res)} not", vault, dry)


# ---------------------------------------------------------------- 129 bilgi tazeliği
FRESH_TYPES = {"proje", "basvuru", "başvuru", "teslim", "odev", "ödev"}


def freshness(notes: list[Note], con, today: date | None = None, days: int = 60) -> list[dict]:
    today = today or date.today()
    cut = int(datetime.combine(today - timedelta(days=days), datetime.min.time()).timestamp() * 1000)
    out = []
    for n in notes:
        if str(n.fm.get("type") or "") not in FRESH_TYPES or str(n.fm.get("status") or "") != "aktif":
            continue
        age = (today - _note_date(n)).days
        if age < days:
            continue
        q, rel = _phrase(n.stem), []
        if q:
            try:
                rel = con.execute("SELECT d.doc_id, d.date_ms FROM chunks_fts f JOIN chunks c ON c.id = f.rowid JOIN docs d ON d.doc_id = c.doc_id "
                                  "WHERE chunks_fts MATCH ? AND d.kind IN ('mail','item') AND d.date_ms >= ?", (q, cut)).fetchall()
            except sqlite3.Error:
                rel = []
        docs = {r[0]: r[1] for r in rel}
        out.append({"note": n, "gun": age, "n": len(docs), "son": max(docs.values()) if docs else None})
    return sorted(out, key=lambda r: (-r["n"], -r["gun"]))


def write_freshness(*, vault=None, con=None, mcon=None, dry=False, today=None) -> str:
    rows = freshness(load_notes(vault), _conn(con), today)
    lines = ["| Not | Tür | Son güncelleme | Son 60 gün ilgili mail/makbuz | Öneri |\n|---|---|---|---|---|"]
    for r in rows:
        n = r["note"]
        tip = "dışarıda hareket var, güncel mi?" if r["n"] else "sessiz: hâlâ aktif mi?"
        lines.append(f"| {_wl(n)} | {n.fm.get('type')} | {_note_date(n)} ({r['gun']} g) | {r['n']}" + (f" (son {_ms(r['son'])})" if r["n"] else "") + f" | {tip} |")
    return _emit("Bilgi tazeliği", "`status: aktif` ama 60+ gündür güncellenmemiş proje/başvuru/teslim notları ve son 60 gündeki ilgili mail/makbuz hareketi.",
                 "\n".join(lines) if rows else "Bayat aktif not yok.", f"{len(rows)} not", vault, dry)


# ---------------------------------------------------------------- 130 çelişki tespiti
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d \-()]{8,16}\d)(?!\d)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
DUE_RE = re.compile(r"son teslim[^\n]{0,40}?(\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{4})", re.I)


def _pk(s: str) -> str:
    d = re.sub(r"\D", "", s)
    return d[-10:] if len(d) >= 10 else ""


def _date_str(s: str) -> date | None:
    m = re.match(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", s)
    try:
        return date(int(m[3]), int(m[2]), int(m[1])) if m else _d(s)
    except ValueError:
        return None


def conflicts(notes: list[Note]) -> list[str]:
    out = []
    for n in notes:
        if n.rel.startswith(MIRROR):
            continue
        if n.rel.startswith("60-Kişiler/"):
            body = _body(n)
            ph = {_pk(p) for p in _list(n.fm.get("phone"))} - {""}
            em = {e.lower() for e in _list(n.fm.get("email"))}
            if len(ph) > 1:
                out.append(f"{_wl(n)}: birden çok farklı telefon ({', '.join(_list(n.fm.get('phone')))})")
            if len(em) > 1:
                out.append(f"{_wl(n)}: birden çok farklı e-posta ({', '.join(sorted(em))})")
            if len(set(map(str.lower, _list(n.fm.get("company")))) ) > 1:
                out.append(f"{_wl(n)}: birden çok şirket ({', '.join(_list(n.fm.get('company')))})")
            bph = {_pk(p) for p in PHONE_RE.findall(body)} - {""}
            if ph and bph - ph:
                out.append(f"{_wl(n)}: gövdedeki telefon frontmatter'dan farklı")
            bem = {e.lower() for e in EMAIL_RE.findall(body)}
            if em and bem - em:
                out.append(f"{_wl(n)}: gövdedeki e-posta frontmatter'dan farklı ({', '.join(sorted(bem - em))})")
            comp = _list(n.fm.get("company"))
            m = re.search(r"^\s*(?:şirket|company)\s*:\s*(.+)$", body, re.I | re.M)
            if comp and m and _fold(m[1]).strip() not in {_fold(c) for c in comp}:
                out.append(f"{_wl(n)}: gövdede şirket “{m[1].strip()}”, frontmatter “{comp[0]}”")
        due = _d(n.fm.get("due"))
        if due:
            claims = {x for x in (_date_str(m) for m in DUE_RE.findall(_body(n))) if x}
            if claims - {due}:
                out.append(f"{_wl(n)}: due {due} ama gövdede son teslim {', '.join(sorted(map(str, claims - {due})))}")
    return out


def write_conflicts(*, vault=None, con=None, mcon=None, dry=False) -> str:
    res = conflicts(load_notes(vault))
    return _emit("Çelişkiler", "Kural tabanlı çelişki taraması: kişi notlarında farklı telefon/e-posta/şirket, tarihli notlarda farklı son teslim.",
                 "\n".join(f"- [ ] {x}" for x in res) or "Çelişki bulunamadı.", f"{len(res)} çelişki", vault, dry)


# ---------------------------------------------------------------- 131 yetenek profili
def skill_profile(notes: list[Note]) -> dict[str, dict]:
    sk: dict[str, dict] = {}

    def add(name, grp, ev):
        d = sk.setdefault(_fold(name), {"ad": name, "grup": grp, "kanit": []})
        if ev not in d["kanit"]:
            d["kanit"].append(ev)

    for n in notes:
        if n.rel.startswith("20-Projeler/"):
            for t in _list(n.fm.get("technologies")):
                add(t, "Teknoloji", _wl(n))
        elif n.rel.startswith("10-Dersler/") and Path(n.rel).parent.as_posix() == "10-Dersler":
            add(n.stem, "Ders", _wl(n))
        elif n.rel == "30-Kariyer/LinkedIn profili.md":
            for t in _list(n.fm.get("technologies")) + _list(n.fm.get("skills")):
                add(t, "Teknoloji", _wl(n))
            sec = False
            for line in n.body.splitlines():
                if line.startswith("#"):
                    sec = bool(re.search(r"beceri|skills|yetenek", line, re.I))
                elif sec and (m := re.match(r"\s*[-*]\s+(.+)", line)):
                    add(re.sub(r"\[\[|\]\]", "", m[1]).strip(), "Teknoloji", _wl(n))
    return sk


def write_skills(*, vault=None, con=None, mcon=None, dry=False) -> str:
    sk = skill_profile(load_notes(vault))
    lines = []
    for grp in ("Teknoloji", "Ders"):
        items = sorted((v for v in sk.values() if v["grup"] == grp), key=lambda v: (-len(v["kanit"]), v["ad"].lower()))
        lines.append(f"### {grp}\n\n| Beceri | Kanıt notları |\n|---|---|")
        lines += [f"| {v['ad']} | {', '.join(v['kanit'][:6])}" + (f" (+{len(v['kanit']) - 6})" if len(v["kanit"]) > 6 else "") + " |" for v in items]
        lines.append("")
    return _emit("Yetenek profili", "Proje teknolojileri, ders notları ve LinkedIn profilinden beceri → kanıt notları.",
                 "\n".join(lines), f"{len(sk)} beceri", vault, dry)


# ---------------------------------------------------------------- 132 kişisel sözlük
ACR_RE = re.compile(r"(?<![\wÇĞİÖŞÜçğıöşü])[A-ZÇĞİÖŞÜ]{2,6}(?![\wÇĞİÖŞÜçğıöşü])")
WORD = r"[\wÇĞİÖŞÜçğıöşü'’-]+"
NOT_ACR = {"TODO", "NOT", "OK", "NB", "VE", "ILE", "IV", "VI", "VII", "VIII", "IX", "II", "III", "XI", "XII"}


def _initials(words: list[str]) -> str:
    return "".join(_fold(w)[0] for w in words if w).upper()


def _expansion_ok(acr: str, words: list[str]) -> bool:
    ini, a = _initials(words), _fold(acr).upper()
    if len(words) < 2 or ini[:1] != a[:1]:
        return False
    if len(words) == len(a):
        return ini == a
    it = iter(ini)
    return len(words) <= len(a) + 2 and all(ch in it for ch in a)


def glossary(notes: list[Note], min_notes: int = 3) -> list[tuple[str, int, str]]:
    cnt: Counter = Counter()
    exp: dict[str, str] = {}
    for n in sorted(notes, key=lambda n: n.rel):
        if n.rel.startswith(MIRROR + ("60-Kişiler/",)):
            continue
        text = re.sub(r"```.*?```|https?://\S+|`[^`]*`", " ", _body(n), flags=re.S)
        for a in set(ACR_RE.findall(text)):
            if a not in NOT_ACR:
                cnt[a] += 1
        for m in re.finditer(rf"((?:{WORD}\s+){{1,7}}{WORD})\s*\(\s*([A-ZÇĞİÖŞÜ]{{2,6}})\s*\)", text):
            words, a = m[1].split(), m[2]
            if a in exp:
                continue
            for k in range(len(a), min(len(words), len(a) + 2) + 1):
                if _expansion_ok(a, words[-k:]):
                    exp[a] = " ".join(words[-k:])
                    break
        for m in re.finditer(rf"(?<![\wÇĞİÖŞÜçğıöşü])([A-ZÇĞİÖŞÜ]{{2,6}})\s*\(\s*((?:{WORD}\s+){{1,6}}{WORD})\s*\)", text):
            a, words = m[1], m[2].split()
            if a not in exp and _expansion_ok(a, words):
                exp[a] = " ".join(words)
    return sorted(((a, c, exp.get(a, "")) for a, c in cnt.items() if c >= min_notes), key=lambda x: (-x[1], x[0]))


def write_glossary(*, vault=None, con=None, mcon=None, dry=False) -> str:
    rows = glossary(load_notes(vault))
    lines = ["| Kısaltma | Açılım | Not sayısı |\n|---|---|---|"] + [f"| {a} | {e or ''} | {c} |" for a, c, e in rows]
    known = sum(1 for _, _, e in rows if e)
    return _emit("Sözlük", "Notlarda ≥3 notta geçen BÜYÜK HARF kısaltmalar. Açılım yalnız notlarda “Açılım (KISALTMA)” kalıbıyla geçiyorsa yazılır; yoksa boş.",
                 "\n".join(lines) if rows else "Kısaltma bulunamadı.", f"{len(rows)} kısaltma, {known} açılım", vault, dry)


# ---------------------------------------------------------------- 133 etiket düzenleyici
def tag_key(tag: str) -> str:
    k = re.sub(r"[^a-z0-9]", "", _fold(tag.lstrip("#")))
    for suf in ("lar", "ler"):
        if len(k) > 5 and k.endswith(suf):
            return k[:-3]
    return k


def tag_groups(notes: list[Note]) -> tuple[Counter, list[list[tuple[str, int]]]]:
    freq = Counter(t.lstrip("#") for n in notes if not n.rel.startswith(FOLDER) for t in _list(n.fm.get("tags")))
    by = defaultdict(list)
    for t, c in freq.items():
        by[tag_key(t)].append((t, c))
    groups = [sorted(g, key=lambda x: (-x[1], x[0])) for g in by.values() if len(g) > 1]
    return freq, sorted(groups, key=lambda g: -sum(c for _, c in g))


def write_tags(*, vault=None, con=None, mcon=None, dry=False) -> str:
    freq, groups = tag_groups(load_notes(vault))
    lines = ["### Birleştirme önerileri (otomatik değiştirme yok)"]
    lines += [f"- [ ] {', '.join(f'`{t}` ({c})' for t, c in g)} → önerilen `{g[0][0]}`" for g in groups] or ["Yazım farkı olan etiket yok."]
    lines += ["", "### Sıklık (ilk 40)", "| Etiket | Not |\n|---|---|"] + [f"| {t} | {c} |" for t, c in freq.most_common(40)]
    return _emit("Etiket önerileri", "Yazım farkıyla aynı olan etiketler (aksan/büyük-küçük/tire/çoğul -ler/-lar). Birleştirme elle yapılır.",
                 "\n".join(lines), f"{len(freq)} etiket, {len(groups)} grup", vault, dry)


# ---------------------------------------------------------------- 134 not kalite puanı
REQUIRED_FM = ("type", "status", "tags", "created", "updated")


def score_note(n: Note, nlinks: int, today: date | None = None) -> int:
    """0-100: frontmatter tamlığı 30 + bağlantı 25 + gövde uzunluğu 25 + tazelik 20."""
    today = today or date.today()
    fm_pts = 6 * sum(1 for k in REQUIRED_FM if n.fm.get(k) not in (None, "", []))
    link_pts = 5 * min(nlinks, 5)
    body_pts = 25 * min(len(_body(n).strip()) / 1500, 1)
    age = max((today - _note_date(n)).days, 0)
    fresh = 20 * max(0.0, 1 - max(age - 90, 0) / 640)
    return round(fm_pts + link_pts + body_pts + fresh)


def quality(notes: list[Note], today: date | None = None) -> list[tuple[int, Note]]:
    out_l, in_l = link_graph(notes)
    res = [(score_note(n, len(out_l.get(n.rel, ())) + len(in_l.get(n.rel, ())), today), n) for n in notes
           if not n.rel.startswith(MIRROR + ("50-Günlük/",))]
    return sorted(res, key=lambda x: (x[0], x[1].rel))


def write_quality(*, vault=None, con=None, mcon=None, dry=False, today=None) -> str:
    res = quality(load_notes(vault), today)
    avg = sum(s for s, _ in res) / len(res) if res else 0
    lines = ["| Puan | Not |\n|---|---|"] + [f"| {s} | {_wl(n)} |" for s, n in res[:30]]
    return _emit("Not kalitesi", "Puan = frontmatter tamlığı (30) + bağlantı (25) + gövde uzunluğu (25) + tazelik (20). En düşük 30 not.",
                 "\n".join(lines), f"{len(res)} not, ortalama {avg:.0f}", vault, dry)


# ---------------------------------------------------------------- 135 kaynak güven puanı
TRUST = {"obs": 0.95, "gcal": 0.9, "invoice": 0.9, "contacts": 0.85, "gmail-main": 0.8, "workspace": 0.8, "github": 0.8, "cargo": 0.8,
         "manual": 0.75, "linkedin": 0.7, "kindle": 0.7, "sms": 0.65, "derived": 0.6, "whatsapp": 0.6, "telegram": 0.6, "web": 0.5,
         "rss": 0.5, "youtube": 0.4, "browser": 0.4, "spotify": 0.3}
OFFICIAL = {"fatura", "sözleşme", "resmi yazı"}
DERIVED_DIRS = ("40-Kaynaklar/Mail/", "40-Kaynaklar/Bilgisayar/", "40-Kaynaklar/Drive/", "40-Kaynaklar/Kümeler/", "40-Kaynaklar/Analiz/")


def trust(doc_id: str, con=None) -> float:
    """Belge güveni 0-1 (arama sıralamasında çarpan). Resmi belge (fatura/sözleşme/resmi yazı) > mail > tahmin/türetilmiş."""
    kind, _, rest = doc_id.partition(":")
    if kind == "note":
        base = TRUST["derived"] if rest.startswith(DERIVED_DIRS) else TRUST["contacts"] if rest.startswith("60-Kişiler/") else TRUST["manual"]
    elif kind == "mail":
        acc = rest.split(":", 1)[0]
        base = TRUST["gmail-main"] if acc == "main" else TRUST.get(acc, TRUST.get(f"gmail-{acc}", 0.7))
    elif kind == "file":
        base = 0.8 if rest.lower().endswith(".pdf") else 0.7
    elif kind == "item":
        base = TRUST.get(rest.split(":", 1)[0], 0.5)
    else:
        base = TRUST["derived"]
    if con is not None and kind == "file":
        try:
            r = con.execute("SELECT cls FROM doc_class WHERE doc_id = ?", (doc_id,)).fetchone()
        except sqlite3.Error:
            r = None
        if r and r[0] in OFFICIAL:
            base = max(base, 0.9)
    return base


def write_trust(*, vault=None, con=None, mcon=None, dry=False) -> str:
    lines = ["| Kaynak | Güven |\n|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(TRUST.items(), key=lambda kv: -kv[1])]
    lines += ["", "Tür kuralları (`sb.analysis.trust`):",
              "- note: kasa notu 0.75; kişi notu 0.85; ayna/küme/analiz notu 0.6 (türetilmiş)",
              "- mail: `main` hesabı 0.8, sms 0.65, whatsapp/telegram 0.6, diğer hesap 0.7",
              "- file: PDF 0.8, diğer 0.7; sınıfı fatura/sözleşme/resmi yazı ise en az 0.9 (resmi belge > mail > tahmin)",
              "- item: kaynağın tablodaki değeri, bilinmiyorsa 0.5"]
    return _emit("Kaynak güveni", "Kaynak başına güven puanı; arama sıralamasında skor çarpanı olarak kullanılır.",
                 "\n".join(lines), f"{len(TRUST)} kaynak", vault, dry)


# ---------------------------------------------------------------- 136 görsel küme haritası
PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac", "#1f77b4", "#d62728"]


def pca2d(x):
    import numpy as np
    c = x - x.mean(axis=0)
    _, _, vt = np.linalg.svd(c, full_matrices=False)
    return c @ vt[:2].T


def cluster_svg(points, labels, titles, width: int = 900, height: int = 640) -> str:
    """Gömülü SVG (harici kaynak/script yok): nokta = not, renk = küme, <title> = başlık."""
    import numpy as np
    from html import escape
    p = np.asarray(points, dtype=float)
    lo, hi = p.min(axis=0), p.max(axis=0)
    span = np.where(hi - lo < 1e-9, 1.0, hi - lo)
    xy = 20 + (p - lo) / span * np.array([width - 40, height - 40])
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{PALETTE[int(l) % len(PALETTE)]}" fill-opacity="0.8">'
                   f"<title>{escape(t)} (küme {int(l) + 1})</title></circle>" for (x, y), l, t in zip(xy, labels, titles))
    return f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Not küme haritası">{dots}</svg>'


def cluster_map(con=None, k: int | None = None) -> tuple[str, int, int] | None:
    import numpy as np
    from html import escape
    from . import entities
    refs, vecs = entities.note_vectors(_conn(con))
    if vecs is None or len(refs) < 3:
        return None
    k = k or max(2, min(30, int(round((len(refs) / 3) ** 0.5))))
    k = min(k, len(refs))
    lab, cent = entities.kmeans(vecs, k)
    svg = cluster_svg(pca2d(vecs), lab, [t for _, t in refs])
    legend = []
    for j in range(k):
        idx = np.where(lab == j)[0]
        if len(idx):
            top = idx[np.argsort(-(vecs[idx] @ cent[j]))[:3]]
            legend.append(f'<li><span style="color:{PALETTE[j % len(PALETTE)]}">●</span> Küme {j + 1} ({len(idx)}): '
                          + ", ".join(escape(refs[i][1]) for i in top) + "</li>")
    page = ('<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Not küme haritası</title>'
            '<style>body{font-family:sans-serif;margin:16px;max-width:1000px}svg{border:1px solid #ccc;background:#fafafa}li{margin:2px 0}</style>'
            f"</head><body><h1>Not küme haritası</h1><p>{len(refs)} not, {k} küme (PCA). Noktanın üstüne gelince başlık görünür.</p>"
            f"{svg}<ul>{''.join(legend)}</ul></body></html>")
    return page, len(refs), k


def write_map(*, vault=None, con=None, mcon=None, dry=False) -> str:
    res = cluster_map(con)
    if res is None:
        return "Küme haritası için yeterli not gömmesi yok (önce sb index)."
    page, n, k = res
    if not dry:
        root = vault or vault_ops.VAULT
        p = root / FOLDER / "Küme haritası.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(page, encoding="utf-8", newline="\n")
    return _emit("Küme haritası", "Notların anlam gömmeleri 2B'ye indirilmiş (PCA); nokta = not, renk = küme.",
                 "[Haritayı aç](<Küme haritası.html>) (tarayıcıda; harici kaynak yok)", f"{n} not, {k} küme", vault, dry)


# ---------------------------------------------------------------- 137 veri hattı panosu
ERR_RE = re.compile(r"\[(?:HATA|FAIL|ERR|ERROR)\]|Traceback|\bHATA\b", re.I)


def pipeline_rows(con=None, mcon=None, vault: Path | None = None, logs: Path | None = None) -> list[tuple[str, str, int, str]]:
    """(bölüm, ad, sayı, son/ek bilgi) satırları."""
    con, mcon = _conn(con), _mconn(mcon)
    vault = vault or vault_ops.VAULT
    rows = []
    if mcon is not None:
        def q(sql):
            try:
                return mcon.execute(sql).fetchall()
            except sqlite3.Error:
                return []
        rows += [("mail.db messages", r[0], r[1], _ms(r[2])) for r in q("SELECT account, COUNT(*), MAX(date_ms) FROM messages GROUP BY account")]
        rows += [("mail.db items", r[0], r[1], _ms(r[2])) for r in q("SELECT source, COUNT(*), MAX(date_ms) FROM items GROUP BY source")]
        r = (q("SELECT COUNT(*), MAX(mtime) FROM file_text") or [(0, None)])[0]
        rows.append(("mail.db file_text", "belge", r[0], _ms(r[1] * 1000) if r[1] else "—"))
        r = (q("SELECT COUNT(*) FROM local_files") or [(0,)])[0]
        rows.append(("mail.db local_files", "dosya", r[0], ""))
    for r in con.execute("SELECT d.kind, COUNT(DISTINCT d.doc_id) n, MAX(d.date_ms) last, COUNT(c.id) ch, COUNT(v.chunk_id) ve "
                         "FROM docs d LEFT JOIN chunks c ON c.doc_id = d.doc_id LEFT JOIN vecs v ON v.chunk_id = c.id GROUP BY d.kind"):
        rows.append(("brain.db", r["kind"], r["n"], f"son {_ms(r['last'])} · gömme %{100 * r['ve'] // r['ch'] if r['ch'] else 0}"))
    per = defaultdict(lambda: [0, 0.0])
    for p in vault.rglob("*.md"):
        rel = p.relative_to(vault)
        if any(x in SKIP for x in rel.parts[:-1]):
            continue
        top = rel.parts[0] if len(rel.parts) > 1 else "(kök)"
        per[top][0] += 1
        per[top][1] = max(per[top][1], p.stat().st_mtime)
    rows += [("kasa", k, v[0], f"son {_ms(v[1] * 1000)}") for k, v in sorted(per.items())]
    logs = logs or config.DATA / "logs"
    daily = sorted(logs.glob("daily-*.log")) if logs.exists() else []
    if daily:
        text = daily[-1].read_text(encoding="utf-8", errors="replace")
        rows.append(("günlük çalışma", daily[-1].name, sum(1 for l in text.splitlines() if ERR_RE.search(l)), "hata satırı"))
    return rows


def write_pipeline(*, vault=None, con=None, mcon=None, dry=False) -> str:
    rows = pipeline_rows(con, mcon, vault)
    lines = ["| Bölüm | Ad | Sayı | Son / ek |\n|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    lines.append(f"\n*Üretildi: {datetime.now():%Y-%m-%d %H:%M}*")
    return _emit("Veri hattı", "Her kaynağın sayısı ve son güncellemesi.", "\n".join(lines), f"{len(rows)} satır", vault, dry) \
        if not dry else f"[dry-run] Veri hattı: {len(rows)} satır\n" + "\n".join(f"  {a} · {b}: {c} ({d})" for a, b, c, d in rows)


# ---------------------------------------------------------------- hepsi
STEPS = [("projects", write_projects), ("classify", write_classify), ("duplicates", write_duplicates), ("aging", write_aging),
         ("freshness", write_freshness), ("conflicts", write_conflicts), ("skills", write_skills), ("glossary", write_glossary),
         ("tags", write_tags), ("quality", write_quality), ("trust", write_trust), ("pipeline", write_pipeline)]


def run_all(log=print, steps=None, **kw) -> dict[str, str]:
    """136 ve 124 hariç hepsi sırayla; biri hata verse de diğerleri sürer. Sonuç: ad → özet ya da 'HATA: ...'."""
    out = {}
    for name, fn in steps or STEPS:
        t0 = time.time()
        try:
            out[name] = fn(**kw)
        except Exception as e:                                  # bir analiz diğerlerini durdurmasın
            out[name] = f"HATA: {type(e).__name__}: {e}"
        log(f"[{name}] ({time.time() - t0:.1f} sn) {out[name].splitlines()[0]}")
    return out


def cli(what: str, topic: str | None, dry: bool) -> int:
    if what == "all":
        res = run_all(dry=dry)
        return 1 if any(v.startswith("HATA") for v in res.values()) else 0
    if what == "timeline":
        if not topic:
            print("timeline için konu ver: sb analyze timeline \"konu\"")
            return 2
        print(write_timeline(topic, dry=dry))
        return 0
    fn = dict(STEPS + [("map", write_map)])[what]
    print(fn(dry=dry))
    return 0
