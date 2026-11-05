"""Kasa şema sürümü + göç sistemi (sb/schema.py, sb/migrations/, doctor/update/kurulum entegrasyonu)."""
from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

from sb import doctor, schema, update
from sb.migrations import m0002_ortak_alanlar as m2


def git(v: Path, *a: str) -> str:
    r = subprocess.run(["git", "-C", str(v), *a], capture_output=True, text=True, encoding="utf-8", check=True)
    return r.stdout


BACKUP_CALLS: list = []
NOTE = "---\ntype: gunluk\ntags: [x]\n---\n# Not\n"


@pytest.fixture
def vault(tmp_path, monkeypatch):
    v = tmp_path / "kasa"
    (v / "_system" / "config").mkdir(parents=True)
    (v / "00-Inbox").mkdir()
    (v / "_system" / "config" / "profile.yaml").write_text("name: t\n", encoding="utf-8")
    (v / "Asistan.md").write_text(NOTE, encoding="utf-8")
    (v / "00-Inbox" / "a.md").write_text("---\ntype: kisi\nsource: gmail-main\nsource_id: \"1\"\n---\nx\n", encoding="utf-8")
    (v / "00-Inbox" / "duz.md").write_text("ön bilgisiz\n", encoding="utf-8")
    (v / "_system" / "ic.md").write_text(NOTE, encoding="utf-8")                # _system'e dokunulmaz
    git(v, "init", "-q")
    git(v, "config", "user.email", "t@t")
    git(v, "config", "user.name", "t")
    git(v, "config", "core.autocrlf", "false")
    git(v, "add", "-A")
    git(v, "commit", "-q", "-m", "ilk")
    calls = BACKUP_CALLS
    calls.clear()
    monkeypatch.setattr(schema, "_backup", lambda: calls.append(1) or {"ok": True, "created": ["vault-test.zip.enc"]})
    return v


def fake_chain(monkeypatch, steps: dict[int, object], current: int | None = None):
    migs = [schema.Migration(n, f"m{n}", f"deneme {n}", types.SimpleNamespace(up=fn)) for n, fn in sorted(steps.items())]
    monkeypatch.setattr(schema, "discover", lambda: migs)
    monkeypatch.setattr(schema, "CURRENT", current or max(steps))


# ---------------------------------------------------------------- sürüm
def test_unversioned_vault_is_1(vault):
    assert schema.read_version(vault) == 1
    (vault / "_system/config/kasa.yaml").write_text("baska: 1\n", encoding="utf-8")
    assert schema.read_version(vault) == 1


def test_write_and_read_version_keeps_other_lines(vault):
    p = schema.config_path(vault)
    p.write_text("# elle yorum\nbaska: x\nschema_version: 1\n", encoding="utf-8")
    schema.write_version(7, vault)
    assert schema.read_version(vault) == 7
    t = p.read_text(encoding="utf-8")
    assert "# elle yorum" in t and "baska: x" in t and t.count("schema_version") == 1


def test_invalid_version_is_error(vault):
    schema.config_path(vault).write_text("schema_version: abc\n", encoding="utf-8")
    with pytest.raises(schema.SchemaError):
        schema.read_version(vault)
    assert schema.status(vault)["state"] == "error"


def test_real_chain_is_contiguous_and_current_matches():
    migs = schema.discover()
    assert [m.version for m in migs] == list(range(2, 2 + len(migs)))
    assert migs[-1].version == schema.CURRENT


# ---------------------------------------------------------------- gerçek m0002
def test_m0002_adds_missing_fields_only(vault):
    out = m2.up(vault, dry_run=True)
    assert sorted(out) == ["Asistan.md: + source, source_id"]
    assert (vault / "Asistan.md").read_text(encoding="utf-8") == NOTE            # dry-run yazmaz
    m2.up(vault, dry_run=False)
    assert (vault / "Asistan.md").read_text(encoding="utf-8") == "---\ntype: gunluk\ntags: [x]\nsource: manual\nsource_id: \"\"\n---\n# Not\n"
    assert (vault / "00-Inbox/duz.md").read_text(encoding="utf-8") == "ön bilgisiz\n"
    assert (vault / "_system/ic.md").read_text(encoding="utf-8") == NOTE
    assert "gmail-main" in (vault / "00-Inbox/a.md").read_text(encoding="utf-8")
    assert m2.up(vault, dry_run=False) == []                                     # idempotent


def test_m0002_keeps_crlf(vault):
    p = vault / "Asistan.md"
    p.write_bytes(b"---\r\ntype: gunluk\r\n---\r\ngovde\r\n")
    git(vault, "commit", "-qam", "crlf")
    m2.up(vault, dry_run=False)
    assert p.read_bytes() == b"---\r\ntype: gunluk\r\nsource: manual\r\nsource_id: \"\"\r\n---\r\ngovde\r\n"


# ---------------------------------------------------------------- uygulama
def test_run_applies_chain_and_commits_once(vault):
    n0 = int(git(vault, "rev-list", "--count", "HEAD"))
    r = schema.run(vault)
    assert r["ok"] and r["applied"] == list(range(2, schema.CURRENT + 1)), r      # her yeni göç eklenince test kendiliğinden uyar
    assert schema.read_version(vault) == schema.CURRENT
    assert int(git(vault, "rev-list", "--count", "HEAD")) == n0 + len(r["applied"])   # göç başına tek commit
    assert git(vault, "log", "-1", "--format=%s").startswith(f"şema göçü {schema.CURRENT - 1}→{schema.CURRENT}")
    assert git(vault, "status", "--porcelain") == ""
    assert "kasa.yaml" in git(vault, "show", "--name-only", "--format=", "HEAD")
    assert len(BACKUP_CALLS) == 1
    again = schema.run(vault)                                                    # idempotent: ikinci çalıştırma işsiz
    assert again["ok"] and again["applied"] == [] and len(BACKUP_CALLS) == 1


def test_chain_runs_in_order_one_commit_each(vault, monkeypatch):
    order = []
    fake_chain(monkeypatch, {n: (lambda v, d, n=n: order.append(n) or [f"adım {n}"]) for n in (4, 2, 3)})
    n0 = int(git(vault, "rev-list", "--count", "HEAD"))
    r = schema.run(vault)
    assert r["ok"] and r["applied"] == [2, 3, 4] and order == [2, 3, 4]
    assert int(git(vault, "rev-list", "--count", "HEAD")) == n0 + 3
    subjects = git(vault, "log", "-3", "--format=%s").splitlines()
    assert subjects[0].startswith("şema göçü 3→4") and subjects[2].startswith("şema göçü 1→2")
    assert len(BACKUP_CALLS) == 1                                                 # zincir başına tek yedek (adım başına değil)


def test_dirty_tree_stops_and_touches_nothing(vault):
    (vault / "Asistan.md").write_text(NOTE + "elle değişiklik\n", encoding="utf-8")
    (vault / "yeni-izlenmeyen.md").write_text("x", encoding="utf-8")
    before = git(vault, "status", "--porcelain")
    r = schema.run(vault)
    assert not r["ok"] and r["applied"] == [] and "commit edilmemiş" in " ".join(r["log"])
    assert git(vault, "status", "--porcelain") == before
    assert not BACKUP_CALLS and not schema.config_path(vault).exists()
    assert "elle değişiklik" in (vault / "Asistan.md").read_text(encoding="utf-8")


def test_untracked_files_do_not_block_and_are_not_committed(vault):
    (vault / "yeni-izlenmeyen.md").write_text("---\ntype: x\n---\n", encoding="utf-8")
    r = schema.run(vault)
    assert r["ok"]
    assert "yeni-izlenmeyen.md" not in git(vault, "show", "--name-only", "--format=", "HEAD")
    assert (vault / "yeni-izlenmeyen.md").read_text(encoding="utf-8") == "---\ntype: x\n---\n"


def test_backup_failure_stops_before_any_change(vault, monkeypatch):
    monkeypatch.setattr(schema, "_backup", lambda: {"ok": False, "message": "şifreleme yok"})
    r = schema.run(vault)
    assert not r["ok"] and "Yedek alınamadı" in " ".join(r["log"]) and "şifreleme yok" in " ".join(r["log"])
    assert git(vault, "status", "--porcelain") == "" and not schema.config_path(vault).exists()
    assert (vault / "Asistan.md").read_text(encoding="utf-8") == NOTE


def test_backup_exception_stops_too(vault, monkeypatch):
    def boom():
        raise RuntimeError("disk dolu")
    monkeypatch.setattr(schema, "_backup", boom)
    r = schema.run(vault)
    assert not r["ok"] and git(vault, "status", "--porcelain") == "" and not schema.config_path(vault).exists()


def test_failure_rolls_back_only_own_changes(vault, monkeypatch):
    def bad(v, dry):
        (v / "Asistan.md").write_text("bozuk yarım yazım\n", encoding="utf-8")
        (v / "00-Inbox" / "duz.md").unlink()
        (v / "olusan.md").write_text("göçün izlenmeyen dosyası", encoding="utf-8")
        raise RuntimeError("yarıda patladı")
    fake_chain(monkeypatch, {2: bad})
    (vault / "baskasi.txt").write_text("kullanıcının izlenmeyen dosyası", encoding="utf-8")   # göçten ÖNCE var
    head = git(vault, "rev-parse", "HEAD")
    r = schema.run(vault)
    assert not r["ok"] and r["applied"] == []
    assert git(vault, "rev-parse", "HEAD") == head
    assert (vault / "Asistan.md").read_text(encoding="utf-8") == NOTE
    assert (vault / "00-Inbox" / "duz.md").exists()
    assert (vault / "baskasi.txt").read_text(encoding="utf-8") == "kullanıcının izlenmeyen dosyası"   # başkasının dosyasına dokunulmadı
    assert "olusan.md" in " ".join(r["log"])                                                           # kalıntı silinmeden raporlandı
    assert git(vault, "status", "--porcelain", "--untracked-files=no") == ""
    assert not schema.config_path(vault).exists() and schema.read_version(vault) == 1


def test_failure_in_second_step_keeps_first(vault, monkeypatch):
    def ok2(v, dry):
        (v / "Asistan.md").write_text(NOTE + "iki\n", encoding="utf-8")
        return ["iki"]

    def bad3(v, dry):
        (v / "Asistan.md").write_text("üç yarım\n", encoding="utf-8")
        raise ValueError("üç patladı")
    fake_chain(monkeypatch, {2: ok2, 3: bad3})
    r = schema.run(vault)
    assert not r["ok"] and r["applied"] == [2]
    assert schema.read_version(vault) == 2
    assert (vault / "Asistan.md").read_text(encoding="utf-8") == NOTE + "iki\n"
    assert git(vault, "status", "--porcelain", "--untracked-files=no") == ""


def test_not_a_git_repo_refuses(tmp_path, monkeypatch):
    v = tmp_path / "gitsiz"
    (v / "_system/config").mkdir(parents=True)
    monkeypatch.setattr(schema, "_backup", lambda: pytest.fail("yedek alınmamalı"))
    r = schema.run(v)
    assert not r["ok"] and "git" in " ".join(r["log"])
    assert not schema.config_path(v).exists()


# ---------------------------------------------------------------- dry-run / check
def test_dry_run_writes_nothing(vault, capsys):
    rc = schema.cli(dry_run=True, vault=vault)
    out = capsys.readouterr().out
    assert rc == 0 and "Asistan.md" in out
    assert git(vault, "status", "--porcelain") == "" and not schema.config_path(vault).exists()
    assert not BACKUP_CALLS
    assert (vault / "Asistan.md").read_text(encoding="utf-8") == NOTE


def test_check_is_read_only_and_exit_codes(vault, capsys):
    assert schema.cli(check_only=True, vault=vault) == schema.EXIT_PENDING
    out = capsys.readouterr().out
    assert f"{schema.CURRENT - 1} göç bekliyor" in out and "Asistan.md" in out
    assert git(vault, "status", "--porcelain") == "" and not BACKUP_CALLS
    schema.write_version(schema.CURRENT, vault)
    assert schema.cli(check_only=True, vault=vault) == 0
    schema.write_version(schema.CURRENT + 1, vault)
    assert schema.cli(check_only=True, vault=vault) == 1


def test_cli_without_yes_asks_and_does_nothing(vault, capsys):
    assert schema.cli(vault=vault) == 1
    assert "--yes" in capsys.readouterr().out
    assert git(vault, "status", "--porcelain") == "" and not BACKUP_CALLS
    assert schema.cli(yes=True, vault=vault) == 0
    assert schema.read_version(vault) == schema.CURRENT


def test_ahead_vault_refuses_to_migrate(vault):
    schema.write_version(schema.CURRENT + 3, vault)
    r = schema.run(vault)
    assert not r["ok"] and "koddan yeni" in " ".join(r["log"])


# ---------------------------------------------------------------- doctor / update / uyarı
def test_doctor_schema_check(vault, monkeypatch):
    from sb import config
    monkeypatch.setattr(config, "VAULT", vault)
    st, name, hint = doctor.schema_check()
    assert st == doctor.FAIL and "sb migrate" in hint and "bekliyor" in name
    schema.write_version(schema.CURRENT, vault)
    assert doctor.schema_check()[0] == doctor.OK
    schema.write_version(schema.CURRENT + 1, vault)
    st, name, hint = doctor.schema_check()
    assert st == doctor.FAIL and "koddan yeni" in name and "sb update" in hint
    schema.config_path(vault).write_text("schema_version: x\n", encoding="utf-8")
    assert doctor.schema_check()[0] == doctor.FAIL


def test_doctor_checks_include_schema_row(monkeypatch):
    monkeypatch.setattr(doctor, "schema_check", lambda: (doctor.FAIL, "SCHEMA-SATIRI", "ipucu"))
    monkeypatch.setattr(doctor, "backup_check", lambda: (doctor.OK, "yedek", ""))
    try:
        rows = doctor.checks()
    except Exception:                                                            # noqa: BLE001 — ortam kontrolleri (ağ, claude...) kırılabilir
        pytest.skip("doctor.checks() bu ortamda çalışmıyor")
    assert (doctor.FAIL, "SCHEMA-SATIRI", "ipucu") in rows


def test_warn_if_ahead(vault, capsys):
    assert not schema.warn_if_ahead(vault) and capsys.readouterr().err == ""
    schema.write_version(schema.CURRENT + 1, vault)
    assert schema.warn_if_ahead(vault)
    assert "UYARI" in capsys.readouterr().err


def _proc(rc, out=""):
    return subprocess.CompletedProcess([], rc, stdout=out, stderr="")


def test_update_lists_and_applies_pending_with_yes(monkeypatch, tmp_path, capsys):
    calls = []
    monkeypatch.setattr(update, "_run_migrate", lambda v, *a: calls.append(a) or _proc(3 if a == ("--check",) else 0, "göç var"))
    assert update.migrate_after_update(tmp_path, yes=True) == 0
    assert calls == [("--check",), ("--yes",)]
    assert "göç var" in capsys.readouterr().out


def test_update_asks_and_defers_without_tty(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(update, "_run_migrate", lambda v, *a: calls.append(a) or _proc(3, "göç var"))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert update.migrate_after_update(tmp_path, yes=False) == 0
    assert calls == [("--check",)]                                               # onaysız uygulanmaz


def test_update_nothing_pending_and_failure(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(update, "_run_migrate", lambda v, *a: calls.append(a) or _proc(0))
    assert update.migrate_after_update(tmp_path, yes=True) == 0 and calls == [("--check",)]
    monkeypatch.setattr(update, "_run_migrate", lambda v, *a: _proc(3 if a == ("--check",) else 1, "x"))
    assert update.migrate_after_update(tmp_path, yes=True) == 1


# ---------------------------------------------------------------- kurulum motoru
def test_engine_stamps_new_vault_only(tmp_path):
    from setup import engine
    system = tmp_path / "v" / "_system"
    (system / "sb").mkdir(parents=True)
    (system / "sb" / "schema.py").write_text("CURRENT = 5\n", encoding="utf-8")
    assert engine.vault_is_new(tmp_path / "yok")
    assert engine.vault_is_new(tmp_path / "v") is False                          # _system var → boş değil
    assert engine.stamp_schema(tmp_path / "v", system) is True
    assert (system / "config" / "kasa.yaml").read_text(encoding="utf-8").splitlines()[-1] == "schema_version: 5"
    assert engine.stamp_schema(tmp_path / "v", system) is False                  # var olana dokunmaz
    from sb import config
    assert schema.read_version(tmp_path / "v") == 5
    _ = config


def test_engine_existing_vault_not_new(tmp_path):
    from setup import engine
    d = tmp_path / "eski"
    d.mkdir()
    (d / "Asistan.md").write_text("x", encoding="utf-8")
    assert engine.vault_is_new(d) is False
    h = tmp_path / "gizli"
    (h / ".git").mkdir(parents=True)
    assert engine.vault_is_new(h) is True


def test_git_sync_does_not_push_when_disabled(vault, monkeypatch):
    """`git_push: false` iken günlük çalışma kasayı yerelde commit'ler ama GitHub'a göndermez."""
    import subprocess
    from sb import runner
    calls = []
    real = subprocess.run

    def spy(cmd, *a, **k):
        calls.append(cmd)
        return real(cmd, *a, **k)
    monkeypatch.setattr(runner, "VAULT", vault)
    monkeypatch.setattr(runner, "git_push_enabled", lambda: False)
    monkeypatch.setattr(runner.subprocess, "run", spy)
    (vault / "yeni-not.md").write_text("x\n", encoding="utf-8")
    msg = runner.git_sync(lambda m: None)
    assert "yerelde commit" in msg
    assert not any(len(c) > 3 and c[3] == "push" for c in calls if isinstance(c, list))
    assert "yeni-not.md" in git(vault, "show", "--name-only", "--format=", "HEAD")
