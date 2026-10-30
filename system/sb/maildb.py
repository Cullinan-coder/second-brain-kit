"""Yerel mail arşivi (SQLite + FTS5). Git'e ve telefona girmez."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    account      TEXT NOT NULL,          -- accounts.yaml takma adı (main, side, <imap takma adları>)
    id           TEXT NOT NULL,          -- kaynaktaki mesaj kimliği
    thread_id    TEXT,
    date_ms      INTEGER NOT NULL,       -- epoch milisaniye
    from_addr    TEXT, from_name TEXT,
    to_addrs     TEXT, cc_addrs TEXT,
    subject      TEXT, snippet TEXT,
    body         TEXT,
    labels       TEXT,                   -- JSON liste
    attachments  TEXT,                   -- JSON liste (dosya adları)
    category     TEXT,
    category_src TEXT,                   -- rule | claude | manual
    fetched_at   TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (account, id)
);
CREATE INDEX IF NOT EXISTS ix_messages_date ON messages(date_ms);
CREATE INDEX IF NOT EXISTS ix_messages_cat ON messages(category, date_ms);
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    subject, body, from_addr, from_name, content='messages', content_rowid='rowid', tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, subject, body, from_addr, from_name) VALUES (new.rowid, new.subject, new.body, new.from_addr, new.from_name);
END;
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, subject, body, from_addr, from_name) VALUES ('delete', old.rowid, old.subject, old.body, old.from_addr, old.from_name);
END;
CREATE TABLE IF NOT EXISTS drive_files (
    id         TEXT PRIMARY KEY,
    name       TEXT,
    mime       TEXT,
    path       TEXT,                     -- "Üst klasör/Alt klasör" (kökteyse "")
    modified   TEXT,                     -- RFC3339
    size       INTEGER,
    link       TEXT,
    text       TEXT,                     -- Google Docs düz metni (son 120 gün)
    seen_at    TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS calls (
    id           TEXT PRIMARY KEY,       -- numara|tarih|tür özeti
    number       TEXT,
    phone_key    TEXT,                   -- son 10 hane (kişi eşleştirme)
    date_ms      INTEGER NOT NULL,
    type         INTEGER,                -- 1 gelen, 2 giden, 3 cevapsız, 5 reddedilen ...
    duration     INTEGER,                -- saniye
    contact_name TEXT
);
CREATE INDEX IF NOT EXISTS ix_calls_phone ON calls(phone_key, date_ms);
CREATE TABLE IF NOT EXISTS state (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS extractions (
    account    TEXT NOT NULL,
    id         TEXT NOT NULL,
    result     TEXT,                     -- JSON: claude çıktısı
    decision   TEXT,                     -- calendar | pending | none
    created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (account, id)
);
"""

FIELDS = ("account", "id", "thread_id", "date_ms", "from_addr", "from_name", "to_addrs", "cc_addrs",
          "subject", "snippet", "body", "labels", "attachments", "category", "category_src")


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=900)  # uzun süren başka bir yazıcı (ör. content-sync) varsa bekle
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def known_ids(con: sqlite3.Connection, account: str) -> set[str]:
    return {r[0] for r in con.execute("SELECT id FROM messages WHERE account = ?", (account,))}


def insert(con: sqlite3.Connection, msg: dict) -> None:
    row = {k: msg.get(k) for k in FIELDS}
    for k in ("labels", "attachments"):
        if not isinstance(row[k], str):
            row[k] = json.dumps(row[k] or [], ensure_ascii=False)
    con.execute(
        f"INSERT OR IGNORE INTO messages ({', '.join(FIELDS)}) VALUES ({', '.join('?' * len(FIELDS))})",
        [row[k] for k in FIELDS],
    )


def get_state(con: sqlite3.Connection, key: str) -> str | None:
    r = con.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
    return r[0] if r else None


def set_state(con: sqlite3.Connection, key: str, value: str) -> None:
    con.execute("INSERT INTO state(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
