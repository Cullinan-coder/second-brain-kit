"""`uv sync` kurulu ekleri (ses, video) sessizce kaldırmamalı; NVIDIA paketleri Windows tekerleği olan sürümde kalmalı."""
import re
import tomllib
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent
FILES = ["setup/accounts.py", "setup/engine.py", "kit/install.py", "sb/update.py"]


def _sync_calls(text: str) -> list[str]:
    # Komut listelerinde "sync" geçen satırlar (yorum ve belge satırları hariç)
    return [ln for ln in text.splitlines()
            if re.search(r'["\']sync["\']', ln) and not ln.lstrip().startswith("#") and '"apps"' not in ln]


def test_every_uv_sync_is_inexact():
    found = []
    for f in FILES:
        p = CODE / f
        if not p.exists():
            continue
        for ln in _sync_calls(p.read_text(encoding="utf-8")):
            if "uv" in ln or "_uv()" in ln:
                found.append((f, ln.strip()))
                assert "--inexact" in ln, f"{f}: `uv sync` --inexact olmadan ekleri siler → {ln.strip()}"
    assert found, "hiç `uv sync` çağrısı bulunamadı (test kalıbı eskidi mi?)"


def test_voice_gpu_pins_windows_wheels_and_skips_macos():
    deps = tomllib.loads((CODE / "pyproject.toml").read_text(encoding="utf-8"))["project"]["optional-dependencies"]["voice-gpu"]
    cublas = next(d for d in deps if d.startswith("nvidia-cublas-cu12"))
    assert "<12.9.3" in cublas                                   # 12.9.3.13 yalnız Linux tekerleğiyle yayınlandı
    for d in deps:
        assert "sys_platform == 'win32'" in d and "darwin" not in d   # macOS'ta NVIDIA paketi aranmaz


def test_lockfile_cublas_has_windows_wheel():
    lock = (CODE / "uv.lock").read_text(encoding="utf-8")
    block = lock.split('name = "nvidia-cublas-cu12"', 1)[1].split("[[package]]", 1)[0]
    assert "win_amd64" in block, "kilitli cublas sürümünün Windows tekerleği yok"
