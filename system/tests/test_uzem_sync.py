"""UZEM/Moodle eşitleme: sahte sunucu (eds.php + Moodle + pluginfile), yalnız GET, sınırlar, tekrar indirmeme, nota/onay deposuna yazım,
git/yedek dışı kalma, sızıntı yok. Gerçek UZEM'e bağlanılmaz."""
import json
import subprocess
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from sb import config, extract, uzem, uzem_sync as us
from tests.test_uzem_parse import DUE, act_html, course_html

PW = "çok-gizli-şifre-123"
TOKEN = "f" * 64
USER = "250100999"
LOGIN = '<form method="post"><input name="ogrno"><input type="password" name="parola"><button>Gönder</button></form>'
GITIGNORE = "40-Kaynaklar/UZEM/**\n!40-Kaynaklar/UZEM/**/*.md\n"


def git(vault, *args):
    r = subprocess.run(["git", "-C", str(vault), "-c", "user.name=t", "-c", "user.email=t@example.com", *args], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


class Fake:
    def __init__(self):
        self.get, self.post, self.bodies = [], [], []
        self.files = {}                      # mid -> (ad, bytes, last_modified, content_disposition?)
        self.session_dead_for = set()       # ders id'leri: oturum düşmüş gibi giriş sayfası döner
        self.evil_resource = None
        self.port = 0


def build_courses(port):
    b = f"http://127.0.0.1:{port}"

    def a(tur, mid, ad, extra="", acc=""):
        return act_html(tur, mid, ad, extra, acc).replace("https://lms.universite.edu.tr", b)

    c11 = course_html(11, "Örnek Algoritmalar (Ayşe DENEME)", [
        ("Genel", [a("forum", 301, "Duyurular", acc="Forum")]),
        ("21 Eylül - 27 Eylül", [a("resource", 311, "Giriş sunumu", acc="Dosya"), a("resource", 312, "Ders kodu", acc="Dosya"),
                                 a("assign", 313, "Ödev 1: Sıralama", DUE, "Ödev"), a("folder", 314, "Dosyalar", acc="Klasör")]),
        ("28 Eylül - 4 Ekim", [a("resource", 315, "Tanıtım videosu", acc="Dosya"), a("resource", 316, "Arşiv", acc="Dosya"),
                               a("page", 317, "Konu Başlıkları", acc="Sayfa"), a("url", 318, "Kaynak sitesi", acc="URL"),
                               a("label", 319, "Duyuru notu", '<div class="activity-altcontent"><div><p>Sınav tarihi belli oldu.</p></div></div>'),
                               a("resource", 320, "Sızıntı denemesi", acc="Dosya")]),
    ])
    c22 = course_html(22, "Sinyaller Sistemler (Can ÖRNEK)", [("Genel", [a("forum", 331, "Duyurular", acc="Forum")]),
                                                              ("5 Ekim - 11 Ekim", [a("resource", 341, "Slayt", acc="Dosya")])])
    c33 = course_html(33, "Kasada Olmayan Ders (Biri KİŞİ)", [("Genel", [a("resource", 351, "Gizli dosya", acc="Dosya")])])
    return {"11": c11, "22": c22, "33": c33}


@pytest.fixture()
def site():
    fk = Fake()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, body, code=200, ctype="text/html; charset=utf-8", extra=None):
            b = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            path = self.path
            fk.get.append(path)
            u = urllib.parse.urlsplit(path)
            q = dict(urllib.parse.parse_qsl(u.query))
            if u.path == "/eds.php":
                return self.send(LOGIN)
            if u.path == "/login/index.php" and "course" in q:
                if q.get("t") != TOKEN:
                    return self.send("yok", 403)
                return self.send("", 302, extra={"Location": f"/course/view.php?id={q['course']}"})
            if u.path == "/course/view.php":
                if q["id"] in fk.session_dead_for:
                    return self.send('<form id="login"></form>')
                return self.send(build_courses(fk.port)[q["id"]])
            if u.path == "/mod/resource/view.php":
                mid = q["id"]
                if mid == "320" and fk.evil_resource:
                    return self.send("", 302, extra={"Location": fk.evil_resource})
                if mid not in fk.files:
                    return self.send("yok", 404)
                return self.send("", 302, extra={"Location": f"/pluginfile.php/5/mod_resource/content/1/{mid}.bin"})
            if u.path.startswith("/pluginfile.php/5/mod_resource/content/1/"):
                mid = u.path.rsplit("/", 1)[-1].split(".")[0]
                name, data, lm = fk.files[mid]
                fk.bodies.append(mid)
                return self.send(data, ctype="application/octet-stream",
                                 extra={"Content-Disposition": f"attachment; filename*=UTF-8''{urllib.parse.quote(name)}", "Last-Modified": lm})
            if u.path == "/mod/folder/view.php":
                return self.send(f'<a href="/pluginfile.php/6/mod_folder/content/0/{urllib.parse.quote("alt")}/notlar.txt?forcedownload=1">n</a>'
                                 f'<a href="/pluginfile.php/6/mod_folder/content/0/ek.py?forcedownload=1">e</a>')
            if u.path.startswith("/pluginfile.php/6/mod_folder/"):
                name = urllib.parse.unquote(u.path.split("/content/0/", 1)[1])
                fk.bodies.append("folder:" + name)
                return self.send(b"print('merhaba')\n" if name.endswith(".py") else "klasor notu".encode(), ctype="application/octet-stream")
            if u.path == "/mod/page/view.php":
                return self.send('<div class="box generalbox center clearfix"><p>Bölüm 11: Matris ayrışımları</p><p>Bölüm 12: Grafikler</p></div>')
            if u.path == "/mod/url/view.php":
                return self.send("", 302, extra={"Location": "http://dis-site.example.org/kaynak"})
            if u.path == "/mod/assign/view.php":
                return self.send('<div id="intro" class="box"><p>Sıralama algoritmalarını yazın.</p></div>')
            if u.path == "/mod/forum/view.php":
                return self.send('<table><tr><td><a href="/mod/forum/discuss.php?d=7">Vize tarihi</a><time>5 Kasım 2026</time></td></tr>'
                                 '<tr><td><a href="/mod/forum/discuss.php?d=9">Ders iptal</a><time>8 Kasım 2026</time></td></tr></table>')
            if u.path == "/mod/forum/discuss.php":
                body = {"7": "Vize 20 Aralık'ta.", "9": "Cuma günkü ders yapılmayacak."}[q["d"]]
                return self.send(f'<div class="post-content-container"><p>{body}</p></div>')
            self.send("yok", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0"))
            form = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8"))
            fk.post.append(self.path)
            ok = form.get("ogrno") == [USER] and form.get("parola") == [PW]
            if not ok:
                return self.send(LOGIN)
            links = "".join(f'<a href="http://127.0.0.1:{fk.port}/login/index.php?u={USER}&ts=1&ip=1.2.3.4&t={TOKEN}&course={c}">d{c}</a>'
                            for c in ("11", "22", "33"))
            self.send(f"<html>Giriş yapan DENEME KİŞİ Fakülteler Dersler listesi {links}<form><input type='password' name='parola'></form></html>")

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    fk.port = srv.server_address[1]
    fk.files = {"311": ("Giriş sunumu.pdf", b"%PDF-1.4 sunum algoritma", "Mon, 05 Oct 2026 10:00:00 GMT"),
                "312": ("kod örneği.py", b"def sirala(x):\n    return sorted(x)\n", "Mon, 05 Oct 2026 10:00:00 GMT"),
                "315": ("tanitim.mp4", b"0" * 5000, "Mon, 05 Oct 2026 10:00:00 GMT"),
                "316": ("arsiv.zip", b"PK" + b"0" * 100, "Mon, 05 Oct 2026 10:00:00 GMT"),
                "341": ("slayt.txt", b"sinyal isleme notlari", "Mon, 05 Oct 2026 10:00:00 GMT"),
                "351": ("gizli.pdf", b"asla", "Mon, 05 Oct 2026 10:00:00 GMT")}
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield fk
    srv.shutdown()


@pytest.fixture()
def env(tmp_path, monkeypatch, site):
    vault = tmp_path / "kasa"
    for d, n in (("ABC101 Örnek Algoritmalar", "ABC101 Örnek Algoritmalar"), ("ABC102 Sinyaller ve Sistemler", "ABC102 Sinyaller ve Sistemler")):
        (vault / "10-Dersler" / d).mkdir(parents=True)
        (vault / "10-Dersler" / d / f"{n}.md").write_text(f"---\ntype: ders\ncode: {n[:6]}\n---\n# {n}\n\nElle yazılan satır.\n", encoding="utf-8")
    (vault / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    git(vault, "init", "-q")
    git(vault, "add", "-A")
    git(vault, "commit", "-q", "-m", "ilk")
    monkeypatch.setattr(config, "VAULT", vault)
    monkeypatch.setattr(extract, "PENDING", vault / "00-Inbox" / "onay-bekleyenler.md")
    (vault / "00-Inbox").mkdir(exist_ok=True)

    def run(dry=False, **kw):
        kw.setdefault("cfg", dict(us.DEFAULTS))
        return us.sync(dry_run=dry, base=f"http://127.0.0.1:{site.port}", user=USER, pw=PW, delay=0,
                       extra_hosts=(f"127.0.0.1:{site.port}",), vault=vault, today=__import__("datetime").date(2026, 10, 1), log=lambda *a: None, **kw)
    return vault, run, site


def uzem_files(vault):
    root = us.files_root(vault)
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()) if root.exists() else []


def test_full_sync_downloads_notes_and_proposals(env, tmp_path):
    vault, run, site = env
    rep = run()
    assert len(rep["dersler"]) == 2 and len(rep["eslesmeyen"]) == 1 and "Kasada Olmayan Ders" in rep["eslesmeyen"][0]
    files = uzem_files(vault)
    assert "ABC101 Örnek Algoritmalar/01 21 Eylül - 27 Eylül/Giriş sunumu.pdf" in files            # Content-Disposition UTF-8 adı
    assert "ABC101 Örnek Algoritmalar/01 21 Eylül - 27 Eylül/kod örneği.py" in files
    assert any(f.endswith("alt_notlar.txt") for f in files) and any(f.endswith("ek.py") for f in files)         # klasör içeriği
    assert any(f.startswith("ABC102 Sinyaller ve Sistemler/") and f.endswith("slayt.txt") for f in files)
    assert not any("tanitim.mp4" in f or "arsiv.zip" in f or "gizli.pdf" in f for f in files)              # video/arşiv/eşleşmeyen ders
    assert "351" not in site.bodies                                                                 # eşleşmeyen derse hiç dokunulmadı
    note = (vault / "10-Dersler" / "ABC101 Örnek Algoritmalar" / "ABC101 Örnek Algoritmalar.md").read_text(encoding="utf-8")
    assert "Elle yazılan satır." in note and note.startswith("---\ntype: ders")                         # elle yazılan ve ön bilgi korunur
    assert "<!-- sb:auto:uzem:start -->" in note and "## Haftalık konular (UZEM)" in note
    assert "[[40-Kaynaklar/UZEM/ABC101 Örnek Algoritmalar/01 21 Eylül - 27 Eylül/Giriş sunumu.pdf|Giriş sunumu.pdf]]" in note
    assert "### 21 Eylül - 27 Eylül" in note and "Konular: Giriş sunumu; Ders kodu; Dosyalar" in note
    assert "Ödev: Ödev 1: Sıralama — teslim: Salı, 6 Ekim 2026, 12:00 AM" in note and "Sıralama algoritmalarını yazın." in note
    assert "Bağlantı: Kaynak sitesi — http://dis-site.example.org/kaynak" in note and "Bölüm 11: Matris ayrışımları" in note
    assert "Sınav tarihi belli oldu." in note and "Atlandı (video (varsayılan atlanır))" in note
    assert "### Duyurular (son 10)" in note and note.index("Ders iptal") < note.index("Vize tarihi") and "Vize 20 Aralık'ta." in note
    assert "dis-site.example.org" not in " ".join(site.get)                                              # dış bağlantıya gidilmedi
    pend = (vault / "00-Inbox" / "onay-bekleyenler.md").read_text(encoding="utf-8")
    assert pend.count("[ÖDEV]") == 1 and "2026-10-06" in pend and "uzem:11:313:2026-10-06" in pend       # öneri, doğrudan takvim yok
    st = json.loads(us.state_path().read_text(encoding="utf-8"))
    assert len(st["dosyalar"]) == 5 and st["son"] and len(st["atlanan"]) >= 2


def test_only_get_after_single_login_and_no_leaks(env, tmp_path, capsys):
    vault, run, site = env
    rep = run()
    us.print_report(rep)
    assert len(site.post) == 1
    seen = capsys.readouterr().out
    for secret in (PW, TOKEN, USER):
        assert secret not in seen
    for p in tmp_path.rglob("*"):
        if p.is_file() and ".git" not in p.parts and p.suffix not in {".pdf"}:
            data = p.read_bytes()
            assert PW.encode() not in data and TOKEN.encode() not in data, p
    assert not any("tamamla" in g.lower() or "complet" in g.lower() for g in site.get)


def test_idempotent_second_run_downloads_nothing_and_note_unchanged(env):
    vault, run, site = env
    run()
    note = vault / "10-Dersler" / "ABC101 Örnek Algoritmalar" / "ABC101 Örnek Algoritmalar.md"
    before, pend = note.read_text(encoding="utf-8"), (vault / "00-Inbox" / "onay-bekleyenler.md").read_text(encoding="utf-8")
    rep = run()
    assert rep["indirilen"] == 0 and rep["notlar"] == 0 and rep["tarih_onerisi"] in (0, 1)
    assert note.read_text(encoding="utf-8") == before
    assert (vault / "00-Inbox" / "onay-bekleyenler.md").read_text(encoding="utf-8") == pend       # aynı ödev+tarih tek kayıt
    assert rep["degismeyen"] >= 3


def test_changed_file_is_saved_as_new_version(env):
    vault, run, site = env
    run()
    site.files["311"] = ("Giriş sunumu.pdf", b"%PDF-1.4 yeni sunum surumu", "Tue, 06 Oct 2026 10:00:00 GMT")
    rep = run()
    assert rep["indirilen"] == 1
    files = uzem_files(vault)
    assert "ABC101 Örnek Algoritmalar/01 21 Eylül - 27 Eylül/Giriş sunumu.pdf" in files
    assert "ABC101 Örnek Algoritmalar/01 21 Eylül - 27 Eylül/Giriş sunumu (v2).pdf" in files


def test_dry_run_logs_in_but_writes_nothing(env):
    vault, run, site = env
    note = vault / "10-Dersler" / "ABC101 Örnek Algoritmalar" / "ABC101 Örnek Algoritmalar.md"
    before = note.read_text(encoding="utf-8")
    rep = run(dry=True)
    assert len(site.post) == 1                                              # giriş yapıldı; dosya yazılmadı (aşağıda)
    assert any("Giriş sunumu.pdf" in p for p in rep["plan"])
    assert uzem_files(vault) == [] and note.read_text(encoding="utf-8") == before
    assert not us.state_path().exists() and not (vault / "00-Inbox" / "onay-bekleyenler.md").exists()


def test_size_type_and_budget_limits(env):
    vault, run, site = env
    cfg = dict(us.DEFAULTS, calistirma_dosya=2, dosya_mb=0.00003)          # ~31 bayt
    site.files["312"] = ("kod örneği.py", b"x" * 60, "Mon, 05 Oct 2026 10:00:00 GMT")      # dosya başı sınırı aşar
    rep = run(cfg=cfg)
    assert any("büyük dosya" in s["neden"] for s in us.load_state()["atlanan"])
    # bütçe: iki dosya indirildi, kalanı bekliyor; ertesi çalışma tamamlar
    assert rep["indirilen"] == 2 and rep["bekleyen"] >= 1
    assert us.load_state()["bekleyen"]
    rep2 = run(cfg=dict(us.DEFAULTS, dosya_mb=0.00003, calistirma_dosya=50))
    assert rep2["indirilen"] >= 1 and us.load_state()["bekleyen"] == []


def test_video_and_archive_can_be_enabled(env):
    vault, run, site = env
    run(cfg=dict(us.DEFAULTS, indir_video=True, indir_arsiv=True))
    files = uzem_files(vault)
    assert any(f.endswith("tanitim.mp4") for f in files) and any(f.endswith("arsiv.zip") for f in files)


def test_untrusted_redirect_is_never_followed(env):
    vault, run, site = env
    site.files["320"] = ("x.pdf", b"x", "Mon, 05 Oct 2026 10:00:00 GMT")
    site.evil_resource = f"http://localhost:{site.port}/pluginfile.php/5/mod_resource/content/1/311.bin"     # güvenilmeyen host adı
    rep = run()
    assert any("Güvenilmeyen" in h for h in rep["hatalar"])
    assert "320" not in site.bodies
    assert not any(p.endswith("/320.bin") for p in site.get)


def test_wrong_password_fails_once_without_leaking(env):
    vault, run, site = env
    with pytest.raises(uzem.UzemError) as e:
        us.sync(base=f"http://127.0.0.1:{site.port}", user=USER, pw="yanlış-şifre-1", delay=0, extra_hosts=(f"127.0.0.1:{site.port}",),
                vault=vault, log=lambda *a: None)
    assert "yanlış-şifre-1" not in str(e.value) and USER not in str(e.value) and len(site.post) == 1
    assert uzem_files(vault) == []


def test_session_loss_stops_and_reports(env):
    vault, run, site = env
    site.session_dead_for = {"22"}
    rep = run()
    assert rep["oturum_dustu"] and any("oturumu düştü" in h for h in rep["hatalar"])
    assert any("ABC101" in d["kod"] for d in rep["dersler"])


def test_refuses_download_when_vault_gitignore_missing(env):
    vault, run, site = env
    (vault / ".gitignore").write_text("", encoding="utf-8")
    rep_err = None
    try:
        run()
    except uzem.UzemError as e:
        rep_err = str(e)
    assert rep_err and "migrate" in rep_err
    assert uzem_files(vault) == []


def test_uzem_files_never_reach_git_even_with_add_all(env):
    vault, run, site = env
    run()
    assert uzem_files(vault)
    git(vault, "add", "-A")
    porcelain = git(vault, "status", "--porcelain")
    assert "40-Kaynaklar/UZEM" not in porcelain and "UZEM" not in git(vault, "ls-files")
    assert "10-Dersler" in porcelain                                         # ders notu ise normal değişiklik olarak görünür


def test_vault_has_only_notes_outside_uzem_folder(env):
    vault, run, site = env
    run()
    for p in vault.rglob("*"):
        if p.is_file() and ".git" not in p.parts and "UZEM" not in p.parts:
            assert p.suffix in {".md", ""}, p


def test_documents_are_indexed_for_search_as_external_content(env):
    from sb import content, maildb
    vault, run, site = env
    run()
    con = maildb.connect(Path(config.DATA) / "mail.db")
    rows = con.execute("SELECT path, text FROM file_text").fetchall()
    assert any("kod örneği.py" in p and "def sirala" in t and t.startswith("[UZEM ders materyali — dış içerik") for p, t in rows)
    assert any("sinyal isleme notlari" in t for _, t in rows)
    hits = content.search(con, "sirala")
    assert hits and "UZEM" in " ".join(h[1] for h in hits)
    con.close()
    # content-sync (yerel dosya taraması) UZEM kayıtlarını silmemeli
    con = maildb.connect(Path(config.DATA) / "mail.db")
    con.execute("CREATE TABLE IF NOT EXISTS local_files (path TEXT PRIMARY KEY, root TEXT, sub TEXT, name TEXT, ext TEXT, size INTEGER, mtime REAL, rel TEXT)")
    content.sync(con, log=lambda *a: None)
    assert con.execute("SELECT COUNT(*) FROM file_text").fetchone()[0] == len(rows)
    con.close()


def test_status_text_and_size_warning(env, monkeypatch):
    vault, run, site = env
    assert "henüz" in us.status_text(vault)
    run()
    t = us.status_text(vault)
    assert "ABC101 Örnek Algoritmalar" in t and "GB" in t and "UYARI" not in t
    monkeypatch.setattr(us, "WARN_BYTES", 10)
    assert "yedekler şişebilir" in us.status_text(vault)


def test_runner_step_and_cli_registered():
    from sb import runner
    steps = {tuple(a): t for _, a, t in runner.DAILY_REST}
    assert steps[("uzem", "sync", "--daily")] == 900          # --daily: ilk elle çalıştırmadan önce hiçbir şey yapmaz
    import sb.__main__ as m
    assert callable(m.cmd_uzem)


def test_debug_dump_is_masked():
    s = us.mask_html('<a href="x?u=1&t=' + TOKEN + '">k</a> {"sesskey":"AbC123xyz9"} ' + PW, (PW,))
    assert TOKEN not in s and "AbC123xyz9" not in s and PW not in s
