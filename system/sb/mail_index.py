"""mail.db → 40-Kaynaklar/Mail/<Kategori>.md indeks notları (her mail ayrı not olmaz)."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime

from .config import accounts
from .notes import NoteSpec
from .redact import redact

FOLDER = "40-Kaynaklar/Mail"
PER_NOTE = 150
TITLES = {
    "okul": "Okul", "basvuru-yarisma": "Başvuru ve Yarışma", "kariyer": "Kariyer", "sirketim": "Sirketim",
    "gelistirici": "Geliştirici", "finans": "Finans", "alisveris": "Alışveriş", "seyahat-bilet": "Seyahat ve Bilet", "sosyal": "Sosyal",
    "reklam": "Reklam", "bildirim": "Bildirim", "forum": "Forum", "kisisel": "Kişisel", "guvenlik": "Güvenlik",
    "gonderilen": "Gönderilen", "diger": "Diğer",
}


def _cell(s: str | None, n: int) -> str:
    # köşeli parantez kaçışlanır: "[ARBİS] ..." konusu bağlantı metninde "[[ARBİS]" olup sahte wikilink üretiyordu
    s = redact((s or "").replace("\n", " ").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]").strip())
    return s if len(s) <= n else s[: n - 1] + "…"


def _link(account: str, thread_id: str) -> str:
    email = accounts()["google"].get(account, {}).get("email")
    return f"https://mail.google.com/mail/u/{email}/#all/{thread_id}" if email else ""


def build_specs(con: sqlite3.Connection) -> list[NoteSpec]:
    specs = []
    for cat, total in con.execute("SELECT category, COUNT(*) FROM messages GROUP BY category ORDER BY COUNT(*) DESC"):
        # Her konuşmanın (thread) en son mesajı, en yeniden eskiye.
        rows = con.execute(
            """SELECT m.* FROM messages m
               JOIN (SELECT account, thread_id, MAX(date_ms) AS d FROM messages WHERE category = ?
                     GROUP BY account, thread_id) t
                 ON m.account = t.account AND m.thread_id = t.thread_id AND m.date_ms = t.d
               WHERE m.category = ? ORDER BY m.date_ms DESC LIMIT ?""",
            (cat, cat, PER_NOTE),
        ).fetchall()
        lines = [
            f"Toplam {total} mesaj. Son {len(rows)} konuşma gösteriliyor; tamamı `mail.db` içinde aranabilir.",
            "",
            "| Tarih | Hesap | Kimden | Konu |",
            "|---|---|---|---|",
        ]
        for r in rows:
            d = datetime.fromtimestamp(r["date_ms"] / 1000).strftime("%Y-%m-%d")
            who = _cell(r["from_name"] or r["from_addr"], 30)
            subj = _cell(r["subject"] or "(konusuz)", 90)
            link = _link(r["account"], r["thread_id"])
            lines.append(f"| {d} | {r['account']} | {who} | {f'[{subj}]({link})' if link else subj} |")
        title = f"Mail – {TITLES.get(cat, cat)}"
        specs.append(NoteSpec(
            folder=FOLDER,
            title=title,
            frontmatter={
                "type": "kaynak", "status": "aktif", "tags": ["mail", f"mail/{cat}"],
                "source": "mail", "source_id": f"mail-index:{cat}", "due": None,
                "category": cat, "message_count": total,
            },
            owned=("message_count",),
            body=f"# {title}\n\nKategori kuralları: `_system/config/mail_rules.yaml`.\n\n"
                 "## Notlar\n\n## Son konuşmalar\n<!-- sb:auto:liste:start -->\n<!-- sb:auto:liste:end -->\n",
            auto={"liste": "\n".join(lines)},
        ))
    return specs
