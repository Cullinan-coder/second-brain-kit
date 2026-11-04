"""Rehber ekran görüntüleri için TAMAMEN uydurma demo kasası ve demo asistan sunucusu.

Her şey `%TEMP%\\sb-demo` altında: kasa `SecondBrain/`, veri `data/`, sahte ev klasörü `home/`.
Gerçek kasaya, `~/.secondbrain`'e, şifre kasasına, takvime ya da Tailscale'e DOKUNMAZ.

Kullanım:
  python tools/demo_vault.py build            # demo kasasını (yeniden) kurar; yalnız kendi demo klasörünü siler
  python tools/demo_vault.py setup-serve --sandbox <klasör>   # kurulum paneli (deneme kipi; telefon adımı uydurma)
  python tools/demo_vault.py serve --port 8799 [--scripted]   # asistanı demo kasasıyla başlatır (Ctrl+C ile durur)

`serve`, `sb chat` ile aynı işleyiciyi (sb.chat.make_handler) kullanır; `sb chat --port` ise gerçek takvim
anahtarını okuyan hatırlatma döngüsünü ve Tailscale dinleyicisini de başlattığı için demo için kullanılmaz.
`--scripted`: model yerine hazır senaryo cevapları (yalnız onay kartı görüntüsü için).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[1]
FORBIDDEN = ("sa" "met", "ko" "ca", "ko" "caeli", "all" "craft", "cull" "inan", "ko" "ca" "sa" "met")


def demo_root() -> Path:
    return Path(os.environ.get("SB_DEMO_ROOT") or Path(tempfile.gettempdir()) / "sb-demo")


def _d(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def _note(type_: str, status: str, tags: list[str], title: str, body: str, due: str | None = None, **extra) -> str:
    t = date.today().isoformat()
    fm = {"type": type_, "status": status, "tags": "[" + ", ".join(tags) + "]", "source": "manual", "source_id": "",
          "created": t, "updated": t, "due": due or ""}
    fm.update(extra)
    head = "\n".join(f"{k}: {v}" for k, v in fm.items())
    return f"---\n{head}\n---\n# {title}\n\n{body.strip()}\n"


def notes() -> dict[str, str]:
    """Göreli yol → içerik. Hepsi uydurma."""
    n: dict[str, str] = {}
    n["10-Dersler/BIL201 Veri Yapıları/BIL201 Veri Yapıları.md"] = _note(
        "ders", "aktif", ["ders"], "BIL201 Veri Yapıları",
        "Bağlı listeler, yığın, kuyruk ve ağaçlar. Hoca: Dr. Elif Arslan.\n\n## Notlar\n- Dizi ile bağlı liste arasındaki ekleme maliyeti farkı.\n- İkili arama ağacında dengesizlik sorunu.",
        code="BIL201", semester="2026-Guz", instructor="Dr. Elif Arslan")
    n["10-Dersler/MAT101 Analiz I/MAT101 Analiz I.md"] = _note(
        "ders", "aktif", ["ders"], "MAT101 Analiz I",
        "Limit, süreklilik, türev. Haftalık alıştırma kâğıdı var.\n\n## Notlar\n- L'Hôpital kuralı örnekleri.",
        code="MAT101", semester="2026-Guz", instructor="Prof. Murat Kaplan")
    n["10-Dersler/BIL201 Veri Yapıları/Ödev 2 - Bağlı Liste.md"] = _note(
        "teslim", "acik", ["teslim"], "BIL201 Ödev 2 - Bağlı Liste",
        "Çift yönlü bağlı liste gerçekle ve birim testlerini yaz.\n\n- [ ] Ekleme/silme\n- [ ] Testler\n- [ ] Rapor",
        due=_d(3), kind="odev", due_time="23:59", course="[[BIL201 Veri Yapıları]]")
    n["10-Dersler/MAT101 Analiz I/Ara Sınav.md"] = _note(
        "teslim", "acik", ["teslim"], "MAT101 Ara Sınav",
        "Konular: limit, süreklilik, türev uygulamaları. Formül kâğıdı serbest.",
        due=_d(9), kind="sinav", due_time="10:30", course="[[MAT101 Analiz I]]")
    n["20-Projeler/Mahalle Kütüphanesi Uygulaması.md"] = _note(
        "proje", "aktif", ["proje"], "Mahalle Kütüphanesi Uygulaması",
        "## Amaç\nMahalle kütüphanesinde ödünç alma kayıtlarını tutan küçük bir web uygulaması.\n\n## Durum\nEkran tasarımları bitti, ödünç alma akışı yazılıyor.\n\n## Kararlar\n- Veritabanı olarak SQLite seçildi (kurulum gerektirmiyor).\n\n## Yapılacaklar\n- [ ] Üye kaydı ekranı\n- [ ] Gecikme hatırlatması",
        due=_d(21), area="yazilim")
    n["20-Projeler/Bahçe Sulama Sensörü.md"] = _note(
        "proje", "beklemede", ["proje"], "Bahçe Sulama Sensörü",
        "## Amaç\nToprak nemine göre sulamayı açıp kapatan küçük bir devre.\n\n## Durum\nParçalar sipariş edildi, kargo bekleniyor.\n\n## Kararlar\n- Nem sensörü kapasitif tipte olacak.",
        area="donanim")
    people = [
        ("Ayşe Yılmaz", "Kullanıcı", "Öğrenci", "kendisi"),
        ("Mehmet Demir", "Örnek Yazılım A.Ş.", "Yazılım mühendisi", "staj mentoru"),
        ("Elif Arslan", "Örnek Üniversitesi", "Öğretim görevlisi", "BIL201 hocası"),
        ("Murat Kaplan", "Örnek Üniversitesi", "Profesör", "MAT101 hocası"),
        ("Zeynep Çelik", "", "Öğrenci", "proje arkadaşı"),
        ("Can Aydın", "Örnek Kütüphane Derneği", "Gönüllü", "kütüphane projesi paydaşı"),
    ]
    for name, company, role, rel in people:
        n[f"60-Kişiler/{name}.md"] = _note(
            "kisi", "aktif", ["kisi"], name,
            f"## Bağlam\n{rel.capitalize()}.\n\n## Beyan\n- Kendisi iletişimi e-posta ile tercih ettiğini söyledi.\n\n## Çıkarım (onay bekliyor)\n- Hafta içi akşamları daha rahat ulaşılıyor olabilir.",
            company=company, role=role, relation=rel, email="ornek@example.com" if name != "Ayşe Yılmaz" else "")
    n["40-Kaynaklar/Kavramlar/Bağlı liste ve dizi farkı.md"] = _note(
        "kaynak", "aktif", ["kavram"], "Bağlı liste ve dizi farkı",
        "Dizi bellekte ardışıktır, indekse göre erişim O(1). Bağlı listede araya ekleme O(1) ama erişim O(n).\n\nBaşlık ilişkisi: [[BIL201 Veri Yapıları]].")
    n["40-Kaynaklar/Kavramlar/Aralıklı tekrar.md"] = _note(
        "kaynak", "aktif", ["kavram"], "Aralıklı tekrar",
        "Bir konuyu giderek açılan aralıklarla tekrar etmek: 1 gün, 3 gün, 7 gün, 21 gün. Sınav haftasına yığmaktan daha kalıcı.")
    n["40-Kaynaklar/Kavramlar/Türev ve eğim.md"] = _note(
        "kaynak", "aktif", ["kavram"], "Türev ve eğim",
        "Bir fonksiyonun bir noktadaki türevi, o noktadaki teğetin eğimidir. İlgili ders: [[MAT101 Analiz I]].")
    n[f"50-Günlük/{_d(0)}.md"] = _note(
        "gunluk", "acik", ["gunluk"], _d(0),
        "- Sabah: Veri Yapıları ödevine başladım, ekleme fonksiyonu çalışıyor.\n- Öğleden sonra: Zeynep ile kütüphane uygulamasının ekranlarını gözden geçirdik.\n- Akşam: Analiz alıştırmalarından 6 soru çözdüm.")
    n["20-Projeler/Mahalle Kütüphanesi Uygulaması Toplantı.md"] = _note(
        "gorusme", "planlandi", ["gorusme"], "Kütüphane projesi toplantısı",
        "Gündem: ödünç alma akışı demosu. Katılımcılar: Can Aydın, Zeynep Çelik.", due=_d(5))
    n["Dashboard.md"] = "---\ntype: dashboard\n---\n# Pano\n\nHoş geldin. Yaklaşan teslimler ve açık işler burada görünür.\n"
    return n


MAILS = [
    ("main", "Ödev 2 için son hatırlatma", "Elif Arslan", "ornek@example.com", "okul", "Merhaba, BIL201 Ödev 2 teslimi için son günler. Sorusu olan ofis saatinde uğrasın."),
    ("main", "Staj görüşmesi için uygun saatler", "Mehmet Demir", "ornek@example.com", "kariyer", "Merhaba Ayşe, staj görüşmesi için perşembe ya da cuma öğleden sonra uygunum."),
    ("main", "Kütüphane projesi: ekran taslakları", "Can Aydın", "ornek@example.com", "kisisel", "Taslakları ekte gönderdim. Üye kartı ekranı için fikirlerini bekliyorum."),
    ("main", "Analiz I ara sınav yeri", "Murat Kaplan", "ornek@example.com", "okul", "Ara sınav B-204 numaralı derslikte, formül kâğıdı serbest."),
    ("main", "Sipariş kargoya verildi", "Örnek Elektronik", "ornek@example.com", "finans", "Siparişiniz kargoya verildi. Tahmini teslim: 3 iş günü."),
    ("main", "Hackathon başvurusu açıldı", "Örnek Kulüp", "ornek@example.com", "basvuru-yarisma", "Üniversiteler arası yazılım maratonu için başvurular açıldı. Son tarih ayın 20'si."),
    ("main", "Haftalık bülten", "Örnek Bülten", "ornek@example.com", "kisisel", "Bu hafta okunacaklar: bağlı listeler, aralıklı tekrar teknikleri."),
    ("main", "Fatura bilgilendirmesi", "Örnek İnternet", "ornek@example.com", "finans", "Aylık fatura tutarınız hazır. Son ödeme tarihi önümüzdeki hafta."),
    ("sms", "Kargo kodu", "Örnek Kargo", "", "finans", "Kargonuz dağıtıma çıktı. Teslim kodu: 4821."),
    ("sms", "Toplantı hatırlatma", "Zeynep Çelik", "", "kisisel", "Yarın 15:00'te kütüphane projesi için kısa bir görüşme yapalım mı?"),
]

CONVS = [
    ("demo-hafta", "Bu hafta neler var?", [
        ("user", "Bu hafta neler var?"),
        ("assistant", "Bu hafta iki teslim görünüyor: BIL201 Ödev 2 (3 gün sonra, 23:59) ve MAT101 Ara Sınav (9 gün sonra, 10:30). Kütüphane projesi toplantısı da 5 gün sonra planlı.")]),
    ("demo-bagli-liste", "Bağlı liste ile dizi farkı", [
        ("user", "Bağlı liste ile dizi arasındaki fark neydi?"),
        ("assistant", "Dizide bellek ardışıktır ve indeksle erişim O(1); bağlı listede araya ekleme O(1) ama erişim O(n). Notun: Bağlı liste ve dizi farkı.")]),
    ("demo-staj", "Staj görüşmesi", [
        ("user", "Mehmet Demir'e staj görüşmesi için ne yazmıştım?"),
        ("assistant", "Mehmet Demir, görüşme için perşembe ya da cuma öğleden sonra uygun olduğunu yazmış. Henüz cevaplamamışsın.")]),
]

PROFILE = """name: Ayşe
full_name: Ayşe Yılmaz
bio: "Örnek Üniversitesi Bilgisayar Mühendisliği öğrencisi"
timezone: Europe/Istanbul
language: tr
github_user: ""
workspace: ~/Projects
important_mail_categories: [okul, basvuru-yarisma, kariyer, is, kisisel, finans]
lms: {}
"""
ACCOUNTS = "google:\n  main:\n    email: ornek@example.com\n    source: gmail-main\n    scopes: [gmail, calendar]\nimap: {}\n"
LLM = """tasks:
  answer: ollama
  chat: ollama
  sessions: ollama
  extract_dates: ollama
  inbox: ollama
  capture: ollama
  flush: ollama
  worker: ollama
  cluster: ollama
fallback_to_local: true
ollama:
  host: http://localhost:11434
  model: qwen3:4b
  num_ctx: 8192
  max_chars: 20000
  max_confidence: 0.79
  vision_model: ""
"""


def demo_env(root: Path | None = None) -> dict[str, str]:
    root = root or demo_root()
    env = dict(os.environ)
    home = root / "home"
    env.update({"SB_VAULT": str(root / "SecondBrain"), "SB_DATA": str(root / "data"), "SB_NO_HOOK": "1",
                "USERPROFILE": str(home), "HOME": str(home), "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    for k in ("SB_SETUP_SANDBOX",):
        env.pop(k, None)
    return env


def build(root: Path | None = None) -> Path:
    """Demo kasasını kurar. Yalnız `root` (varsayılan %TEMP%\\sb-demo) altındaki kendi klasörlerini yeniden oluşturur."""
    root = (root or demo_root()).resolve()
    if root.name != "sb-demo" and not os.environ.get("SB_DEMO_ROOT"):
        raise SystemExit("demo kökü beklenmedik: " + str(root))
    vault, data = root / "SecondBrain", root / "data"
    for d in (vault, data, root / "home"):                      # yalnız demo klasörleri
        if d.exists():
            shutil.rmtree(d)
    for rel, text in notes().items():
        p = vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    cfg = vault / "_system" / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "profile.yaml").write_text(PROFILE, encoding="utf-8")
    (cfg / "accounts.yaml").write_text(ACCOUNTS, encoding="utf-8")
    (cfg / "llm.yaml").write_text(LLM, encoding="utf-8")
    (root / "home").mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    _mail_db(data / "mail.db")
    _convs(data)
    return root


def _mail_db(path: Path) -> None:
    sys.path.insert(0, str(SYSTEM))
    from sb import maildb
    con = maildb.connect(path)
    now = datetime.now()
    for i, (acc, subj, name, addr, cat, body) in enumerate(MAILS):
        maildb.insert(con, {"account": acc, "id": f"demo-{i}", "thread_id": f"t{i}", "date_ms": int((now - timedelta(hours=7 * i + 2)).timestamp() * 1000),
                            "from_addr": addr, "from_name": name, "to_addrs": "ornek@example.com", "cc_addrs": "", "subject": subj,
                            "snippet": body[:90], "body": body, "labels": [], "attachments": [], "category": cat, "category_src": "rule"})
    con.commit()
    con.close()


def _convs(data: Path) -> None:
    d = data / "convs"
    d.mkdir(parents=True, exist_ok=True)
    base = datetime.now().replace(microsecond=0)
    for i, (sid, title, msgs) in enumerate(CONVS):
        t = (base - timedelta(hours=3 * (i + 1))).isoformat()
        ms = [{"id": f"m{sid}{j}", "role": r, "text": x, "ts": t} for j, (r, x) in enumerate(msgs)]
        (d / f"{sid}.json").write_text(json.dumps({"sid": sid, "title": title, "created": t, "updated": t, "pinned": i == 0,
                                                   "archived": False, "messages": ms}, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ demo asistan sunucusu
class _FakeCal:
    """Ağ yok: takvim boş döner; ekleme/silme çağrıları hata verir (demoda onaylanmaz)."""
    cal = "demo"

    def list_events(self, start, end):
        return []

    def __getattr__(self, name):
        raise RuntimeError("demo takvimi salt okunur")


def _scripted_chat(messages, cfg):
    last = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    if any(m.get("role") == "tool" for m in messages[-2:]):
        return {"role": "assistant", "content": "Hazır: yarın 15:00 için «Kütüphane projesi görüşmesi» etkinliğini onayına sundum. Onayla'ya basarsan takvime eklenir."}
    if "takvim" in last.lower() or "ekle" in last.lower():
        return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "calendar_add", "arguments": {
            "tag": "GÖRÜŞME", "title": "Kütüphane projesi görüşmesi", "date": "yarın", "time": "15:00", "duration_min": 45}}}]}
    return {"role": "assistant", "content": "Bu hafta BIL201 Ödev 2 (3 gün sonra) ve MAT101 Ara Sınav (9 gün sonra) var."}


def serve(port: int, scripted: bool = False) -> None:
    root = demo_root()
    for k, v in demo_env(root).items():
        os.environ[k] = v
    sys.path.insert(0, str(SYSTEM))
    from http.server import ThreadingHTTPServer
    from sb import chat
    chat.ALLOWED_HOSTS.update({f"127.0.0.1:{port}", f"localhost:{port}"})
    chat.ALLOWED_ORIGINS.update({f"http://127.0.0.1:{port}", f"http://localhost:{port}"})
    kw = {"chat_fn": _scripted_chat} if scripted else {}
    srv = ThreadingHTTPServer(("127.0.0.1", port), chat.make_handler(calendar=_FakeCal(), **kw))
    print(f"Demo asistan hazır: http://127.0.0.1:{port}/", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def fake_phone_info(port: int = 8765) -> dict:
    """Telefon adımı için UYDURMA durum: gerçek asistana (8765) ve gerçek Tailscale'e hiç bağlanılmaz."""
    return {"installed": True, "connected": True, "ip": "100.64.0.7", "address": "http://100.64.0.7:8799",
            "pairing_code": "123456", "devices": 0, "assistant_running": True}


def setup_serve(sandbox: str) -> None:
    """Kurulum panelini deneme kipinde başlatır; gerçek asistana/Tailscale'e bakan telefon uç noktasını uydurma veriyle değiştirir.
    İlk satıra panel adresini (jetonlu) yazar."""
    root = demo_root()
    for k, v in demo_env(root).items():
        os.environ[k] = v
    os.environ["SB_SETUP_SANDBOX"] = str(Path(sandbox).resolve())
    sys.path.insert(0, str(SYSTEM))
    from setup import accounts as A
    from setup import server
    A.phone_info = fake_phone_info
    srv = server.make_server(sandbox=sandbox)
    print(srv.url, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def main(argv=None) -> int:
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8799)
    s.add_argument("--scripted", action="store_true")
    t = sub.add_parser("setup-serve")
    t.add_argument("--sandbox", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        print(build())
        return 0
    if a.cmd == "setup-serve":
        setup_serve(a.sandbox)
        return 0
    if a.port == 8765:
        raise SystemExit("8765 gerçek asistanın portu; demo için başka port kullan")
    serve(a.port, a.scripted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
