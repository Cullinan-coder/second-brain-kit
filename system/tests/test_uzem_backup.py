"""UZEM dosyaları: yedek (akışlı, bellek sınırlı, geri uyumlu), kasa göçü m0003, doctor denetimi."""
import importlib
import subprocess
import zipfile
from pathlib import Path

import pytest

from sb import config, doctor, vault_ops
from sb import privacy as pv
from sb import uzem_sync as us

mig = importlib.import_module("sb.migrations.m0003_uzem_ignore")


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", *args], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


class SpyCipher:
    """Basit şifre (tersine çevirme) + her çağrının en büyük girdisini izler: bellek tepesi parça boyutunu aşmamalı."""

    def __init__(self):
        self.max_in = 0

    def enc(self, b):
        self.max_in = max(self.max_in, len(b))
        return b"ENC" + bytes(b)[::-1]

    def dec(self, t):
        return bytes(t[3:][::-1])


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    v = tmp_path / "kasa"
    (v / "10-Dersler").mkdir(parents=True)
    (v / "10-Dersler" / "not.md").write_text("ders notu", encoding="utf-8")
    big = v / "40-Kaynaklar" / "UZEM" / "ABC101 Örnek" / "01 hafta"
    big.mkdir(parents=True)
    (big / "sunum.pdf").write_bytes(bytes(range(256)) * 4000)          # ~1 MB sahte "büyük" dosya
    (big / "kod.py").write_text("print('x')\n", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    for mod in (pv, vault_ops):
        monkeypatch.setattr(mod, "VAULT", v)
    monkeypatch.setattr(pv, "BACKUPS", data / "backups")
    monkeypatch.setattr(pv, "GIZLILIK_CFG", tmp_path / "gizlilik.yaml")
    monkeypatch.setattr(config, "DATA", data)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    from sb import update
    monkeypatch.setattr(update, "backup", lambda dest=None: (dest / "system-x.zip").write_bytes(b"x") or (dest / "system-x.zip"))
    return v


def test_main_backup_excludes_uzem_and_separate_streamed_backup_is_made(vault, monkeypatch):
    spy = SpyCipher()
    monkeypatch.setattr(pv, "_cipher", lambda: (spy.enc, spy.dec))
    assert {a for _, a in pv._vault_files()} == {"10-Dersler/not.md"}
    assert len(pv._vault_files(uzem=True)) == 2
    r = pv.create_backup()
    assert r["ok"] and any(n.startswith("vault-tum-") for n in r["created"]) and any(n.startswith("vault-uzem-") for n in r["created"])
    assert "UZEM dosyaları ayrı akışlı yedekte" in r["note"]
    main = next(pv.BACKUPS.glob("vault-tum-*.zip.enc"))
    assert b"ders notu" not in main.read_bytes()


def test_uzem_backup_is_streamed_in_chunks_and_restorable(vault, monkeypatch):
    spy = SpyCipher()
    monkeypatch.setattr(pv, "_cipher", lambda: (spy.enc, spy.dec))
    out = pv.uzem_backup(cipher=(spy.enc, spy.dec), chunk=64 * 1024)
    assert out.name.startswith("vault-uzem-") and out.read_bytes().startswith(pv.STREAM_MAGIC)
    assert spy.max_in <= 64 * 1024                                         # ~1 MB dosya, tek seferde belleğe alınmadı (parça ≤ 64 KB)
    assert b"print(" not in out.read_bytes() and not list(pv.BACKUPS.glob("*.part"))
    pdf = vault / "40-Kaynaklar/UZEM/ABC101 Örnek/01 hafta/sunum.pdf"
    orig = pdf.read_bytes()
    pdf.unlink()
    (vault / "40-Kaynaklar/UZEM/ABC101 Örnek/01 hafta/kod.py").write_text("bozuk", encoding="utf-8")
    assert pv.restore(out.name)["dry_run"]
    r = pv.restore(out.name, confirm=True)
    assert r["ok"] and r["restored"] == 2
    assert pdf.read_bytes() == orig
    assert (vault / "40-Kaynaklar/UZEM/ABC101 Örnek/01 hafta/kod.py").read_text(encoding="utf-8").startswith("print")


def test_old_in_memory_backup_format_still_restores(vault, monkeypatch):
    spy = SpyCipher()
    monkeypatch.setattr(pv, "_cipher", lambda: (spy.enc, spy.dec))
    out = pv.vault_backup(cipher=(spy.enc, spy.dec))
    assert not out.read_bytes().startswith(pv.STREAM_MAGIC)
    (vault / "10-Dersler" / "not.md").write_text("bozuk", encoding="utf-8")
    assert pv.restore(out.name, confirm=True)["ok"]
    assert (vault / "10-Dersler" / "not.md").read_text(encoding="utf-8") == "ders notu"


def test_backup_without_uzem_says_so_and_skips(vault, monkeypatch, tmp_path):
    spy = SpyCipher()
    monkeypatch.setattr(pv, "_cipher", lambda: (spy.enc, spy.dec))
    (tmp_path / "gizlilik.yaml").write_text("backup_include_uzem: false\n", encoding="utf-8")
    assert pv.backup_include_uzem() is False
    r = pv.create_backup()
    assert "UZEM dosyaları yedeğe dahil değil" in r["note"] and not list(pv.BACKUPS.glob("vault-uzem-*"))


def test_uzem_backups_are_pruned_to_few(vault, monkeypatch):
    pv.BACKUPS.mkdir(parents=True, exist_ok=True)
    for i in range(5):
        (pv.BACKUPS / f"vault-uzem-2026110{i}-000000.zip.enc").write_bytes(b"x")
    gone = pv.prune_backups()
    assert len(list(pv.BACKUPS.glob("vault-uzem-*"))) == pv.UZEM_BACKUP_KEEP and len(gone) == 3


def test_doctor_backup_age_looks_at_main_backup_only(vault, monkeypatch):
    pv.BACKUPS.mkdir(parents=True, exist_ok=True)
    (pv.BACKUPS / "vault-uzem-20261101-000000.zip.enc").write_bytes(b"x")
    assert pv.last_backup() is None                                        # yalnız vault-tum-* sayılır


# ---- göç m0003 -----------------------------------------------------------------------------------------------------
def test_migration_adds_ignore_lines_idempotently_and_dry_run_writes_nothing(tmp_path):
    v = tmp_path / "k"
    v.mkdir()
    (v / ".gitignore").write_text("*.db\n", encoding="utf-8")
    (v / ".stignore").write_text("// x\n.git\n", encoding="utf-8")
    assert mig.VERSION == 3
    plan = mig.up(v, True)
    assert len(plan) == 2 and (v / ".gitignore").read_text(encoding="utf-8") == "*.db\n"
    assert len(mig.up(v, False)) == 2
    assert mig.up(v, False) == []
    assert "40-Kaynaklar/UZEM/**" in (v / ".gitignore").read_text(encoding="utf-8")
    assert "40-Kaynaklar/UZEM" in (v / ".stignore").read_text(encoding="utf-8").splitlines()
    git(v, "init", "-q")
    f = v / "40-Kaynaklar" / "UZEM" / "D" / "h" / "a.pdf"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"x")
    assert us.is_ignored(v, "40-Kaynaklar/UZEM/D/h/a.pdf") is True


def test_schema_current_is_3_and_repo_ignore_files_have_uzem_lines():
    from sb import schema
    assert schema.CURRENT == 3
    root = Path(__file__).resolve().parents[2]
    assert "40-Kaynaklar/UZEM/**" in (root / ".gitignore").read_text(encoding="utf-8")
    assert "40-Kaynaklar/UZEM" in (root / ".stignore").read_text(encoding="utf-8")


# ---- doctor -----------------------------------------------------------------------------------------------------------
def test_doctor_flags_tracked_uzem_files_and_big_folder(vault, monkeypatch):
    monkeypatch.setattr(doctor, "VAULT", vault)
    monkeypatch.setattr(config, "VAULT", vault)
    git(vault, "init", "-q")
    row = doctor.uzem_check()
    assert row[0] == doctor.OK
    git(vault, "add", "-f", "-A")                                          # ignore yokmuş gibi zorla izlet
    row = doctor.uzem_check()
    assert row[0] == doctor.FAIL and "git rm -r --cached" in row[2]
    git(vault, "rm", "-r", "-q", "--cached", ".")
    monkeypatch.setattr(doctor, "UZEM_WARN_GB", 0.0000001)
    assert doctor.uzem_check()[0] == doctor.WARN and "yedekler şişebilir" in doctor.uzem_check()[1]


def test_doctor_warns_when_backup_folder_over_30_gb(vault, monkeypatch):
    pv.BACKUPS.mkdir(parents=True, exist_ok=True)
    (pv.BACKUPS / "vault-tum-x.zip.enc").write_bytes(b"x" * 2048)
    assert doctor.backup_size_check() is None
    monkeypatch.setattr(doctor, "BACKUP_WARN_GB", 0.0000001)
    assert doctor.backup_size_check()[0] == doctor.WARN
