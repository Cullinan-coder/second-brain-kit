"""Burak'ın v0.12.0 incelemesi (0.13.1): git diff no-index okuma, SHA256SUMS normalizasyonu + `sb verify`,
denetim özeti belgesi, ClipBoardLine/Nashi güven zinciri (sabit sürüm + özet). Her test eski kodda başarısız olur."""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from argparse import Namespace
from pathlib import Path

import pytest

from sb import actions, apps, config

SYSTEM = Path(__file__).resolve().parents[1]
KIT = SYSTEM / "kit"
# Kaynak deposuna özgü dosyalar (kit/, tools/build_kit.py) kurulu kopyada yoktur: o testler orada atlanır.
_needs_source = pytest.mark.skipif(not (KIT / "install.py").exists() or not (SYSTEM / "tools" / "build_kit.py").exists(),
                                   reason="kit/ ve tools/build_kit.py yalnız kaynak deposunda var")


# ------------------------------------------------------------------ B-01 git diff / depo dışı no-index okuma
@pytest.fixture
def cmd(tmp_path, monkeypatch):
    monkeypatch.setattr(actions.Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(config, "VAULT", tmp_path / "SecondBrain")
    return actions.classify_command


GIT_SERBEST = [
    "git status", "git status --short", "git log", "git log -5", "git log --oneline", "git log --stat", "git diff", "git diff --stat",
    "git diff HEAD", "git show", "git show HEAD", "git show HEAD~1", "git log main..HEAD", "git diff --name-only",
    "git log -p -- Workspace/projects/a.py", "git diff -- Workspace/projects/a.py", "git show HEAD:Workspace/projects/a.py",
    "git status Workspace/projects",
]
GIT_ONAYLI = [
    # Burak'ın elle denediği iki biçim
    r"git diff C:\Users\x\Desktop\a.txt NUL",
    "git diff ../../AppData/Roaming/x.json NUL",
    # aynı açık, varyantlar: yolsuz ad + NUL, iki düz yol, mutlak yol, /dev/null
    "git diff config NUL", "git diff a.txt b.txt", "git diff a b", "git diff /dev/null C:/Users/x/Desktop/a.txt",
    "git diff HEAD~1 HEAD", "git diff HEAD -- Workspace/projects/a.py",
    # tek yol bağımsız değişkeni depo dışına çıkıyor
    r"git diff C:\Users\x\Desktop\a.txt", "git diff ../../AppData/Roaming/x.json", "git diff NUL", "git diff .", "git diff ..",
    r"git log -p -- C:\Users\x\Desktop\a.txt", "git log -p -- ../x", "git log -- secretfile", "git log -p -- NUL",
    "git show HEAD:../../AppData/x.json", "git show :../../AppData/x.json", r"git show HEAD:C:\Users\x\a.txt",
    r"git show C:\Users\x\Desktop\a.txt", "git status ../../AppData", "git status C:/Users/x",
    # SecondBrain/_system/config kasa içinde olsa da onaylı
    "git diff SecondBrain/_system/config/accounts.yaml NUL", "git log -p -- SecondBrain/_system/config/accounts.yaml",
    # seçenekler: --no-index (kısaltma dahil), dosyaya yazma, harici program, yapılandırma/dizin değişimi
    "git diff --no-index a.txt b.txt", "git diff --no-index a b", "git diff --NO-INDEX a b",
    "git diff --output=x.txt", "git diff --output x.txt", "git diff --outpu=x.txt", "git diff --out=x.txt", "git log --output=x.txt",
    "git show --output=x.txt", "git diff -Oorder.txt", "git diff -O order.txt", "git diff --orderfile=a.txt",
    "git diff --ext-diff", "git diff --textconv", "git log --paginate", "git log --help", "git status -h",
    "git -c core.pager=calc log", "git -c core.pager=calc status", "git --git-dir=C:/x/.git log", "git --work-tree=C:/x status",
    "git -C C:/Users/x log", "git --paginate log", "git --exec-path=C:/x status", "git log --git-dir=C:/x", "git log --work-tree=C:/x",
    "GIT_DIR=C:/x git log", "GIT_WORK_TREE=C:/x git status", "$env:GIT_DIR='C:/x'; git log",
    # alt komut izin listesinin dışı
    "git grep --no-index secret C:/x", "git grep -e pw", "git hash-object C:/Users/x/a.txt", "git cat-file -p HEAD:a.txt",
    "git config --list", "git config core.pager calc", "git blame a.txt", "git ls-files", "git archive HEAD", "git bundle create x HEAD",
    "git fetch", "git clone http://x/y", "git checkout -- a.txt", "git show-ref", "git format-patch HEAD~1", "git diff-files",
    "git diff-index HEAD", "git diff-tree HEAD", "git difftool a b", "git remote -v",
]


@pytest.mark.parametrize("c", GIT_SERBEST)
def test_b01_git_legit_stays_free(cmd, c):
    assert cmd(c) == "serbest", c


@pytest.mark.parametrize("c", GIT_ONAYLI)
def test_b01_git_path_escapes_need_approval(cmd, c):
    assert cmd(c) in ("onayli", "yasak"), c


def test_b01_git_diff_two_paths_really_reads_outside_a_repo(tmp_path):
    """Gerçek git: depo dışında `git diff A B` içerik gösterir; bu yüzden iki yol argümanı serbest sayılmamalı."""
    if not shutil.which("git"):
        pytest.skip("git yok")
    a = tmp_path / "gizli.txt"
    a.write_text("GIZLI-ICERIK\n", encoding="utf-8")
    env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(tmp_path.parent)}
    r = subprocess.run(["git", "diff", str(a), os.devnull], cwd=tmp_path, capture_output=True, text=True, env=env)
    assert "GIZLI-ICERIK" in r.stdout


# ------------------------------------------------------------------ B-02 SHA256SUMS: git'in saklayacağı içerikten
def _tool_mod():
    sys.path.insert(0, str(SYSTEM))
    from sb import kitsums
    return kitsums


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def test_b02_normalized_digest_text_crlf_lf_binary_nul():
    ks = _tool_mod()
    lf = b"satir bir\nsatir iki\n"
    crlf = b"satir bir\r\nsatir iki\r\n"
    assert ks.normalized_bytes(crlf, "a.md") == lf
    assert ks.normalized_bytes(lf, "a.md") == lf
    assert ks.sha256_normalized(crlf, "a.md") == ks.sha256_normalized(lf, "a.md") == _sha(lf)
    png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + bytes(range(256))              # NUL var: ikili, olduğu gibi
    assert ks.normalized_bytes(png, "x.png") == png and ks.sha256_normalized(png, "x.png") == _sha(png)
    nul = b"metin gibi\r\nama NUL var\x00\r\n"
    assert ks.normalized_bytes(nul, "x.dat") == nul
    lone_cr = b"eski mac\rsatirlari\r\n"                                             # yalın CR: git ikili sayar, dokunmaz
    assert ks.normalized_bytes(lone_cr, "x.txt") == lone_cr
    assert ks.normalized_bytes(b"", "bos.txt") == b""
    assert ks.normalized_bytes("türkçe ğüşiöç\r\n".encode(), "t.md") == "türkçe ğüşiöç\n".encode()


def test_b02_gitattributes_binary_and_text_rules():
    ks = _tool_mod()
    rules = ks.parse_gitattributes("* text=auto eol=lf\n*.ps1 text eol=crlf\n*.bin binary\ndocs/raw/* -text\n# yorum\n")
    crlf = b"a\r\nb\r\n"
    assert ks.normalized_bytes(crlf, "x.bin", rules) == crlf                       # binary: dokunma
    assert ks.normalized_bytes(crlf, "docs/raw/x.txt", rules) == crlf               # -text
    assert ks.normalized_bytes(crlf, "x.txt", rules) == b"a\nb\n"
    assert ks.normalized_bytes(b"a\r\nb\x00\r\n", "x.ps1", rules) == b"a\nb\x00\n"   # text: ikili sezgisi aranmaz
    assert ks.normalized_bytes(crlf, "sub/dir/y.bin", rules) == crlf               # kalıp her derinlikte


def test_b02_digest_matches_real_git_blob(tmp_path):
    """Gerçek geçici depoda `git add` + `git show HEAD:f` ile aynı içerik → aynı sha256."""
    if not shutil.which("git"):
        pytest.skip("git yok")
    ks = _tool_mod()
    attrs = "* text=auto eol=lf\n*.ps1 text eol=crlf\n"
    files = {"crlf.md": b"bir\r\niki\r\n", "lf.md": b"bir\niki\n", "karisik.txt": b"bir\r\niki\nuc\r\n", "x.png": b"\x89PNG\r\n\x1a\n\x00\x01" + bytes(range(256)),
             "nulbayt.dat": b"yazi\r\nNUL\x00sonra\r\n", "lonecr.txt": b"a\rb\r\nc\r\n", "k.ps1": b"Write-Host 1\r\nWrite-Host 2\r\n",
             "k2.ps1": b"Write-Host 1\nWrite-Host 2\n", "bos.txt": b"", "tr.md": "ğüşıöç\r\n".encode(), "sub/dir/derin.py": b"x = 1\r\n"}
    (tmp_path / ".gitattributes").write_bytes(attrs.encode())
    for n, b in files.items():
        p = tmp_path / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
    def run(*a):
        r = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "user.name=t", "-c", "user.email=t@t", *a],
                           cwd=tmp_path, capture_output=True)
        assert r.returncode == 0, r.stderr.decode(errors="replace")
        return r
    run("init", "-q")
    run("add", "-A")
    run("commit", "-q", "-m", "x")
    rules = ks.parse_gitattributes(attrs)
    for n, b in files.items():
        blob = run("show", f"HEAD:{n}").stdout
        assert _sha(ks.normalized_bytes(b, n, rules)) == _sha(blob), n           # depoda saklanan içerik
    # Özet = temiz klonda diske düşen bayt dizisi (eol=crlf kuralı dahil); kullanıcı bunu doğrular.
    clone = tmp_path.parent / (tmp_path.name + "-klon")
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "clone", "-q", str(tmp_path), str(clone)], capture_output=True)
    assert r.returncode == 0, r.stderr.decode(errors="replace")
    for n, b in files.items():
        assert ks.sha256_normalized(b, n, rules) == _sha((clone / n).read_bytes()), n


def _fake_kit(tmp_path):
    out = tmp_path / "kit"
    (out / "system" / "sb").mkdir(parents=True)
    (out / "system" / "sb" / "a.py").write_bytes(b"x = 1\r\ny = 2\r\n")
    (out / "system" / "sb" / "ikili.png").write_bytes(b"\x89PNG\x00\r\n")
    (out / ".gitattributes").write_text("* text=auto eol=lf\n", encoding="utf-8")
    return out


@_needs_source
def test_b02_write_sums_hashes_git_content_not_crlf_worktree(tmp_path, monkeypatch):
    sys.path.insert(0, str(SYSTEM / "tools"))
    import importlib
    monkeypatch.setattr(sys, "argv", ["build_kit.py", str(tmp_path / "kit")])
    bk = importlib.import_module("build_kit")
    bk = importlib.reload(bk)
    out = _fake_kit(tmp_path)
    bk.write_sums()
    rows = dict(reversed(l.split("  ", 1)) for l in (out / "SHA256SUMS").read_text(encoding="utf-8").splitlines())
    assert rows["system/sb/a.py"] == _sha(b"x = 1\ny = 2\n")
    assert rows["system/sb/ikili.png"] == _sha(b"\x89PNG\x00\r\n")
    assert "SHA256SUMS" not in rows


# ------------------------------------------------------------------ B-02b `sb verify`
def _install_copy(tmp_path):
    """Kitin `system/` klasörünün kurulu kopyası + kökteki SHA256SUMS'un `_system/SHA256SUMS` olarak kopyası."""
    ks = _tool_mod()
    kit = _fake_kit(tmp_path)
    (kit / "system" / "pyproject.toml").write_bytes(b"[project]\r\nname='x'\r\n")
    rows = []
    for p in sorted((kit / "system").rglob("*")):
        if p.is_file():
            rel = p.relative_to(kit).as_posix()
            rows.append(f"{ks.sha256_normalized(p.read_bytes(), rel, ks.parse_gitattributes((kit / '.gitattributes').read_text()))}  {rel}")
    (kit / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")
    inst = tmp_path / "vault" / "_system"
    shutil.copytree(kit / "system", inst)
    shutil.copy2(kit / "SHA256SUMS", inst / "SHA256SUMS")
    return inst


def test_b02_verify_clean_install_passes_and_crlf_checkout_is_tolerated(tmp_path):
    ks = _tool_mod()
    inst = _install_copy(tmp_path)
    (inst / "sb" / "a.py").write_bytes(b"x = 1\r\ny = 2\r\n")                       # Windows CRLF çalışma kopyası: değişiklik sayılmaz
    r = ks.verify_install(inst)
    assert r["ok"] and not r["changed"] and not r["missing"] and not r["extra"] and r["checked"] == 3


def test_b02_verify_reports_changed_missing_extra_and_skips_user_data(tmp_path):
    ks = _tool_mod()
    inst = _install_copy(tmp_path)
    (inst / "sb" / "a.py").write_bytes(b"x = 999\n")
    (inst / "sb" / "ikili.png").unlink()
    (inst / "sb" / "yeni.py").write_text("print(1)\n")
    for skip in ("config", ".venv", "data", "__pycache__", "sb/__pycache__"):
        (inst / skip).mkdir(parents=True, exist_ok=True)
        (inst / skip / "x.yaml").write_text("kisisel: 1\n")
    (inst / "sb" / "x.pyc").write_bytes(b"\x00")
    r = ks.verify_install(inst)
    assert not r["ok"]
    assert r["changed"] == ["sb/a.py"] and r["missing"] == ["sb/ikili.png"] and r["extra"] == ["sb/yeni.py"]
    assert "config" in r["skipped"] and ".venv" in r["skipped"] and "__pycache__" in r["skipped"]


def test_b02_verify_without_sums_file_says_so(tmp_path):
    ks = _tool_mod()
    inst = _install_copy(tmp_path)
    (inst / "SHA256SUMS").unlink()
    r = ks.verify_install(inst)
    assert r["ok"] is None and "SHA256SUMS" in r["message"]


def test_b02_sb_verify_cli(tmp_path, monkeypatch, capsys):
    inst = _install_copy(tmp_path)
    ks = _tool_mod()
    assert '"verify"' in (SYSTEM / "sb" / "__main__.py").read_text(encoding="utf-8")        # alt komut kayıtlı
    monkeypatch.setattr(config, "SYSTEM", inst)
    rc = ks.cli()
    out = capsys.readouterr().out
    assert rc == 0 and "yerel değişiklik yok" in out
    assert "config" in out                                                          # atlananlar çıktıda söyleniyor
    (inst / "sb" / "a.py").write_bytes(b"x = 0\n")
    rc = ks.cli()
    assert rc == 1 and "sb/a.py" in capsys.readouterr().out


@_needs_source
def test_b02_installers_copy_sha256sums_into_system():
    for f in ("kit/install.py", "setup/engine.py"):
        src = (SYSTEM / f).read_text(encoding="utf-8")
        assert "SHA256SUMS" in src, f


# ------------------------------------------------------------------ B-03 denetim özeti belgesi
@_needs_source
def test_b03_changelog_has_no_dangling_audit_report_refs():
    txt = (KIT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "denetim-2026-11" not in txt
    assert "GUVENLIK-DENETIM-OZET" in txt


@_needs_source
def test_b03_summary_doc_covers_30_findings_without_attack_details():
    doc = (KIT / "docs" / "GUVENLIK-DENETIM-OZET.md").read_text(encoding="utf-8")
    for i in range(1, 31):
        assert f"D-{i:02d}" in doc, i
    assert "B-01" in doc and "git diff" in doc
    for d in ("D-07", "D-17", "D-30"):
        assert re.search(rf"##+ .*{d}", doc), d
    assert re.search(r"D-30[^\n]*0\.13\.0|0\.13\.0[^\n]*D-30", doc)
    assert "denetim-2026-11" not in doc
    assert not re.search(r"\.py:\d+", doc), "dosya:satır yok"
    assert "Invoke-" not in doc and "http://" not in doc


@_needs_source
def test_b03_build_kit_copies_summary_doc_and_still_excludes_report():
    src = (SYSTEM / "tools" / "build_kit.py").read_text(encoding="utf-8")
    assert '(KIT_SRC / "docs").glob("*.md")' in src
    assert '"denetim" not in p.name' in src


# ------------------------------------------------------------------ B-05b ClipBoardLine/Nashi güven zinciri
CBL_SHA = "69a2e7708c9846985a128b4cd5d9e5bb467ed02dd6e5bd66af8b284f8b507387"
NL = chr(10)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def test_b05_manifests_pin_sha256_per_platform_asset():
    for aid in ("clipboardline", "nashi"):
        c = apps.get(aid)
        for plat_ in ("win", "mac"):
            s = c["app"][plat_]
            assert HEX64.match(str(s.get("sha256", ""))), (aid, plat_)
    assert apps.get("clipboardline")["app"]["win"]["sha256"] == CBL_SHA
    assert apps.get("clipboardline")["app"]["win"]["tag"] == "windows-1.7.8-build71"
    assert apps.get("nashi")["app"]["win"]["tag"] == "v0.7.14-45"


def test_b05_manifest_validation_requires_pin():
    from sb import plugins
    m = json.loads(json.dumps(plugins.get("clipboardline", "module")))
    del m["app"]["win"]["sha256"]
    errs = plugins.validate_manifest(m, {x["id"] for x in plugins.all("module")})
    assert any("sha256" in e for e in errs)
    assert not plugins.validate()


def test_b05_tekstil_pack_keeps_clipboard_and_nashi_off():
    from sb import plugins
    t = plugins.get("tekstil", "sector")
    assert "clipboardline" not in (t.get("modules") or []) and "nashi" not in (t.get("modules") or [])
    assert {"clipboardline", "nashi"} <= set(t.get("disabled") or [])
    assert not plugins.validate()


class Resp(io.BytesIO):
    def __init__(self, data: bytes):
        super().__init__(data)
        self.status = 200
        self.headers = {"Content-Length": str(len(data))}


CBL_REL = "https://github.com/orkunisitmak/clipboardline/releases/download/windows-1.7.8-build71/"


@pytest.fixture
def aenv(monkeypatch, tmp_path):
    monkeypatch.delenv("SB_SETUP_SANDBOX", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setattr(apps, "plat", lambda: "win")
    monkeypatch.setattr(apps, "_reg_set", lambda n, v: None)
    monkeypatch.setattr(apps, "_reg_get", lambda n: None)
    monkeypatch.setattr(apps, "_reg_del", lambda n: None)
    monkeypatch.setattr(apps, "_proc_running", lambda name: False)
    monkeypatch.setattr(apps, "_spawn", lambda cmd, cwd=None: None)
    monkeypatch.setattr(apps, "NSIS_WAIT", 0)
    monkeypatch.setattr(apps, "start_menu_shortcut", lambda name, exe: None)
    monkeypatch.setattr(apps, "_data", lambda: tmp_path / "data")
    served: dict[str, bytes] = {}
    opened: list[str] = []
    ran: list = []

    def fake_open(url, headers=None, timeout=60):
        apps.check_url(url)
        opened.append(url)
        if url not in served:
            raise OSError("404")
        return Resp(served[url])
    monkeypatch.setattr(apps, "_open", fake_open)

    def fake_run(cmd, timeout=600):
        ran.append(cmd)
        exe = apps.expand(apps.spec("clipboardline")["exe"])
        exe.parent.mkdir(parents=True, exist_ok=True)
        exe.write_bytes(b"MZ")
        return 0, ""
    monkeypatch.setattr(apps, "_run", fake_run)
    return type("E", (), {"served": served, "opened": opened, "ran": ran, "tmp": tmp_path})


def _pin_cbl(monkeypatch, payload: bytes):
    """Kataloğun sabit özetini sahte yüke çevirir (ağsız test)."""
    c = apps.get("clipboardline")
    monkeypatch.setitem(c["app"]["win"], "sha256", _sha(payload))
    assert apps.spec("clipboardline")["sha256"] == _sha(payload)
    return c


def test_b05_install_downloads_only_pinned_and_checks_pinned_digest(aenv, monkeypatch):
    payload = b"MZ-iyi-surum" * 10
    c = _pin_cbl(monkeypatch, payload)
    s = c["app"]["win"]
    aenv.served[CBL_REL + s["asset"]] = payload
    aenv.served[CBL_REL + s["sums"]] = f"{_sha(payload)}  {s['asset']}\n".encode()
    r = apps.install("clipboardline")
    assert r["ok"] and r["installed"]
    assert not any("/releases?per_page" in u or "/releases/latest" in u for u in aenv.opened)       # en son sürüm sorulmaz


def test_b05_pinned_digest_mismatch_deletes_and_stops_even_if_release_sums_agree(aenv, monkeypatch):
    """Yayıncı hesabı ele geçirildi: dosya da, aynı sürümdeki SHA256SUMS de kötü ama birbiriyle uyumlu."""
    good = b"MZ-iyi" * 10
    evil = b"MZ-kotu" * 10
    c = _pin_cbl(monkeypatch, good)
    s = c["app"]["win"]
    aenv.served[CBL_REL + s["asset"]] = evil
    aenv.served[CBL_REL + s["sums"]] = f"{_sha(evil)}  {s['asset']}\n".encode()
    with pytest.raises(apps.AppsError, match="sabit"):
        apps.install("clipboardline")
    assert not aenv.ran                                                            # kurucu çalışmadı
    assert not (apps.downloads_dir() / s["asset"]).exists()
    assert not apps.installed("clipboardline")


def test_b05_downloaded_file_not_matching_pinned_digest_is_deleted(aenv, monkeypatch):
    """CDN/aracı dosyayı değiştirdi ama yayıncı SHA256SUMS'u (sabitle uyumlu) değişmedi: indirilen SABİT özete uymuyor -> sil, dur."""
    good = b"MZ-iyi" * 10
    c = _pin_cbl(monkeypatch, good)
    s = c["app"]["win"]
    aenv.served[CBL_REL + s["asset"]] = b"MZ-degistirilmis" * 10
    aenv.served[CBL_REL + s["sums"]] = f"{_sha(good)}  {s['asset']}\n".encode()
    with pytest.raises(apps.AppsError, match="sabit özetle uyuşmuyor"):
        apps.install("clipboardline")
    assert not aenv.ran
    assert not (apps.downloads_dir() / s["asset"]).exists()
    assert not apps.installed("clipboardline")


def test_b05_release_sums_is_second_check(aenv, monkeypatch):
    good = b"MZ-iyi" * 10
    c = _pin_cbl(monkeypatch, good)
    s = c["app"]["win"]
    aenv.served[CBL_REL + s["asset"]] = good
    aenv.served[CBL_REL + s["sums"]] = f"{_sha(b'baska')}  {s['asset']}\n".encode()   # sürümdeki özet sabitle çelişiyor
    with pytest.raises(apps.AppsError, match="SHA256SUMS"):
        apps.install("clipboardline")
    assert not aenv.ran


def test_b05_cached_download_with_wrong_digest_is_not_trusted(aenv, monkeypatch):
    good = b"MZ-iyi" * 10
    c = _pin_cbl(monkeypatch, good)
    s = c["app"]["win"]
    dl = apps.downloads_dir()
    dl.mkdir(parents=True, exist_ok=True)
    (dl / s["asset"]).write_bytes(b"onceden-birakilmis-kotu")
    aenv.served[CBL_REL + s["asset"]] = good
    aenv.served[CBL_REL + s["sums"]] = f"{_sha(good)}  {s['asset']}\n".encode()
    assert apps.install("clipboardline")["installed"]
    assert any(CBL_REL + s["asset"] == u for u in aenv.opened)                      # önbellekteki kötü dosya yerine yeniden indirildi


def test_b05_update_only_reports_never_installs(aenv, monkeypatch):
    c = apps.get("clipboardline")
    rels = [{"tag_name": "windows-1.8.0-build80", "draft": False, "prerelease": False,
             "html_url": "https://github.com/orkunisitmak/clipboardline/releases/tag/windows-1.8.0-build80"},
            {"tag_name": "windows-1.7.8-build71", "draft": False, "prerelease": False}]
    aenv.served["https://api.github.com/repos/orkunisitmak/clipboardline/releases?per_page=30"] = json.dumps(rels).encode()
    new_asset = "ClipBoardLine-Setup-1.8.0-x64.exe"
    aenv.served[CBL_REL.replace("windows-1.7.8-build71", "windows-1.8.0-build80") + "SHA256SUMS"] = f"{'ab' * 32}  {new_asset}\n".encode()
    u = apps.update_available("clipboardline")
    assert u["available"] and u["latest"] == "1.8.0" and u["tag"] == "windows-1.8.0-build80"
    assert u["notes_url"].endswith("/releases/tag/windows-1.8.0-build80")
    assert u.get("digest") == "ab" * 32 and u["accept_cmd"] == "sb apps update clipboardline --accept 1.8.0"
    assert not aenv.ran and not apps.installed("clipboardline")
    assert not (aenv.tmp / "data" / "apps_pins.json").exists()


def test_b05_cli_update_prints_notice_and_accept_requires_exact_version(aenv, capsys, monkeypatch):
    rels = [{"tag_name": "windows-1.8.0-build80", "draft": False, "prerelease": False}]
    aenv.served["https://api.github.com/repos/orkunisitmak/clipboardline/releases?per_page=30"] = json.dumps(rels).encode()
    aenv.served[CBL_REL.replace("windows-1.7.8-build71", "windows-1.8.0-build80") + "SHA256SUMS"] = f"{'cd' * 32}  ClipBoardLine-Setup-1.8.0-x64.exe\n".encode()
    rc = apps.cli(Namespace(action="update", id="clipboardline", accept="", force=False, dry_run=False, background=False, mode=""))
    out = capsys.readouterr().out
    assert rc == 0 and "1.8.0" in out and "--accept 1.8.0" in out and "cd" * 8 in out
    assert not (aenv.tmp / "data" / "apps_pins.json").exists()
    rc = apps.cli(Namespace(action="update", id="clipboardline", accept="9.9.9", force=False, dry_run=False, background=False, mode=""))
    assert rc == 1 and not (aenv.tmp / "data" / "apps_pins.json").exists()


def test_b05_accept_pins_version_and_digest_then_install_uses_user_pin(aenv, monkeypatch):
    new = b"MZ-yeni-surum" * 10
    rels = [{"tag_name": "windows-1.8.0-build80", "draft": False, "prerelease": False}]
    aenv.served["https://api.github.com/repos/orkunisitmak/clipboardline/releases?per_page=30"] = json.dumps(rels).encode()
    base = CBL_REL.replace("windows-1.7.8-build71", "windows-1.8.0-build80")
    asset = "ClipBoardLine-Setup-1.8.0-x64.exe"
    aenv.served[base + "SHA256SUMS"] = f"{_sha(new)}  {asset}\n".encode()
    aenv.served[base + asset] = new
    r = apps.accept_update("clipboardline", "1.8.0")
    assert r["ok"] and r["pinned"]["sha256"] == _sha(new)
    pins = json.loads((aenv.tmp / "data" / "apps_pins.json").read_text(encoding="utf-8"))
    assert pins["clipboardline"]["win"] == {"version": "1.8.0", "tag": "windows-1.8.0-build80", "asset": asset, "sha256": _sha(new)} or \
        pins["clipboardline"]["win"].items() >= {"version": "1.8.0", "tag": "windows-1.8.0-build80", "asset": asset, "sha256": _sha(new)}.items()
    assert apps.spec("clipboardline")["version"] == "1.8.0" and apps.spec("clipboardline")["sha256"] == _sha(new)   # install artık kullanıcı sabitini kullanır
    assert apps.install("clipboardline")["installed"]
    assert apps.load_state()["clipboardline"]["version"] == "1.8.0"


def test_b05_accept_refuses_when_release_sums_lacks_asset_or_not_newer(aenv):
    rels = [{"tag_name": "windows-1.8.0-build80", "draft": False, "prerelease": False}]
    aenv.served["https://api.github.com/repos/orkunisitmak/clipboardline/releases?per_page=30"] = json.dumps(rels).encode()
    aenv.served[CBL_REL.replace("windows-1.7.8-build71", "windows-1.8.0-build80") + "SHA256SUMS"] = b"ab" * 32 + b"  baska.exe\n"
    with pytest.raises(apps.AppsError):
        apps.accept_update("clipboardline", "1.8.0")
    with pytest.raises(apps.AppsError):
        apps.accept_update("clipboardline", "1.7.8")                              # daha yeni değil
    assert not (aenv.tmp / "data" / "apps_pins.json").exists()


def test_b05_user_pin_ignored_if_not_newer_than_catalog(aenv):
    (aenv.tmp / "data" / "apps_pins.json").write_text(json.dumps({"clipboardline": {"win": {"version": "1.0.0", "tag": "windows-1.0.0-build1",
                                                                                  "asset": "x.exe", "sha256": "0" * 64}}}), encoding="utf-8")
    assert apps.spec("clipboardline")["version"] == "1.7.8"                          # eski/bozuk sabit katalogu geri çekemez


def test_b05_api_exposes_update_notice_without_installing(aenv, monkeypatch):
    from sb import api_apps
    assert hasattr(api_apps, "update") and hasattr(api_apps, "accept")
def test_b02_nested_gitattributes_apply_only_below_their_folder(tmp_path):
    ks = _tool_mod()
    (tmp_path / "vault").mkdir()
    (tmp_path / ".gitattributes").write_bytes(b"* text=auto eol=lf" + bytes([10]))
    (tmp_path / "vault" / ".gitattributes").write_bytes(b"*.dat -text" + bytes([10]))
    rules = ks.load_gitattributes(tmp_path)
    crlf = b"a" + bytes([13, 10]) + b"b" + bytes([13, 10])
    lf = b"a" + bytes([10]) + b"b" + bytes([10])
    assert ks.normalized_bytes(crlf, "vault/x.dat", rules) == crlf               # iç içe dosya kendi klasöründe baskın
    assert ks.normalized_bytes(crlf, "vault/sub/y.dat", rules) == crlf
    assert ks.normalized_bytes(crlf, "other/x.dat", rules) == lf                  # başka klasörde etkisiz


def test_b05_status_reports_pinned_version_and_digest(aenv):
    st = apps.status("clipboardline")
    assert st["pinned_version"] == "1.7.8" and st["pinned_sha256"] == CBL_SHA and st["pinned_by_user"] is False


def test_sums_match_clean_checkout_for_crlf_scripts():
    """`*.ps1 text eol=crlf`: temiz klonda diske CRLF düşer; özet diskteki baytlarla tutmalı (2026-11-05, 15 dosya tutmuyordu)."""
    from sb import kitsums
    import hashlib
    lf = b"Write-Host a\nWrite-Host b\n"
    crlf = lf.replace(b"\n", b"\r\n")
    for src in (lf, crlf):                                     # kaynak hangi satır sonuyla olursa olsun
        assert kitsums.sha256_normalized(src, "tools/x.ps1") == hashlib.sha256(crlf).hexdigest()
        assert kitsums.sha256_normalized(src, "README.md") == hashlib.sha256(lf).hexdigest()
    b = b"\x00\x01\r\n\x02"
    assert kitsums.sha256_normalized(b, "x.bin") == hashlib.sha256(b).hexdigest()   # ikili: dokunulmaz
