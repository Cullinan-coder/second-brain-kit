"""Rehber ekran görüntülerini üretir: Edge/Chrome (başsız) + Chrome DevTools Protocol (stdlib WebSocket istemcisi).

Her şey demo verisiyle ve ayrı portlarda çalışır; gerçek asistana (8765), gerçek kasaya, ~/.secondbrain'e,
şifre kasasına dokunmaz (bkz. tools/demo_vault.py). Çıktı: docs/rehber/img/<ad>.png (1280x800, koyu tema).

Kullanım:
  python tools/guide_shots.py                 # tüm kataloğu çek
  python tools/guide_shots.py sihirbaz-3-ozellikler uygulama-ayarlar   # yalnız bunlar
  python tools/guide_shots.py --list          # katalog
Çıktıdan sonra:  python tools/build_guide.py   (görüntüler rehbere girer)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[1]
OUT = SYSTEM / "docs" / "rehber" / "img"
SRC = SYSTEM / "docs" / "rehber-src"
sys.path.insert(0, str(Path(__file__).resolve().parent))

W, H = 1280, 800
CHAT_PORT = 8799
CDP_PORT = 9333
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]

# ------------------------------------------------------------------ katalog: ad -> (hedef, adımlar)
# hedef: "wizard" (kurulum sihirbazı, deneme kipi) | "settings" (aynı panel, ?mode=settings) | "chat" (demo asistan)
# adımlar: ("step", n) sihirbaz adımına git · ("js", ifade) · ("wait", ms) · ("view", ad) asistan görünümü ·
#          ("click", "metin") görünür düğmeyi metne göre tıkla · ("tab", "metin") ayarlar sekmesi · ("send", "soru") sohbete yaz
# Uydurma kasa yolu (OneDrive içinde → sihirbazın yol uyarısı görünür). Sunucuya bu yol YALNIZ profil adımında gider;
# o yüzden bu görüntü en sona bırakılır (sunucu sonrasında bu yola yazabilecek bir adıma gidilmez).
DEMO_VAULT_PATH = "C:" + chr(92) + chr(92).join(["Users", "ayse", "OneDrive", "Belgeler", "SecondBrain"])
FILL_PROFILE = ("js", "S.profile.name='Ayşe'; S.profile.full_name='Ayşe Yılmaz'; S.profile.org='Örnek Üniversitesi'; S.profile.role='Öğrenci'; "
                f"S.profile.vault={json.dumps(DEMO_VAULT_PATH)}; renderWizard(); saveProfile()")
LAST = ("sihirbaz-4-profil",)
CATALOG: dict[str, tuple[str, list[tuple]]] = {
    "sihirbaz-genel": ("wizard", [("step", 2)]),
    "sihirbaz-1-hos-geldin": ("wizard", [("step", 0)]),
    "sihirbaz-2-hazir-secim": ("wizard", [("step", 1), ("wait", 800)]),
    "sihirbaz-3-ozellikler": ("wizard", [("step", 2), ("wait", 800)]),
    "sihirbaz-4-profil": ("wizard", [("step", 3), FILL_PROFILE, ("wait", 300)]),
    "sihirbaz-5-hesaplar": ("wizard", [("step", 4)]),
    "sihirbaz-6-anahtarlar": ("wizard", [("step", 5)]),
    "sihirbaz-7-modeller": ("wizard", [("step", 6), ("wait_gone", "Yükleniyor", 15)]),
    "sihirbaz-8-mcp": ("wizard", [("step", 7), ("wait", 800)]),
    "sihirbaz-9-veri": ("wizard", [("step", 8), ("wait", 500)]),
    "sihirbaz-10-telefon": ("wizard", [("step", 9), ("wait", 2500)]),
    "sihirbaz-11-baslangic": ("wizard", [("step", 10), ("wait", 500)]),
    "sihirbaz-12-ozet": ("wizard", [("js", "S.profile.name='Ayşe'; S.profile.full_name='Ayşe Yılmaz'"), ("step", 11), ("wait_gone", "Yükleniyor", 15)]),
    "anahtarlar-ekran": ("settings", [("tab", "Anahtarlar"), ("wait", 600)]),
    "modeller-ollama": ("settings", [("tab", "Modeller"), ("wait_gone", "Yükleniyor", 15)]),
    "mcp-katalog": ("settings", [("tab", "MCP"), ("wait", 800)]),
    "veri-yukleme-kart": ("settings", [("tab", "Veri yükleme"), ("wait", 800)]),
    "uygulama-ayarlar": ("settings", [("wait", 600)]),
    "uygulama-ana-pencere": ("chat", [("open_conv", "demo-hafta"), ("wait", 600)]),
    "uygulama-calismaya-basla": ("chat", [("view", "startup"), ("wait", 800)]),
    "gizlilik-ekran": ("chat", [("view", "privacy"), ("wait", 1500)]),
    "asistan-ilk-soru": ("chat", [("send", "Bu hafta hangi teslimlerim var?"), ("wait_reply", 90)]),
    "asistan-onay-karti": ("chat_scripted", [("send", "Yarın 15:00'e kütüphane projesi görüşmesi ekle"), ("wait_reply", 60)]),
    # modeller-indirme: gerçek indirme gerektirir, otomatik çekilmez.
}
# Çekilemeyen ya da kart başına olanlar kasıtlı katalog dışı: google-1..7, kurulum-*, kaynak-<id>, yukleme-<id>, mcp-<id>, modeller-indirme.


def demo_vault_dir() -> Path:
    import demo_vault
    return demo_vault.demo_root()


def catalog_names() -> list[str]:
    """Çekim sırası: asistan, ayarlar, sihirbaz; kasa yolunu sunucuya yazan görüntü en sonda."""
    order = {"chat": 0, "chat_scripted": 0, "settings": 1, "wizard": 2}
    return sorted(CATALOG, key=lambda n: (n in LAST, order[CATALOG[n][0]]))


def guide_image_names() -> set[str]:
    """rehber-src içinde adı geçen görüntü adları (uzantısız)."""
    names: set[str] = set()
    for p in SRC.glob("*.md"):
        names.update(re.findall(r"\]\(img/([A-Za-z0-9_-]+)\.png\)", p.read_text(encoding="utf-8")))
    return names


# ------------------------------------------------------------------ küçük WebSocket istemcisi (stdlib)
class WS:
    def __init__(self, url: str):
        m = re.match(r"ws://([^:/]+):(\d+)(/.*)", url)
        host, port, path = m.group(1), int(m.group(2)), m.group(3)
        self.s = socket.create_connection((host, port), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        if b" 101 " not in buf.split(b"\r\n")[0]:
            raise RuntimeError("WebSocket el sıkışması başarısız: " + buf[:100].decode(errors="replace"))
        self.rest = buf.split(b"\r\n\r\n", 1)[1]
        self.id = 0

    def _read(self, n: int) -> bytes:
        while len(self.rest) < n:
            chunk = self.s.recv(65536)
            if not chunk:
                raise ConnectionError("WebSocket kapandı")
            self.rest += chunk
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, text: str) -> None:
        data = text.encode()
        head = bytearray([0x81])
        n = len(data)
        if n < 126:
            head.append(0x80 | n)
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        self.s.sendall(bytes(head) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self) -> str:
        msg = b""
        while True:
            b1, b2 = self._read(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            op = b1 & 0x0F
            if op == 8:
                raise ConnectionError("WebSocket kapandı")
            if op in (9, 10):
                continue
            msg += payload
            if b1 & 0x80:
                return msg.decode()

    def call(self, method: str, params: dict | None = None) -> dict:
        self.id += 1
        self.send(json.dumps({"id": self.id, "method": method, "params": params or {}}))
        while True:
            r = json.loads(self.recv())
            if r.get("id") == self.id:
                if "error" in r:
                    raise RuntimeError(f"{method}: {r['error']}")
                return r.get("result", {})

    def close(self) -> None:
        try:
            self.s.close()
        except OSError:
            pass


class Page:
    def __init__(self, ws: WS, target_id: str = ""):
        self.ws = ws
        self.target_id = target_id
        for m in ("Page.enable", "Runtime.enable"):
            ws.call(m)
        ws.call("Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False})
        ws.call("Emulation.setEmulatedMedia", {"media": "screen", "features": [{"name": "prefers-color-scheme", "value": "dark"}]})

    def goto(self, url: str) -> None:
        self.ws.call("Page.navigate", {"url": url})
        time.sleep(1.2)
        self.wait_js("document.readyState==='complete'", 20)

    def js(self, expr: str):
        r = self.ws.call("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        if "exceptionDetails" in r:
            raise RuntimeError("JS hatası: " + json.dumps(r["exceptionDetails"], ensure_ascii=False)[:300])
        return r.get("result", {}).get("value")

    def wait_js(self, expr: str, timeout: float = 10) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            try:
                if self.js(expr):
                    return True
            except RuntimeError:
                pass
            time.sleep(0.25)
        return False

    def click_text(self, text: str) -> bool:
        t = json.dumps(text)
        return bool(self.js(f"""(()=>{{const t={t}.toLowerCase();const els=[...document.querySelectorAll('button,a,[role=tab],[role=button],label')]
          .filter(e=>e.offsetParent!==null&&(e.textContent||'').trim().toLowerCase().includes(t));
          if(!els.length) return false; els.sort((a,b)=>a.textContent.length-b.textContent.length); els[0].click(); return true;}})()"""))

    # JS içindeki ters eğik çizgi "BS" imiyle yazılır (kaçış karışıklığı olmasın), çalışmadan önce değiştirilir.
    SCRUB_JS = '''(()=>{const re=/([A-Za-z]:)[BSBS/]+Users[BSBS/]+kullanici/gi, to='$1BSBSUsersBSBSayse';
      const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),ns=[];while(w.nextNode())ns.push(w.currentNode);
      ns.forEach(t=>{if(re.test(t.nodeValue)){re.lastIndex=0;t.nodeValue=t.nodeValue.replace(re,to);}re.lastIndex=0;});
      document.querySelectorAll('input,textarea').forEach(i=>{if(typeof i.value==='string'&&re.test(i.value)){re.lastIndex=0;i.value=i.value.replace(re,to);}re.lastIndex=0;});
      const vals=[...document.querySelectorAll('input,textarea')].map(i=>i.value).join(' ');
      return (document.body.innerText+' '+vals+' '+document.title).toLowerCase();})()'''.replace("BS", chr(92))

    def shot(self, path: Path) -> None:
        """Çekimden önce: yoldaki kullanıcı adını demo adıyla değiştir, sonra görünen metinde yasak sözcük ara (varsa çekme)."""
        import demo_vault
        self.js("window.scrollTo(0,0);document.documentElement.scrollLeft=0;document.body.scrollLeft=0")
        time.sleep(0.6)
        text = self.js(self.SCRUB_JS) or ""
        bad = [w for w in (*demo_vault.FORBIDDEN, "kullanici") if w in text]
        if bad:
            i = text.find(bad[0])
            raise RuntimeError("görüntüde kişisel veri olabilir, çekilmedi: " + ", ".join(bad) + f" ... {text[max(0, i - 50):i + 40]!r}")
        r = self.ws.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(r["data"]))


# ------------------------------------------------------------------ süreçler
def find_browser() -> str:
    for b in BROWSERS:
        if Path(b).is_file():
            return b
    raise SystemExit("Edge ya da Chrome bulunamadı (BROWSERS listesine yol ekle).")


class Stack:
    """Demo asistan + deneme kipi kurulum paneli + başsız tarayıcı; kapanışta hepsi kapatılır."""

    def __init__(self):
        self.procs: list[subprocess.Popen] = []
        self.tmp = Path(tempfile.mkdtemp(prefix="sb-shots-"))
        self.setup_url = ""
        self.chat_scripted_port = CHAT_PORT + 1

    def _env(self) -> dict:
        import demo_vault
        return demo_vault.demo_env()

    def start(self, chat: bool = True, setup: bool = True) -> None:
        import demo_vault
        py = sys.executable
        root = demo_vault.build()
        if setup:
            sandbox = root.parent / "sb-demo-setup"
            if sandbox.exists():
                shutil.rmtree(sandbox)
            sandbox.mkdir(parents=True, exist_ok=True)         # "kayıtlı" rozeti için SAHTE değerler (yalnız deneme şifre kasası dosyası)
            (sandbox / "keyring.json").write_text(json.dumps({"second-brain/api-openai": "sahte-demo-degeri", "second-brain/api-gemini": "sahte-demo-degeri"}),
                                                  encoding="utf-8")
            env = self._env()
            env["SB_SETUP_SANDBOX"] = str(sandbox)
            p = subprocess.Popen([py, str(Path(__file__).parent / "demo_vault.py"), "setup-serve", "--sandbox", str(sandbox)], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", cwd=str(SYSTEM))
            self.procs.append(p)
            self.setup_url = p.stdout.readline().strip()
            if not self.setup_url.startswith("http://127.0.0.1:"):
                raise SystemExit("kurulum paneli açılamadı: " + self.setup_url)
        if chat:
            for port, extra in ((CHAT_PORT, []), (self.chat_scripted_port, ["--scripted"])):
                self.procs.append(subprocess.Popen([py, str(Path(__file__).parent / "demo_vault.py"), "serve", "--port", str(port), *extra],
                                                   env=self._env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(SYSTEM)))
            for port in (CHAT_PORT, self.chat_scripted_port):
                for _ in range(60):
                    try:
                        urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2).read(1)
                        break
                    except Exception:
                        time.sleep(0.5)
                else:
                    raise SystemExit(f"demo asistan açılmadı (port {port})")
        browser = find_browser()
        self.procs.append(subprocess.Popen([browser, "--headless=new", f"--remote-debugging-port={CDP_PORT}", f"--user-data-dir={self.tmp / 'profile'}",
                                            f"--window-size={W},{H}", "--hide-scrollbars", "--no-first-run", "--lang=tr-TR", "--accept-lang=tr-TR", "--disable-gpu", "--disable-extensions",
                                            "--remote-allow-origins=*", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=2).read()
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise SystemExit("tarayıcı hata ayıklama portu açılmadı")

    def reset_wizard(self) -> None:
        """Sihirbazın kayıtlı durumunu sil (yalnız deneme klasöründeki dosya): her görüntü sıfırdan başlasın."""
        f = demo_vault_dir() / "sb-demo-setup" / "data" / "setup_wizard.json"
        if f.exists():
            f.unlink()

    def new_page(self) -> Page:
        req = urllib.request.Request(f"http://127.0.0.1:{CDP_PORT}/json/new?about:blank", method="PUT")
        info = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return Page(WS(info["webSocketDebuggerUrl"]), info.get("id", ""))

    def close_page(self, page: Page) -> None:
        """Sekmeyi gerçekten kapat (açık kalan sekme sihirbaz durumunu sonradan yeniden yazar)."""
        page.ws.close()
        if page.target_id:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/close/{page.target_id}", timeout=10).read()
            except Exception:
                pass
        time.sleep(0.5)

    def stop(self) -> None:
        for p in reversed(self.procs):
            try:                                              # venv başlatıcısı çocuk süreç açar: ağacı birlikte kapat
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, timeout=20) if os.name == "nt" else p.terminate()
                p.wait(timeout=8)
            except Exception:
                pass
        self.procs.clear()
        if os.name == "nt":                                   # başsız tarayıcı çocukları ayrı kopabilir: bizim profil klasörünü taşıyanları kapat
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            f"Get-CimInstance Win32_Process | Where-Object {{ $_.CommandLine -like '*{self.tmp.name}*' -and $_.ProcessId -ne $PID }} | "
                            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
                           capture_output=True, timeout=60)
            time.sleep(1)
        shutil.rmtree(self.tmp, ignore_errors=True)


# ------------------------------------------------------------------ adımları çalıştır
def run_steps(page: Page, steps: list[tuple]) -> None:
    for st in steps:
        op = st[0]
        if op == "step":
            page.js(f"goStep({st[1]})")
            time.sleep(0.7)
        elif op == "js":
            page.js(st[1])
            time.sleep(0.3)
        elif op == "wait":
            time.sleep(st[1] / 1000)
        elif op == "tab":
            if not page.click_text(st[1]):
                raise RuntimeError(f"sekme bulunamadı: {st[1]}")
            time.sleep(0.5)
        elif op == "click":
            if not page.click_text(st[1]):
                raise RuntimeError(f"düğme bulunamadı: {st[1]}")
        elif op == "view":
            page.wait_js("window.SB&&SB.openView&&SB.has&&SB.routes", 20)
            if not page.js(f"SB.openView({json.dumps(st[1])})"):
                raise RuntimeError(f"görünüm açılamadı: {st[1]}")
        elif op == "open_conv":
            page.wait_js("window.SB&&SB.openConversation", 20)
            page.js(f"SB.openConversation({json.dumps(st[1])})")
            time.sleep(0.8)
        elif op == "send":
            page.wait_js("window.SB&&SB.sendMessage", 20)
            page.js("SB.newConversation&&SB.newConversation()")
            time.sleep(0.5)
            page.js(f"SB.sendMessage({json.dumps(st[1])})")
        elif op == "wait_gone":
            page.wait_js(f"!document.body.innerText.includes({json.dumps(st[1])})", st[2])
            time.sleep(0.5)
        elif op == "wait_reply":
            ok = page.wait_js("document.querySelectorAll('.msg.assistant, .msg.bot, .msg[data-role=assistant]').length>0 && !document.querySelector('.typing,.thinking,[aria-busy=true]')", st[1])
            if not ok:
                raise RuntimeError("cevap gelmedi (model çalışmıyor olabilir)")
            time.sleep(1.5)
            if page.js("/think>/i.test(document.body.innerText)"):
                raise RuntimeError("model düşünme metnini sızdırdı; görüntü atlandı")
        else:
            raise ValueError(op)


def page_url(stack: Stack, target: str) -> str:
    if target == "wizard":
        return stack.setup_url
    if target == "settings":
        return stack.setup_url.replace("/?t=", "/?mode=settings&t=")
    port = stack.chat_scripted_port if target == "chat_scripted" else CHAT_PORT
    return f"http://127.0.0.1:{port}/"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Rehber ekran görüntülerini üretir (demo verisiyle).")
    ap.add_argument("names", nargs="*", help="yalnız bu görüntüler (boşsa hepsi)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        for n, (t, s) in CATALOG.items():
            print(f"{n:28s} {t:14s} {s}")
        return 0
    names = sorted(a.names, key=catalog_names().index) if a.names and not [n for n in a.names if n not in CATALOG] else (a.names or catalog_names())
    bad = [n for n in names if n not in CATALOG]
    if bad:
        raise SystemExit("katalogda yok: " + ", ".join(bad))
    stack = Stack()
    done, failed = [], {}
    try:
        stack.start()
        for n in names:
            target, steps = CATALOG[n]
            page = None
            try:
                if target in ("wizard", "settings"):
                    stack.reset_wizard()
                page = stack.new_page()
                page.goto(page_url(stack, target))
                if target in ("wizard", "settings"):
                    page.js("try{localStorage.clear()}catch(e){}")
                page.wait_js("document.body&&document.body.innerText.length>20", 15)
                time.sleep(1.0)
                if target == "wizard":                       # "yarım kalan kurulum sürdürüldü" gibi geçici şerit görüntüye girmesin
                    page.js("try{showBanner('')}catch(e){}")
                run_steps(page, steps)
                page.shot(OUT / f"{n}.png")
                done.append(n)
                print("ok  ", n, flush=True)
            except Exception as e:                             # tek görüntü başarısız olsa da diğerleri sürer
                failed[n] = f"{type(e).__name__}: {e}"
                print("HATA", n, failed[n], flush=True)
            finally:
                if page:
                    try:
                        stack.close_page(page)
                    except Exception:
                        pass
    finally:
        stack.stop()
    print(f"\n{len(done)} görüntü üretildi, {len(failed)} başarısız.")
    return 0 if not failed else 1


if __name__ == "__main__":
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    raise SystemExit(main())
