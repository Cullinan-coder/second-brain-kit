"""Google Takeout (Türkçe ya da İngilizce dışa aktarım) — zip'lerden yalnız işe yarayan kısımlar, açmadan okunur.

Alınanlar:
- Gemini sohbetleri (Etkinliğim/Gemini Uygulamaları | My Activity/Gemini Apps) → `sb.history` ile aylık sohbet notları
- Etkinlik geçmişi (Arama, YouTube, Chrome, Drive, Play...) → items source `activity`, kind = ürün
- Chrome geçmişi (Chrome/Tarih.json | BrowserHistory.json) → items source `browser` (giriş/banka/token süzgeci aynen)
- Keep notları (Keep/*.json) → kasada `40-Kaynaklar/Keep/<başlık>.md` (çöp kutusundakiler hariç)
- YouTube izleme geçmişi + abonelikler (YouTube ve YouTube Music/...) → items source `youtube`
- Play Store yüklemeler/siparişler → items source `play`
Alınmayanlar: Fotoğraflar, YouTube Music dosyaları, posta (mbox — Gmail zaten bağlı), video/ek dosyaları.
`--dry-run`: hiçbir şey yazmadan ne alınacağını sayar.
"""
from __future__ import annotations

import html
import json
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from ._common import clean, ingest_items, sid, text_date

CELL = re.compile(r'<div class="outer-cell.*?<p class="mdl-typography--title">(.*?)<br></p>.*?'
                  r'<div class="content-cell[^"]*body-1">(.*?)</div><div class="content-cell', re.S)
ACT_DIR = re.compile(r"/(?:Etkinliğim|My Activity)/([^/]+)/(?:Etkinliğim|MyActivity|My Activity)\.html$", re.I)
GEMINI_Q = re.compile(r"^(.*?)\s*(?:sorgusuna yanıt istendi|Prompted|İstem:)\s*", re.S)


def _strip(h: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", h)).strip()


def activity_entries(text: str) -> list[dict]:
    """Etkinliğim.html → [{urun, metin, link, date_ms, ham}]. Tarih satırı 'GMT+03:00' içeren ilk <br> parçasıdır."""
    out = []
    for prod, body in CELL.findall(text):
        parts = re.split(r"<br\s*/?>", body)
        di = next((i for i, p in enumerate(parts) if re.search(r"\b(19|20)\d{2}\b.*\d{1,2}:\d{2}", _strip(p))), None)
        if di is None:
            continue
        head = " ".join(_strip(p) for p in parts[:di])
        link = (re.search(r'href="([^"]+)"', "".join(parts[:di])) or [None, None])[1]
        out.append({"urun": _strip(prod), "metin": " ".join(head.split()), "link": html.unescape(link) if link else None,
                    "date_ms": text_date(_strip(parts[di])), "ham": "<br>".join(parts[di + 1:])})
    return out


def gemini_convs(text: str) -> list[dict]:
    convs = []
    for e in activity_entries(text):
        m = GEMINI_Q.match(e["metin"])
        prompt = (m.group(1) if m else e["metin"]).strip()
        if not prompt or not e["date_ms"] or not 0 < e["date_ms"] < 4_102_444_800_000:   # tarih okunamadı / 2100 sonrası
            continue
        answer = " ".join(_strip(e["ham"]).split())
        turns = [("user", prompt)] + ([("assistant", answer)] if answer else [])
        convs.append({"title": prompt[:80], "when": datetime.fromtimestamp(e["date_ms"] / 1000, tz=timezone.utc),
                      "turns": turns, "src": "Gemini"})
    return convs


def chrome_json(text: str) -> list[dict]:
    from .browser import keep_url
    data = json.loads(text)
    rows = []
    for e in data.get("Browser History") or []:
        url = e.get("url") or ""
        if not keep_url(url):
            continue
        ms = int(e.get("time_usec", 0)) // 1000 or None
        rows.append({"source": "browser", "id": sid(url), "date_ms": ms, "kind": "visit", "title": clean(e.get("title") or url)[:300],
                     "url": url, "body": clean(e.get("title") or ""), "meta": {"from": "takeout"}})
    return rows


def keep_notes(z: zipfile.ZipFile) -> list[dict]:
    notes = []
    for n in z.namelist():
        if not (re.search(r"/Keep/[^/]+\.json$", n)):
            continue
        try:
            d = json.loads(z.read(n).decode("utf-8"))
        except ValueError:
            continue
        if d.get("isTrashed"):
            continue
        body = d.get("textContent") or ""
        if d.get("listContent"):
            body += "\n" + "\n".join(f"- [{'x' if i.get('isChecked') else ' '}] {i.get('text', '')}" for i in d["listContent"])
        if not body.strip() and not d.get("title"):
            continue
        ms = int(d.get("userEditedTimestampUsec") or d.get("createdTimestampUsec") or 0) // 1000
        labels = [l.get("name") for l in d.get("labels") or [] if l.get("name")]
        notes.append({"title": (d.get("title") or body.strip().splitlines()[0])[:80], "body": clean(body), "date_ms": ms,
                      "labels": labels, "id": Path(n).stem, "archived": bool(d.get("isArchived"))})
    return notes


def write_keep(notes: list[dict], account: str) -> list[str]:
    from datetime import date
    from .. import vault_ops
    from ..notes import dump_note, safe_filename
    folder = vault_ops.VAULT / "40-Kaynaklar" / "Keep"
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for k in notes:
        d = datetime.fromtimestamp(k["date_ms"] / 1000).date() if k["date_ms"] else date.today()
        name = safe_filename(k["title"]) or f"Keep {k['id']}"
        p = folder / f"{name}.md"
        fm = {"type": "kaynak", "status": "arsiv" if k["archived"] else "aktif", "tags": ["keep", *[re.sub(r"\W", "-", l.lower()) for l in k["labels"]]],
              "source": "keep", "source_id": f"keep:{account}:{k['id']}", "created": d, "updated": d, "due": None}
        if p.exists() and f"keep:{account}:{k['id']}" not in p.read_text(encoding="utf-8"):
            p = folder / f"{name} ({k['id'][:8]}).md"
        p.write_text(dump_note(fm, f"# {k['title']}\n\n{k['body']}\n"), encoding="utf-8")
        written.append(vault_ops._rel(p))
    if written:
        vault_ops.commit(written, f"Keep notları ({account}): {len(written)}")
    return written


NB_RE = re.compile(r"/NotebookLM/([^/]+)/(?:(Sources|Artifacts|Chat History)/)?([^/]+)$")
NB_SOURCE_CHARS, NB_TEXT_CHARS = 60_000, 6_000


def _html_text(raw: bytes) -> str:
    h = raw.decode("utf-8", "replace")
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", h)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", h)).split())


def notebooklm(z: zipfile.ZipFile) -> list[dict]:
    """NotebookLM defterleri: {title, id, created, sources:[{name,text}], artifacts:[{title,type,text}], chats:[text]}."""
    nbs: dict[str, dict] = {}
    names = set(z.namelist())
    for n in z.namelist():
        m = NB_RE.search(n)
        if not m:
            continue
        nb = nbs.setdefault(m.group(1), {"title": m.group(1), "id": "", "created": "", "sources": [], "artifacts": [], "chats": []})
        part, name = m.group(2), m.group(3)
        if not part and name.endswith(" metadata.json"):
            try:
                meta = json.loads(z.read(n).decode("utf-8"))
            except ValueError:
                continue
            nb.update(title=meta.get("title") or nb["title"], id=meta.get("id", ""),
                      created=(meta.get("metadata") or {}).get("createTime", "")[:10])
        elif part == "Sources" and name.endswith(".html"):
            nb["sources"].append({"name": name[:-5], "text": _html_text(z.read(n))[:NB_SOURCE_CHARS]})
        elif part == "Chat History" and name.endswith(".html"):
            nb["chats"].append(_html_text(z.read(n))[:NB_TEXT_CHARS])
        elif part == "Artifacts" and name.endswith((".mp4", ".m4a", ".wav")):
            nb["artifacts"].append({"title": name, "type": "sesli/görüntülü özet", "text": ""})
        elif part == "Artifacts" and not name.endswith((" metadata.json", ".png", ".jpg")):
            kind = ""
            if n + " metadata.json" in names:
                try:
                    kind = json.loads(z.read(n + " metadata.json").decode("utf-8")).get("type", "")
                except ValueError:
                    pass
            nb["artifacts"].append({"title": name, "type": kind.replace("ARTIFACT_TYPE_", "").lower(),
                                    "text": _html_text(z.read(n))[:NB_TEXT_CHARS]})
    return list(nbs.values())


def write_notebooklm(nbs: list[dict], account: str, con) -> list[str]:
    """Defter başına 40-Kaynaklar/NotebookLM notu; kaynak metinleri beyin dizini için items'a (source=notebooklm)."""
    from datetime import date
    from .. import vault_ops
    from ..notes import dump_note, safe_filename
    from ..redact import redact
    folder = vault_ops.VAULT / "40-Kaynaklar" / "NotebookLM"
    folder.mkdir(parents=True, exist_ok=True)
    written, items = [], []
    for nb in nbs:
        d = date.fromisoformat(nb["created"]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", nb["created"] or "") else date.today()
        b = [f"# {nb['title']}", "", f"NotebookLM defteri ({account}) · {d}", "", f"## Kaynaklar ({len(nb['sources'])})", ""]
        b += [f"- {s['name']} ({len(s['text'])} karakter)" for s in nb["sources"]] or ["- (yok)"]
        if nb["artifacts"]:
            b += ["", f"## Üretilenler ({len(nb['artifacts'])})"]
            for a in nb["artifacts"]:
                b += ["", f"### {a['title']}" + (f" · {a['type']}" if a["type"] else "")] + ([a["text"][:3000]] if a["text"] else [])
        for i, c in enumerate(nb["chats"], 1):
            b += ["", f"## Sohbet {i}", "", c]
        fm = {"type": "kaynak", "status": "aktif", "tags": ["notebooklm"], "source": "notebooklm",
              "source_id": f"notebooklm:{account}:{nb['id'] or nb['title']}", "created": d, "updated": date.today(), "due": None}
        p = folder / f"{safe_filename(nb['title']) or nb['id']}.md"
        p.write_text(dump_note(fm, redact("\n".join(b)) + "\n"), encoding="utf-8", newline="\n")
        written.append(vault_ops._rel(p))
        when = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)
        items += [{"source": "notebooklm", "id": sid(nb["title"], s["name"]), "date_ms": when, "kind": "source",
                   "title": f"{nb['title']} › {s['name']}", "url": None, "body": redact(s["text"]),
                   "meta": {"notebook": nb["title"], "account": account}} for s in nb["sources"] if s["text"]]
    if items:
        ingest_items("notebooklm", items, con, refresh=True)
    if written:
        vault_ops.commit(written, f"NotebookLM defterleri ({account}): {len(written)}")
    return written


def run(paths: list[str], con, account: str = "google", dry_run: bool = False, log=print) -> dict:
    from .. import history
    from . import youtube
    zips = [Path(p) for p in paths]
    stats = {"gemini": 0, "activity": 0, "browser": 0, "keep": 0, "youtube": 0, "play": 0, "notebooklm": 0}
    convs, items, keep, nbs = [], [], [], []
    with tempfile.TemporaryDirectory() as tmp:
        for zp in zips:
            with zipfile.ZipFile(zp) as z:
                for n in z.namelist():
                    if (m := ACT_DIR.search(n)):
                        text = z.read(n).decode("utf-8", "replace")
                        prod = m.group(1)
                        if prod.lower().startswith("gemini"):
                            convs += gemini_convs(text)
                            continue
                        from .browser import keep_url
                        for e in activity_entries(text):
                            if not e["metin"] or (e["link"] and not keep_url(e["link"])):   # giriş/token adresleri alınmaz
                                continue
                            items.append({"source": "activity", "id": sid(prod, e["metin"], e["date_ms"]), "date_ms": e["date_ms"],
                                          "kind": prod, "title": clean(e["metin"])[:300], "url": e["link"],
                                          "body": clean(e["metin"]), "meta": {"account": account}})
                    elif re.search(r"/Chrome/(?:Tarih|BrowserHistory|History)\.json$", n):
                        items += chrome_json(z.read(n).decode("utf-8-sig", "replace"))
                    elif re.search(r"/YouTube[^/]*/(?:geçmiş|history)/[^/]+\.(?:html|json)$", n, re.I) or \
                            re.search(r"/YouTube[^/]*/(?:abonelikler|subscriptions)/[^/]+\.csv$", n, re.I):
                        f = Path(tmp) / Path(n).name
                        f.write_bytes(z.read(n))
                        items += [r for r in youtube.parse(f)]
                    elif re.search(r"/Google Play Store/(?:Installs|Order History)\.json$", n):
                        try:
                            data = json.loads(z.read(n).decode("utf-8"))
                        except ValueError:
                            continue
                        kind = "install" if "Installs" in n else "order"
                        for e in data:
                            d = e.get("install") or e.get("orderHistory") or e
                            title = ((d.get("doc") or {}).get("title") or d.get("title") or "").strip()
                            if title:
                                when = d.get("firstInstallationTime") or d.get("creationTime") or ""
                                items.append({"source": "play", "id": sid(kind, title, when), "date_ms": None, "kind": kind,
                                              "title": clean(title), "url": None, "body": clean(title), "meta": {"time": when}})
                keep += keep_notes(z)
                nbs += notebooklm(z)
    for it in items:
        stats[it["source"] if it["source"] in stats else "activity"] += 1
    stats["gemini"], stats["keep"], stats["notebooklm"] = len(convs), len(keep), len(nbs)
    if dry_run:
        return {**stats, "yazıldı": False}
    for src in sorted({i["source"] for i in items}):
        ingest_items(src, [i for i in items if i["source"] == src], con, refresh=(src == "browser"))
    out = history.write_convs(convs, apply=True) if convs else ""
    written = write_keep(keep, account) if keep else []
    nb_written = write_notebooklm(nbs, account, con) if nbs else []
    log(out)
    return {**stats, "yazıldı": True, "keep_notları": len(written), "notebooklm_notları": len(nb_written)}
