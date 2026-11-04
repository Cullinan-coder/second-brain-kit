"""Denetim 2026-11, ikinci tur (v0.12.0): ertelenen bulgular D-10, D-13, D-18, D-20, D-22, D-23, D-25, D-27, D-28, D-29 +
zamanlanmış şifreli yedek. Her test raporun gerçek arıza/saldırı yolunu yeniden üretir; eski kodda başarısız olduğu görüldü."""
import http.server
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from sb import automation, capture, chat, config, convstore, mobile, vault_ops
from sb import privacy as pv

SYSTEM = Path(__file__).resolve().parents[1]
KIT = SYSTEM / "kit"


def fake_cipher():
    return (lambda b: b"ENC" + b[::-1]), (lambda t: t[3:][::-1])


def run_git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


# ================================================================== D-10 şifreleme: git geçmişi + düz yedek
@pytest.fixture
def gitvault(tmp_path, monkeypatch):
    """Düz metin notları commit edilmiş geçici kasa (gerçek kasaya dokunmaz)."""
    vault, data = tmp_path / "vault", tmp_path / "data"
    (vault / "30-Kariyer").mkdir(parents=True)
    (vault / "50-Günlük").mkdir()
    data.mkdir(exist_ok=True)
    for mod in (pv, vault_ops):
        monkeypatch.setattr(mod, "VAULT", vault)
    monkeypatch.setattr(pv, "BACKUPS", data / "backups")
    monkeypatch.setattr(pv, "GIZLILIK_CFG", tmp_path / "gizlilik.yaml")
    monkeypatch.setattr(config, "DATA", data)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    run_git(vault, "init", "-q")
    (vault / "30-Kariyer" / "cv.md").write_text("GIZLI-CV-METNI", encoding="utf-8")
    (vault / "30-Kariyer" / "maas.md").write_text("GIZLI-MAAS", encoding="utf-8")
    (vault / "50-Günlük" / "g.md").write_text("gun", encoding="utf-8")
    run_git(vault, "add", "-A")
    run_git(vault, "commit", "-q", "-m", "ilk")
    (vault / "30-Kariyer" / "cv.md").write_text("GIZLI-CV-METNI v2", encoding="utf-8")
    run_git(vault, "commit", "-q", "-am", "ikinci")
    monkeypatch.setattr(pv, "_cipher", fake_cipher)
    return vault


def _commit_all(vault, msg):
    run_git(vault, "add", "-A")
    run_git(vault, "commit", "-q", "-m", msg)


def test_d10_encrypt_warns_plaintext_remains_in_git_history(gitvault):
    r = pv.encrypt_folder("30-Kariyer", confirm=True)
    assert r["ok"] and r["encrypted"] == 2
    w = r["history_warning"]
    assert "2 notun" in w and "2 commit" in w and "--purge-history 30-Kariyer --confirm" in w and "ZORLA" in w.upper()


def test_d10_encrypt_cli_prints_history_warning(gitvault, capsys):
    assert pv.encrypt_cli(["30-Kariyer", "--confirm"]) == 0
    out = capsys.readouterr().out
    assert "git geçmişinde" in out and "sb encrypt --purge-history 30-Kariyer --confirm" in out


def test_d10_history_exposure_counts_only_plain_notes_in_folder(gitvault):
    assert pv.history_exposure("30-Kariyer")["files"] == 2
    assert pv.history_exposure("yok-klasor")["files"] == 0


def test_d10_encrypt_never_writes_plain_zip_backup(gitvault):
    r = pv.encrypt_folder("30-Kariyer", confirm=True)
    assert not list(pv.BACKUPS.glob("*.zip")), "düz zip diske yazılmamalı"
    raw = (pv.BACKUPS / r["backup"]).read_bytes()
    assert r["backup"].endswith(".zip.enc") and b"GIZLI-CV" not in raw and b"PK\x03\x04" not in raw[:4]
    # geri dönüş: şifreli yedek geri yüklenebilir
    (gitvault / "30-Kariyer" / "cv.md").write_text("bozuk", encoding="utf-8")
    res = pv.restore(r["backup"], confirm=True)
    assert res["ok"] and "GIZLI-CV-METNI v2" in (gitvault / "30-Kariyer" / "cv.md").read_text(encoding="utf-8")


def test_d10_create_backup_is_encrypted_and_restorable(gitvault, monkeypatch):
    from sb import update
    monkeypatch.setattr(update, "backup", lambda dest=None: (dest / "system-x.zip").write_bytes(b"x") or (dest / "system-x.zip"))
    r = pv.create_backup()
    assert r["ok"] and r["created"][0].endswith(".zip.enc") and r["encrypted"]
    files = list(pv.BACKUPS.glob("vault-*"))
    assert [f.suffix for f in files] == [".enc"]
    assert b"GIZLI-CV" not in files[0].read_bytes()
    kinds = {z["name"]: z for z in pv.backups()["zips"]}
    assert kinds[files[0].name]["encrypted"] and kinds[files[0].name]["kind"] == "kasa"
    (gitvault / "30-Kariyer" / "cv.md").write_text("bozuk", encoding="utf-8")
    assert pv.restore(files[0].name)["dry_run"]
    assert pv.restore(files[0].name, confirm=True)["restored"] >= 3
    assert (gitvault / "30-Kariyer" / "cv.md").read_text(encoding="utf-8").startswith("GIZLI-CV-METNI")


def test_d10_create_backup_refuses_plain_when_cipher_missing(gitvault, monkeypatch):
    monkeypatch.setattr(pv, "_cipher", lambda: None)
    r = pv.create_backup()
    assert r["ok"] is False and "düz metin yedek alınmadı" in r["message"]
    assert not pv.BACKUPS.exists() or not list(pv.BACKUPS.glob("vault-*"))


def test_d10_create_backup_refuses_when_key_lost(gitvault, monkeypatch):
    def lost():
        raise pv.KeyLost("anahtar yok")
    monkeypatch.setattr(pv, "_cipher", lost)
    assert pv.create_backup()["ok"] is False
    assert not pv.BACKUPS.exists() or not list(pv.BACKUPS.glob("vault-*"))


def test_d10_restore_encrypted_with_wrong_key_fails_cleanly(gitvault, monkeypatch):
    r = pv.create_backup()
    name = r["created"][0]

    def other():
        return (lambda b: b"X" + b), (lambda t: (_ for _ in ()).throw(ValueError("yanlış anahtar")))
    monkeypatch.setattr(pv, "_cipher", other)
    out = pv.restore(name, confirm=True)
    assert out["ok"] is False and "çözülemedi" in out["message"]


def test_d10_purge_history_requires_confirm_and_changes_nothing(gitvault, capsys):
    pv.encrypt_folder("30-Kariyer", confirm=True)
    _commit_all(gitvault, "şifrelendi")
    before = run_git(gitvault, "rev-list", "--all")
    r = pv.purge_history("30-Kariyer")
    assert r["dry_run"] and "--confirm" in r["message"] and r["exposure"]["files"] == 2
    assert run_git(gitvault, "rev-list", "--all") == before
    assert pv.encrypt_cli(["--purge-history", "30-Kariyer"]) == 0                 # CLI de yalnız anlatır
    assert "ZORLA" in capsys.readouterr().out.upper()
    assert run_git(gitvault, "rev-list", "--all") == before


def test_d10_purge_history_refuses_without_filter_repo(gitvault, monkeypatch):
    pv.encrypt_folder("30-Kariyer", confirm=True)
    _commit_all(gitvault, "şifrelendi")
    monkeypatch.setattr(pv, "_filter_repo_available", lambda: False)
    monkeypatch.setattr(pv, "_run_filter_repo", lambda rel: pytest.fail("çalıştırılmamalı"))
    r = pv.purge_history("30-Kariyer", confirm=True)
    assert r["ok"] is False and "git-filter-repo" in r["message"] and "ZORLA" in r["message"].upper()
    assert not pv.BACKUPS.exists() or not list(pv.BACKUPS.glob("*bundle*"))


def test_d10_purge_history_refuses_with_plain_notes_or_dirty_tree(gitvault, monkeypatch):
    monkeypatch.setattr(pv, "_filter_repo_available", lambda: True)
    monkeypatch.setattr(pv, "_run_filter_repo", lambda rel: pytest.fail("çalıştırılmamalı"))
    r = pv.purge_history("30-Kariyer", confirm=True)                              # düz notlar hâlâ duruyor
    assert r["ok"] is False and "önce klasörü şifrele" in r["message"]
    pv.encrypt_folder("30-Kariyer", confirm=True)                                 # commit edilmemiş değişiklik var
    r = pv.purge_history("30-Kariyer", confirm=True)
    assert r["ok"] is False and "commit edilmemiş" in r["message"]


def test_d10_purge_history_takes_full_encrypted_backup_first(gitvault, monkeypatch):
    pv.encrypt_folder("30-Kariyer", confirm=True)
    _commit_all(gitvault, "şifrelendi")
    monkeypatch.setattr(pv, "_filter_repo_available", lambda: True)
    seen = {}

    def fake_run(rel):
        # filter-repo çalışmadan önce şifreli tam yedekler hazır olmalı
        seen["files"] = sorted(p.name for p in pv.BACKUPS.iterdir())
        seen["rel"] = rel
        return subprocess.CompletedProcess([], 0, "", "")
    monkeypatch.setattr(pv, "_run_filter_repo", fake_run)
    r = pv.purge_history("30-Kariyer", confirm=True)
    assert r["ok"] and r["purged"] and seen["rel"] == "30-Kariyer"
    names = seen["files"]
    assert any(n.startswith("vault-tum-") and n.endswith(".zip.enc") for n in names)
    assert any(n.startswith("vault-git-") and n.endswith(".bundle.enc") for n in names)
    assert not [n for n in names if not n.endswith(".enc")], "düz yedek kalmamalı"
    assert "git push --force --all" in r["message"] and "git remote add origin" in r["message"]
    enc = (pv.BACKUPS / r["git_backup"]).read_bytes()
    plain = fake_cipher()[1](enc)
    assert plain[:16] == b"# v2 git bundle\n"                                      # gerçek, kurtarılabilir git paketi


@pytest.mark.skipif(subprocess.run(["git", "filter-repo", "--version"], capture_output=True).returncode != 0,
                    reason="git filter-repo kurulu değil (gerçek uçtan uca deneme atlandı)")
def test_d10_purge_history_real_filter_repo(gitvault):
    pv.encrypt_folder("30-Kariyer", confirm=True)
    _commit_all(gitvault, "şifrelendi")
    assert "GIZLI-CV-METNI" in run_git(gitvault, "log", "--all", "-p")
    r = pv.purge_history("30-Kariyer", confirm=True)
    assert r["ok"], r["message"]
    assert "GIZLI-CV-METNI" not in run_git(gitvault, "log", "--all", "-p")
    assert (gitvault / "30-Kariyer" / "cv.md.enc").exists() and (gitvault / "50-Günlük" / "g.md").exists()


# ================================================================== zamanlanmış şifreli yedek
def _stamp_file(d, name, age_days):
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_bytes(b"x")
    t = time.time() - age_days * 86400
    os.utime(p, (t, t))
    return p


def test_weekly_backup_keeps_last_n_and_config_overrides(gitvault, monkeypatch):
    from sb import update
    monkeypatch.setattr(update, "backup", lambda dest=None: (dest / "system-x.zip").write_bytes(b"x") or (dest / "system-x.zip"))
    for i in range(10):
        _stamp_file(pv.BACKUPS, f"vault-tum-202601{i + 10:02d}-000000.zip.enc", 60 - i)
    _stamp_file(pv.BACKUPS, "vault-30-Kariyer-20250101-000000.zip.enc", 400)         # klasör yedeğine dokunulmaz
    assert pv.backup_keep() == 8
    r = pv.create_backup(scheduled=True)
    tum = sorted(p.name for p in pv.BACKUPS.glob("vault-tum-*.zip.enc"))
    assert len(tum) == 8 and len(r["removed"]) == 3 and (pv.BACKUPS / "vault-30-Kariyer-20250101-000000.zip.enc").exists()
    assert "vault-tum-20260110-000000.zip.enc" not in tum and r["created"][0] in tum
    pv.GIZLILIK_CFG.write_text("backup_keep: 3\n", encoding="utf-8")
    assert pv.backup_keep() == 3
    pv.create_backup(scheduled=True)
    assert len(list(pv.BACKUPS.glob("vault-tum-*.zip.enc"))) == 3


def test_manual_backup_does_not_prune(gitvault, monkeypatch):
    from sb import update
    monkeypatch.setattr(update, "backup", lambda dest=None: (dest / "system-x.zip").write_bytes(b"x") or (dest / "system-x.zip"))
    pv.GIZLILIK_CFG.write_text("backup_keep: 1\n", encoding="utf-8")
    for i in range(3):
        _stamp_file(pv.BACKUPS, f"vault-tum-202601{i + 10:02d}-000000.zip.enc", 30 - i)
    pv.create_backup()
    assert len(list(pv.BACKUPS.glob("vault-tum-*.zip.enc"))) == 4


def test_weekly_runs_backup_step_and_reports_failure(gitvault, monkeypatch):
    import inspect

    from sb import runner
    assert "weekly_backup(log)" in inspect.getsource(runner.weekly)
    lines = []
    monkeypatch.setattr(pv, "_cipher", lambda: None)
    msg = runner.weekly_backup(lines.append)
    assert msg.startswith("⚠ Yedek alınamadı") and lines
    monkeypatch.setattr(pv, "_cipher", fake_cipher)
    from sb import update
    monkeypatch.setattr(update, "backup", lambda dest=None: (dest / "system-x.zip").write_bytes(b"x") or (dest / "system-x.zip"))
    assert runner.weekly_backup(lines.append).startswith("💾 Şifreli yedek alındı")


def test_doctor_shows_backup_age_and_fails_after_14_days(gitvault):
    from sb import doctor
    st, name, hint = doctor.backup_check()
    assert st == doctor.FAIL and "hiç yok" in name
    _stamp_file(pv.BACKUPS, "vault-tum-20260101-000000.zip.enc", 20)
    st, name, hint = doctor.backup_check()
    assert st == doctor.FAIL and "20 gün önce" in name
    _stamp_file(pv.BACKUPS, "vault-tum-20260102-000000.zip.enc", 3)
    st, name, hint = doctor.backup_check()
    assert st == doctor.OK and "3 gün önce" in name


# ================================================================== D-13 yayın zinciri
_needs_kit = pytest.mark.skipif(not (KIT / "release.yml").exists(), reason="kit/ kaynağı bu kopyada yok (kurulu kopyada dosyalar repo kökünde)")


def _workflow_files():
    out = [KIT / "release.yml", KIT / "ci.yml"]
    return [p for p in out if p.exists()]


def test_d13_actions_pinned_to_commit_sha_with_tag_comment():
    for p in _workflow_files():
        text = p.read_text(encoding="utf-8")
        uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)(.*)$", text, re.M)
        assert uses, p.name
        for ref, rest in uses:
            assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", ref), f"{p.name}: SHA'ya sabitlenmemiş: {ref}"
            assert re.search(r"#\s*v\d+\.\d+\.\d+", rest), f"{p.name}: yanında sürüm etiketi yok: {ref}"


@_needs_kit
def test_d13_release_builds_from_lock_and_publishes_sha256sums():
    yaml = pytest.importorskip("yaml")
    wf = yaml.safe_load((KIT / "release.yml").read_text(encoding="utf-8"))
    text = json.dumps(wf)
    assert "--frozen" in text and "--require-hashes" in text and "pip install --upgrade pip pyinstaller" not in text
    pub = wf["jobs"]["publish"]
    steps = json.dumps(pub)
    assert "SHA256SUMS" in steps and "Second-Brain-Setup.exe" in steps and "Second-Brain-Setup-macOS.zip" in steps and "sha256sum" in steps
    assert pub["permissions"]["contents"] == "write" and wf["permissions"]["contents"] == "read"
    assert "contents" not in (wf["jobs"]["build"].get("permissions") or {}) or wf["jobs"]["build"]["permissions"]["contents"] == "read"
    assert "release-files/*" in steps                                              # SHA256SUMS dosyası da sürüme eklenir


@_needs_kit
def test_d13_ci_uses_frozen_lock():
    text = (KIT / "ci.yml").read_text(encoding="utf-8")
    assert text.count("uv run --frozen") >= 3 and not re.search(r"uv run (?!--)", text.replace("uv run --no-project", ""))


def test_d13_lockfile_has_build_group():
    lock = (SYSTEM / "uv.lock").read_text(encoding="utf-8")
    assert 'name = "pyinstaller"' in lock and "[dependency-groups]" in (SYSTEM / "pyproject.toml").read_text(encoding="utf-8")


def _extract_sh_func(name):
    sh = (KIT / "install.sh").read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.search(rf"^{name}\(\) \{{.*?^\}}\n", sh, re.M | re.S)
    assert m, name
    return m.group(0)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash yok")
@_needs_kit
def test_d13_install_sh_verifies_setup_hash(tmp_path):
    import hashlib
    fn = tmp_path / "fn.sh"
    fn.write_bytes(_extract_sh_func("verify_setup").encode("utf-8"))
    z = tmp_path / "Second-Brain-Setup-macOS.zip"

    def run(file):
        return subprocess.run(["bash", "-c", f'. ./fn.sh; verify_setup "./{file.name}"'], capture_output=True, text=True, cwd=tmp_path)
    z.write_bytes(b"gercek")
    (tmp_path / "SHA256SUMS").write_text(f"{hashlib.sha256(b'gercek').hexdigest()}  Second-Brain-Setup-macOS.zip\n", encoding="utf-8")
    assert run(z).returncode == 0 and z.exists()
    z.write_bytes(b"degistirilmis")                                                 # uyuşmazlık: sil ve dur
    assert run(z).returncode == 1 and not z.exists()
    z.write_bytes(b"gercek")
    (tmp_path / "SHA256SUMS").unlink()                                              # özet dosyası yok: doğrulanamaz → sil
    assert run(z).returncode == 1 and not z.exists()


@_needs_kit
def test_d13_install_scripts_download_sums_and_stop_on_mismatch():
    sh = (KIT / "install.sh").read_text(encoding="utf-8")
    ps = (KIT / "install.ps1").read_text(encoding="utf-8")
    assert "SHA256SUMS" in sh and "verify_setup" in sh and "exit 1" in sh.split("verify_setup \"$ZIP\"")[1][:300]
    assert "SHA256SUMS" in ps and "Test-SetupHash" in ps and "Get-FileHash" in ps and "exit 1" in ps.split("Test-SetupHash $exe")[1][:300]


@pytest.mark.skipif(shutil.which("powershell") is None, reason="powershell yok")
@_needs_kit
def test_d13_install_ps1_verifies_setup_hash(tmp_path):
    import hashlib
    ps = (KIT / "install.ps1").read_text(encoding="utf-8")
    m = re.search(r"^function Test-SetupHash.*?^\}\r?\n", ps, re.M | re.S)
    assert m
    fn = tmp_path / "fn.ps1"
    fn.write_text(m.group(0), encoding="utf-8-sig")
    exe = tmp_path / "Second-Brain-Setup.exe"

    def run():
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                            f'. "{fn}"; if (Test-SetupHash "{exe}") {{ exit 0 }} else {{ exit 3 }}'], capture_output=True, text=True)
        return r.returncode
    exe.write_bytes(b"gercek")
    (tmp_path / "SHA256SUMS").write_text(f"{hashlib.sha256(b'gercek').hexdigest()}  Second-Brain-Setup.exe\n", encoding="utf-8")
    assert run() == 0 and exe.exists()
    exe.write_bytes(b"kotu")
    assert run() == 3 and not exe.exists()
    exe.write_bytes(b"gercek")
    (tmp_path / "SHA256SUMS").unlink()
    assert run() == 3 and not exe.exists()


# ================================================================== D-18 SSRF: DNS rebinding
class _LocalHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/redir"):
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:%d/gizli" % self.server.server_port)
            self.end_headers()
            return
        body = b"YEREL-SIR " + (self.headers.get("Host") or "").encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def rebind(monkeypatch):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _LocalHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_port
    resolves, targets = {}, []
    real_cc = socket.create_connection

    def fake_getaddrinfo(host, p, *a, **k):
        if host.endswith(".example"):
            n = resolves[host] = resolves.get(host, 0) + 1
            ip = "93.184.216.34" if n == 1 else "127.0.0.1"                      # ilk çözümleme herkese açık, sonrakiler yerel
            return [(2, 1, 6, "", (ip, p or 80))]
        return [(2, 1, 6, "", (host, p or 80))]

    def fake_cc(addr, timeout=None, *a, **k):
        host, p = addr
        ip = host if re.fullmatch(r"[\d.]+", host) else socket.getaddrinfo(host, p)[0][4][0]
        targets.append(ip)
        return real_cc(("127.0.0.1", port), timeout)                            # simülasyon: hedef ne olursa olsun yerel sunucuya
    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(socket, "create_connection", fake_cc)
    yield port, resolves, targets
    srv.shutdown()


def test_d18_connection_goes_to_validated_ip_not_re_resolved(rebind):
    port, resolves, targets = rebind
    out = capture._get(f"http://rebind.example:{port}/x")
    assert targets == ["93.184.216.34"], f"bağlantı doğrulanan IP'ye yapılmalı, yeniden çözümleme olmamalı: {targets}"
    assert resolves["rebind.example"] == 1
    assert f"rebind.example:{port}" in out                                         # Host başlığı alan adı olarak kaldı


def test_d18_each_redirect_hop_is_validated(rebind):
    port, resolves, targets = rebind
    with pytest.raises(capture.UnsafeUrl):
        capture._get(f"http://public.example:{port}/redir")                        # 302 → 127.0.0.1
    assert targets == ["93.184.216.34"]                                            # yerel adrese hiç bağlanılmadı


def test_d18_proxy_env_cannot_bypass_check(rebind, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setattr(urllib.request, "getproxies", lambda: pytest.fail("ortam proxy'si okunmamalı"))
    port, _, targets = rebind
    capture._get(f"http://rebind.example:{port}/x")
    assert targets == ["93.184.216.34"]


def test_d18_https_pins_ip_but_keeps_sni_and_cert_name(monkeypatch):
    calls = {}
    monkeypatch.setattr(socket, "create_connection", lambda addr, timeout=None, *a, **k: calls.setdefault("addr", addr) and object())
    conn = capture._PinnedHTTPSConnection("example.com", "93.184.216.34", port=443)
    conn._context = type("C", (), {"wrap_socket": lambda self, sock, server_hostname=None: calls.setdefault("sni", server_hostname) or sock})()
    conn.connect()
    assert calls["addr"] == ("93.184.216.34", 443) and calls["sni"] == "example.com"


# ================================================================== D-20 kilitsiz oku-değiştir-yaz
def test_d20_threads_append_200_lines_without_loss(tmp_path, monkeypatch):
    from sb import filelock
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    f = tmp_path / "log.jsonl"

    def work(k):
        for i in range(25):
            filelock.append_line(f, f"{k}-{i}")
    ts = [threading.Thread(target=work, args=(k,)) for k in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    lines = f.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 200 and len(set(lines)) == 200


_PROC = '''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from sb import config
config.DATA = Path(sys.argv[2])
from sb import filelock
f, counter, tag = Path(sys.argv[3]), Path(sys.argv[4]), sys.argv[5]
for i in range(100):
    filelock.append_line(f, f"{tag}-{i}")
    filelock.read_modify_write(counter, lambda t: str(int(t or "0") + 1))
'''


def test_d20_two_processes_append_and_increment_without_loss(tmp_path):
    script = tmp_path / "w.py"
    script.write_text(_PROC, encoding="utf-8")
    f, counter = tmp_path / "log.txt", tmp_path / "counter.txt"
    procs = [subprocess.Popen([sys.executable, str(script), str(SYSTEM), str(tmp_path / "data"), str(f), str(counter), t]) for t in ("a", "b")]
    assert [p.wait(timeout=180) for p in procs] == [0, 0]
    assert len(f.read_text(encoding="utf-8").splitlines()) == 200
    assert counter.read_text(encoding="utf-8") == "200"


def test_d20_atomic_write_never_leaves_partial_file(tmp_path, monkeypatch):
    from sb import filelock
    p = tmp_path / "state.json"
    p.write_text("ESKI", encoding="utf-8")
    monkeypatch.setattr(os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("disk dolu")))
    with pytest.raises(OSError):
        filelock.atomic_write(p, "YENI-YARIM")
    assert p.read_text(encoding="utf-8") == "ESKI" and not list(tmp_path.glob("*.tmp"))


def test_d20_lock_times_out_instead_of_hanging(tmp_path, monkeypatch):
    from sb import filelock
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    f = tmp_path / "x.txt"
    got = []

    def holder():
        with filelock.locked(f):
            got.append(1)
            time.sleep(1.0)
    t = threading.Thread(target=holder)
    t.start()
    while not got:
        time.sleep(0.01)
    with pytest.raises(filelock.LockTimeout):
        with filelock.locked(f, timeout=0.2):
            pass
    t.join()


def test_d20_approval_log_survives_concurrent_queue_and_decide(tmp_path, monkeypatch):
    monkeypatch.setattr(automation, "DATA", tmp_path)
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(convstore, "notify", lambda *a, **k: {})
    rule = {"id": "r1"}
    old_ids = [automation._queue(rule, "whatsapp_taslak", f"eski{i}", "d", {})["id"] for i in range(25)]
    real_read = automation._read_pending

    def slow_read():                                                              # okuma–yazma penceresini genişlet
        rows = real_read()
        time.sleep(0.01)
        return rows
    monkeypatch.setattr(automation, "_read_pending", slow_read)
    new_ids = []

    def decider():
        for i in old_ids:
            automation.decide(i, False)

    def queuer():
        for i in range(25):
            new_ids.append(automation._queue(rule, "whatsapp_taslak", f"yeni{i}", "d", {})["id"])
    ts = [threading.Thread(target=decider), threading.Thread(target=queuer)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    rows = {r["id"]: r for r in real_read()}
    assert all(i in rows for i in new_ids), f"eşzamanlı onay kararı yeni kaydı sildi: {len(new_ids)} yeni, {len(rows)} satır, eksik {[i for i in new_ids if i not in rows]}"
    assert all(rows[i]["durum"] == "reddedildi" for i in old_ids)


def test_d20_add_rule_note_concurrent_adds_all_kept(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    monkeypatch.setattr(vault_ops, "VAULT", vault)
    monkeypatch.setattr(vault_ops, "RULES_NOTE", vault / "Asistan kuralları.md")
    monkeypatch.setattr(vault_ops, "commit", lambda *a, **k: "")
    monkeypatch.setattr(vault_ops, "log", lambda *a, **k: {})
    real_fold = vault_ops._fold
    monkeypatch.setattr(vault_ops, "_fold", lambda s: (time.sleep(0.01), real_fold(s))[1])     # oku–yaz penceresini genişlet
    ts = [threading.Thread(target=vault_ops.add_rule, args=(f"kural numara {i}",)) for i in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    body = (vault / "Asistan kuralları.md").read_text(encoding="utf-8")
    assert all(f"kural numara {i}" in body for i in range(8))


def test_d20_note_update_append_concurrent_all_kept(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "20-Projeler").mkdir(parents=True)
    note = vault / "20-Projeler" / "x.md"
    note.write_text("---\ntype: proje\nstatus: aktif\n---\n# X\n", encoding="utf-8")
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    monkeypatch.setattr(vault_ops, "VAULT", vault)
    monkeypatch.setattr(vault_ops, "resolve", lambda q: note)
    monkeypatch.setattr(vault_ops, "commit", lambda *a, **k: "")
    monkeypatch.setattr(vault_ops, "log", lambda *a, **k: {})
    real_dump = vault_ops.dump_note
    monkeypatch.setattr(vault_ops, "dump_note", lambda fm, body: (time.sleep(0.01), real_dump(fm, body))[1])
    ts = [threading.Thread(target=vault_ops.update, args=("x",), kwargs={"append": f"ekleme {i}"}) for i in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    text = note.read_text(encoding="utf-8")
    assert all(f"ekleme {i}" in text for i in range(8))


def test_d20_pair_tokens_file_concurrent_devices_all_kept(tmp_path, monkeypatch):
    path = tmp_path / "t.json"
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    auths = [chat.RemoteAuth(path) for _ in range(5)]
    real_load = chat.RemoteAuth._load

    def slow_load(self):
        rows = real_load(self)
        time.sleep(0.02)
        return rows
    monkeypatch.setattr(chat.RemoteAuth, "_load", slow_load)
    ts = [threading.Thread(target=lambda a=a: a.pair(a.pin, ip="1.1.1.1")) for a in auths]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(json.loads(path.read_text(encoding="utf-8"))) == 5


def test_d20_pair_tokens_written_atomically(tmp_path, monkeypatch):
    path = tmp_path / "t.json"
    monkeypatch.setattr(config, "DATA", tmp_path / "data")
    a = chat.RemoteAuth(path)
    tok, _ = a.pair(a.pin)
    path.write_text("[]", encoding="utf-8")
    a2 = chat.RemoteAuth(path)
    monkeypatch.setattr(os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("kesildi")))
    before = path.read_text(encoding="utf-8")
    with pytest.raises(OSError):
        a2.pair(a2.pin)
    assert path.read_text(encoding="utf-8") == before                              # yarım yazma jeton listesini bozmaz


# ================================================================== D-22 Ollama kurulumu
def test_d22_macos_install_uses_private_temp_dir_and_verifies_signature(monkeypatch):
    from setup import accounts
    monkeypatch.setattr(accounts.E, "WIN", False)
    monkeypatch.setattr(accounts.E, "MAC", True)
    cmd = " ".join(accounts._install_cmds()[0])
    assert "/tmp/Ollama.zip" not in cmd and "mktemp -d" in cmd and "codesign --verify" in cmd
    assert cmd.index("codesign --verify") < cmd.index("ditto")                     # doğrulama kopyalamadan önce


def test_d22_windows_install_checks_authenticode_signer(monkeypatch):
    from setup import accounts
    monkeypatch.setattr(accounts.E, "WIN", True)
    monkeypatch.setattr(accounts.E, "MAC", False)
    ps = accounts._install_cmds()[0][-1]
    assert "Get-AuthenticodeSignature" in ps and "NewGuid" in ps and "Ollama" in ps
    assert ps.index("Get-AuthenticodeSignature") < ps.index("Start-Process")


@pytest.mark.skipif(sys.platform != "win32" or shutil.which("powershell") is None, reason="Windows PowerShell gerek")
@pytest.mark.parametrize("kind", ["unsigned", "signed_by_microsoft"])
def test_d22_windows_installer_not_run_without_ollama_signature(monkeypatch, tmp_path, kind):
    """Gerçek PowerShell: imzasız ya da başka yayıncı imzalı kurucu ÇALIŞTIRILMAZ ve silinir."""
    from setup import accounts
    monkeypatch.setattr(accounts.E, "WIN", True)
    monkeypatch.setattr(accounts.E, "MAC", False)
    ps = accounts._install_cmds()[0][-1]
    marker = tmp_path / "calisti.txt"
    src = tmp_path / "src.exe"
    if kind == "unsigned":
        src.write_bytes(b"MZ not a real signed exe")
    else:
        shutil.copy(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "whoami.exe"), src)
    ps = re.sub(r"Invoke-WebRequest [^;]+;", lambda m: f"Copy-Item -LiteralPath '{src}' -Destination $f;", ps, count=1)
    ps = ps.replace("Start-Process -FilePath $f", f"Set-Content -LiteralPath '{marker}' -Value 'calisti'; Start-Process -FilePath $f")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], capture_output=True, text=True, timeout=120)
    assert r.returncode != 0 and "dogrulanamadi" in (r.stderr + r.stdout)
    assert not marker.exists()


# ================================================================== D-23 eşleme kilidi
def test_d23_lockout_is_per_client_not_global(tmp_path):
    a = chat.RemoteAuth(tmp_path / "t.json")
    for _ in range(5):
        a.pair("xxxxxx", now=10, ip="100.64.0.9")                                  # tailnet'teki saldırgan
    assert a.pair(a.pin, now=20, ip="100.64.0.9")[1].startswith("Çok fazla")       # onun kilidi
    tok, err = a.pair(a.pin, now=20, ip="100.64.0.5")                              # gerçek telefon etkilenmez
    assert tok and not err


def test_d23_pin_expires_after_ten_minutes(tmp_path, monkeypatch):
    a = chat.RemoteAuth(tmp_path / "t.json")
    codes = iter(["222222", "333333", "444444"])
    monkeypatch.setattr(a, "_new_pin", lambda: next(codes))
    a.pin, a.pin_ts = "111111", 1000.0
    assert a.current_pin(1000.0 + 599) == "111111"
    assert a.current_pin(1000.0 + 601) == "222222" and a.pin_ts == 1601.0


def test_d23_expired_pin_rejected_deterministically(tmp_path, monkeypatch):
    a = chat.RemoteAuth(tmp_path / "t.json")
    monkeypatch.setattr(a, "_new_pin", lambda: "999999" if a.pin == "123456" else "123456")
    a.pin, a.pin_ts = "123456", 1000.0
    tok, err = a.pair("123456", now=1000.0 + 601, ip="1.2.3.4")
    assert tok is None and a.pin == "999999"
    assert a.pair("123456", now=1000.0 + 602)[0] is None


def test_d23_fail_counter_is_thread_safe(tmp_path):
    a = chat.RemoteAuth(tmp_path / "t.json")
    a.pin = "123456"
    barrier = threading.Barrier(40)

    def hit():
        barrier.wait()
        a.pair("000000", now=5, ip="9.9.9.9")
    ts = [threading.Thread(target=hit) for _ in range(40)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    # 40 yanlış deneme: 5'te kilitlenir; kilit sonrası denemeler sayılmaz → kilit etkin ve sayaç tutarlı
    assert a.pair("123456", now=6, ip="9.9.9.9")[1].startswith("Çok fazla")
    assert a._clients["9.9.9.9"][0] == 0


def test_d23_distributed_guessing_rotates_pin(tmp_path, monkeypatch):
    a = chat.RemoteAuth(tmp_path / "t.json")
    codes = iter(["222222", "333333"])
    monkeypatch.setattr(a, "_new_pin", lambda: next(codes))
    a.pin, a.pin_ts = "111111", 1.0
    for i in range(a.GLOBAL_FAILS):
        a.pair("000000", now=2, ip=f"10.0.{i // 200}.{i % 200}")                    # her istemci birkaç deneme: kimse kilitlenmez ama toplam çok
    assert a.pin == "222222"


def test_d23_http_pair_uses_client_ip(tmp_path, monkeypatch):
    monkeypatch.setattr(chat, "retrieve", lambda t: ("", ""))
    a = chat.RemoteAuth(tmp_path / "t.json")
    a.ip = "127.0.0.1"
    seen = []
    real = a.pair
    monkeypatch.setattr(a, "pair", lambda pin, now=None, ip="": seen.append(ip) or real(pin, now, ip))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), chat.make_handler(chat_fn=lambda m, c: {"content": "ok"}, auth=a, is_remote=True))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    try:
        req = urllib.request.Request(base + "/api/pair", json.dumps({"pin": "000000"}).encode(),
                                     {"Content-Type": "application/json", "X-SB": "1", "Origin": base})
        urllib.request.urlopen(req).read()
    finally:
        srv.shutdown()
    assert seen == ["127.0.0.1"]


# ================================================================== D-25 schedule.ps1
def _schedule():
    return (SYSTEM / "tools" / "schedule.ps1").read_text(encoding="utf-8-sig")


def test_d25_syncthing_not_first_found_under_home():
    ps = _schedule()
    assert "-Recurse" not in ps.split("Syncthing (telefon")[1].split("Register-ScheduledTask")[0]
    assert "Get-ChildItem -Path $env:USERPROFILE" not in ps
    assert "Programs\\Syncthing\\syncthing.exe" in ps and "Get-Command syncthing -CommandType Application" in ps


@pytest.mark.skipif(shutil.which("powershell") is None, reason="powershell yok")
def test_d25_single_quote_in_path_is_escaped_and_roundtrips():
    ps = _schedule()
    m = re.search(r"^function Quote-Ps.*$", ps, re.M)
    assert m and "Quote-Ps $uv" in ps and "Quote-Ps $sys" in ps and "'$uv'" not in ps
    script = m.group(0) + r'''
$p = "C:\Users\O'Brien\uv.exe"
$inner = "& $(Quote-Ps $p) run --directory $(Quote-Ps 'C:\x\O''Neil\sys') python"
$err = $null; $ast = [System.Management.Automation.Language.Parser]::ParseInput($inner, [ref]$null, [ref]$err)
if ($err.Count -ne 0) { Write-Output "PARSE-HATASI"; exit 2 }
$cmd = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)
Write-Output ($cmd.CommandElements[0].Value)
Write-Output ($cmd.CommandElements[3].Value)
'''
    r = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=60)
    lines = r.stdout.strip().splitlines()
    assert r.returncode == 0 and lines == [r"C:\Users\O'Brien\uv.exe", r"C:\x\O'Neil\sys"], r.stdout + r.stderr


# ================================================================== D-27 push aboneliği
def _sub(host, i="a"):
    return {"endpoint": f"https://{host}/send/{i}", "keys": {"p256dh": "B" * 40, "auth": "a" * 16}}


@pytest.mark.parametrize("host", ["fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com", "wns2-par02p.notify.windows.com"])
def test_d27_known_push_services_accepted(host):
    assert mobile.valid_subscription(_sub(host)) is not None


@pytest.mark.parametrize("ep", ["https://attacker.example/push", "https://fcm.googleapis.com.attacker.example/x",
                                "https://fcm.googleapis.com@attacker.example/x", "https://attacker.example/fcm.googleapis.com",
                                "http://fcm.googleapis.com/x", "https://127.0.0.1/x", "https://fcm.googleapis.com:8443/x",
                                "https://notfcm.googleapis.com.evil.io/x"])
def test_d27_arbitrary_endpoint_rejected(ep):
    sub = _sub("fcm.googleapis.com")
    sub["endpoint"] = ep
    assert mobile.valid_subscription(sub) is None


def test_d27_subscribe_bound_to_paired_device_and_capped(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    assert mobile.subscribe(_sub("fcm.googleapis.com", "x"), "")[0] is False                  # eşlenmemiş: reddedilir
    for i in range(5):
        assert mobile.subscribe(_sub("fcm.googleapis.com", f"d1-{i}"), "dev1")[0]
    rows = mobile.subscriptions()
    assert len([r for r in rows if r["device"] == "dev1"]) == mobile.MAX_SUBS_PER_DEVICE


def test_d27_one_device_cannot_evict_other_devices(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    for i in range(7):
        for j in range(3 if i < 6 else 2):
            assert mobile.subscribe(_sub("fcm.googleapis.com", f"d{i}-{j}"), f"dev{i}")[0]
    assert len(mobile.subscriptions()) == 20                                       # toplam sınır
    ok, why = mobile.subscribe(_sub("fcm.googleapis.com", "ek"), "saldirgan")
    assert not ok and "sınır" in why
    assert len(mobile.subscriptions()) == 20 and not [r for r in mobile.subscriptions() if r["device"] == "saldirgan"]
    assert {r["device"] for r in mobile.subscriptions()} == {f"dev{i}" for i in range(7)}   # gerçek abonelikler düşmedi


def test_d27_route_requires_paired_device(monkeypatch, tmp_path):
    from sb import api_mobile, webroutes
    from sb.webroutes import Ctx
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(mobile, "push_available", lambda: True)
    r = webroutes.find("POST", "/api/v2/push/subscribe")
    mk = lambda dev: Ctx("POST", "/api/v2/push/subscribe", {"subscription": _sub("fcm.googleapis.com")}, {}, b"", "", "s", True, chat.Session(), None, None, dev)  # noqa: E731
    assert webroutes.call(r, mk(""))[0] == 403
    assert webroutes.call(r, mk("dev1"))[0] == 200
    assert api_mobile and mobile.subscriptions()[0]["device"] == "dev1"


def test_d27_device_id_comes_from_pairing_cookie(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    a = chat.RemoteAuth(tmp_path / "t.json")
    tok, _ = a.pair(a.pin)
    assert a.device_id(f"sbs={tok}") and a.device_id("sbs=" + "a" * 43) == "" and a.device_id("") == ""


# ================================================================== D-28 yükleme ve zip bombası
@pytest.fixture
def local_srv(monkeypatch):
    monkeypatch.setattr(chat, "retrieve", lambda t: ("", ""))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), chat.make_handler(chat_fn=lambda m, c: {"content": "ok"}))
    port = srv.server_address[1]
    monkeypatch.setattr(chat, "ALLOWED_HOSTS", {f"127.0.0.1:{port}"})
    monkeypatch.setattr(chat, "ALLOWED_ORIGINS", {f"http://127.0.0.1:{port}"})
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()


def _upload(base):
    from sb import localauth
    req = urllib.request.Request(base + "/api/v2/upload?name=a.txt", b"merhaba", {"Content-Type": "application/octet-stream", "X-SB": "1",
                                 "X-SB-Token": localauth.token()})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def test_d28_concurrent_uploads_are_limited(local_srv, monkeypatch, tmp_path):
    monkeypatch.setattr(convstore, "att_dir", lambda aid: tmp_path / aid)
    assert _upload(local_srv) == 200
    held = [chat.UPLOAD_SLOTS.acquire(timeout=5) for _ in range(chat.MAX_CONCURRENT_UPLOADS)]       # sunucu iş parçacığı yuvayı bırakana kadar bekle
    try:
        assert all(held) and _upload(local_srv) == 429                              # yuvalar doluyken yeni yükleme reddedilir
    finally:
        for _ in held:
            chat.UPLOAD_SLOTS.release()
    assert _upload(local_srv) == 200


def test_d28_upload_slot_released_after_error(local_srv, monkeypatch, tmp_path):
    monkeypatch.setattr(convstore, "att_dir", lambda aid: (_ for _ in ()).throw(RuntimeError("disk")))
    for _ in range(chat.MAX_CONCURRENT_UPLOADS + 2):
        assert _upload(local_srv) in (200, 500)
    assert chat.UPLOAD_SLOTS.acquire(blocking=False)
    chat.UPLOAD_SLOTS.release()


def _bomb(path, member_mb, name="word/document.xml"):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<x/>")
        with z.open(name, "w", force_zip64=True) as f:
            chunk = b"\0" * (1024 * 1024)
            for _ in range(member_mb):
                f.write(chunk)
    return path


def test_d28_high_ratio_zip_member_rejected_before_parsing(tmp_path):
    from sb import content
    p = _bomb(tmp_path / "b.docx", 60)                                             # 60 MB sıfır → ~60 KB: toplam sınırın altında ama oran 1000x
    with pytest.raises(ValueError, match="oran"):
        content.guard_zip(p)
    with pytest.raises(ValueError):
        content.extract(p)


def test_d28_oversized_member_and_total_rejected(tmp_path, monkeypatch):
    from sb import content
    monkeypatch.setattr(content, "RATIO_MIN_SIZE", 10 ** 12)                       # oran denetimini kapat: yalnız boyut sınırları
    monkeypatch.setattr(content, "MAX_MEMBER", 5 * 1024 * 1024)
    with pytest.raises(ValueError, match="üye"):
        content.guard_zip(_bomb(tmp_path / "m.docx", 6))
    monkeypatch.setattr(content, "MAX_MEMBER", 10 ** 9)
    monkeypatch.setattr(content, "MAX_UNZIPPED", 5 * 1024 * 1024)
    with pytest.raises(ValueError, match="boyut"):
        content.guard_zip(_bomb(tmp_path / "t.docx", 6))
    monkeypatch.setattr(content, "MAX_UNZIPPED", 10 ** 9)
    monkeypatch.setattr(content, "MAX_ZIP_FILES", 3)
    z = tmp_path / "many.docx"
    with zipfile.ZipFile(z, "w") as zf:
        for i in range(5):
            zf.writestr(f"f{i}", "x")
    with pytest.raises(ValueError, match="dosya"):
        content.guard_zip(z)


def test_d28_other_zip_readers_use_guard(tmp_path, monkeypatch):
    from sb import content, history, linkedin
    monkeypatch.setattr(content, "MAX_MEMBER", 1024)
    p = tmp_path / "conversations.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("conversations.json", "[" + "1," * 2000 + "1]")
    with pytest.raises(ValueError):
        history._load(p)
    with pytest.raises(ValueError):
        monkeypatch.setattr(config, "DATA", tmp_path / "d")
        monkeypatch.setattr(linkedin, "DATA", tmp_path / "d")
        linkedin.extract(p)


def test_d28_normal_office_file_still_extracts(tmp_path):
    docx = pytest.importorskip("docx")
    from sb import content
    p = tmp_path / "a.docx"
    d = docx.Document()
    d.add_paragraph("merhaba dünya")
    d.save(str(p))
    assert "merhaba" in content.extract(p)


# ================================================================== D-29 testler gerçek atlatma yollarını kapsıyor mu
def test_d29_security_test_covers_command_and_mail_scenarios():
    rep = pv.security_test_rules()
    assert len(rep) >= 55 and all(r["pass"] for r in rep), [r for r in rep if not r["pass"]]
    names = " ".join(r["scenario"] for r in rep)
    for needle in ("mail bağlamı + run_command", "kural ekle", "hafıza ekle", "not güncelle", "arşivle", "kutuya ekle"):
        assert needle in names
    assert any(r["proposals"] == 1 for r in rep if r["scenario"].startswith("mail"))             # eylem onay kartına düştü


def test_d29_security_test_command_list_covers_all_unit_test_attacks():
    from test_audit_2026_11 import D01_ATTACKS
    assert set(D01_ATTACKS) <= set(pv.COMMAND_ATTACKS)
    joined = "\n".join(pv.COMMAND_ATTACKS)
    for needle in ("Select-String -Path", "git diff --no-index", "python -v", "node -e", "$(calc)", "Sort-Object { calc }"):    # D-01 ve D-09 sınıfları
        assert needle in joined


def test_d29_security_test_cli_runs_rule_checks_first(monkeypatch, capsys):
    monkeypatch.setattr(pv, "security_test", lambda *a, **k: [{"scenario": "ocr", "executed": [], "proposals": 0, "tainted": True, "pass": True, "error": ""}])
    assert pv.security_test_cli([]) == 0
    out = capsys.readouterr().out
    assert "mail bağlamı + run_command" in out and "senaryo geçti" in out


def test_d29_every_covered_audit_item_has_a_test():
    names = set()
    for f in (SYSTEM / "tests").glob("test_audit_2026_11*.py"):
        names |= set(re.findall(r"^def test_(d\d\d)_", f.read_text(encoding="utf-8"), re.M))
    # D-09 (Select-String/git diff/virgüllü yol) test_d01_attacks_never_free içinde; D-07/D-17/D-30 kullanıcı kararı bekliyor
    expected = {f"d{n:02d}" for n in range(1, 30)} - {"d07", "d09", "d17"}
    assert expected <= names, sorted(expected - names)


# ================================================================== yedek kapsamı (2026-11-05)
def test_backup_includes_office_attachments_and_obsidian_but_not_code(tmp_path, monkeypatch):
    v = tmp_path / "kasa"
    for rel, data in {"10-Dersler/not.md": b"# not", "_attachments/Gelen/cv.docx": b"PK-docx", "_attachments/sunum.pptx": b"PK",
                      "_attachments/tablo.xlsx": b"PK", "_attachments/foto.jpeg": b"\xff\xd8", "_attachments/g.webp": b"RIFF",
                      ".obsidian/app.json": b"{}", "Plan.canvas": b"{}", "00-Inbox/x.base": b"",
                      "_attachments/~$cv.docx": b"kilit", "_system/sb/kod.py": b"x=1", ".git/HEAD": b"ref"}.items():
        f = v / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
    monkeypatch.setattr(pv, "VAULT", v)
    got = {a for _, a in pv._vault_files()}
    for want in ("10-Dersler/not.md", "_attachments/Gelen/cv.docx", "_attachments/sunum.pptx", "_attachments/tablo.xlsx",
                 "_attachments/foto.jpeg", "_attachments/g.webp", ".obsidian/app.json", "Plan.canvas", "00-Inbox/x.base"):
        assert want in got, f"yedeğe girmiyor: {want}"
    for no in ("_attachments/~$cv.docx", "_system/sb/kod.py", ".git/HEAD"):
        assert no not in got, f"yedeğe girmemeli: {no}"


def test_backup_skips_oversized_file(tmp_path, monkeypatch):
    v = tmp_path / "kasa"
    (v / "_attachments").mkdir(parents=True)
    (v / "_attachments" / "dev.mp4").write_bytes(b"0" * 2048)
    (v / "_attachments" / "kucuk.mp4").write_bytes(b"0" * 10)
    monkeypatch.setattr(pv, "VAULT", v)
    monkeypatch.setattr(pv, "BACKUP_MAX_FILE", 1024)
    got = {a for _, a in pv._vault_files()}
    assert "_attachments/kucuk.mp4" in got and "_attachments/dev.mp4" not in got
