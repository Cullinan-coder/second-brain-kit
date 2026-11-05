"""Moodle bağlayıcısı (buraqfe05, PR #3) sertleştirmeleri: jeton yalnız okul sunucusuna, dosyalar kasada ama git dışı."""
import subprocess
from pathlib import Path

import pytest

from sb import moodle


@pytest.fixture(autouse=True)
def _base(monkeypatch):
    monkeypatch.setattr(moodle, "BASE", "https://lms.universite.edu.tr")


def test_same_host_only():
    assert moodle._same_host("https://lms.universite.edu.tr/webservice/pluginfile.php/1/a.pdf")
    assert not moodle._same_host("https://evil.example.com/a.pdf")
    assert not moodle._same_host("https://lms.universite.edu.tr.evil.com/a.pdf")
    assert not moodle._same_host("ftp://lms.universite.edu.tr/a.pdf")


def test_download_never_sends_token_to_other_host(monkeypatch, tmp_path):
    monkeypatch.setattr(moodle, "_token", lambda: "SECRET-TOKEN")
    monkeypatch.setattr(moodle.urllib.request, "urlopen", lambda *a, **k: pytest.fail("yabancı sunucuya istek atılmamalıydı"))
    with pytest.raises(RuntimeError, match="Moodle sunucusunda değil"):
        moodle._download("https://evil.example.com/x.pdf", tmp_path / "x.pdf", 10)
    assert not (tmp_path / "x.pdf").exists()


def _git(vault: Path, *a):
    subprocess.run(["git", "-C", str(vault), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True)


def test_files_root_default_is_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(moodle, "LMS", {})
    assert moodle.files_root(tmp_path / "kasa", tmp_path / "veri") == tmp_path / "veri" / "moodle"


def test_vault_mode_requires_gitignore(tmp_path, monkeypatch):
    monkeypatch.setattr(moodle, "LMS", {"moodle_files": "vault"})
    vault = tmp_path / "kasa"
    vault.mkdir()
    _git(vault, "init", "-q")
    with pytest.raises(RuntimeError, match="yok sayılmıyor"):                 # .gitignore yok: dosyalar GitHub'a giderdi
        moodle.files_root(vault, tmp_path / "veri")
    (vault / ".gitignore").write_text("40-Kaynaklar/UZEM/**\n", encoding="utf-8")
    assert moodle.files_root(vault, tmp_path / "veri") == vault / "40-Kaynaklar" / "UZEM"


def test_vault_mode_files_never_show_in_git_status(tmp_path, monkeypatch):
    monkeypatch.setattr(moodle, "LMS", {"moodle_files": "vault"})
    vault = tmp_path / "kasa"
    vault.mkdir()
    _git(vault, "init", "-q")
    (vault / ".gitignore").write_text("40-Kaynaklar/UZEM/**\n!40-Kaynaklar/UZEM/**/*.md\n", encoding="utf-8")
    root = moodle.files_root(vault, tmp_path / "veri")
    f = root / "MAT101" / "Hafta 1" / "ders.pdf"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"%PDF-1.4 x" * 1000)
    _git(vault, "add", "-A")
    out = subprocess.run(["git", "-C", str(vault), "status", "--porcelain"], capture_output=True, text=True).stdout
    assert "UZEM" not in out and "ders.pdf" not in out
