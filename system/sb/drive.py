"""Google Drive (drive.readonly) → mail.db `drive_files` + 40-Kaynaklar/Drive indeks notları.

Üç kaynak taranır: (1) "Drive'ım" ağacı, (2) "Benimle paylaşılanlar" (paylaşılan klasörlerin içine de inilir),
(3) ortak drive'lar. "Bilgisayarlar" (Drive masaüstü senkronu) taranmaz; o dosyalar zaten bu PC'nin kendi indeksinde.
Dosyalar indirilmez; ad, klasör yolu, sahip, tarih ve link tutulur. Sadece KENDİ Google Docs belgelerinin
(son 120 gün) düz metni alınır. Drive'a hiçbir şey yazılmaz.
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .google_auth import service
from .notes import NoteSpec
from .redact import redact

FOLDER_MIME = "application/vnd.google-apps.folder"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
DOC_MIME = "application/vnd.google-apps.document"
SKIP_TOP = ("SMSBackupRestore",)
TEXT_DAYS = 120
PER_NOTE = 200
NOTE_FOLDER = "40-Kaynaklar/Drive"
FIELDS = "id,name,mimeType,modifiedTime,parents,webViewLink,size,owners(emailAddress,me)"
LOOSE_LABEL = "Paylaşılan – tek dosyalar"
MIME_LABEL = {
    DOC_MIME: "Doküman", "application/vnd.google-apps.spreadsheet": "E-tablo",
    "application/vnd.google-apps.presentation": "Sunum", "application/pdf": "PDF",
}


def _owner(f: dict) -> str:
    o = (f.get("owners") or [{}])[0]
    return "ben" if o.get("me") else (o.get("emailAddress") or "?")


def _short(email: str) -> str:
    return email.split("@")[0][:24] if email and email != "ben" else "ben"


def _children(api, folder: str, drive_id: str | None = None):
    token = None
    while True:
        kw = dict(q=f"'{folder}' in parents and trashed = false", pageSize=1000, pageToken=token,
                  fields=f"nextPageToken, files({FIELDS})", supportsAllDrives=True, includeItemsFromAllDrives=True)
        resp = api.list(**kw).execute()
        yield from resp.get("files", [])
        token = resp.get("nextPageToken")
        if not token:
            return


WORKERS = 8


def _crawl(api, roots: list[dict], out: list[dict], seen: set[str], log, skip=SKIP_TOP, factory=None) -> None:
    """roots: başlangıç klasörleri (zaten `out` içinde); altlarındaki her şeyi `out`'a ekler.
    `factory` verilirse klasörler WORKERS iş parçacığıyla paralel gezilir (her iş parçacığının kendi API nesnesi olur)."""
    if factory is None:                                   # sıralı (testler / küçük ağaçlar)
        queue = [r["id"] for r in roots]
        while queue:
            folder = queue.pop()
            for f in _children(api, folder):
                if f["id"] in seen:
                    continue
                seen.add(f["id"])
                out.append(f)
                if f["mimeType"] == FOLDER_MIME and not f["name"].startswith(skip):
                    queue.append(f["id"])
            if len(seen) % 100 == 0:
                log(f"  {len(seen)} öğe...")
        return
    import threading
    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
    local = threading.local()

    def list_folder(fid: str) -> list[dict]:
        if not hasattr(local, "api"):
            local.api = factory()
        return list(_children(local.api, fid))

    last_log = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        pending = {ex.submit(list_folder, r["id"]) for r in roots}
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for fut in done:
                for f in fut.result():
                    if f["id"] in seen:
                        continue
                    seen.add(f["id"])
                    out.append(f)
                    if f["mimeType"] == FOLDER_MIME and not f["name"].startswith(skip):
                        pending.add(ex.submit(list_folder, f["id"]))
            if len(seen) - last_log >= 2000:
                last_log = len(seen)
                log(f"  {len(seen)} öğe...")


def list_all(api, drives_api=None, log=print, factory=None) -> tuple[list[dict], dict]:
    """(öğeler, durum). Durum: shared_ok / drives_ok (o kaynak başarıyla tarandı mı)."""
    status = {"shared_ok": True, "drives_ok": True}
    out: list[dict] = []
    seen: set[str] = set()

    root = api.get(fileId="root", fields="id").execute()["id"]
    seen.add(root)
    _crawl(api, [{"id": root}], out, seen, log, factory=factory)
    log(f"  Drive'ım: {len(out)} öğe")

    try:  # Benimle paylaşılanlar: üst düzey öğeler + paylaşılan klasörlerin altı
        shared, token = [], None
        while True:
            resp = api.list(q="sharedWithMe = true and trashed = false", pageSize=1000, pageToken=token,
                            fields=f"nextPageToken, files({FIELDS})", supportsAllDrives=True,
                            includeItemsFromAllDrives=True).execute()
            shared += resp.get("files", [])
            token = resp.get("nextPageToken")
            if not token:
                break
        folders = []
        for f in shared:
            if f["id"] in seen or f["mimeType"] == SHORTCUT_MIME:
                continue
            seen.add(f["id"])
            f["_shared"] = True
            if f["mimeType"] == FOLDER_MIME:
                f["_label"] = f"Paylaşılan – {f['name']} ({_short(_owner(f))})"
                folders.append(f)
            else:
                f["_loose"] = LOOSE_LABEL
            out.append(f)
        before = len(out)
        _crawl(api, folders, out, seen, log, factory=factory)
        for f in out[before:]:
            f["_shared"] = True
        log(f"  Paylaşılanlar: {len(shared)} üst öğe ({len(folders)} klasör), altlarıyla {len(out) - before + len(shared)} öğe")
    except Exception as e:  # yetki/ağ hatası: paylaşılan kayıtlar silinmesin
        status["shared_ok"] = False
        log(f"  Paylaşılanlar taranamadı ({type(e).__name__}: {str(e)[:120]})")

    if drives_api is not None:
        try:
            drives = drives_api.list(pageSize=100).execute().get("drives", [])
            for d in drives:
                synthetic = {"id": d["id"], "name": d["name"], "mimeType": FOLDER_MIME, "_label": f"Ortak drive – {d['name']}",
                             "_shared": True, "modifiedTime": "1970-01-01T00:00:00Z"}
                out.append(synthetic)
                token = None
                while True:
                    resp = api.list(corpora="drive", driveId=d["id"], q="trashed = false", pageSize=1000, pageToken=token,
                                    fields=f"nextPageToken, files({FIELDS})", supportsAllDrives=True,
                                    includeItemsFromAllDrives=True).execute()
                    for f in resp.get("files", []):
                        if f["id"] not in seen:
                            seen.add(f["id"])
                            f["_shared"] = True
                            out.append(f)
                    token = resp.get("nextPageToken")
                    if not token:
                        break
            log(f"  Ortak drive'lar: {len(drives)}")
        except Exception as e:
            status["drives_ok"] = False
            log(f"  Ortak drive'lar taranamadı ({type(e).__name__}: {str(e)[:120]})")
    return out, status


def paths(files: list[dict]) -> dict[str, str]:
    """dosya id → klasör yolu ("A/B"); kökteyse "". Paylaşılan kökler `_label` ile adlandırılır."""
    folders = {f["id"]: f for f in files if f["mimeType"] == FOLDER_MIME}
    cache: dict[str, str] = {}

    def folder_path(fid: str, depth: int = 0) -> str:
        if fid in cache:
            return cache[fid]
        f = folders.get(fid)
        if not f or depth > 30:
            return ""
        if f.get("_label"):
            cache[fid] = f["_label"]
            return cache[fid]
        parent = (f.get("parents") or [None])[0]
        p = folder_path(parent, depth + 1) if parent in folders else ""
        cache[fid] = f"{p}/{f['name']}" if p else f["name"]
        return cache[fid]

    out = {}
    for f in files:
        parent = (f.get("parents") or [None])[0]
        if f.get("_loose"):
            out[f["id"]] = f["_loose"]
        elif f.get("_label"):
            out[f["id"]] = f["_label"].rsplit("/", 1)[0] if "/" in f["_label"] else ""
        else:
            out[f["id"]] = folder_path(parent) if parent in folders else ""
    return out


MIGRATIONS = ("ALTER TABLE drive_files ADD COLUMN owner TEXT", "ALTER TABLE drive_files ADD COLUMN shared INTEGER DEFAULT 0")


def migrate(con: sqlite3.Connection) -> None:
    for sql in MIGRATIONS:
        try:
            con.execute(sql)
        except sqlite3.OperationalError:  # sütun zaten var
            pass


def sync(con: sqlite3.Connection, alias: str = "main", log=print) -> int:
    migrate(con)
    svc = service(alias, "drive", "v3")
    files, status = list_all(svc.files(), svc.drives(), log,
                             factory=lambda: service(alias, "drive", "v3").files())      # paralel tarama: iş parçacığı başına API nesnesi
    api = svc.files()
    where = paths(files)
    cutoff = datetime.now(timezone.utc) - timedelta(days=TEXT_DAYS)
    known = {r[0]: (r[1], r[2]) for r in con.execute("SELECT id, modified, text FROM drive_files")}
    n_text = 0
    for f in files:
        if f["mimeType"] == FOLDER_MIME or f["mimeType"] == SHORTCUT_MIME:
            continue
        owner = _owner(f)
        text = known.get(f["id"], (None, None))[1]
        modified = datetime.fromisoformat(f["modifiedTime"].replace("Z", "+00:00"))
        if (f["mimeType"] == DOC_MIME and owner == "ben" and modified >= cutoff
                and known.get(f["id"], (None,))[0] != f["modifiedTime"]):
            try:
                text = api.export(fileId=f["id"], mimeType="text/plain").execute().decode("utf-8", "replace")[:50000]
                n_text += 1
            except Exception as e:  # dışa aktarılamayan belge (boyut vb.) metinsiz kalır
                log(f"  metin alınamadı: {f['name']} ({type(e).__name__})")
        con.execute(
            "INSERT OR REPLACE INTO drive_files(id, name, mime, path, modified, size, link, text, owner, shared) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (f["id"], f["name"], f["mimeType"], where.get(f["id"], ""), f["modifiedTime"], int(f.get("size") or 0),
             f.get("webViewLink"), text, owner, 1 if f.get("_shared") else 0),
        )
    # Silinen / artık görünmeyen kayıtlar kaldırılır; bir kaynak taranamadıysa onun kayıtları korunur.
    current = {f["id"] for f in files}
    stale = []
    for rid, shared in con.execute("SELECT id, shared FROM drive_files"):
        if rid in current:
            continue
        if shared and not (status["shared_ok"] and status["drives_ok"]):
            continue
        stale.append(rid)
    con.executemany("DELETE FROM drive_files WHERE id = ?", [(i,) for i in stale])
    if stale:
        log(f"drive: {len(stale)} eski kayıt kaldırıldı")
    con.commit()
    n_files = sum(1 for f in files if f["mimeType"] not in (FOLDER_MIME, SHORTCUT_MIME))
    n_shared = sum(1 for f in files if f.get("_shared") and f["mimeType"] not in (FOLDER_MIME, SHORTCUT_MIME))
    log(f"drive: {n_files} dosya ({n_shared} paylaşılan), {sum(1 for f in files if f['mimeType'] == FOLDER_MIME)} klasör, "
        f"{n_text} belgenin metni alındı")
    return len(files)


def build_specs(con: sqlite3.Connection) -> list[NoteSpec]:
    migrate(con)
    groups: dict[str, list] = defaultdict(list)
    for r in con.execute("SELECT name, mime, path, modified, link, owner FROM drive_files ORDER BY modified DESC"):
        top = (r[2] or "").split("/")[0] or "Kök"
        if top.startswith(SKIP_TOP):
            continue
        groups[top].append(r)
    specs = []
    for top, rows in sorted(groups.items(), key=lambda kv: kv[0].lower()):
        shared = top.startswith(("Paylaşılan", "Ortak drive"))
        lines = [f"{len(rows)} dosya" + (" · başkalarının sana paylaştığı klasör" if shared else "") +
                 ". Son değişenler önce" + (f", ilk {PER_NOTE} gösteriliyor." if len(rows) > PER_NOTE else "."),
                 "", "| Tarih | Tür | Konum | Sahip | Dosya |", "|---|---|---|---|---|"]
        for name, mime, path, modified, link, owner in rows[:PER_NOTE]:
            sub = "/".join((path or "").split("/")[1:]) or "—"
            label = MIME_LABEL.get(mime, (mime or "").split("/")[-1][:12])
            safe = redact(name).replace("|", "/").replace("[", "(").replace("]", ")")
            lines.append(f"| {modified[:10]} | {label} | {sub.replace('|', '/')} | {_short(owner or '?')} | [{safe}]({link}) |")
        title = f"Drive – {top}"
        specs.append(NoteSpec(
            folder=NOTE_FOLDER, title=title,
            frontmatter={"type": "kaynak", "status": "aktif", "tags": ["drive"] + (["paylasilan"] if shared else []),
                         "source": "gdrive", "source_id": f"drive-index:{top}", "due": None, "file_count": len(rows)},
            owned=("file_count",),
            body=f"# {title}\n\n## Notlar\n\n## Dosyalar\n<!-- sb:auto:liste:start -->\n<!-- sb:auto:liste:end -->\n",
            auto={"liste": "\n".join(lines)},
        ))
    return specs
