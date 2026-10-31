"""Tarayıcı geçmişi ve yer imleri (Chrome/Edge/Brave History + Bookmarks, Firefox places.sqlite) → items (source=browser).

Veritabanı açık tarayıcıda kilitli olabilir: geçici klasöre kopyalanıp salt okunur açılır. Oturum/şifre/token
içeren ve bankacılık/e-devlet adresleri hiç okunmaz.
"""
from __future__ import annotations

import fnmatch
import json
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from ._common import clean, ingest_items, sid

CHROMIUM_EPOCH_MS = 11_644_473_600_000
BANK_HOSTS = ["*bank*", "*.enpara.com", "enpara.com", "*.garantibbva.com.tr", "*.isbank.com.tr", "*.akbank.com",
              "*.ziraatbank.com.tr", "*.yapikredi.com.tr", "*.qnb.com.tr", "*edevlet*", "turkiye.gov.tr",
              "*.turkiye.gov.tr", "*.paypal.com", "*.papara.com"]
_SENS_KEY = ("token", "password", "passwd", "pwd", "session", "secret", "otp")
_SENS_EXACT = {"code", "auth", "sig", "apikey", "api_key", "state", "client_id", "redirect_uri", "nonce", "id_token",
               "access_type", "response_type", "login_hint", "ticket", "saml", "samlrequest", "samlresponse"}
# Giriş/OAuth sayfaları (adres satırında istemci kimliği, durum belirteci taşır): hiç alınmaz
AUTH_HOSTS = ["accounts.google.com", "login.microsoftonline.com", "login.live.com", "appleid.apple.com", "github.com/login*",
              "*.auth0.com", "*.okta.com", "auth.*", "login.*", "sso.*", "oauth.*"]
_AUTH_PATH = ("/oauth", "/o/oauth2", "/authorize", "/signin", "/login", "/sso", "/auth/")


def keep_url(url: str) -> bool:
    try:
        u = urlsplit(url)
    except ValueError:
        return False
    if u.scheme not in ("http", "https"):  # chrome://, edge://, about:, file://, eklenti vb. atlanır
        return False
    host = (u.hostname or "").lower()
    if any(fnmatch.fnmatch(host, p) for p in BANK_HOSTS):
        return False
    segs = {s for s in u.path.lower().split("/") if s}
    if any(fnmatch.fnmatch(host, p) or fnmatch.fnmatch(host + u.path, p) for p in AUTH_HOSTS) or u.path.lower().startswith(_AUTH_PATH) \
            or segs & {"login", "signin", "sign-in", "oauth", "oauth2", "authorize", "sso", "logout"}:
        return False
    from urllib.parse import unquote
    raw = unquote(unquote(f"{u.path}?{u.query}&{u.fragment}")).lower()     # iç içe kodlanmış adresler (next=, q=, continue=)
    if any(k in raw for k in ("token=", "client_id=", "redirect_uri=", "id_token", "access_token", "password", "passwd",
                              "otp=", "/login", "loginpage", "loginrequest", "/oauth", "/verification", "/settings/tokens",
                              "secret", "apikey", "api_key")):
        return False                                           # giriş/doğrulama/anahtar sayfaları hiç alınmaz
    for k, _ in parse_qsl(u.query + "&" + u.fragment, keep_blank_values=True):
        k = k.lower()
        if k in _SENS_EXACT or any(s in k for s in _SENS_KEY) or k.endswith("state"):
            return False
    return True


def _copy_ro(path: Path, tmp: Path) -> sqlite3.Connection:
    dst = tmp / "db.sqlite"
    shutil.copy2(path, dst)
    for suf in ("-wal", "-shm"):
        side = path.with_name(path.name + suf)
        if side.exists():
            try:
                shutil.copy2(side, tmp / ("db.sqlite" + suf))
            except OSError:
                pass
    return sqlite3.connect(f"{dst.as_uri()}?mode=ro", uri=True)


def _item(kind, url, title, ms, browser, **meta) -> dict:
    title = clean(title) or url
    return {"source": "browser", "id": sid(kind, url), "date_ms": ms, "kind": kind, "title": title, "url": url,
            "body": clean(f"{title} {urlsplit(url).hostname or ''}"), "meta": {"browser": browser, **meta}}


def _chromium(con, cutoff_ms, browser) -> list[dict]:
    cut = (cutoff_ms + CHROMIUM_EPOCH_MS) * 1000
    q = ("SELECT u.url, u.title, MAX(v.visit_time), COUNT(*) FROM visits v JOIN urls u ON u.id = v.url "
         "WHERE v.visit_time >= ? GROUP BY u.id")
    return [_item("visit", url, title, t // 1000 - CHROMIUM_EPOCH_MS, browser, visits=n)
            for url, title, t, n in con.execute(q, (cut,)) if keep_url(url)]


def _firefox(con, cutoff_ms) -> list[dict]:
    q = ("SELECT p.url, p.title, MAX(v.visit_date), COUNT(*) FROM moz_historyvisits v "
         "JOIN moz_places p ON p.id = v.place_id WHERE v.visit_date >= ? GROUP BY p.id")
    return [_item("visit", url, title, t // 1000, "firefox", visits=n)
            for url, title, t, n in con.execute(q, (cutoff_ms * 1000,)) if keep_url(url)]


def _firefox_bookmarks(con) -> list[dict]:
    q = ("SELECT p.url, COALESCE(b.title, p.title), b.dateAdded FROM moz_bookmarks b "
         "JOIN moz_places p ON p.id = b.fk WHERE b.type = 1")
    return [_item("bookmark", url, title, (t or 0) // 1000 or None, "firefox")
            for url, title, t in con.execute(q) if keep_url(url)]


def _chromium_bookmarks(path: Path, browser: str) -> list[dict]:
    rows = []

    def walk(node, trail):
        if node.get("type") == "url":
            if keep_url(node.get("url", "")):
                t = int(node.get("date_added") or 0)
                rows.append(_item("bookmark", node["url"], node.get("name"),
                                  t // 1000 - CHROMIUM_EPOCH_MS if t else None, browser, folder="/".join(trail)))
        for c in node.get("children", []):
            walk(c, trail + ([node["name"]] if node.get("name") else []))

    for root in (json.loads(path.read_text(encoding="utf-8-sig")).get("roots") or {}).values():
        if isinstance(root, dict):
            walk(root, [])
    return rows


def parse(path, days: int = 365) -> list[dict]:
    path = Path(path)
    browser = next((b for b, k in (("edge", "edge"), ("brave", "brave"), ("chrome", "chrome"))
                    if k in str(path).lower()), "chromium")
    if path.name == "Bookmarks" or path.suffix.lower() == ".json":
        return _chromium_bookmarks(path, browser)
    cutoff = int(time.time() * 1000) - days * 86_400_000
    with tempfile.TemporaryDirectory() as tmp:
        con = _copy_ro(path, Path(tmp))
        try:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            if "moz_places" in tables:
                return _firefox(con, cutoff) + (_firefox_bookmarks(con) if "moz_bookmarks" in tables else [])
            if "urls" in tables:
                return _chromium(con, cutoff, browser)
            raise ValueError("tanınmayan tarayıcı veritabanı")
        finally:
            con.close()


def discover() -> list[dict]:
    home = Path.home()
    chromium_roots, firefox_roots = [], []
    for env in (os.environ.get("LOCALAPPDATA"), str(home / "AppData" / "Local")):
        if env:
            b = Path(env)
            chromium_roots += [("chrome", b / "Google/Chrome/User Data"), ("edge", b / "Microsoft/Edge/User Data"),
                               ("brave", b / "BraveSoftware/Brave-Browser/User Data")]
    mac = home / "Library/Application Support"
    chromium_roots += [("chrome", mac / "Google/Chrome"), ("edge", mac / "Microsoft Edge"),
                       ("brave", mac / "BraveSoftware/Brave-Browser")]
    cfg = home / ".config"
    chromium_roots += [("chrome", cfg / "google-chrome"), ("edge", cfg / "microsoft-edge"),
                       ("brave", cfg / "BraveSoftware/Brave-Browser")]
    firefox_roots += [Path(os.environ.get("APPDATA") or home / "AppData/Roaming") / "Mozilla/Firefox/Profiles",
                      mac / "Firefox/Profiles", home / ".mozilla/firefox"]
    found, seen = [], set()

    def add(browser, profile, kind, p):
        if p.exists() and p.resolve() not in seen:
            seen.add(p.resolve())
            found.append({"tarayici": browser, "profil": profile, "tur": kind, "yol": str(p), "boyut": p.stat().st_size})

    for browser, root in chromium_roots:
        if root.is_dir():
            for prof in sorted(root.iterdir()):
                if prof.is_dir() and (prof.name == "Default" or prof.name.startswith("Profile ")):
                    add(browser, prof.name, "gecmis", prof / "History")
                    add(browser, prof.name, "yer imi", prof / "Bookmarks")
    for root in firefox_roots:
        if root.is_dir():
            for prof in sorted(root.iterdir()):
                add("firefox", prof.name, "gecmis+yer imi", prof / "places.sqlite")
    return found


def run(path, con, dry_run: bool = False, days: int = 365, **_) -> dict:
    return ingest_items("browser", parse(path, days=days), con, dry_run, refresh=True)
