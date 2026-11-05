"""ÜNİ UZEM EDS (uzem.universite.edu.tr/eds.php): dersler, haftalık konular, ders dosyaları.

Aşama 1 — KEŞİF (`python -m sb.uzem probe`): giriş yapar, menüdeki ve ders sayfalarındaki bağlantıları SALT OKUNUR gezer,
ham HTML'i `~/.secondbrain/work/uzem-probe/` altına kaydeder (kasa ve git dışı). Dosya İNDİRMEZ, hiçbir şeyi değiştirmez
(yalnız GET; çıkış/silme/kayıt gibi bağlantıları atlar). Şifre yalnız bellekte tutulur, hiçbir yere yazılmaz ya da yazdırılmaz.

Kimlik: `config/accounts.yaml` `school.user` (öğrenci no) + işletim sistemi anahtarlığında `svc-school-password` (sihirbazın «Okul» adımı).
"""
from __future__ import annotations

import html as _html
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://uzem.universite.edu.tr"
LOGIN_PATH = "/eds.php"
UA = "SecondBrain/0.15 (kisisel kullanim; salt okunur)"
DELAY = 0.7                                         # istekler arası bekleme (sunucuyu yormamak için)
MAX_PAGES = 40
# Gezilmeyecek bağlantılar: oturum kapatma, silme/değiştirme, kayıt, e-posta, dosya indirme.
SKIP_LINK = re.compile(r"(cikis|logout|signout|sil\b|silme|delete|remove|kaydet|gonder|mailto:|javascript:|#|tel:)", re.I)
FILE_EXT = re.compile(r"\.(pdf|zip|rar|7z|docx?|pptx?|xlsx?|mp4|mp3|mov|avi|ipynb|py|c|cpp|java|txt|csv|png|jpe?g|gif)(\?|$)", re.I)


class UzemError(Exception):
    pass


def credentials() -> tuple[str, str]:
    """(öğrenci no, şifre). Eksikse açıklayıcı hata; şifre ASLA hata mesajına girmez."""
    from . import config
    school = (config.accounts() or {}).get("school") or {}
    user = str(school.get("user") or "").strip()
    try:
        import keyring
        pw = keyring.get_password(config.KEYRING_SERVICE, "svc-school-password") or ""
    except Exception:                                # noqa: BLE001
        pw = ""
    if not user or not pw:
        raise UzemError("Okul girişi eksik: kurulum sihirbazının «Okul» adımında öğrenci numarası ve şifre kaydedilmeli "
                        "(`sb set-secret svc-school-password`).")
    return user, pw


def _opener(base: str, extra_handlers: tuple = ()):
    jar = http.cookiejar.CookieJar()
    handlers: list = [urllib.request.HTTPCookieProcessor(jar), *extra_handlers]
    if base.startswith("https://"):
        import ssl
        try:
            import truststore                         # işletim sistemi sertifika deposu (eksik ara sertifikayı tamamlar)
            ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except ImportError:
            ctx = ssl.create_default_context()
        handlers.append(urllib.request.HTTPSHandler(context=ctx))          # sertifika DOĞRULAMASI açık kalır
    op = urllib.request.build_opener(*handlers)
    op.addheaders = [("User-Agent", UA), ("Accept-Language", "tr,en;q=0.8")]
    return op


def _get(op, url: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        with op.open(url, timeout=timeout) as r:
            raw = r.read(5_000_000)
            ctype = r.headers.get("Content-Type", "")
            enc = re.search(r"charset=([\w-]+)", ctype)
            return r.status, raw.decode(enc.group(1) if enc else "utf-8", "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, "", url


def login(op, base: str, user: str, pw: str) -> str:
    """Giriş formunu gönderir; başarılıysa giriş sonrası ilk sayfanın HTML'ini döner. Başarısızsa UzemError."""
    st, page, _ = _get(op, base + LOGIN_PATH)
    if st != 200 or "parola" not in page:
        raise UzemError(f"UZEM giriş sayfası beklenen biçimde değil (durum {st}).")
    if re.search(r"recaptcha|hcaptcha|turnstile|g-recaptcha", page, re.I):
        raise UzemError("UZEM giriş sayfasında CAPTCHA çıktı; otomatik giriş yapılmaz. Tarayıcıdan gir.")
    data = urllib.parse.urlencode({"ogrno": user, "parola": pw}).encode()
    req = urllib.request.Request(base + LOGIN_PATH, data=data, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": base + LOGIN_PATH})
    try:
        with op.open(req, timeout=30) as r:
            body = r.read(5_000_000).decode("utf-8", "replace")
            status, final = r.status, r.geturl()
    except urllib.error.HTTPError as e:
        raise UzemError(f"UZEM giriş isteği reddedildi (durum {e.code}).") from None
    if not _logged_in(page, body):
        raise UzemError("UZEM girişi başarısız: öğrenci numarası ya da şifre kabul edilmedi (ÖBS şifresiyle aynı olmalı). "
                        "Çok denemeyi önlemek için tekrar denenmedi. Sunucu yanıtı: " + _diagnostic(body, status, final, user, pw))
    return body


ERROR_WORDS = re.compile(r"hatal[ıi]|yanl[ıi]ş|geçersiz|başarısız|kabul edilme|bulunamad[ıi]|kilitl", re.I)


def _visible_words(html: str) -> set[str]:
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t))
    return set(re.findall(r"[\wçğıöşüÇĞİÖŞÜ]{3,}", t.lower()))


def _logged_in(login_page: str, response: str) -> bool:
    """Giriş sonrası sayfada da bir şifre alanı olabilir («Bilgileri Tekrar Gir» paneli); bu yüzden alan varlığına bakılmaz.
    Başarı = yanıt, giriş sayfasında olmayan yeterince yeni sözcük taşıyor (ad soyad, ders adları…) ve hata sözcüğü yok."""
    if ERROR_WORDS.search(re.sub(r"<(script|style)\b.*?</\1>", " ", response, flags=re.S | re.I)):
        return False
    return len(_visible_words(response) - _visible_words(login_page)) >= 4


def _diagnostic(body: str, status: int, final_url: str, user: str, pw: str) -> str:
    """Başarısız girişte sunucunun söylediği (form dışı görünen metin). Şifre ve numara olduğu gibi çıkarılır."""
    text = re.sub(r"<(script|style|form)\b.*?</\1>", " ", body, flags=re.S | re.I)
    text = _html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text).strip()
    for secret in (pw, user):
        if secret:
            text = text.replace(secret, "***")
    msgs = re.findall(r"[^.!?]{0,80}(?:hatal[ıi]|yanl[ıi]ş|geçersiz|bulunamad[ıi]|engel|kilit|deneme)[^.!?]{0,80}", text, re.I)
    shown = " | ".join(m.strip() for m in msgs[:3]) or text[:160] or "(form dışında görünen bir mesaj yok)"
    return f"durum {status}, adres {final_url.split('?')[0]}, metin: «{shown[:240]}»"


TRUSTED_SUFFIX = ".universite.edu.tr"                  # giriş anahtarı yalnız okulun kendi sunucularına gider


def trusted(url: str, extra_hosts: tuple[str, ...] = ()) -> bool:
    p = urllib.parse.urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme in ("http", "https") and (host.endswith(TRUSTED_SUFFIX) or p.netloc in extra_hosts)


def mask_url(url: str) -> str:
    """Kayıt/çıktıda adresteki uzun değerleri (tek kullanımlık giriş anahtarı, jeton) gizler: `t=<64 krkt>`."""
    p = urllib.parse.urlsplit(url)
    q = "&".join(f"{k}={v if len(v) <= 8 else '<' + str(len(v)) + ' krkt>'}" for k, v in urllib.parse.parse_qsl(p.query))
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, q, ""))


def sso_course_links(html: str, base_url: str, extra_hosts: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    """eds.php'nin ürettiği ders giriş bağlantıları: `<moodle>/login/index.php?u=…&ts=…&ip=…&t=…&course=<id>` → [(ders_id, adres)].
    Bağlantılar tek kullanımlıktır, zaman ve IP'ye bağlıdır; yalnız okulun sunucularına (`*.universite.edu.tr`) yönelenler alınır."""
    out, seen = [], set()
    for m in re.finditer(r'<a\b[^>]*?href=["\']([^"\']+)["\']', html, re.I):
        url = urllib.parse.urljoin(base_url, _html.unescape(m.group(1)).strip())
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        if "/login/index.php" not in url or "course" not in q or "t" not in q or not trusted(url, extra_hosts):
            continue
        if q["course"] not in seen:
            seen.add(q["course"])
            out.append((q["course"], url))
    return out


def links(html: str, base_url: str) -> list[tuple[str, str]]:
    """(metin, mutlak adres) listesi; aynı sunucu, tekrarsız."""
    host = urllib.parse.urlparse(base_url).netloc
    out, seen = [], set()
    for m in re.finditer(r'<a\b[^>]*?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href = _html.unescape(m.group(1)).strip()
        text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
        if not href or SKIP_LINK.search(href) or SKIP_LINK.search(text):
            continue
        url = urllib.parse.urljoin(base_url, href).split("#")[0]
        if urllib.parse.urlparse(url).netloc != host or url in seen:
            continue
        seen.add(url)
        out.append((text, url))
    return out


def probe(base: str = BASE, out_dir: Path | None = None, user: str | None = None, pw: str | None = None,
          max_pages: int = MAX_PAGES, delay: float = DELAY, extra_hosts: tuple[str, ...] = ()) -> dict:
    """Giriş yap; ana sayfayı, oradan açılan sayfaları ve her dersin Moodle sayfasını (ders giriş bağlantısıyla) HTML olarak
    kaydet. Dosya indirmez, hiçbir şeyi değiştirmez (yalnız GET). Özet döner (şifresiz, anahtarsız)."""
    from . import config
    out = Path(out_dir) if out_dir else Path(config.DATA) / "work" / "uzem-probe"
    out.mkdir(parents=True, exist_ok=True)
    if user is None or pw is None:
        user, pw = credentials()
    op = _opener(base)
    login_html = _get(op, base + LOGIN_PATH)[1]
    landing = login(op, base, user, pw)
    pages: list[dict] = []

    def save(name: str, url: str, body: str, status: int, text: str = "") -> None:
        fn = f"{len(pages):02d}-{re.sub(r'[^a-z0-9]+', '-', name.lower())[:40].strip('-') or 'sayfa'}.html"
        (out / fn).write_text(body, encoding="utf-8")
        pages.append({"file": fn, "url": mask_url(url), "text": text, "status": status, "bytes": len(body.encode("utf-8"))})

    save("giris-sonrasi", base + LOGIN_PATH, landing, 200, "giriş sonrası ilk sayfa")
    courses: list[dict] = []
    for cid, sso in sso_course_links(landing, base + LOGIN_PATH, extra_hosts):
        if len(pages) >= max_pages:
            break
        time.sleep(delay)
        st, body, final = _get(op, sso)
        ok = st == 200 and bool(body) and "/course/view.php" in final and 'id="login"' not in body
        courses.append({"ders_id": cid, "durum": st, "acildi": ok, "adres": mask_url(final)})
        if ok:
            save(f"ders-{cid}", final, body, st, f"Moodle dersi {cid}")
    todo = links(landing, base + LOGIN_PATH)
    files = [(t, u) for t, u in todo if FILE_EXT.search(u)]
    todo = [(t, u) for t, u in todo if not FILE_EXT.search(u)]
    seen: set[str] = set()
    for text, url in todo:
        if len(pages) >= max_pages:
            break
        if url in seen:
            continue
        seen.add(url)
        time.sleep(delay)
        st, body, final = _get(op, url)
        if st == 200 and body:
            save(text or "sayfa", final, body, st, text)
            if 'name="ogrno"' in body and not _logged_in(login_html, body):      # oturum düştü (giriş sayfasına döndü)
                raise UzemError("UZEM oturumu gezinirken düştü; keşif durduruldu.")
    index = {"base": base, "pages": pages, "dersler": courses,
             "bulunan_dosya_baglantilari": [{"text": t, "url": mask_url(u)} for t, u in files][:200]}
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"klasor": str(out), "sayfa": len(pages), "dosya_baglantisi": len(files),
            "ders_acilan": sum(1 for c in courses if c["acildi"]), "ders_toplam": len(courses),
            "menu": [p["text"] for p in pages[1:41] if p["text"]]}


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "probe":
        print("kullanım: python -m sb.uzem probe")
        return 2
    try:
        res = probe()
    except UzemError as e:
        print(f"HATA: {e}")
        return 1
    print(f"Tamam: {res['sayfa']} sayfa kaydedildi → {res['klasor']}")
    print(f"Moodle dersleri: {res['ders_acilan']} / {res['ders_toplam']} açıldı")
    print(f"Dosya bağlantısı (indirilmedi): {res['dosya_baglantisi']}")
    if res["menu"]:
        print("Gezilen bölümler:\n  " + "\n  ".join(res["menu"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
