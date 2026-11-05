"""UZEM keşif komutu: yalnız GET, çıkış/silme/dosya bağlantılarına dokunmaz, şifreyi sızdırmaz, yanlış şifrede tekrar denemez."""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

import pytest

from sb import uzem

PW = "çok-gizli-şifre-123"
LOGIN = '<form method="post"><input name="ogrno"><input type="password" name="parola"><button>Gönder</button></form>'
HOME = ('<html><body><h2>Giriş yapan: DENEME KİŞİ</h2><p>Fakülteler (Fen) Yapay Sinir Ağları</p>'
        '<form><input type="password" name="parola"></form><a href="/dersler.php">Derslerim</a> <a href="/ders.php?id=7">Yapay Sinir Ağları</a>'
        '<a href="/cikis.php">Çıkış</a> <a href="/sil.php?id=1">Sil</a> <a href="/dosya/hafta1.pdf">Hafta 1</a>'
        '<a href="https://baska.example.com/x">Dış</a></body></html>')


@pytest.fixture()
def site():
    log = {"get": [], "post": []}
    mode = {"captcha": False}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body, code=200):
            b = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            log["get"].append(self.path)
            if self.path.startswith("/eds.php"):
                self._send(LOGIN + ('<div class="g-recaptcha"></div>' if mode["captcha"] else ""))
            elif self.path.startswith("/dersler.php"):
                self._send("<html><h1>Dersler</h1><a href=\"/ders.php?id=7\">Yapay Sinir Ağları</a></html>")
            elif self.path.startswith("/ders.php"):
                self._send("<html><h1>Hafta 1: Perceptron</h1></html>")
            else:
                self._send("yok", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(n).decode("utf-8"))
            log["post"].append(self.path)
            ok = form.get("ogrno") == ["240121014"] and form.get("parola") == [PW]
            self._send(HOME if ok else LOGIN)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", log, mode
    srv.shutdown()


def test_probe_saves_pages_without_touching_dangerous_links(site, tmp_path, capsys):
    base, log, _ = site
    res = uzem.probe(base, tmp_path / "out", user="240121014", pw=PW, delay=0)
    assert res["sayfa"] >= 3                                                   # giriş sonrası + dersler + ders
    gets = " ".join(log["get"])
    for yasak in ("cikis", "sil.php", ".pdf"):
        assert yasak not in gets, f"{yasak} istenmemeliydi: {log['get']}"
    assert "baska.example.com" not in gets
    assert res["dosya_baglantisi"] == 1                                        # pdf bağlantısı bulundu, indirilmedi
    saved = " ".join(p.read_text(encoding="utf-8") for p in (tmp_path / "out").iterdir())
    assert PW not in saved and "Perceptron" in saved
    assert len(log["post"]) == 1                                               # tek giriş isteği


def test_wrong_password_fails_once_without_leaking(site, tmp_path):
    base, log, _ = site
    with pytest.raises(uzem.UzemError) as e:
        uzem.probe(base, tmp_path / "o", user="240121014", pw="yanlış-şifre-999", delay=0)
    assert "yanlış-şifre-999" not in str(e.value) and "başarısız" in str(e.value)
    assert len(log["post"]) == 1                                               # hesabı kilitlememek için yeniden denenmez


def test_captcha_page_is_never_automated(site, tmp_path):
    base, log, mode = site
    mode["captcha"] = True
    with pytest.raises(uzem.UzemError, match="CAPTCHA"):
        uzem.probe(base, tmp_path / "o", user="240121014", pw=PW, delay=0)
    assert log["post"] == []                                                   # forma hiç gönderilmedi


def test_links_filters(site):
    got = uzem.links(HOME, "http://127.0.0.1:1/eds.php")
    urls = [u for _, u in got]
    assert "http://127.0.0.1:1/dersler.php" in urls and all("cikis" not in u and "sil.php" not in u for u in urls)
    assert all("baska.example.com" not in u for u in urls)


def test_missing_credentials_message_has_no_secret(monkeypatch):
    from sb import config
    monkeypatch.setattr(config, "accounts", lambda: {"school": {"user": "240121014"}})
    import keyring
    monkeypatch.setattr(keyring, "get_password", lambda *a, **k: "")
    with pytest.raises(uzem.UzemError, match="eksik"):
        uzem.credentials()


def test_failed_login_message_explains_without_leaking(site, tmp_path):
    base, log, _ = site
    with pytest.raises(uzem.UzemError) as e:
        uzem.probe(base, tmp_path / "o", user="240121014", pw="yanlış-şifre-999", delay=0)
    msg = str(e.value)
    assert "yanlış-şifre-999" not in msg and "240121014" not in msg
    assert "durum 200" in msg and "Sunucu yanıtı" in msg
    d = uzem._diagnostic("<p>Şifre hatalı: yanlis123 ve 240121014 için</p><form>x</form>", 200, "http://x/eds.php?a=1", "240121014", "yanlis123")
    assert "yanlis123" not in d and "240121014" not in d and "hatalı" in d and "?a=1" not in d


def test_set_secret_accepts_school_password_name():
    """Okul şifresi `sb set-secret svc-school-password` ile (gizli girişle) yazılabilmeli; UZEM hata mesajı bu komutu öneriyor."""
    import subprocess, sys
    r = subprocess.run([sys.executable, "-X", "utf8", "-m", "sb", "set-secret", "--help"], capture_output=True, text=True,
                       encoding="utf-8", timeout=60)
    assert "svc-school-password" in r.stdout


def test_success_page_that_still_has_password_field_counts_as_logged_in():
    """Gerçek UZEM: giriş sonrası sayfada «Bilgileri Tekrar Gir» paneli yüzünden şifre alanı kalıyor (ilk sürüm bunu hata saydı)."""
    pre = '<html>ÜNİUZEM Edestek <form><input name="ogrno"><input name="parola" type="password"></form></html>'
    post = ('<html>ÜNİUZEM Edestek Bilgileri Tekrar Gir <form><input name="parola" type="password"></form>'
            'Fakülteler (Fen) DENEME KİŞİ Diferansiyel Denklemler (Banu PAZAR VAROL)</html>')
    assert uzem._logged_in(pre, post)
    assert not uzem._logged_in(pre, pre)                                              # aynı sayfa: giriş olmamış
    assert not uzem._logged_in(pre, pre + "<p>Şifre hatalı, tekrar deneyin lütfen</p>")


# ---- Moodle (lms) giriş bağlantıları ----------------------------------------------------------------------------
SECRET_T = "a" * 64


def _landing_with_sso(port: int, evil: bool = False) -> str:
    host = "evil.example.com" if evil else f"127.0.0.1:{port}"
    return ("<html>Giriş yapan DENEME KİŞİ Fakülteler (Fen) Dersler "
            f'<a href="http://{host}/login/index.php?u=240121014&ts=1700000000&ip=1.2.3.4&t={SECRET_T}&course=172">Diferansiyel</a>'
            f'<a href="http://{host}/login/index.php?u=240121014&ts=1700000000&ip=1.2.3.4&t={SECRET_T}&course=372">Teknik</a>'
            '<form><input name="parola" type="password"></form></html>')


@pytest.fixture()
def moodle():
    seen = []

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body, code=200, extra=None):
            b = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            seen.append(self.path)
            if self.path.startswith("/eds.php"):
                self._send(LOGIN)
            elif self.path.startswith("/login/index.php") and "course=" in self.path:
                cid = self.path.split("course=")[1].split("&")[0]
                self._send("", 302, {"Location": f"/course/view.php?id={cid}"})
            elif self.path.startswith("/course/view.php"):
                self._send("<html><h3>16 Kasım - 22 Kasım</h3><a href='/mod/resource/view.php?id=9'>12. Yüksek Mertebeden</a></html>")
            else:
                self._send("yok", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(n)
            self._send(_landing_with_sso(self.server.server_address[1]))

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", seen, srv.server_address[1]
    srv.shutdown()


def test_probe_follows_sso_links_to_course_pages_without_leaking_token(moodle, tmp_path):
    base, seen, port = moodle
    host = f"127.0.0.1:{port}"
    res = uzem.probe(base, tmp_path / "o", user="240121014", pw=PW, delay=0, extra_hosts=(host,))
    assert res["ders_toplam"] == 2 and res["ders_acilan"] == 2
    assert any(p.startswith("/course/view.php?id=172") for p in seen)
    assert not any("mod/resource" in p for p in seen)                          # dosya bağlantısı açılmaz (indirme yok)
    idx = (tmp_path / "o" / "index.json").read_text(encoding="utf-8")
    assert SECRET_T not in idx and "t=" not in idx                              # giriş anahtarı kayıtlara girmez
    assert "Yüksek Mertebeden" in " ".join(p.read_text(encoding="utf-8") for p in (tmp_path / "o").glob("*ders-172*.html"))


def test_sso_links_to_untrusted_host_are_ignored():
    html = _landing_with_sso(1234, evil=True)
    assert uzem.sso_course_links(html, "https://uzem.universite.edu.tr/eds.php") == []        # anahtar yabancı sunucuya gitmez
    ok = ('<a href="https://lms.universite.edu.tr/login/index.php?u=1&ts=2&ip=3&t=' + SECRET_T + '&course=172">x</a>')
    assert [c for c, _ in uzem.sso_course_links(ok, "https://uzem.universite.edu.tr/eds.php")] == ["172"]


def test_mask_url_hides_long_values():
    m = uzem.mask_url("https://lms.universite.edu.tr/login/index.php?u=240121014&t=" + SECRET_T + "&course=172#x")
    assert SECRET_T not in m and "course=172" in m and "<64 krkt>" in m


def test_daily_step_never_logs_in_before_first_manual_run(monkeypatch, tmp_path):
    """Günlük çalışma UZEM'e kendiliğinden giriş yapmaz: önce kullanıcı elle `sb uzem sync` çalıştırmalı."""
    import argparse
    from sb import __main__ as m, runner, uzem_sync
    assert any(a == ["uzem", "sync", "--daily"] for _, a, _ in runner.DAILY_REST)
    monkeypatch.setattr(uzem_sync, "state_path", lambda: tmp_path / "durum.json")
    monkeypatch.setattr(uzem_sync, "sync", lambda **k: pytest.fail("ilk elle çalıştırma olmadan giriş yapılmamalı"))
    args = argparse.Namespace(uzem_cmd="sync", dry_run=False, debug=False, daily=True)
    assert m.cmd_uzem(args) == 0
