---
name: beyin
description: Second Brain kasasında hafıza işleri — iş sonucu makbuzu, son günler özeti, öğrenim/kavram/bağlantı notları, görev, kişi bilgisi, kural, sohbet izi, hata kataloğu, beyne atma. "makbuz yaz", "ne yaptık", "son günlerde", "bunu öğrendik", "kavram notu", "görev aç", "kişi notu", "kural ekle", "hata kataloğu", "beyne at", oturum kapanışı ve anlamlı bir iş bittiğinde kullan.
---

# Beyin (Second Brain hafıza protokolü)

Kasa: profildeki Obsidian kasası (ör. `~/SecondBrain`). Komut: `sb <komut>` (her klasörden çalışır; yoksa
`uv run --directory <kasa>/_system python -m sb <komut>`). Okuma için second-brain MCP araçlarını kullan
(brain_overview, brain_project, brain_search, brain_note, brain_recap). Her yazım ayrı git commit'idir; `sb asistan-undo` geri alır.

## Anlamlı iş bitince (her cevapta değil)
1. **Makbuz**: `sb receipt --summary "Yapılan iş + doğrulama + açık kalan" --ref <kasa-içi-yol> [--link https://pr] --learned "<tek cümle ya da boş>" --project <proje> --session <oturum-id-8>`
   - Planı bitmiş iş gibi yazma. `--ref` kasada var olan dosya olmalı (yoksa komut reddeder).
   - Öğrenim yoksa `--learned` boş bırak (makbuzda "Öğrenilen: yok" yazar).
2. **Kalıcı öğrenim** varsa önce `40-Kaynaklar/Kavramlar/_Dizin.md`'yi oku, sonra yalnız ilgili kavramı:
   `sb concept "Konu" --text "kısa açıklama" --point "..." --limits "sınır/gerekçe" --source <kasa-yolu>` (varsa tarihli ekleme yapar).
   Olgunlaşmamışsa: `sb learn "aday" --source <yol> --scope <proje>`; liste: `sb learn --list`.
3. İki not arasında **gerçek** ilişki varsa: `sb connect "A" "B" --why "neden bağlı (bir cümle)"`. Kota doldurmak için bağlantı kurma.
4. **Devir kartı**: `Son oturum.md` en üstüne kendi kartın (Ne yapıldı / Kararlar / Nerede kaldık / Sıradaki); yarım kalanlar `Açık konular.md` → `## Aktif`.
5. Dosya değişmeyen ama anlamlı sohbet: `sb trace "≤450 karakter özet"`.

## Hatırlama
- "Son günlerde ne yaptık": `sb recap --days 7 [--project p]`. Makbuz satırları ajan beyanıdır; önemliyse kaynağı aç.
- Bulamazsan uydurma: "kasada bulamadım" de. Kaynağı ve tarihini söyle.
- `visibility: private` notlar otomatik bağlama girmez; kullanıcı açıkça istemedikçe açma.

## Görev ve kişi
- Görev: `sb task add "Başlık" --owner <kişi> --project <p> [--due YYYY-AA-GG] [--criterion "gözlenebilir bitiş ölçütü"]`.
  Sorumluyu uydurma; bilinmiyorsa sor. Bitirme: `sb task update "Başlık" --status tamamlandi --evidence <kasa-yolu>`
  (ölçütlü görev kanıtsız bitmez; görevin kendi dosyası kanıt olamaz). Liste: `sb task list`.
- Kişi: kullanıcının söylediği → `sb person "Ad Soyad" "bilgi"` (Beyan); senin tahminin → `--inference` (onay bekler);
  kullanıcı reddederse → `sb person "Ad" "metin" --reject`; takma ad → `--alias "Ayşe hoca"`.
  Sağlık, siyasi/dini görüş, finans, kimlik numarası yazma.

## Kurallar ve hatalar
- Kullanıcı düzeltirse kuralı beklemeden kaydet: genel → `sb rule "kural"`; tek projeye ait → `sb rule "kural" --scope <proje>`
  (ya da proje notunda `## Kurallar` bölümü). Tek seferlik biçim isteğini evrensel kural yapma.
- Aynı hata tekrarlanıyorsa: `sb error-log "hata" --fix "çözüm"` — ikinci kez yazılınca çözüm otomatik kural olur.
- Bir işi ikinci kez yapıyorsan onu **skill'e çevir**: `~/.claude/skills/<ad>/SKILL.md` (name, description tetikleyicileriyle;
  adım adım komutlar). Kaynağını `<kasa>/_system/skills/` altına da koy ki kit'e girsin.

## Beyne atma
- Bağlantı/metin: `sb capture "https://..."` (YouTube altyazısı ve web sayfası özetlenir), dosya: `sb capture --file <yol>`.
- Kullanıcı: Ctrl+Alt+B (pano), Sağ tık › Gönder › Beyne At (dosya), Obsidian Web Clipper şablonu (`_system/docs/web-clipper-beyne-at.json`).

## Sınırlar
Mail salt okunur (gönderme/silme yok). Şifre, kart, TC kimlik, IBAN kasaya yazılmaz. Takvim, WhatsApp ve dışarıya giden her
şey kullanıcı onayıyla. Basit soru ya da selamlaşmada kayıt yazma.
