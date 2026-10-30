"""macOS karşılıkları (actions.py Mac'te bunları çağırır). Windows'ta hiç yüklenmez.

Gereken izinler (Sistem Ayarları › Gizlilik ve Güvenlik):
- Erişilebilirlik: medya/Enter tuşu gönderme (WhatsApp onaylı gönderme) için Terminal/Python'a izin.
- Ekran Kaydı: ekran okuma için. Kamera: kamera okuma için. Otomasyon: Spotify/Music/WhatsApp'ı AppleScript ile kontrol.
NOT: Bu modül Windows makinede yazıldı; macOS'ta birim testleri dışında gerçek cihazda doğrulanmadı (docs/MAC.md).
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def osa(script: str, timeout: int = 15) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "").strip()


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def open_uri(uri: str) -> None:
    subprocess.Popen(["open", uri])


# ---------------------------------------------------------------- uygulamalar
def installed_apps() -> list[tuple[str, str]]:
    out = []
    for root in (Path("/Applications"), Path("/System/Applications"), Path.home() / "Applications"):
        if root.exists():
            for app in sorted(root.glob("*.app")):
                out.append((app.stem, str(app)))
            for app in sorted(root.glob("*/*.app")):            # Utilities gibi alt klasörler
                out.append((app.stem, str(app)))
    return out


def launch_app(path: str) -> None:
    subprocess.Popen(["open", path])


# ---------------------------------------------------------------- medya
def media(action: str, steps: int = 1) -> str:
    steps = max(1, min(int(steps or 1), 25))
    if action in ("ses_artir", "ses_azalt"):
        delta = 6 * steps * (1 if action == "ses_artir" else -1)
        osa(f"set volume output volume ((output volume of (get volume settings)) + {delta})")
        return f"Ses: {'arttı' if delta > 0 else 'azaldı'}"
    if action == "sessiz":
        osa("set volume output muted (not (output muted of (get volume settings)))")
        return "Ses: sessiz aç/kapa"
    cmd = {"oynat_duraklat": "playpause", "sonraki": "next track", "onceki": "previous track"}.get(action)
    if not cmd:
        return f"Hata: bilinmeyen medya komutu: {action}"
    for app in ("Spotify", "Music"):                             # hangisi açıksa onu kontrol et
        if osa(f'application "{app}" is running') == "true":
            osa(f'tell application "{app}" to {cmd}')
            return f"Medya ({app}): {action}"
    return "Açık bir müzik uygulaması (Spotify/Music) bulunamadı."


# ---------------------------------------------------------------- pencere ve klavye
def frontmost_app() -> str:
    return osa('tell application "System Events" to get name of first application process whose frontmost is true')


def focus_app(name: str) -> bool:
    osa(f'tell application "{_esc(name)}" to activate')
    return name.lower() in frontmost_app().lower()


def press_enter() -> None:
    osa('tell application "System Events" to key code 36')     # Return


# ---------------------------------------------------------------- bildirim, komut, kamera
def toast(title: str, body: str) -> None:
    osa(f'display notification "{_esc(body[:300])}" with title "{_esc(title[:120])}" sound name "Glass"')


def shell(cmd: str, timeout: int, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(["/bin/zsh", "-lc", cmd], capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, cwd=cwd)


def ocr(png: bytes) -> str:
    """macOS Vision (pyobjc-framework-Vision kuruluysa). Yoksa boş döner; görsel model yine anlatır."""
    try:
        import Quartz
        import Vision
        from Foundation import NSData
    except ImportError:
        return ""
    data = NSData.dataWithBytes_length_(png, len(png))
    src = Quartz.CGImageSourceCreateWithData(data, None)
    img = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLanguages_(["tr-TR", "en-US"])
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(img, None)
    handler.performRequests_error_([req], None)
    return "\n".join(o.topCandidates_(1)[0].string() for o in (req.results() or []))


def spotify_running() -> bool:
    return subprocess.run(["pgrep", "-x", "Spotify"], capture_output=True).returncode == 0


TAILSCALE_CANDIDATES = ("/Applications/Tailscale.app/Contents/MacOS/Tailscale", "/usr/local/bin/tailscale", "/opt/homebrew/bin/tailscale")
