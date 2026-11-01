"""Second Brain masaüstü tepsi simgesi (pystray + PIL). Elle çalıştırılır: python tray.py"""
import json
import subprocess
import sys
import urllib.request
import webbrowser

URL = "http://127.0.0.1:8765/"
TASK = "SecondBrain-Chat"


def _deps():
    try:
        import pystray
        from PIL import Image, ImageDraw
        return pystray, Image, ImageDraw
    except ImportError:
        print("pystray ve Pillow gerekli: pip install pystray pillow", file=sys.stderr)
        sys.exit(1)


def restart_server() -> None:
    subprocess.run(["schtasks", "/End", "/TN", TASK], capture_output=True)
    subprocess.run(["schtasks", "/Run", "/TN", TASK], capture_output=True)


def today_text() -> str:
    try:
        req = urllib.request.Request(URL + "api/v2/dashboard", headers={"X-SB": "1"})
        d = json.load(urllib.request.urlopen(req, timeout=5))
        return "\n".join(f"{t.get('time', '')} {t.get('title', '')}" for t in d.get("today", [])[:5]) or "Bugün plan yok"
    except Exception as e:
        return f"Alınamadı: {type(e).__name__}"


def main() -> None:
    pystray, Image, ImageDraw = _deps()
    img = Image.new("RGB", (64, 64), (40, 40, 60))
    ImageDraw.Draw(img).ellipse((14, 14, 50, 50), fill=(120, 180, 255))
    menu = pystray.Menu(
        pystray.MenuItem("Asistanı aç", lambda i, it: webbrowser.open(URL)),
        pystray.MenuItem("Bugünün planı", lambda i, it: i.notify(today_text(), "Bugünün planı")),
        pystray.MenuItem("Sunucuyu yeniden başlat", lambda i, it: restart_server()),
        pystray.MenuItem("Çık", lambda i, it: i.stop()),
    )
    pystray.Icon("secondbrain", img, "Second Brain", menu).run()


if __name__ == "__main__":
    main()
