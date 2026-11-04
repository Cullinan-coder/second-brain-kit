"""Eski sohbet geçmişini içe aktarma: ChatGPT, Claude.ai ve Gemini (Google Takeout) dışa aktarımları.

`sb history-import <zip|klasör|json> [--since 2025-01-01] [--until ...] [--exclude "kelime1,kelime2"] [--private] [--apply]`
- Önce --apply olmadan çalıştır: kaç sohbetin hangi aylara gideceğini gösterir, hiçbir şey yazmaz (onay kapısı).
- Dışa aktarım YEREL okunur; hiçbir yere gönderilmez. Özel/hassas sohbetler --exclude ya da tarih sınırıyla elenmezse dahil olur.
- Çıktı: `40-Kaynaklar/Sohbet geçmişi/<Kaynak> YYYY-AA.md` (ay başına bir not; her sohbet başlık + kısaltılmış turlar).
  Yeniden çalıştırmak aynı notları baştan üretir (kopya olmaz). --private notları otomatik bağlamdan çıkarır.
- Metin `redact` ve hassas veri süzgecinden geçer. Bilgi damıtma (kavram notu) ayrı adımdır: Claude `gecmis-import` skill'iyle yapar.
"""
from __future__ import annotations

import json
import re
import zipfile
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from . import vault_ops
from .notes import dump_note
from .redact import redact

FOLDER = "40-Kaynaklar/Sohbet geçmişi"
USER_CHARS, BOT_CHARS, MAX_TURNS = 500, 700, 14


def _load(src: Path) -> list[tuple[str, object]]:
    """(dosya adı, JSON) listesi: zip içinden, klasörden ya da tek dosyadan."""
    out = []
    if src.suffix.lower() == ".zip":
        from .content import guard_zip
        guard_zip(src)                                   # zip bombası denetimi (D-28)
        with zipfile.ZipFile(src) as z:
            for n in z.namelist():
                if n.lower().endswith(".json") and ("conversations" in n.lower() or "myactivity" in n.lower().replace(" ", "")):
                    out.append((n, json.loads(z.read(n).decode("utf-8"))))
    elif src.is_dir():
        for p in src.rglob("*.json"):
            if "conversations" in p.name.lower() or "myactivity" in p.name.lower().replace(" ", ""):
                out.append((str(p), json.loads(p.read_text(encoding="utf-8"))))
    else:
        out.append((src.name, json.loads(src.read_text(encoding="utf-8"))))
    return out


def _ts(v) -> datetime | None:
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, tz=timezone.utc)
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None


def _chatgpt(conv: dict) -> dict | None:
    """ChatGPT: mapping ağacında current_node'dan köke yürü (dallanmada son seçilen yol)."""
    mapping, node, turns = conv.get("mapping") or {}, conv.get("current_node"), []
    while node and node in mapping:
        m = mapping[node].get("message") or {}
        role = (m.get("author") or {}).get("role")
        parts = (m.get("content") or {}).get("parts") or []
        text = "\n".join(p for p in parts if isinstance(p, str)).strip()
        if role in ("user", "assistant") and text:
            turns.append((role, text))
        node = mapping[node].get("parent")
    turns.reverse()
    when = _ts(conv.get("create_time"))
    return {"title": conv.get("title") or "(başlıksız)", "when": when, "turns": turns, "src": "ChatGPT"} if turns and when else None


def _claude(conv: dict) -> dict | None:
    turns = []
    for m in conv.get("chat_messages") or []:
        text = (m.get("text") or "").strip() or "\n".join(c.get("text", "") for c in m.get("content") or [] if isinstance(c, dict)).strip()
        if text:
            turns.append(("user" if m.get("sender") == "human" else "assistant", text))
    when = _ts(conv.get("created_at"))
    return {"title": conv.get("name") or "(başlıksız)", "when": when, "turns": turns, "src": "Claude"} if turns and when else None


def _gemini(item: dict) -> dict | None:
    """Takeout 'Gemini Apps' etkinliği: her kayıt tek istem (+ varsa cevap HTML'i)."""
    title = str(item.get("title") or "")
    prompt = re.sub(r"^(Prompted|Şunu sordunuz:|İstem:)\s*", "", title).strip()
    if not prompt:
        return None
    ans = " ".join(re.sub(r"<[^>]+>", " ", h) for h in (item.get("safeHtmlItem") or [{}])[0].values()) if item.get("safeHtmlItem") else ""
    turns = [("user", prompt)] + ([("assistant", " ".join(ans.split()))] if ans.strip() else [])
    when = _ts(item.get("time"))
    return {"title": prompt[:80], "when": when, "turns": turns, "src": "Gemini"} if when else None


def parse(src: Path) -> list[dict]:
    convs = []
    for name, data in _load(src):
        items = data if isinstance(data, list) else data.get("conversations") or []
        for c in items:
            if not isinstance(c, dict):
                continue
            if "mapping" in c:
                convs.append(_chatgpt(c))
            elif "chat_messages" in c:
                convs.append(_claude(c))
            elif "Gemini" in str(c.get("header", "")) or "Bard" in str(c.get("header", "")):
                convs.append(_gemini(c))
    return [c for c in convs if c]


def select(convs: list[dict], since: date | None = None, until: date | None = None, exclude: list[str] | None = None) -> list[dict]:
    ex = [e.strip().lower() for e in exclude or [] if e.strip()]
    out = []
    for c in convs:
        d = c["when"].date()
        if (since and d < since) or (until and d > until):
            continue
        blob = (c["title"] + " " + " ".join(t for _, t in c["turns"])).lower()
        if any(e in blob for e in ex):
            continue
        out.append(c)
    return sorted(out, key=lambda c: c["when"])


def render(convs: list[dict]) -> str:
    parts = []
    for c in convs:
        lines = [f"### {c['title'][:120]} ({c['when']:%Y-%m-%d %H:%M})"]
        for role, text in c["turns"][:MAX_TURNS]:
            cap = USER_CHARS if role == "user" else BOT_CHARS
            t = " ".join(text.split())
            lines.append(f"- **{'Ben' if role == 'user' else c['src']}:** {t[:cap]}{'…' if len(t) > cap else ''}")
        if len(c["turns"]) > MAX_TURNS:
            lines.append(f"- … ({len(c['turns']) - MAX_TURNS} tur daha)")
        parts.append("\n".join(lines))
    text = redact("\n\n".join(parts))
    return vault_ops.SENSITIVE_RE.sub("[gizli]", text)


def run(src: str, since: str = "", until: str = "", exclude: str = "", private: bool = False, apply: bool = False) -> str:
    path = Path(src).expanduser()
    if not path.exists():
        return f"Bulunamadı: {src}"
    convs = select(parse(path), date.fromisoformat(since) if since else None, date.fromisoformat(until) if until else None,
                   exclude.split(",") if exclude else [])
    if not convs:
        return "İçe aktarılacak sohbet bulunamadı (biçim tanınmadı ya da hepsi elendi)."
    return write_convs(convs, apply, private)


def write_convs(convs: list[dict], apply: bool = True, private: bool = False) -> str:
    """Sohbetleri kaynak+ay başına not olarak yazar. Aynı ay notunda daha önce yazılmış sohbetler korunur (birleşir)."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in convs:
        groups[(c["src"], f"{c['when']:%Y-%m}")].append(c)
    plan = "\n".join(f"- {s} {m}: {len(v)} sohbet" for (s, m), v in sorted(groups.items()))
    if not apply:
        return (f"DENEME (yazılmadı): {len(convs)} sohbet, {len(groups)} aylık not → {FOLDER}/\n{plan}\n"
                "Özel/hassas sohbetler dahil olur; elemek için --exclude \"kelime1,kelime2\" ya da --since/--until. "
                "Uygunsa aynı komutu --apply ile çalıştır.")
    folder = vault_ops.VAULT / FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for (s, m), v in sorted(groups.items()):
        p = folder / f"{s} {m}.md"
        v = sorted({(c["when"], c["title"]): c for c in v}.values(), key=lambda c: c["when"])
        fm = {"type": "kaynak", "status": "aktif", "tags": ["sohbet-gecmisi", s.lower()], "source": "manual",
              "source_id": f"gecmis:{s.lower()}:{m}", "created": date.today(), "updated": date.today(), "due": None,
              "visibility": "private" if private else "internal"}
        p.write_text(dump_note(fm, f"# {s} sohbetleri {m}\n\n{len(v)} sohbet (içe aktarım {date.today()}).\n\n{render(v)}\n"), encoding="utf-8")
        written.append(vault_ops._rel(p))
    sha = vault_ops.commit(written, f"sohbet geçmişi içe aktarıldı: {len(convs)} sohbet")
    vault_ops.log("claude", "geçmiş içe aktarım", FOLDER, f"{len(convs)} sohbet, {len(written)} not", sha)
    return f"İçe aktarıldı: {len(convs)} sohbet → {len(written)} not ({FOLDER})\n{plan}"
