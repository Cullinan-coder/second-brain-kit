"""Süreçler arası dosya kilidi + atomik yazma (D-20).

`locked(path)`: `~/.secondbrain/locks/` altındaki kilit dosyası üzerinde işletim sistemi kilidi (Windows `msvcrt.locking`, POSIX `fcntl.flock`);
zaman aşımında `LockTimeout`. Aynı süreçteki iş parçacıkları için ayrıca süreç içi kilit tutulur (Windows'ta aynı süreç
aynı bölgeyi iki kez kilitleyemez, POSIX flock ise iş parçacıkları arasında güvenilir değildir).
`atomic_write`: geçici dosya + fsync + `os.replace`: yarıda kesilen yazma hedefi bozmaz.
`append_line`: kilit altında satır ekler (kayıp yok).
"""
from __future__ import annotations

import contextlib
import hashlib
import os
import threading
import time
from pathlib import Path

try:
    import msvcrt  # type: ignore[import-not-found]
except ImportError:                                           # POSIX
    msvcrt = None
    import fcntl

DEFAULT_TIMEOUT = 15.0
_local: dict[str, threading.RLock] = {}
_local_guard = threading.Lock()


class LockTimeout(TimeoutError):
    pass


def _thread_lock(key: str) -> threading.RLock:
    with _local_guard:
        return _local.setdefault(key, threading.RLock())


def _lock_path(p: Path) -> Path:
    """Kilit dosyaları kasayı kirletmesin: `~/.secondbrain/locks/<yolun karması>.lock`."""
    from . import config
    key = hashlib.sha1(str(p.resolve()).lower().encode("utf-8")).hexdigest()[:20]
    return Path(config.DATA) / "locks" / f"{key}.lock"


@contextlib.contextmanager
def locked(path: str | Path, timeout: float = DEFAULT_TIMEOUT):
    p = Path(path)
    lock_path = _lock_path(p)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    tl = _thread_lock(str(lock_path.resolve()))
    if not tl.acquire(timeout=timeout):
        raise LockTimeout(f"kilit alınamadı: {p.name}")
    fh = None
    try:
        fh = open(lock_path, "a+b")
        deadline = time.monotonic() + timeout
        while True:
            try:
                if msvcrt is not None:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise LockTimeout(f"kilit alınamadı: {p.name}") from None
                time.sleep(0.02)
        try:
            yield
        finally:
            try:
                if msvcrt is not None:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
    finally:
        if fh is not None:
            fh.close()
        tl.release()


def atomic_write(path: str | Path, data: str | bytes, encoding: str = "utf-8") -> None:
    """Geçici dosyaya yaz, fsync, `os.replace` ile yerine koy."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = data if isinstance(data, bytes) else data.encode(encoding)
    tmp = p.with_name(f"{p.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        for i in range(50):                                   # Windows: hedef başka süreçte açıkken replace kısa süre reddedilebilir
            try:
                os.replace(tmp, p)
                break
            except PermissionError:
                if i == 49:
                    raise
                time.sleep(0.02)
    finally:
        tmp.unlink(missing_ok=True)


def append_line(path: str | Path, line: str, encoding: str = "utf-8") -> None:
    """Kilit altında dosyaya tek satır ekler (satır sonu eklenir)."""
    p = Path(path)
    with locked(p):
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "ab") as f:
            f.write((line.rstrip("\n") + "\n").encode(encoding))
            f.flush()
            os.fsync(f.fileno())


def read_modify_write(path: str | Path, fn, encoding: str = "utf-8") -> None:
    """Kilit altında oku → `fn(eski_metin) -> yeni_metin` → atomik yaz. Dosya yoksa eski metin ''."""
    p = Path(path)
    with locked(p):
        try:
            old = p.read_text(encoding=encoding)
        except FileNotFoundError:
            old = ""
        atomic_write(p, fn(old), encoding)
