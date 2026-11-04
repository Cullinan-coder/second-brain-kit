"""Özellik anahtarları: kullanıcı neyi kullanıyorsa o çalışır (winutil'deki seçim kutularının çalışma zamanı karşılığı).

- Modüller (`MODULES`): bugün çalışan her parça bir anahtar. Seçim `config/features.yaml` (kurulum paneli yazacak; elle de olur).
  Dosyada olmayan anahtar varsayılan değerini alır (geriye uyumlu: mevcut kurulumlarda her şey açık kalır).
- Günlük çalışma kapalı modülün adımını atlar, asistan kapalı modülün araçlarını modele hiç göstermez, doctor kontrol etmez.
- Katalog (`features.yaml`): 258 maddelik yol haritası; `sb roadmap` ilerlemeyi gösterir.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path

import yaml

from .config import SYSTEM

CONFIG = SYSTEM / "config" / "features.yaml"
CATALOG = SYSTEM / "features.yaml"

# anahtar: (görünen ad, açıklama, gereksinim, varsayılan)
MODULES: dict[str, tuple[str, str, str, bool]] = {
    "gmail": ("Gmail", "Gmail hesaplarını salt okunur arşivler, kategorilere ayırır", "Google girişi", True),
    "imap": ("Şirket/okul maili (IMAP)", "IMAP hesaplarını salt okunur arşivler", "IMAP şifresi", True),
    "calendar": ("Google Takvim", "Takvimi kasaya alır; onaylı ekleme ve silme", "Google girişi", True),
    "dates": ("Tarih çıkarma", "Mail/SMS'ten teslim ve randevu tarihlerini çıkarıp onaya sunar", "model", True),
    "contacts": ("Google Rehber", "Kişi notları", "Google girişi", True),
    "drive": ("Google Drive", "Drive dosya listesi ve notları", "Google girişi", True),
    "sms": ("SMS ve aramalar", "Telefon yedeğinden SMS/arama", "telefon yedeği", True),
    "local_files": ("Bilgisayar dosyaları", "Klasör notları ve belge içerik dizini", "—", True),
    "projects": ("Projeler ve GitHub", "Kod projelerini tarar; proje dosyası derler", "GitHub (isteğe bağlı), Claude", True),
    "courses": ("Okul (ÖBS/LMS)", "Ders notları, ders dosyaları, ders derlemesi", "okul hesabı", True),
    "sessions": ("Claude Code oturumları", "Proje oturum günlükleri", "Claude Code", True),
    "linkedin": ("LinkedIn arşivi", "LinkedIn veri arşivini içe aktarır", "arşiv zip", True),
    "telegram": ("Telegram botu", "Telegram'dan not alma ve özet", "bot belirteci", True),
    "digest": ("Sabah özeti maili", "Her gün özet maili ve günlük not", "SMTP (isteğe bağlı)", True),
    "inbox": ("Not kutusu", "00-Inbox/Dump notlarını yerine dağıtır", "model", True),
    "assistant": ("Yerel asistan", "Obsidian yan paneli ve telefondan sohbet", "model", True),
    "phone": ("Telefon erişimi", "Asistana telefondan Tailscale ile erişim", "Tailscale", True),
    "computer": ("Bilgisayar kontrolü", "Uygulama açma, ses, sistem bilgisi, komut (onaylı)", "—", True),
    "media": ("Spotify ve YouTube", "Şarkı/video açma", "Spotify Premium (isteğe bağlı)", True),
    "whatsapp": ("WhatsApp", "Onaylı mesaj taslağı ve gönderme", "WhatsApp masaüstü", True),
    "vision": ("Ekran ve kamera", "Ekranı/kamerayı okuyup anlatma", "görsel model", True),
    "capture": ("Beyne at", "Ctrl+Alt+B, Gönder › Beyne At, ekran görüntüsü, web/video özeti", "model", True),
    "claude_hooks": ("Claude Code hafızası", "Kancalar, son oturum kartları, makbuz, skill'ler", "Claude Code", True),
    "flush": ("Oturum özetleri", "Sıkıştırma öncesi / oturum sonu yerel model özeti", "model", True),
    "night": ("Gece koşusu", "İstenince gece işlerini Claude Code'a sırayla yaptırır", "Claude Code", True),
    "brain": ("Beyin dizini", "Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler", "gömme modeli", True),
    "browser": ("Tarayıcı geçmişi", "Chrome/Edge/Firefox geçmişi ve yer imleri (giriş/banka sayfaları hariç)", "—", True),
    "derived": ("Fatura ve kargo", "Maillerden fatura ve kargo kayıtları", "Gmail", True),
    "github": ("GitHub derin", "Issue, PR, commit ve release kayıtları", "gh girişi", True),
    "voice": ("Ses", "Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı", "faster-whisper", True),
    "wake_word": ("Uyandırma sözcüğü", "'Hey <asistan>' ile dinlemeye başlar (yalnız sekme açıkken)", "Ses", False),
    "screen_watch": ("Ekran izleme", "İzin verilince belirli süre ekranı okuyup gün özeti çıkarır (görüntü saklanmaz)", "görsel model", False),
    "image_gen": ("Görsel üretme", "Metinden görsel (bulut sağlayıcı anahtarı gerekir)", "OpenAI/Gemini anahtarı", False),
    "clipboardline": ("ClipBoardLine", "Hazır kopya geçmişi uygulamasını kurar/başlatır; içeriğini (sırlar hariç) beyne okur", "uygulama kurulumu (~520 MB)", True),
    "nashi": ("Nashi", "Hazır dosya dönüştürücü uygulamayı kurar/başlatır; dışa aktardığı dosyaları beyne okur", "uygulama kurulumu (~91 MB)", True),
    "memory_ui": ("Hafıza ve kişilik", "Asistan kimliği, ortak günlük, tercih öğrenme, hafıza düzenleyici, yansıma", "model", True),
    "cards": ("Bilgi kartları", "Notlardan kart üretme ve aralıklı tekrar", "model", True),
    "automation": ("Otomasyonlar ve ajanlar", "Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu", "model", True),
}
TOOL_MODULE = {          # asistan aracı → modül (listede olmayan araç her zaman açık)
    "calendar_add": "calendar", "calendar_delete": "calendar", "calendar_list": "calendar",
    "open_app": "computer", "media": "computer", "sys_info": "computer", "run_command": "computer", "web_search": "computer",
    "play_spotify": "media", "play_youtube": "media", "whatsapp_draft": "whatsapp",
    "screen_read": "vision", "camera_read": "vision", "brain_capture": "capture", "inbox_add": "inbox",
}
STEP_MODULE = {          # günlük çalışma komutu → modül
    "mail-fetch": None, "sms-sync": "sms", "mail-categorize": "gmail", "extract-dates": "dates", "approve": "calendar",
    "sync-gcal": "calendar", "inbox-process": "inbox", "contacts-sync": "contacts", "drive-sync": "drive", "drive-index": "drive",
    "local-files": "local_files", "content-sync": "local_files", "projects-sync": "projects", "project-deep": "projects",
    "course-files": "courses", "course-deep": "courses", "sessions-sync": "sessions", "obs-import": "courses", "mail-index": "gmail",
    "index": "brain", "mentions": "brain", "chat-links": "brain", "merge-people": "brain", "search2": "brain", "derive": "derived",
    "github-deep": "github", "apps": None, "clusters": "brain", "suggest-links": "brain", "analyze": "brain", "persona": "memory_ui", "graph-style": "brain", "automation-tick": "automation",
}


@lru_cache(maxsize=1)
def _choices() -> dict:
    if not CONFIG.exists():
        return {}
    return (yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}).get("modules") or {}


def reload() -> None:
    _choices.cache_clear()


def enabled(key: str | None) -> bool:
    if not key:
        return True
    if key not in MODULES:
        return True
    return bool(_choices().get(key, MODULES[key][3]))


def step_enabled(args: list[str]) -> bool:
    return enabled(STEP_MODULE.get(args[0])) if args else True


def tool_enabled(name: str) -> bool:
    return enabled(TOOL_MODULE.get(name))


def set_modules(on: list[str] | None = None, off: list[str] | None = None) -> str:
    bad = [k for k in (on or []) + (off or []) if k not in MODULES]
    if bad:
        return f"Bilinmeyen modül: {', '.join(bad)}. Liste: sb features"
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else None
    data = data or {}
    mods = data.setdefault("modules", {})
    for k in on or []:
        mods[k] = True
    for k in off or []:
        mods[k] = False
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text("# Hangi modüller açık (sb features --on/--off ya da kurulum paneli yazar). Olmayan anahtar varsayılanı alır.\n"
                      + yaml.safe_dump(data, allow_unicode=True, sort_keys=True), encoding="utf-8")
    reload()
    return listing()


def listing() -> str:
    rows = [f"{'✓' if enabled(k) else '·'} {k:13} {ad} — {desc} (gerekir: {req})" for k, (ad, desc, req, _) in MODULES.items()]
    return "\n".join(rows)


def catalog() -> list[dict]:
    if not CATALOG.exists():
        return []
    return (yaml.safe_load(CATALOG.read_text(encoding="utf-8")) or {}).get("ozellikler") or []


def roadmap() -> str:
    items = catalog()
    if not items:
        return "Katalog yok (features.yaml)."
    out = [f"Toplam {len(items)} özellik: " + ", ".join(f"{k} {v}" for k, v in Counter(i["durum"] for i in items).most_common())]
    for faz in sorted({i["faz"] for i in items}):
        part = [i for i in items if i["faz"] == faz]
        done = sum(1 for i in part if i["durum"] == "tamamlandi")
        out.append(f"Faz {faz} ({part[0]['surum']}): {done}/{len(part)} tamam")
    return "\n".join(out)


def mark(ids: list[int], status: str) -> str:
    text = CATALOG.read_text(encoding="utf-8")
    head = "".join(l for l in text.splitlines(keepends=True) if l.startswith("#"))
    data = yaml.safe_load(text)
    hit = 0
    for i in data["ozellikler"]:
        if i["id"] in ids:
            i["durum"] = status
            hit += 1
    CATALOG.write_text(head + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8")
    return f"{hit} madde → {status}"
