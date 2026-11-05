"""TDK Güncel Türkçe Sözlük (sozluk.gov.tr/gts) — kelime anlamı, kökeni, örnekleri, birleşikler, deyim/atasözleri.

Salt okunur: yalnız TDK'nın herkese açık arama ucu, kelime kelime ve istek üzerine sorgulanır (toplu indirme yok).
Cevaplar `~/.secondbrain/tdk.db` önbelleğine yazılır (git'e girmez); aynı kelime ikinci kez ağa gitmez, ağ yoksa önbellek kullanılır.
`kaydet=True` ise kelime kısa anlamıyla kasadaki `40-Kaynaklar/Kelime defteri.md`ye eklenir (kullanıcının öğrendiği kelimeler).
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import date

from .config import DATA, VAULT

URL = "https://sozluk.gov.tr/gts?ara="
DB = DATA / "tdk.db"
NOTEBOOK = VAULT / "40-Kaynaklar" / "Kelime defteri.md"
TTL_DAYS = 90                       # bulunan kelime 90 günde bir tazelenir; "bulunamadı" 7 günde bir


def _db() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS gts(kelime TEXT PRIMARY KEY, json TEXT, fetched REAL)")
    return con


def _key(word: str) -> str:
    return " ".join(word.replace("İ", "i").replace("I", "ı").lower().split())


def fetch(word: str) -> list[dict]:
    """TDK'dan ham madde listesi (önbellekli). Bulunamazsa []."""
    k = _key(word)
    if not k or len(k) > 60:
        return []
    con = _db()
    row = con.execute("SELECT json, fetched FROM gts WHERE kelime=?", (k,)).fetchone()
    if row:
        data = json.loads(row[0])
        ttl = (TTL_DAYS if data else 7) * 86400
        if time.time() - row[1] < ttl:
            return data
    try:
        req = urllib.request.Request(URL + urllib.parse.quote(k), headers={"User-Agent": "Mozilla/5.0 (second-brain)"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = json.loads(r.read().decode("utf-8"))
    except Exception:
        if row:                                     # ağ yok: eski önbellek
            return json.loads(row[0])
        raise
    data = raw if isinstance(raw, list) else []     # {"error": "Sonuç bulunamadı"} → []
    con.execute("INSERT OR REPLACE INTO gts VALUES (?,?,?)", (k, json.dumps(data, ensure_ascii=False), time.time()))
    con.commit()
    return data


def _clean(s: str | None) -> str:
    return " ".join(re.sub(r"<[^>]+>", "", s or "").split())


def format_entries(data: list[dict], max_senses: int = 8) -> str:
    out = []
    for e in data:
        head = e.get("madde", "")
        if e.get("on_taki"):
            head = f"{_clean(e['on_taki'])} {head}"
        if e.get("lisan"):
            head += f" ({e['lisan']})"
        out.append(f"## {head}")
        for a in (e.get("anlamlarListe") or [])[:max_senses]:
            tags = ", ".join(o.get("tam_adi", "") for o in a.get("ozelliklerListe") or [])
            line = f"{a.get('anlam_sira', '')}. " + (f"[{tags}] " if tags else "") + _clean(a.get("anlam"))
            for o in (a.get("orneklerListe") or [])[:1]:
                who = ", ".join(y.get("tam_adi", "") for y in o.get("yazar") or [])
                line += f"\n   Örnek: \"{_clean(o.get('ornek'))}\"" + (f" — {who}" if who else "")
            out.append(line)
        if e.get("birlesikler"):
            b = e["birlesikler"].split(", ")
            out.append("Birleşik sözler: " + ", ".join(b[:15]) + (" …" if len(b) > 15 else ""))
        atas = [x.get("madde", "") for x in e.get("atasozu") or []]
        if atas:
            out.append("Deyim/atasözü: " + "; ".join(atas[:10]) + (" …" if len(atas) > 10 else ""))
    return "\n".join(out)


def _short(data: list[dict]) -> str:
    """Kelime defteri için: ilk maddenin ilk iki anlamı."""
    e = data[0]
    senses = [_clean(a.get("anlam")) for a in (e.get("anlamlarListe") or [])[:2]]
    origin = f" ({e['lisan']})" if e.get("lisan") else ""
    return f"{origin} — " + " · ".join(f"{i}. {s}" for i, s in enumerate(senses, 1))


def save_to_notebook(word: str, data: list[dict]) -> str:
    madde = data[0].get("madde", word)
    if NOTEBOOK.exists():
        text = NOTEBOOK.read_text(encoding="utf-8")
    else:
        NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
        text = ("---\ntype: kaynak\nstatus: aktif\ntags: [kelime, turkce, tdk]\nsource: tdk\nsource_id: kelime-defteri\n"
                f"created: {date.today()}\nupdated: {date.today()}\n---\n# Kelime defteri\n\n"
                "Öğrendiğim kelimeler (kaynak: TDK Güncel Türkçe Sözlük, sozluk.gov.tr). Asistana \"… kelimesini deftere ekle\" de.\n\n")
    if re.search(rf"^- \*\*{re.escape(madde)}\*\*", text, re.M):
        return f"'{madde}' zaten kelime defterinde."
    text = re.sub(r"^updated: .*$", f"updated: {date.today()}", text, count=1, flags=re.M)
    text = text.rstrip("\n") + f"\n- **{madde}**{_short(data)} _(eklendi {date.today()})_\n"
    NOTEBOOK.write_text(text, encoding="utf-8")
    return f"'{madde}' kelime defterine eklendi."


def lookup(word: str, save: bool = False) -> str:
    """Kelimeyi TDK'da arar; biçimli metin döndürür. save=True: kelime defterine de ekler."""
    word = word.strip().strip("\"'“”.,!?")
    try:
        data = fetch(word)
    except Exception as e:
        return f"TDK sözlüğüne ulaşılamadı ({type(e).__name__}); önbellekte de yok."
    if not data:
        return (f"TDK Güncel Türkçe Sözlük'te '{word}' bulunamadı. Yazımı farklı olabilir (ör. şapka, ek almış hâl) "
                "ya da özel ad / yerel söz olabilir; kökünü dene.")
    text = "Kaynak: TDK Güncel Türkçe Sözlük (sozluk.gov.tr)\n" + format_entries(data)
    if save:
        text += "\n\n" + save_to_notebook(word, data)
    return text
