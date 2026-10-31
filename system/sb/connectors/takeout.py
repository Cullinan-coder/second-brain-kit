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
        if not prompt or not e["date_ms"]:
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


def run(paths: list[str], con, account: str = "google", dry_run: bool = False, log=print) -> dict:
    from .. import history
    from . import youtube
    zips = [Path(p) for p in paths]
    stats = {"gemini": 0, "activity": 0, "browser": 0, "keep": 0, "youtube": 0, "play": 0}
    convs, items, keep = [], [], []
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
    for it in items:
        stats[it["source"] if it["source"] in stats else "activity"] += 1
    stats["gemini"], stats["keep"] = len(convs), len(keep)
    if dry_run:
        return {**stats, "yazıldı": False}
    for src in sorted({i["source"] for i in items}):
        ingest_items(src, [i for i in items if i["source"] == src], con, refresh=(src == "browser"))
    out = history.write_convs(convs, apply=True) if convs else ""
    written = write_keep(keep, account) if keep else []
    log(out)
    return {**stats, "yazıldı": True, "keep_notları": len(written)}
