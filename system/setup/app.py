"""Kurulum paneli penceresi: sunucuyu başlatır, jetonlu adresi pywebview penceresinde (yoksa tarayıcıda) açar.

Sunucu: `server.make_server(port=0).start()` → `.url` (jetonlu `?t=`), `.stop()`.
Kullanım: `python setup/app.py` (kurulum paneli) — kurulum bitmeden de çalışır (yalnız stdlib gerekir).
"""
from __future__ import annotations

import sys
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
TITLE = "Second Brain Kurulum"
SIZE = (1100, 760)


def _load_server():
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import server  # setup/server.py
    return server


def run_window(url: str, stop, webview=None, browser=webbrowser, sleep=time.sleep) -> str:
    """Pencereyi/tarayıcıyı açar; kapanınca sunucuyu durdurur. Döner: "window" ya da "browser"."""
    mode = "browser"
    try:
        if webview is not None:
            webview.create_window(TITLE, url, width=SIZE[0], height=SIZE[1])
            mode = "window"
            webview.start()                       # pencere kapanana dek bloklar
        else:
            browser.open(url)
            print(f"{TITLE}: {url}\nKapatmak için Ctrl+C.")
            while True:
                sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop()
    return mode


def main(argv: list[str] | None = None) -> int:
    server = _load_server()
    srv = server.make_server(port=0).start()
    url, stop = srv.url, srv.stop
    try:
        import webview                            # pywebview (isteğe bağlı)
    except Exception:
        webview = None
    run_window(url, stop, webview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
