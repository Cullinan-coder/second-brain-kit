"""`sb` komut başlatıcısı: her klasörden çalışır, PATH yalnız gerçek kurulumda değişir."""
import importlib.util
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parent.parent / "setup" / "engine.py"
pytestmark = pytest.mark.skipif(not ENGINE.exists(), reason="kurulum motoru bu kopyada yok")


@pytest.fixture(scope="module")
def eng():
    spec = importlib.util.spec_from_file_location("engine_shim", ENGINE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_windows_shim_sets_pythonpath_and_forwards_args(eng, tmp_path):
    t = eng.cli_shim_text(tmp_path / "code", tmp_path / "kasa", tmp_path / "data", "win32")
    assert t.startswith("@echo off\r\n")
    assert f'set "PYTHONPATH={tmp_path / "code"};%PYTHONPATH%"' in t          # sb paketi her klasörden bulunur
    assert f'set "SB_VAULT={tmp_path / "kasa"}"' in t and f'set "SB_DATA={tmp_path / "data"}"' in t
    assert t.rstrip().endswith(f'"{tmp_path / "code" / ".venv" / "Scripts" / "python.exe"}" -X utf8 -m sb %*')
    assert "cd " not in t and "pushd" not in t                                 # çalışma klasörü değişmez (göreli yollar)


def test_posix_shim_quotes_paths(eng, tmp_path):
    t = eng.cli_shim_text(Path("/opt/sb's code"), None, Path("/home/a/.secondbrain"), "darwin")
    assert t.startswith("#!/bin/sh\n") and 'exec ' in t and '"$@"' in t
    assert "sb'\\''s code'" in t                                                 # tek tırnak kaçışı (ayırıcı platforma göre)
    assert "SB_VAULT" not in t


def test_install_windows_writes_cmd_and_updates_user_path(eng, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(eng, "_run_capture", lambda cmd, timeout=15, cwd=None: calls.append(cmd) or (0, ""))
    msg = eng.install_cli_shim(tmp_path / "code", tmp_path / "kasa", tmp_path / "data", "win32")
    f = tmp_path / "data" / "bin" / "sb.cmd"
    assert f.exists() and "-m sb %*" in f.read_text(encoding="utf-8")
    ps = calls[0][-1]
    assert len(calls) == 1 and "OpenSubKey('Environment',$true)" in ps
    assert "DoNotExpandEnvironmentNames" in ps and "ExpandString" in ps                 # %DEĞİŞKEN% başvuruları korunur
    assert "-contains $d" in ps                                                          # zaten varsa ikinci kez eklenmez
    assert str(tmp_path / "data" / "bin") in calls[0][-1]
    assert "hazır" in msg


def test_install_sandbox_does_not_touch_path(eng, tmp_path, monkeypatch):
    monkeypatch.setattr(eng, "_run_capture", lambda *a, **k: pytest.fail("deneme kipinde PATH değişmemeli"))
    msg = eng.install_cli_shim(tmp_path / "code", None, tmp_path / "data", "win32", sandbox=True)
    assert msg.startswith("[deneme]") and (tmp_path / "data" / "bin" / "sb.cmd").exists()


def test_install_path_failure_is_reported_not_raised(eng, tmp_path, monkeypatch):
    monkeypatch.setattr(eng, "_run_capture", lambda *a, **k: (1, "erişim engellendi"))
    msg = eng.install_cli_shim(tmp_path / "code", None, tmp_path / "data", "win32")
    assert "PATH'e eklenemedi" in msg
