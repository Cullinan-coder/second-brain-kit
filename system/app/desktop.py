"""Second Brain masaüstü uygulaması: pywebview penceresi + (varsa) pystray tepsi simgesi.

Kullanım: `python -m app.desktop [--minimized]` (sistem kökünden). Asistan sunucusu (127.0.0.1:8765) çalışmıyorsa uygulamanın
alt süreci olarak `python -m sb chat` başlatılır ve uygulama çıkarken durdurulur; zamanlanmış görevin sunucusuna dokunulmaz.
Tek örnek: 127.0.0.1:8767 yerel soketi; ikinci açılış "show" gönderip çıkar, ilki pencereyi öne getirir.
pywebview yoksa tarayıcıda açılır.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent.parent
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/"
LOCK_PORT = 8767
TITLE = "Second Brain"
SIZE = (1280, 820)


# ------------------------------------------------------------ sunucu
def server_up(url: str = URL, timeout: float = 2) -> bool:
    try:
        urllib.request.urlopen(url + "api/v2/routes", timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True                                              # yanıt veriyor (401 vb.)
    except Exception:                                            # noqa: BLE001
        return False


def ensure_server(up=server_up, popen=subprocess.Popen, sleep=time.sleep, wait: int = 30):
    """Sunucu çalışıyorsa None (dokunma); değilse alt süreci başlatıp döndürür. Açılmazsa süreç durdurulur, RuntimeError."""
    if up():
        return None
    flags = 0x08000000 if sys.platform == "win32" else 0                 # CREATE_NO_WINDOW
    proc = popen([sys.executable, "-m", "sb", "chat"], cwd=str(SYSTEM), stdin=subprocess.DEVNULL,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    for _ in range(wait):
        if up():
            return proc
        sleep(1)
    stop_child(proc)
    raise RuntimeError(f"Asistan sunucusu {wait} sn içinde açılmadı")


def stop_child(proc) -> None:
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=8)
    except Exception:                                            # noqa: BLE001
        try:
            proc.kill()
        except Exception:                                        # noqa: BLE001
            pass


# ------------------------------------------------------------ tek örnek
class SingleInstance:
    """acquire() → True: ilk örnek (soketi tutar, dinler); False: ilki var, ona "show" gönderildi."""

    def __init__(self, port: int = LOCK_PORT, on_show=None) -> None:
        self.port, self.on_show, self.sock = port, on_show, None

    def acquire(self) -> bool:
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", self.port))
        except OSError:
            s.close()
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=2) as c:
                    c.sendall(b"show\n")
            except OSError:
                pass
            return False
        s.listen(4)
        self.sock = s
        threading.Thread(target=self._loop, daemon=True, name="sb-single").start()
        return True

    def _loop(self) -> None:
        while self.sock:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            try:
                c.settimeout(2)
                if c.recv(16).strip() == b"show" and self.on_show:
                    self.on_show()
            except Exception:                                    # noqa: BLE001
                pass
            finally:
                c.close()

    def release(self) -> None:
        s, self.sock = self.sock, None
        if s:
            s.close()


# ------------------------------------------------------------ uygulama

def _chat_token() -> str:
    """Yerel asistanın oturum jetonu (~/.secondbrain/chat.token; sb/localauth.py). Dosya yoksa '' (sunucu 403 verir)."""
    import os
    d = Path(os.environ.get("SB_DATA") or Path.home() / ".secondbrain")
    try:
        return (d / "chat.token").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _api(path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(URL + path, data=data, headers={"X-SB": "1", "X-SB-Token": _chat_token(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


class App:
    def __init__(self, webview=None, pystray=None, browser=webbrowser) -> None:
        self.webview, self.pystray, self.browser = webview, pystray, browser
        self.window = None
        self.icon = None
        self.child = None
        self.quitting = False

    # pencere denetimi
    def show(self) -> None:
        w = self.window
        if w is None:
            self.browser.open(URL)
            return
        for name in ("show", "restore"):
            try:
                getattr(w, name)()
            except Exception:                                    # noqa: BLE001
                pass

    def start_work(self) -> None:
        try:
            _api("api/v2/startup/run", {})
        except Exception:                                        # noqa: BLE001
            pass
        self.show()

    def open_settings(self) -> None:
        try:
            url = _api("api/v2/startup/settings-url")["url"]
        except Exception:                                        # noqa: BLE001
            return
        if self.webview is not None:
            self.webview.create_window(TITLE + " · Ayarlar", url, width=1100, height=760)
        else:
            self.browser.open(url)

    def quit(self) -> None:
        self.quitting = True
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:                                    # noqa: BLE001
                pass
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:                                    # noqa: BLE001
                pass

    def _on_closing(self):
        """Tepsi varken pencereyi gizler (False = kapatma iptal); çıkışta ya da tepsi yokken kapanır."""
        if self.quitting or self.icon is None:
            return True
        try:
            self.window.hide()
        except Exception:                                        # noqa: BLE001
            return True
        return False

    def _tray(self) -> None:
        ps = self.pystray
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return
        img = Image.new("RGB", (64, 64), (40, 40, 60))
        ImageDraw.Draw(img).ellipse((14, 14, 50, 50), fill=(120, 180, 255))
        menu = ps.Menu(
            ps.MenuItem("Aç", lambda i, it: self.show(), default=True),
            ps.MenuItem("Çalışmaya başla", lambda i, it: self.start_work()),
            ps.MenuItem("Ayarlar", lambda i, it: self.open_settings()),
            ps.MenuItem("Çık", lambda i, it: self.quit()),
        )
        self.icon = ps.Icon("secondbrain", img, TITLE, menu)
        self.icon.run_detached()

    def run(self, minimized: bool = False) -> int:
        try:
            self.child = ensure_server()
        except RuntimeError as e:
            print(f"{TITLE}: {e}", file=sys.stderr)
            return 1
        try:
            if self.pystray is not None:
                try:
                    self._tray()
                except Exception:                                # noqa: BLE001
                    self.icon = None
            if self.webview is None:
                self.browser.open(URL)
                print(f"{TITLE}: {URL}\nKapatmak için Ctrl+C.")
                try:
                    while not self.quitting:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
                return 0
            hidden = minimized and self.icon is not None
            self.window = self.webview.create_window(TITLE, URL, width=SIZE[0], height=SIZE[1], hidden=hidden)
            self.window.events.closing += self._on_closing
            self.webview.start()                                 # pencere kapanana dek bloklar
            return 0
        finally:
            self.quitting = True
            if self.icon is not None:
                try:
                    self.icon.stop()
                except Exception:                                # noqa: BLE001
                    pass
            stop_child(self.child)                               # yalnız bizim başlattığımız alt süreç


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    app_holder: dict = {}
    lock = SingleInstance(on_show=lambda: app_holder["app"].show() if "app" in app_holder else None)
    if not lock.acquire():
        return 0
    try:
        try:
            import webview
        except Exception:                                        # noqa: BLE001
            webview = None
        try:
            import pystray
        except Exception:                                        # noqa: BLE001
            pystray = None
        app = App(webview, pystray)
        app_holder["app"] = app
        return app.run(minimized="--minimized" in argv)
    finally:
        lock.release()


if __name__ == "__main__":
    if str(SYSTEM) not in sys.path:
        sys.path.insert(0, str(SYSTEM))
    raise SystemExit(main())
