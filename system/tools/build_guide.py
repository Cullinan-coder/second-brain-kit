"""Kullanıcı rehberi üretici: manifestlerden (module/source/mcp/sector/presets/categories) + features.yaml'dan sayfalar üretir.

Çıktı: `docs/rehber/` (Markdown). Elle yazılan bölümler `docs/rehber-src/*.md` aynı klasöre kopyalanır; üretilen sayfalar:
  15-hazir-secimler · 16-moduller (+ moduller/<id>) · 17-ozellik-katalogu (250 madde) · 18-veri-kaynaklari (+ kaynaklar/<id>)
  19-mcp-katalogu (+ mcp/<id>) · 20-sektor-paketleri · 21-ne-ister · README (içindekiler).

Kullanım (``_system`` klasöründen):
    python tools/build_guide.py            # docs/rehber/ yeniden üretilir
    python tools/build_guide.py --check    # yazmaz; eksik madde/sayfa/bağlantı, sır benzeri metin ya da bayat çıktı varsa 1 döner
Üretici deterministiktir (zaman damgası, rastgelelik yok) ve ağa çıkmaz.
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

CODE = Path(__file__).resolve().parent.parent
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from sb import plugins as P  # noqa: E402

SRC = CODE / "docs" / "rehber-src"
OUT = CODE / "docs" / "rehber"
FEATURES = CODE / "features.yaml"

# Elle yazılan sayfalar (rehber-src) — hepsi bulunmalı.
HAND_PAGES = [
    "00-baslangic", "01-kurulum", "02-sihirbaz-adim-adim", "03-hesaplar", "04-api-anahtarlari", "05-modeller-ses",
    "06-mcp", "07-veri-yukleme", "08-uygulama-turu", "09-asistan-kullanimi", "10-guvenlik-gizlilik", "11-sorun-giderme",
    "12-sss", "13-sozluk", "14-komut-referansi",
]
GEN_TOP = ["15-hazir-secimler", "16-moduller", "17-ozellik-katalogu", "18-veri-kaynaklari", "19-mcp-katalogu",
           "20-sektor-paketleri", "21-ne-ister"]

ACCOUNT_NAME = {
    "google": "Google", "imap": "E-posta (IMAP)", "outlook": "Outlook", "icloud": "iCloud", "github": "GitHub",
    "telegram": "Telegram", "spotify": "Spotify", "tailscale": "Tailscale", "openai": "OpenAI", "anthropic": "Anthropic",
    "gemini": "Gemini", "openrouter": "OpenRouter", "groq": "Groq", "deepseek": "DeepSeek", "mistral": "Mistral",
    "school": "Okul (ÖBS / LMS)", "notion": "Notion", "slack": "Slack", "atlassian": "Atlassian (Jira)", "linear": "Linear",
    "brave": "Brave Search", "sentry": "Sentry", "figma": "Figma", "whatsapp": "WhatsApp", "linkedin": "LinkedIn",
}
# hesap türü → rehber sayfası (üretilen sayfalardan göreli değil, kök göreli; rel() ile çevrilir)
ACCOUNT_LINK = {
    "google": "03-hesaplar.md#hesap-google", "imap": "03-hesaplar.md#hesap-imap", "outlook": "03-hesaplar.md#hesap-outlook",
    "icloud": "03-hesaplar.md#hesap-icloud", "github": "03-hesaplar.md#hesap-github", "telegram": "03-hesaplar.md#hesap-telegram",
    "spotify": "03-hesaplar.md#hesap-spotify", "tailscale": "03-hesaplar.md#hesap-tailscale", "school": "03-hesaplar.md#hesap-okul",
    "whatsapp": "03-hesaplar.md#hesap-whatsapp", "linkedin": "03-hesaplar.md#hesap-linkedin",
    "openai": "04-api-anahtarlari.md#anahtar-openai", "anthropic": "04-api-anahtarlari.md#anahtar-anthropic",
    "gemini": "04-api-anahtarlari.md#anahtar-gemini", "openrouter": "04-api-anahtarlari.md#anahtar-openrouter",
    "groq": "04-api-anahtarlari.md#anahtar-groq", "deepseek": "04-api-anahtarlari.md#anahtar-deepseek",
    "mistral": "04-api-anahtarlari.md#anahtar-mistral",
    "notion": "mcp/notion.md", "slack": "mcp/slack.md", "atlassian": "mcp/atlassian.md", "linear": "mcp/linear.md",
    "brave": "mcp/brave-search.md", "sentry": "mcp/sentry.md", "figma": "mcp/figma.md",
}
KIND_TR = {"text": "metin", "path": "dosya ya da klasör yolu", "email": "e-posta adresi", "secret": "gizli değer (yalnız şifre kasasına yazılır)",
           "url": "web adresi", "bool": "aç/kapa", "choice": "seçim", "number": "sayı"}
STATUS_TR = {"tamamlandi": "hazır", "planlandi": "planlandı (henüz yok)", "yapiliyor": "yapım aşamasında (kısmen)", "ertelendi": "ertelendi"}
HW_TR = {"gpu_vram_gb": "ekran kartı belleği (VRAM)", "ram_gb": "bellek (RAM)", "sensor": "sensör"}
AXIS_TR = {"meslek": "Meslek", "donanim": "Donanım", "gizlilik": "Gizlilik", "yogunluk": "Yoğunluk"}

# Modül → asistan/uygulama ekranları (başlıklar sb/web/*.js registerView çağrılarından)
MODULE_VIEWS = {
    "courses": ["Dersler", "Çalışma planı"], "career": ["Kariyer", "Çalışma araçları"],
    "automation": ["Otomasyonlar", "Ajanlar", "Ajan izleme"], "comms": ["İletişim", "Taslaklar"],
    "memory_ui": ["Hafıza", "Ortak günlük"], "life": ["Yaşam"], "tasks_plan": ["Bugün planı", "Görev panosu"],
    "privacy": ["Gizlilik"], "cards": ["Bilgi kartları"],
    "ui_core": ["Pano", "Bilgi grafı", "Zaman çizelgesi", "Kişi", "Proje", "Ayarlar", "Hata panosu", "Öğrenme yolları"],
    "setup": ["Çalışmaya başla", "Uygulama ayarları"], "inbox": ["İletişim"], "brain": ["Bilgi grafı"],
    "contacts": ["Kişi"], "projects": ["Proje"], "phone": ["Telefon eşleme (üst çubuktaki telefon simgesi)"],
    "assistant": ["Sohbet ekranı (ana pencere)"], "voice": ["Sohbet kutusundaki mikrofon düğmesi", "Ayarlar (Cevapları sesli oku, Ses)"],
    "wake_word": ["Ayarlar (Uyandırma sözcüğü kutusu)"], "models": ["Uygulama ayarları → Modeller sekmesi"],
    "capture": ["Gönder menüsü → Beyne At; Ctrl+Alt+B"], "vision": ["Sohbet: «ekranımda ne var?» gibi istekler"],
    "pano": ["Kopya geçmişi (Görünümler menüsü; kısayol: /)"],
    "gmail": ["İletişim", "Pano"], "calendar": ["Pano (Bugün)", "Bugün planı"], "dates": ["Pano (Onay bekleyen)"],
}
# Modül → ek komutlar (sb --help çıktısından; STEP_MODULE'den gelenlere eklenir)
MODULE_CMDS = {
    "gmail": ["login", "mail-fetch", "mail-ics-backfill", "mail-categorize", "mail-index"], "imap": ["mail-fetch"],
    "calendar": ["sync-gcal", "import-gcal", "add-event", "approve", "extract-dates"], "contacts": ["contacts-sync", "merge-people"],
    "drive": ["drive-sync", "drive-index"], "sms": ["sms-sync"], "dates": ["extract-dates", "approve", "housekeep"],
    "telegram": ["telegram"], "digest": ["daily", "weekly", "notify-test"], "voice": ["voice"], "capture": ["capture"],
    "inbox": ["inbox-process"], "assistant": ["chat", "ask", "asistan-undo"], "models": ["models", "usage", "embed-test", "qwen", "ask"],
    "claude_hooks": ["receipt", "recap", "learn", "concept", "connect", "trace", "error-log", "knowledge-index", "rule", "hygiene", "mode", "hook-flush", "task", "person"],
    "flush": ["hook-flush"], "night": ["night"], "search": ["search", "find", "answer", "similar", "search2"],
    "brain": ["index", "find", "answer", "similar", "mentions", "chat-links", "clusters", "suggest-links", "analyze", "merge-people", "graph-style"],
    "tasks_plan": ["plan", "tasks-board", "task"], "courses": ["courses", "gpa", "obs-import", "course-files", "course-deep"],
    "privacy": ["vault-encrypt", "vault-decrypt", "vault-key", "restore", "security-test"], "memory_ui": ["persona"],
    "setup": ["doctor", "update", "version", "features", "roadmap", "logs", "whatsnew"], "quality": ["perf", "logs", "e2e", "doctor"],
    "linkedin": ["linkedin-import"], "automation": ["automation-tick"], "derived": ["derive"],
    "github": ["github-deep"], "projects": ["projects-sync", "project-deep"], "local_files": ["local-files", "content-sync"],
    "sessions": ["sessions-sync"], "imports_comm": ["import"], "imports_life": ["import", "history-import", "takeout"],
    "imports_media": ["import"], "imports_notes": ["import"], "whatsapp": ["import"], "browser": ["import"],
    "pano": ["pano"], "media": [], "computer": [], "vision": [], "phone": [], "career": [], "life": [], "comms": [], "cards": [],
}


# ------------------------------------------------------------------ yardımcılar
def slug(text: str) -> str:
    """GitHub benzeri başlık bağlantısı (bağlantı denetimi için)."""
    s = text.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s, flags=re.UNICODE)
    return s.replace(" ", "-")


def rel(from_dir: str, target: str) -> str:
    """Kök göreli hedefi (ör. 'mcp/notion.md#x'), from_dir ('' ya da 'mcp') içindeki sayfadan göreli yaz."""
    return ("../" if from_dir else "") + target


def bi(v) -> str:
    return (v or {}).get("tr", "") if isinstance(v, dict) else str(v or "")


def one_line(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def esc(s: str) -> str:
    return one_line(s).replace("|", "\\|")


def step_modules() -> dict:
    for node in ast.parse((CODE / "sb" / "features.py").read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "STEP_MODULE":
            return ast.literal_eval(node.value)
    return {}


def cmd_names() -> set[str]:
    """14-komut-referansi.md içindeki `### sb <komut>` başlıkları."""
    p = SRC / "14-komut-referansi.md"
    if not p.exists():
        return set()
    return set(re.findall(r"^###\s+sb\s+([\w-]+)", p.read_text(encoding="utf-8"), re.M))


def load_features() -> tuple[dict, list[dict]]:
    d = yaml.safe_load(FEATURES.read_text(encoding="utf-8"))
    return d.get("kategoriler") or {}, d.get("ozellikler") or []


class Ctx:
    def __init__(self) -> None:
        self.modules = {m["id"]: m for m in P.all("module")}
        self.sources = {m["id"]: m for m in P.all("source")}
        self.mcps = {m["id"]: m for m in P.all("mcp")}
        self.sectors = {m["id"]: m for m in P.all("sector")}
        self.presets = P.presets()
        self.cats = P.categories()
        self.fcats, self.items = load_features()
        self.items_by_id = {i["id"]: i for i in self.items}
        self.item_module: dict[int, str] = {}
        for mid, m in self.modules.items():
            for i in m.get("catalog_ids") or []:
                self.item_module[i] = mid
        steps = step_modules()
        self.mod_cmds: dict[str, list[str]] = {}
        known = cmd_names()
        for mid in self.modules:
            lst = [c for c, mod in steps.items() if mod == mid] + MODULE_CMDS.get(mid, [])
            seen, out = set(), []
            for c in lst:
                if c not in seen and (not known or c in known):
                    seen.add(c)
                    out.append(c)
            self.mod_cmds[mid] = out


def name(m: dict) -> str:
    return bi(m.get("name"))


def mod_link(from_dir: str, mid: str) -> str:
    return f"[{name(CTX.modules[mid])}]({rel(from_dir, f'moduller/{mid}.md')})" if mid in CTX.modules else f"`{mid}`"


def acc_label(from_dir: str, a: str) -> str:
    n = ACCOUNT_NAME.get(a, a)
    return f"[{n}]({rel(from_dir, ACCOUNT_LINK[a])})" if a in ACCOUNT_LINK else n


def cmd_label(from_dir: str, c: str) -> str:
    return f"[`sb {c}`]({rel(from_dir, '14-komut-referansi.md#sb-' + c)})"


def presets_of(mid: str) -> dict[str, list[str]]:
    """Modülün hangi hazır seçimlerde açık olduğu (presets.yaml'dan) ve nerede kapatıldığı."""
    on: dict[str, list[str]] = {"yogunluk": [], "meslek": []}
    off: dict[str, list[str]] = {"donanim": [], "gizlilik": []}
    ax = CTX.presets["axes"]
    for k, v in ax["yogunluk"].items():
        if mid in (v.get("modules") or []):
            on["yogunluk"].append(bi(v["name"]))
    for k, v in ax["meslek"].items():
        if mid in (v.get("add") or []):
            on["meslek"].append(bi(v["name"]))
    for a in ("donanim", "gizlilik"):
        for k, v in ax[a].items():
            if mid in (v.get("off") or []):
                off[a].append(bi(v["name"]))
    return {**on, **off}


def requires_summary(from_dir: str, m: dict) -> str:
    r = m.get("requires") or {}
    parts = []
    if r.get("accounts"):
        parts.append("hesap: " + ", ".join(acc_label(from_dir, a) for a in r["accounts"]))
    sec = [f for f in r.get("fields") or [] if f.get("secret")]
    if sec:
        parts.append("gizli değer: " + ", ".join(f"{bi(f.get('label'))} (`{f['key']}`)" for f in sec))
    other = [f for f in r.get("fields") or [] if not f.get("secret")]
    if other:
        parts.append("alan: " + ", ".join(f"{bi(f.get('label'))} (`{f['key']}`)" for f in other))
    if r.get("hardware"):
        parts.append("donanım: " + ", ".join(f"{HW_TR.get(k, k)} ≥ {v}" + ("" if k == "sensor" else " GB") for k, v in r["hardware"].items()))
    if r.get("apps"):
        parts.append("program: " + ", ".join(r["apps"]))
    return "; ".join(parts) if parts else "ek hesap, anahtar ya da program gerekmez"


def requires_block(from_dir: str, m: dict) -> list[str]:
    r = m.get("requires") or {}
    out: list[str] = []
    if not (r.get("accounts") or r.get("fields") or r.get("hardware") or r.get("apps")):
        return ["Bu kayıt için ek hesap, anahtar ya da program gerekmez."]
    if r.get("accounts"):
        out += ["**Hesaplar:** " + ", ".join(acc_label(from_dir, a) for a in r["accounts"]), ""]
    if r.get("apps"):
        out += ["**Bilgisayarda kurulu olması gereken programlar:** " + ", ".join(r["apps"]), ""]
    if r.get("hardware"):
        out += ["**Donanım:** " + ", ".join(f"{HW_TR.get(k, k)} en az {v}" + (" GB" if k != "sensor" else "") for k, v in r["hardware"].items()
                                              if not isinstance(v, str)) + ".", ""]
    fl = r.get("fields") or []
    if fl:
        out += ["", "| Alan | Ne girilir | Zorunlu mu | Açıklama |", "|---|---|---|---|"]
        for f in fl:
            out.append(f"| {esc(bi(f.get('label')))} (`{f['key']}`) | {KIND_TR.get(f.get('kind'), f.get('kind'))} | "
                       f"{'evet' if f.get('required') else 'hayır'} | {esc(bi(f.get('help'))) or '—'} |")
    if r.get("secrets"):
        out += ["", "Gizli değerler (" + ", ".join(f"`{s}`" for s in r["secrets"]) + ") **yalnız işletim sisteminin şifre kasasına** yazılır; "
                "ayar dosyalarında, günlükte ya da bu rehberde görünmez."]
    return out


def preset_lines(mid: str) -> list[str]:
    p = presets_of(mid)
    out = []
    if p["yogunluk"]:
        out.append("- **Yoğunluk:** " + ", ".join(p["yogunluk"]) + " seçildiğinde açıktır.")
    else:
        out.append("- **Yoğunluk:** hiçbir yoğunluk seçiminde kendiliğinden açılmaz; elle açarsın.")
    if p["meslek"]:
        out.append("- **Meslek:** " + ", ".join(p["meslek"]) + " seçimlerinde ayrıca eklenir.")
    if p["donanim"]:
        out.append("- **Donanım nedeniyle kapanır:** " + ", ".join(p["donanim"]) + ".")
    if p["gizlilik"]:
        out.append("- **Gizlilik nedeniyle kapanır:** " + ", ".join(p["gizlilik"]) + ".")
    return out


# ------------------------------------------------------------------ modül sayfası
def module_page(m: dict) -> str:
    mid, d = m["id"], "moduller"
    items = [CTX.items_by_id[i] for i in m.get("catalog_ids") or [] if i in CTX.items_by_id]
    on = "açık" if m.get("default_on", True) else "kapalı (isteğe bağlı özellik)"
    cat = bi(CTX.cats.get(m["category"]))
    L = [f"# {name(m)}", "", f"> {bi(m['desc'])}", "",
         "| | |", "|---|---|",
         f"| Modül kimliği | `{mid}` |", f"| Kategori | {cat} |", f"| Varsayılan | {on} |",
         f"| Madde sayısı | {len(items)} |", f"| Ne ister | {requires_summary(d, m)} |", "",
         "## Ne işe yarar", "", f"{bi(m['desc'])}.".replace("..", "."), ""]
    if items:
        L.append(f"Bu modül özellik kataloğundan **{len(items)} maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.")
    else:
        L.append("Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.")
    L += ["", '<a id="nasil-acilir"></a>', "", "## Nasıl açılır", "",
          "1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`" + name(m) + "`) → modül kutusunu işaretle. "
          "Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.",
          "2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).",
          ]
    if m.get("module"):
        L.append(f"3. **Komutla:** `sb features --on {mid}` açar, `sb features --off {mid}` kapatır, `sb features` durumu listeler "
                 f"(bkz. {cmd_label(d, 'features')}).")
    else:
        L.append("3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.")
    if m.get("docs"):
        L.append(f"4. Ek kurulum belgesi: `{m['docs']}` (kitin `docs` klasöründe; rehberdeki karşılığı için {docs_hint(m['docs'], d)}).")
    L += ["", "## Hangi hesap, veri ya da anahtar ister", ""] + requires_block(d, m) + ["", "## Hazır seçimlerde", ""] + preset_lines(mid)
    L += ["", "Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.", "",
          "## Nasıl kullanılır", ""]
    views = MODULE_VIEWS.get(mid, [])
    cmds = CTX.mod_cmds.get(mid, [])
    if views:
        L.append("- **Ekranlar / kullanım yeri:** " + ", ".join(f"**{v}**" for v in views) + " (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).")
    else:
        L.append("- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün "
                 "([Uygulama turu](../08-uygulama-turu.md)).")
    if cmds:
        L.append("- **Komutlar:** " + ", ".join(cmd_label(d, c) for c in cmds) + " (tümü: [Komut referansı](../14-komut-referansi.md)).")
    else:
        L.append("- **Komutlar:** bu modülün kendine ait komutu yoktur; asistan ya da uygulama üzerinden çalışır.")
    L.append("- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).")
    srcs = [s for s in CTX.sources.values() if s.get("parent") == mid]
    if srcs:
        L += ["", "## Bağlı veri kaynakları", ""]
        L += [f"- [{name(s)}](../kaynaklar/{s['id']}.md): {bi(s['desc'])}" for s in srcs]
    L += ["", "## Sağlık testi", "",
          f"Çalışıp çalışmadığını `{(m.get('health') or {}).get('cli', 'sb doctor')}` ile denetle (ayrıntı: {cmd_label(d, 'doctor')}). "
          "Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.", ""]
    if items:
        L += ["## Maddeler", "", "| No | Madde | Durum | Sürüm |", "|---|---|---|---|"]
        for it in items:
            L.append(f"| [{it['id']}](#madde-{it['id']}) | {esc(it['ad'])} | {STATUS_TR.get(it['durum'], it['durum'])} | {it['surum']} |")
        L.append("")
        for it in items:
            L += item_section(m, it)
    return "\n".join(L).rstrip() + "\n"


def docs_hint(doc: str, d: str) -> str:
    base = Path(doc).stem
    return {"google-cloud-kurulum": f"[Hesaplar](../03-hesaplar.md#hesap-google)", "telefon-pwa": "[Telefon](../08-uygulama-turu.md#telefon)",
            "telefon-sms-kurulum": "[SMS kaynağı](../kaynaklar/sms.md)", "telegram-kurulum": "[Telegram](../03-hesaplar.md#hesap-telegram)"}.get(base, "ilgili bölüm")


def item_section(m: dict, it: dict) -> list[str]:
    mid, d = m["id"], "moduller"
    st = it["durum"]
    cmds = CTX.mod_cmds.get(mid, [])
    views = MODULE_VIEWS.get(mid, [])
    kategori = CTX.fcats.get(it["kategori"], it["kategori"])
    L = [f'<a id="madde-{it["id"]}"></a>', "", f"### {it['id']}. {it['ad']}", "",
         f"- **Ne işe yarar:** «{it['ad']}» ({kategori} kategorisi), «{name(m)}» modülünün parçasıdır. Modülün amacı: {bi(m['desc']).rstrip('.')}."]
    if st == "tamamlandi":
        L.append(f"- **Durum:** hazır (sürüm {it['surum']}).")
    else:
        L.append(f"- **Durum:** {STATUS_TR.get(st, st)}; yol haritasında Faz {it['faz']} / sürüm {it['surum']} için yer alır. Şu an tam çalışmasını bekleme.")
    L.append(f"- **Nasıl açılır:** «{name(m)}» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).")
    L.append(f"- **Ne ister:** {requires_summary(d, m)}.")
    use = []
    if views:
        use.append("ekran: " + ", ".join(f"**{v}**" for v in views))
    if cmds:
        use.append("komut: " + ", ".join(cmd_label(d, c) for c in cmds[:6]))
    if st == "tamamlandi":
        L.append("- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa " +
                 ("şuralardan kullanılır: " + "; ".join(use) + ". " if use else "arka planda ya da asistan üzerinden çalışır. ") +
                 "Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).")
    else:
        L.append("- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.")
    L.append("- **İlgili ekran/komut:** " + ("; ".join(use) if use else "yok (altyapı)") + ".")
    L.append("")
    return L


# ------------------------------------------------------------------ kaynak sayfası
SRC_CMD_SPECIAL = {
    "history-import": ("sb history-import <dosya>", "önizleme (hiçbir şey yazmaz); gerçekten içe aktarmak için sonuna `--apply` ekle"),
    "takeout": ("sb takeout <zip> --dry-run", "yazmadan say; gerçek aktarım için `--dry-run` olmadan"),
    "linkedin": ("sb linkedin-import", "zip'i `00-Inbox/_imports` klasörüne koyduktan sonra çalıştır"),
    "sms": ("sb sms-sync", "Drive'daki SMS Backup & Restore yedeğini çeker"),
    "outlook": ("sb mail-fetch <takma-ad>", "IMAP hesabı eklendikten sonra; takvim için `sb caldav-sync` (Outlook ICS)"),
    "icloud": ("sb mail-fetch <takma-ad>", "IMAP hesabı eklendikten sonra; takvim/kişi için `sb caldav-sync icloud`"),
    "browser": ("sb import browser --discover", "bu bilgisayardaki tarayıcı profillerini ve dosya yollarını listeler"),
}


def split_howto(txt: str) -> tuple[list[str], list[str]]:
    steps, notes = [], []
    for ln in (txt or "").splitlines():
        ln = ln.rstrip()
        if not ln.strip():
            continue
        if re.match(r"^\d+\.\s", ln):
            steps.append(re.sub(r"^\d+\.\s*", "", ln))
        elif ln.startswith("Dosyayı Second Brain"):
            continue
        else:
            notes.append(ln)
    return steps, notes


def source_page(s: dict) -> str:
    sid, d = s["id"], "kaynaklar"
    imp = s["import"]
    conn = imp.get("connector")
    steps, notes = split_howto(bi(imp["how_to"]))
    parent = s.get("parent")
    L = [f"# {name(s)}", "", f"> {bi(s['desc'])}", "", "| | |", "|---|---|",
         f"| Kaynak kimliği | `{sid}` |", f"| Dosya biçimi | {', '.join(f'`{f}`' for f in imp['formats'])} |",
         f"| Bağlayıcı | {('`' + conn + '`') if conn else 'özel yol (aşağıya bak)'} |",
         f"| Bağlı modül | {mod_link(d, parent)} |", f"| Ne ister | {requires_summary(d, s)} |", "",
         "## Başlamadan önce", "",
         "- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.",
         "- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, "
         "takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).",
         "- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.", ""]
    if "hesap" in imp["formats"]:
        L += ["- Bu kaynak bir **dosya değil bir hesaptır**: sihirbazın 5. adımında e-posta (IMAP) hesabı olarak eklenir.", ""]
    L += ["## Dışa aktarma adımları", ""]
    L += [f"{i}. {t}" for i, t in enumerate(steps, 1)]
    if notes:
        L += [""] + [f"> {n}" for n in notes]
    L += ["", f"![{name(s)} dışa aktarma ekranı](../img/kaynak-{sid}.png)", "",
          "## Sihirbazda yükleme (9. adım: Veri yükleme)", ""]
    if "hesap" in imp["formats"]:
        L += ["1. Sihirbazın **5. adımına (Hesaplar)** git, **E-posta (IMAP)** bölümünde ilgili hazır sunucuyu seç ([Hesaplar](../03-hesaplar.md#hesap-imap)).",
              "2. Takma ad, e-posta ve uygulama şifresini gir → **Test et ve kaydet**.",
              "3. 9. adımda bu kaynak yalnız bilgi olarak görünür; arşivleme günlük işlerle (`sb daily`) ya da `sb mail-fetch <takma-ad>` ile yapılır.", ""]
    elif any(f.startswith("config/") for f in imp["formats"]):
        L += ["1. Dosya yüklemen gerekmez; adım listesindeki ayar dosyasını düzenle (kurulum paneli de bu dosyayı yazar).",
              "2. 9. adımdaki kaynak kartında **Önizle** ile ne geleceğini gör, sonra **İçe aktar**.", ""]
    else:
        L += ["1. 9. adımda kaynak kartını bul (seçimin için gerekenler üstte; öbürleri **Bütün kaynakları göster** ile açılır).",
              "2. Kartın içindeki **Bu dosyayı nasıl alırsın?** bölümü yukarıdaki adımların aynısını gösterir.",
              "3. Dosyayı kutuya **sürükle-bırak** ya da **Dosya seç** ile seç. Üstte `Yükleniyor: <ad> (<MB> MB)…` yazar, bitince `Yüklendi: <ad>`.",
              "4. **Önizle**'ye bas: dosyaya dokunmadan kaç kayıt okunacağı, tarih aralığı ve örnek başlıklar gösterilir. Sayı 0 ya da beklediğinden çok farklıysa "
              "yanlış dosyayı seçmiş olabilirsin.",
              "5. Sorun yoksa **İçe aktar**'a bas; ilerleme altta görünür, bitince `N kayıt içe aktarıldı` ve **Yapılan içe aktarmalar** listesine düşer.", ""]
    L += [f"![{name(s)} veri yükleme ekranı](../img/yukleme-{sid}.png)", "", "## Komut satırından", ""]
    if sid in SRC_CMD_SPECIAL:
        c, why = SRC_CMD_SPECIAL[sid]
        L.append(f"`{c}` — {why}.")
    elif conn:
        extra = " `--me \"Adın\"` ekle: senin mesajların `me` olarak işaretlenir." if any(f["key"] == "me" for f in (s["requires"].get("fields") or [])) else ""
        L.append(f"`sb import {conn} <dosya> --dry-run` — önce yazmadan say (kayıt sayısı, tarih aralığı, 3 örnek başlık); sorun yoksa `--dry-run` olmadan çalıştır.{extra}")
    else:
        L.append("Bu kaynağın ayrı bir komutu yoktur; sihirbazdan ya da uygulamadan yüklenir.")
    L += ["", "Genel komut açıklaması: " + cmd_label(d, "import") + ".", "", "## Sorun giderme", "",
          "| Belirti | Neden olabilir | Ne yap |", "|---|---|---|",
          "| `dosya çok büyük (en çok 2 GB)` | Yükleme sınırı 2 GB | Dışa aktarmayı daha dar bir tarih aralığıyla yeniden iste ya da komut satırından `sb import` kullan |",
          "| `geçersiz dosya adı` | Ad boş ya da yasak karakter içeriyor | Dosyayı kısa, sade bir adla kaydet (harf, rakam, boşluk, nokta, tire) |",
          "| `yükleme yarım kaldı` | Bağlantı/disk sorunu | Dosyayı yeniden yükle |",
          "| Önizlemede 0 kayıt | Yanlış dosya ya da boş dışa aktarma | Yukarıdaki adımları baştan izle; zip'in içeriğini kontrol et |",
          "| `Bu kaynağın içe aktarıcısı henüz yok; dosya hazır bekliyor.` | Bu kaynak için bağlayıcı yazılmamış | Dosya `import_staging` klasöründe bekler; bağlayıcı eklenince içe aktarılır |",
          "| Sağlayıcıda menü bulunamıyor | Menü adları sürüme göre değişir | Adım listesindeki resmi yardım adresine ya da sağlayıcının yardım sayfasında «verilerimi indir» aramasına bak |",
          "", "Genel sorunlar: [Sorun giderme](../11-sorun-giderme.md) · Veri yükleme genel rehberi: [Veri yükleme](../07-veri-yukleme.md).", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ MCP sayfası
def mcp_page(m: dict) -> str:
    mid, d = m["id"], "mcp"
    mc = m["mcp"]
    remote = bool(mc.get("remote")) or not mc.get("command")
    L = [f"# {name(m)} (MCP)", "", f"> {bi(m['desc'])}", "", "| | |", "|---|---|",
         f"| MCP kimliği | `{mid}` |", f"| Varsayılan | {'açık' if m.get('default_on') else 'kapalı (isteğe bağlı)'} |",
         f"| Tür | {'uzak sunucu (elle bağlanır)' if remote else 'yerel komut (sihirbaz kurar)'} |",
         f"| Resmi belge | {mc.get('docs_url')} |", f"| Ne ister | {requires_summary(d, m)} |", "",
         "## MCP nedir, bu ne işe yarar", "",
         "MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: "
         f"{bi(m['desc']).rstrip('.')}. Genel anlatım: [MCP](../06-mcp.md).", ""]
    if "arşivlen" in bi(m["desc"]):
        L += ["> **Dikkat:** açıklamada belirtildiği gibi bu paket arşivlenmiş olabilir. Güncel sürüm için resmi belge adresine bak; sihirbaz yine de kurmayı dener.", ""]
    L += ["## Gerekenler", ""] + requires_block(d, m) + ["", "## Sihirbazda kurulum (8. adım: MCP)", ""]
    if mc.get("install") is None:
        L += ["Bu MCP sihirbaz tarafından kurulmaz; kartında yalnız **Belge** bağlantısı görünür ve `Elle kurulum: belgeye bak.` yazar.",
              f"1. Resmi belgeyi aç: {mc.get('docs_url')}", "2. Belgedeki bağlama adımlarını izle (menü adları sürüme göre değişebilir).",
              "3. Claude Code'da `claude mcp list` ile bağlandığını doğrula."]
    else:
        n = 1
        L.append(f"{n}. 8. adımda **{name(m)}** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).")
        for f in (m.get("requires") or {}).get("fields") or []:
            n += 1
            L.append(f"{n}. **{bi(f.get('label'))}** alanını doldur ({KIND_TR.get(f.get('kind'))}" + (", zorunlu" if f.get("required") else "") + ")."
                     + (f" {bi(f.get('help'))}" if f.get("help") else ""))
        n += 1
        L.append(f"{n}. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`{mc['install']}`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.")
        n += 1
        L.append(f"{n}. Başarılıysa kartta `{name(m)} kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.")
        L += ["", "Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):", "", "```",
              "claude mcp add " + mid + " --scope user " + "".join(f"-e {k}=<{re.sub(r'[{}]', '', v)}> " for k, v in (mc.get("env") or {}).items()) +
              "-- " + " ".join([str(mc.get("command"))] + [str(a) for a in mc.get("args") or []]), "```"]
    L += ["", f"![{name(m)} MCP kartı](../img/mcp-{mid}.png)", "", "## Sorun giderme", "",
          "| Belirti | Ne yap |", "|---|---|",
          "| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |"]
    for app in (m.get("requires") or {}).get("apps") or []:
        L.append(f"| `Ön koşul başarısız: … kurulu mu?` | **{app}** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |")
    for f in (m.get("requires") or {}).get("fields") or []:
        if f.get("required"):
            L.append(f"| `gerekli alan eksik: {f['key']}` | **{bi(f.get('label'))}** alanını doldur |")
    if any(f.get("secret") for f in (m.get("requires") or {}).get("fields") or []):
        L.append("| `şifre kasası (keyring) yok` | İşletim sisteminin şifre kasası kullanılamıyor; Windows'ta Kimlik Bilgisi Yöneticisi'nin açık olduğundan emin ol |")
    L += ["| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |", "",
          "Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ üst sayfalar
def page_presets() -> str:
    ax = CTX.presets["axes"]
    dfl = CTX.presets.get("defaults") or {}
    L = ["# Hazır seçimler", "",
         "Sihirbazın 2. adımı dört ekseni birlikte seçtirir. Sonuç, 3. adımda tek tek değiştirebileceğin bir başlangıç listesidir.", "",
         "**Birleştirme sırası:** önce *yoğunluk* temel modül listesini verir → *meslek* modül ekler → *gizlilik* ve *donanım* kısıtlar (modül kapatır, model profili belirler). "
         "Bir modül kapanırsa ona bağlı olan da kapanır (ör. ses kapanınca uyandırma sözcüğü; Gmail ve IMAP ikisi de kapanınca sabah özeti).", ""]
    L.append("Varsayılan seçimler: " + ", ".join(f"{AXIS_TR[a]} = **{bi(ax[a][dfl[a]]['name'])}**" for a in ("donanim", "gizlilik", "yogunluk") if dfl.get(a)) +
             "; meslek varsayılan olarak seçili değildir.")
    L.append("")
    for a in ("yogunluk", "meslek", "gizlilik", "donanim"):
        L += [f"## {AXIS_TR[a]}", ""]
        for k, v in ax[a].items():
            L += [f"### {bi(v['name'])}", "", f"{bi(v['desc'])}", ""]
            if v.get("modules"):
                L.append("**Açılan modüller (" + str(len(v["modules"])) + "):** " + ", ".join(mod_link("", x) for x in v["modules"]))
            if v.get("add"):
                L.append("**Eklenen modüller (" + str(len(v["add"])) + "):** " + ", ".join(mod_link("", x) for x in v["add"]))
            if v.get("off"):
                L.append("**Kapatılan modüller:** " + ", ".join(mod_link("", x) for x in v["off"]))
            elif a in ("donanim", "gizlilik"):
                L.append("**Kapatılan modül:** yok.")
            if v.get("models"):
                L.append("**Model ayarı:** " + ", ".join(f"`{kk}` = `{vv}`" for kk, vv in v["models"].items()))
            if v.get("privacy_profile"):
                L.append("**Gizlilik profili:** " + ", ".join(f"`{kk}` = `{vv}`" for kk, vv in v["privacy_profile"].items()))
            L.append("")
    L += ["## Modül × yoğunluk tablosu", "", "| Modül | " + " | ".join(bi(v["name"]) for v in ax["yogunluk"].values()) + " |",
          "|---|" + "---|" * len(ax["yogunluk"])]
    for mid in sorted(CTX.modules):
        L.append(f"| {mod_link('', mid)} | " + " | ".join("●" if mid in (v.get("modules") or []) else "" for v in ax["yogunluk"].values()) + " |")
    L += ["", "● = o yoğunlukta açık.", "", "## Modül × meslek tablosu", "", "| Modül | " + " | ".join(bi(v["name"]) for v in ax["meslek"].values()) + " |",
          "|---|" + "---|" * len(ax["meslek"])]
    for mid in sorted(CTX.modules):
        L.append(f"| {mod_link('', mid)} | " + " | ".join("●" if mid in (v.get("add") or []) else "" for v in ax["meslek"].values()) + " |")
    L += ["", "● = o meslek seçilince eklenir.", "", "Sihirbazdaki ekranın tanıtımı: [Sihirbaz adım adım](02-sihirbaz-adim-adim.md#adim-2-hazir-secim).", ""]
    return "\n".join(L)


def page_modules() -> str:
    L = ["# Modüller (özellik grupları)", "",
         f"Second Brain **{len(CTX.modules)} modül**den oluşur; her modül özellik kataloğundaki maddeleri gruplar. Her modülün sayfasında: ne işe yarar, nasıl açılır, "
         "ne ister, nasıl kullanılır, hangi hazır seçimlerde açıktır ve maddeleri tek tek bulunur.", ""]
    by: dict[str, list[dict]] = {}
    for m in CTX.modules.values():
        by.setdefault(m["category"], []).append(m)
    for c, title in CTX.cats.items():
        if c not in by:
            continue
        L += [f"## {bi(title)}", "", "| Modül | Ne yapar | Madde | Varsayılan |", "|---|---|---|---|"]
        for m in sorted(by[c], key=lambda x: x["id"]):
            L.append(f"| [{name(m)}](moduller/{m['id']}.md) | {esc(bi(m['desc']))} | {len(m.get('catalog_ids') or [])} | {'açık' if m.get('default_on', True) else 'kapalı'} |")
        L.append("")
    return "\n".join(L)


def page_catalog() -> str:
    L = ["# Özellik kataloğu (250 madde)", "",
         "Aşağıda katalogdaki **her madde** modülüyle birlikte listelenir; maddeye tıklayınca modül sayfasındaki ayrıntısına gidersin "
         "(ne işe yarar, nasıl açılır, ne ister, nasıl kullanılır).", "",
         "Durumlar: " + ", ".join(f"**{v}**" for v in STATUS_TR.values()) + ".", ""]
    by: dict[str, list[dict]] = {}
    for it in CTX.items:
        by.setdefault(it["kategori"], []).append(it)
    for c, title in CTX.fcats.items():
        L += [f"## {title}", "", "| No | Madde | Modül | Durum |", "|---|---|---|---|"]
        for it in by.get(c, []):
            mid = CTX.item_module.get(it["id"])
            L.append(f"| {it['id']} | [{esc(it['ad'])}](moduller/{mid}.md#madde-{it['id']}) | {name(CTX.modules[mid])} | {STATUS_TR.get(it['durum'], it['durum'])} |")
        L.append("")
    return "\n".join(L)


def page_sources() -> str:
    L = ["# Veri kaynakları", "",
         f"Sihirbazın 9. adımı **{len(CTX.sources)} kaynaktan** veri alır. Her kaynağın sayfasında dışa aktarma adımları, sihirbazda yükleme, komut ve sorun giderme vardır. "
         "Genel anlatım: [Veri yükleme](07-veri-yukleme.md).", "", "| Kaynak | Biçim | Bağlı modül | Hesap |", "|---|---|---|---|"]
    for s in sorted(CTX.sources.values(), key=lambda x: name(x).lower()):
        L.append(f"| [{name(s)}](kaynaklar/{s['id']}.md) | {', '.join(s['import']['formats'])} | {mod_link('', s['parent'])} | "
                 f"{', '.join(acc_label('', a) for a in s['requires'].get('accounts') or []) or '—'} |")
    return "\n".join(L) + "\n"


def page_mcps() -> str:
    L = ["# MCP kataloğu", "",
         f"Sihirbazın 8. adımında **{len(CTX.mcps)} hazır MCP** vardır. Her birinin sayfasında ne işe yaradığı, ne istediği, sihirbazda kurulum ve sorun giderme yazar. "
         "Genel anlatım: [MCP](06-mcp.md).", "", "| MCP | Ne yapar | Tür | Ne ister |", "|---|---|---|---|"]
    for m in sorted(CTX.mcps.values(), key=lambda x: x["id"]):
        mc = m["mcp"]
        L.append(f"| [{name(m)}](mcp/{m['id']}.md) | {esc(bi(m['desc']))} | {'uzak/elle' if (mc.get('remote') or not mc.get('command')) else 'yerel'} | {requires_summary('', m)} |")
    return "\n".join(L) + "\n"


def page_sectors() -> str:
    L = ["# Sektör paketleri", "",
         "Sektör paketi = çekirdek + bir tanım (modül/kaynak/MCP listesi, hazır seçim, roller, rapor şablonları, terimler). Kod değişmeden yeni sektör eklenir. "
         "Bu bir **şirket ürünü** yönüdür; kişisel kullanımda gerekmez.", ""]
    for s in CTX.sectors.values():
        L += [f"## {name(s)}", "", bi(s["desc"]), "", f"- **Kimlik:** `{s['id']}`", "- **Hazır seçim:** " +
              ", ".join(f"{AXIS_TR[k]} = {bi(CTX.presets['axes'][k][v]['name'])}" for k, v in (s.get("presets") or {}).items() if v),
              "- **Modüller:** " + ", ".join(mod_link("", x) for x in s.get("modules") or []),
              "- **Veri kaynakları:** " + ", ".join(f"[{name(CTX.sources[x])}](kaynaklar/{x}.md)" for x in s.get("sources") or []),
              "- **MCP'ler:** " + ", ".join(f"[{name(CTX.mcps[x])}](mcp/{x}.md)" for x in s.get("mcp") or []), "",
              "### Roller", "", "| Rol | Raporlar |", "|---|---|"]
        reps = {r["id"]: r for r in s.get("reports") or []}
        for r in s.get("roles") or []:
            L.append(f"| {bi(r['name'])} | {', '.join(bi(reps[x]['name']) for x in r.get('reports') or [])} |")
        L += ["", "### Rapor şablonları", "", "| Rapor | Sıklık | Kaynaklar | Not |", "|---|---|---|---|"]
        for r in s.get("reports") or []:
            L.append(f"| {bi(r['name'])} | {r.get('schedule', '—')} | {', '.join(r.get('source') or []) or '—'} | "
                     f"{esc(bi(r.get('note'))) or ('yakında' if r.get('status') == 'yakinda' else '—')} |")
        if s.get("terms"):
            L += ["", "### Terimler", ""] + [f"- **{k}:** {bi(v)}" for k, v in s["terms"].items()]
        if s.get("coming_soon"):
            L += ["", "### Yakında", ""] + [f"- **{bi(c['name'])}:** {bi(c['desc'])}" for c in s["coming_soon"]]
        if s.get("notes"):
            L += ["", "### Not", "", bi(s["notes"])]
        L.append("")
    return "\n".join(L)


def page_needs() -> str:
    L = ["# Hangi özellik ne ister", "",
         "Kurulumdan önce hangi hesap/anahtarın gerekeceğini görmek için tek tablo. Ayrıntı için modül adına tıkla.", "",
         "| Modül | Hesaplar | Gizli değerler | Programlar | Donanım |", "|---|---|---|---|---|"]
    for mid in sorted(CTX.modules):
        m = CTX.modules[mid]
        r = m["requires"]
        L.append(f"| {mod_link('', mid)} | {', '.join(acc_label('', a) for a in r.get('accounts') or []) or '—'} | "
                 f"{', '.join('`' + s + '`' for s in r.get('secrets') or []) or '—'} | {', '.join(r.get('apps') or []) or '—'} | "
                 f"{', '.join(f'{HW_TR.get(k, k)} ≥ {v}' for k, v in (r.get('hardware') or {}).items()) or '—'} |")
    accs: dict[str, list[str]] = {}
    for m in list(CTX.modules.values()) + list(CTX.sources.values()) + list(CTX.mcps.values()):
        for a in m["requires"].get("accounts") or []:
            accs.setdefault(a, []).append(m["id"])
    L += ["", "## Hesap türüne göre", "", "| Hesap | Nerede gerekir |", "|---|---|"]
    for a in sorted(accs):
        users = [x for x in accs[a]]
        L.append(f"| {acc_label('', a)} | " + ", ".join(sorted({f'`{x}`' for x in users})) + " |")
    return "\n".join(L) + "\n"


def readme(pages: list[tuple[str, str]]) -> str:
    L = ["# Second Brain 1.0 — kullanıcı rehberi", "",
         "Bu rehber Second Brain'i kurmaktan günlük kullanıma, hesap bağlamaktan sorun gidermeye kadar **her şeyi adım adım** anlatır. "
         "Teknik bilgi gerekmez: her yerde «şuna tıkla → şunu gör» biçimi kullanılır.", "",
         "> Bu klasör `tools/build_guide.py` ile üretilir; elle yazılan bölümler `docs/rehber-src/` içindedir. Burayı elle düzenleme.", "",
         "## Nereden başlamalıyım?", "",
         "1. Ürünü tanımak için [00 · Başlangıç](00-baslangic.md).", "2. Kurmak için [01 · Kurulum](01-kurulum.md), sonra [02 · Sihirbaz adım adım](02-sihirbaz-adim-adim.md).",
         "3. Bir şey takılırsa [11 · Sorun giderme](11-sorun-giderme.md).", "", "## İçindekiler", ""]
    for fn, title in pages:
        L.append(f"- [{title}]({fn})")
    L += ["", "## Sayfa sayıları", "", f"- Elle yazılan bölüm: {len(HAND_PAGES)}", f"- Modül sayfası: {len(CTX.modules)}",
          f"- Veri kaynağı sayfası: {len(CTX.sources)}", f"- MCP sayfası: {len(CTX.mcps)}", f"- Özellik maddesi: {len(CTX.items)}", ""]
    return "\n".join(L)


# ------------------------------------------------------------------ üretim
CTX: Ctx = None  # type: ignore


def first_h1(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


_IMG_RE = re.compile(r"(?<!`)!\[[^\]]*\]\((?:\.\./)?img/([^)\s]+\.(?:png|jpg|jpeg|gif|webp))\)")
_EMPTY_BULLET_RE = re.compile(r"^[ \t]*[-*][ \t]*\n", re.M)


def _drop_missing_images(text: str) -> str:
    """Dosyası `docs/rehber/img/` altında olmayan görüntü bağlantılarını atar (kırık simge yerine metin kalır).
    Kod örneği içindeki (`![açıklama](img/...)`) anlatım bozulmaz; görüntüsü gitmiş madde işareti de temizlenir."""
    out = _IMG_RE.sub(lambda m: m.group(0) if (OUT / "img" / m.group(1)).is_file() else "", text)
    return _EMPTY_BULLET_RE.sub("", out) if out != text else out


def build(out: Path = OUT, src: Path = SRC) -> dict:
    global CTX
    CTX = Ctx()
    if out.exists():
        for p in sorted(out.rglob("*"), reverse=True):
            if p.is_file() and p.name != ".gitkeep" and "img" not in p.relative_to(out).parts:
                p.unlink()
    out.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    for h in HAND_PAGES:
        p = src / f"{h}.md"
        if p.exists():
            files[f"{h}.md"] = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    files["15-hazir-secimler.md"] = page_presets()
    files["16-moduller.md"] = page_modules()
    files["17-ozellik-katalogu.md"] = page_catalog()
    files["18-veri-kaynaklari.md"] = page_sources()
    files["19-mcp-katalogu.md"] = page_mcps()
    files["20-sektor-paketleri.md"] = page_sectors()
    files["21-ne-ister.md"] = page_needs()
    for mid, m in sorted(CTX.modules.items()):
        files[f"moduller/{mid}.md"] = module_page(m)
    for sid, s in sorted(CTX.sources.items()):
        files[f"kaynaklar/{sid}.md"] = source_page(s)
    for mid, m in sorted(CTX.mcps.items()):
        files[f"mcp/{mid}.md"] = mcp_page(m)
    toc = [(fn, first_h1(files[fn], fn)) for fn in sorted(k for k in files if "/" not in k)]
    files["README.md"] = readme(toc)
    files = {k: _drop_missing_images(v) for k, v in files.items()}
    for rel_path, text in files.items():
        dest = out / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    return {"files": files, "hand": len(HAND_PAGES), "modules": len(CTX.modules), "sources": len(CTX.sources), "mcps": len(CTX.mcps),
            "items": len(CTX.items)}


# ------------------------------------------------------------------ denetim
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")
SECRET_PATTERNS = [
    (re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"), "Google API anahtarı"),
    (re.compile(r"\bsk-(?:ant-|proj-)?[0-9A-Za-z_-]{20,}"), "sk- anahtarı"),
    (re.compile(r"\bgh[pousr]_[0-9A-Za-z]{30,}"), "GitHub belirteci"),
    (re.compile(r"\bxox[abp]-[0-9A-Za-z-]{20,}"), "Slack belirteci"),
    (re.compile(r"\b\d{8,10}:AA[0-9A-Za-z_-]{30,}"), "Telegram bot belirteci"),
    (re.compile(r"(?<![\w.])(?:\+90|0090|0)\s?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"), "telefon numarası"),
    (re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b"), "IBAN"),
]
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
EMAIL_OK_LOCAL = {"ornek", "ayse", "ayse.yilmaz", "mehmet", "ornek.kisi", "kullanici", "adiniz", "ad.soyad", "ahmet"}
EMAIL_OK_DOMAIN = {"ornek.com", "example.com", "ornek.com.tr", "sirket.com.tr", "ornek.edu.tr", "okul.edu.tr", "noreply.github.com"}


def secret_findings(text: str) -> list[str]:
    out = [f"{label}: {m.group(0)[:24]}…" for rx, label in SECRET_PATTERNS for m in rx.finditer(text)]
    for m in EMAIL_RE.finditer(text):
        local, _, dom = m.group(0).lower().rpartition("@")
        if local in EMAIL_OK_LOCAL or dom in EMAIL_OK_DOMAIN:
            continue
        if dom.endswith(("png", "jpg", "js", "py", "md", "json", "yaml")):      # `a@b.png` gibi dosya adı sanılanlar
            continue
        out.append(f"e-posta: {m.group(0)}")
    return out


def anchors_of(text: str) -> set[str]:
    a = set(re.findall(r'<a id="([^"]+)"', text))
    for h in re.findall(r"^#{1,6}\s+(.+?)\s*$", text, re.M):
        a.add(slug(re.sub(r"[`*]", "", h)))
    return a


def validate(files_dir: Path) -> list[str]:
    errs: list[str] = []
    ctx = CTX
    allmd = {p.relative_to(files_dir).as_posix(): p.read_text(encoding="utf-8") for p in files_dir.rglob("*.md")}
    for h in HAND_PAGES:
        if f"{h}.md" not in allmd:
            errs.append(f"elle yazılan sayfa eksik: docs/rehber-src/{h}.md")
    for t in GEN_TOP + ["README"]:
        if f"{t}.md" not in allmd:
            errs.append(f"üretilen sayfa eksik: {t}.md")
    for mid in ctx.modules:
        if f"moduller/{mid}.md" not in allmd:
            errs.append(f"modül sayfası eksik: {mid}")
    for sid in ctx.sources:
        if f"kaynaklar/{sid}.md" not in allmd:
            errs.append(f"kaynak sayfası eksik: {sid}")
    for mid in ctx.mcps:
        if f"mcp/{mid}.md" not in allmd:
            errs.append(f"MCP sayfası eksik: {mid}")
    for it in ctx.items:
        mid = ctx.item_module.get(it["id"])
        if not mid:
            errs.append(f"madde {it['id']} hiçbir modülde yok (catalog_ids)")
            continue
        txt = allmd.get(f"moduller/{mid}.md", "")
        if f'<a id="madde-{it["id"]}"></a>' not in txt or not re.search(rf"^### {it['id']}\. ", txt, re.M):
            errs.append(f"madde {it['id']} ({it['ad']}) moduller/{mid}.md içinde yok")
    for fn, text in allmd.items():
        base = Path(fn).parent
        for target in LINK_RE.findall(text):
            if re.match(r"^(https?:|mailto:|#)", target):
                if target.startswith("#") and target[1:] not in anchors_of(text):
                    errs.append(f"{fn}: sayfa içi bağlantı bulunamadı {target}")
                continue
            path, _, frag = target.partition("#")
            dest = (files_dir / base / path).resolve() if path else files_dir / fn
            try:
                key = dest.relative_to(files_dir.resolve()).as_posix()
            except ValueError:
                errs.append(f"{fn}: rehber dışına bağlantı {target}")
                continue
            if key not in allmd:
                errs.append(f"{fn}: bağlantı hedefi yok {target}")
            elif frag and frag not in anchors_of(allmd[key]):
                errs.append(f"{fn}: bağlantı bölümü yok {target}")
        for f in secret_findings(text):
            errs.append(f"{fn}: sır/kişisel veri benzeri metin → {f}")
    return errs


def check() -> list[str]:
    tmp = Path(tempfile.mkdtemp(prefix="sb-guide-"))
    try:
        stats = build(tmp)
        errs = validate(tmp)
        if OUT.exists():
            for rel_path, text in stats["files"].items():
                cur = OUT / rel_path
                if not cur.exists() or cur.read_text(encoding="utf-8") != text.rstrip("\n") + "\n":
                    errs.append(f"bayat çıktı: docs/rehber/{rel_path} (python tools/build_guide.py çalıştır)")
                    break
            extra = [p.relative_to(OUT).as_posix() for p in OUT.rglob("*.md") if p.relative_to(OUT).as_posix() not in stats["files"]]
            if extra:
                errs.append(f"docs/rehber içinde fazladan dosya: {extra[0]} (+{len(extra) - 1})")
        else:
            errs.append("docs/rehber yok (python tools/build_guide.py çalıştır)")
        return errs
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        if s:
            s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Kullanıcı rehberini üret")
    ap.add_argument("--check", action="store_true", help="yazmadan denetle: eksik madde/sayfa/bağlantı, sır benzeri metin, bayat çıktı")
    ap.add_argument("--out", help="çıktı klasörü (varsayılan docs/rehber)")
    a = ap.parse_args(argv)
    if a.check:
        errs = check()
        for e in errs[:60]:
            print("✗", e)
        print(f"{len(errs)} sorun" if errs else "rehber temiz")
        return 1 if errs else 0
    stats = build(Path(a.out) if a.out else OUT)
    errs = validate(Path(a.out) if a.out else OUT)
    print(f"{len(stats['files'])} sayfa: {stats['hand']} elle, {stats['modules']} modül, {stats['sources']} kaynak, {stats['mcps']} MCP, {stats['items']} madde")
    for e in errs[:60]:
        print("✗", e)
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
