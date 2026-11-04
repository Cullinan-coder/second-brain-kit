# Modüller (özellik grupları)

Second Brain **51 modül**den oluşur; her modül özellik kataloğundaki maddeleri gruplar. Her modülün sayfasında: ne işe yarar, nasıl açılır, ne ister, nasıl kullanılır, hangi hazır seçimlerde açıktır ve maddeleri tek tek bulunur.

## Mail ve takvim

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Google Takvim](moduller/calendar.md) | Takvimi kasaya alır; onaylı ekleme ve silme | 2 | açık |
| [Google Rehber](moduller/contacts.md) | Kişi notları | 1 | açık |
| [Tarih çıkarma](moduller/dates.md) | Mail/SMS'ten teslim ve randevu tarihlerini çıkarıp onaya sunar | 1 | açık |
| [Fatura ve kargo](moduller/derived.md) | Maillerden fatura ve kargo kayıtları | 3 | açık |
| [Sabah özeti maili](moduller/digest.md) | Her gün özet maili ve günlük not | 0 | açık |
| [Google Drive](moduller/drive.md) | Drive dosya listesi ve notları | 0 | açık |
| [Gmail](moduller/gmail.md) | Gmail hesaplarını salt okunur arşivler, kategorilere ayırır | 0 | açık |
| [Şirket/okul maili (IMAP)](moduller/imap.md) | IMAP hesaplarını salt okunur arşivler | 0 | açık |

## Telefon ve mesaj

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Telefon erişimi](moduller/phone.md) | Asistana telefondan Tailscale ile erişim | 8 | açık |
| [SMS ve aramalar](moduller/sms.md) | Telefon yedeğinden SMS/arama | 1 | açık |
| [Telegram botu](moduller/telegram.md) | Telegram'dan not alma ve özet | 0 | açık |
| [WhatsApp](moduller/whatsapp.md) | Onaylı mesaj taslağı ve gönderme | 2 | açık |

## Okul ve proje

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Tarayıcı geçmişi](moduller/browser.md) | Chrome/Edge/Firefox geçmişi ve yer imleri (giriş/banka sayfaları hariç) | 1 | açık |
| [Okul (ÖBS/LMS)](moduller/courses.md) | Ders notları, ders dosyaları, ders derlemesi | 13 | açık |
| [GitHub derin](moduller/github.md) | Issue, PR, commit ve release kayıtları | 2 | açık |
| [LinkedIn arşivi](moduller/linkedin.md) | LinkedIn veri arşivini içe aktarır | 0 | açık |
| [Bilgisayar dosyaları](moduller/local_files.md) | Klasör notları ve belge içerik dizini | 0 | açık |
| [Projeler ve GitHub](moduller/projects.md) | Kod projelerini tarar; proje dosyası derler | 0 | açık |
| [Claude Code oturumları](moduller/sessions.md) | Proje oturum günlükleri | 0 | açık |

## Asistan ve hafıza

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Yerel asistan](moduller/assistant.md) | Obsidian yan paneli ve telefondan sohbet | 10 | açık |
| [Otomasyonlar ve ajanlar](moduller/automation.md) | Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu | 10 | açık |
| [Beyne at](moduller/capture.md) | Ctrl+Alt+B, Gönder › Beyne At, ekran görüntüsü, web/video özeti | 3 | açık |
| [Bilgi kartları](moduller/cards.md) | Notlardan kart üretme ve aralıklı tekrar | 4 | açık |
| [Claude Code hafızası](moduller/claude_hooks.md) | Kancalar, son oturum kartları, makbuz, skill'ler | 1 | açık |
| [Oturum özetleri](moduller/flush.md) | Sıkıştırma öncesi / oturum sonu yerel model özeti | 0 | açık |
| [Not kutusu](moduller/inbox.md) | 00-Inbox/Dump notlarını yerine dağıtır | 0 | açık |
| [Hafıza ve kişilik](moduller/memory_ui.md) | Asistan kimliği, ortak günlük, tercih öğrenme, hafıza düzenleyici, yansıma | 9 | açık |
| [Gece koşusu](moduller/night.md) | İstenince gece işlerini Claude Code'a sırayla yaptırır | 1 | açık |

## Bilgisayar ve ses

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Bilgisayar kontrolü](moduller/computer.md) | Uygulama açma, ses, sistem bilgisi, komut (onaylı) | 1 | açık |
| [Görsel üretme](moduller/image_gen.md) | Metinden görsel (bulut sağlayıcı anahtarı gerekir) | 1 | kapalı |
| [Spotify ve YouTube](moduller/media.md) | Şarkı/video açma | 0 | açık |
| [Ekran izleme](moduller/screen_watch.md) | İzin verilince belirli süre ekranı okuyup gün özeti çıkarır (görüntü saklanmaz) | 1 | kapalı |
| [Ekran ve kamera](moduller/vision.md) | Ekranı/kamerayı okuyup anlatma | 3 | açık |
| [Ses](moduller/voice.md) | Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı | 10 | açık |
| [Uyandırma sözcüğü](moduller/wake_word.md) | 'Hey <asistan>' ile dinlemeye başlar (yalnız sekme açıkken) | 1 | kapalı |

## Kurulum ve model

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Model katmanı](moduller/models.md) | Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi. | 15 | açık |
| [Kurulum paneli ve ürünleşme](moduller/setup.md) | Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık. | 22 | açık |

## Arayüz ve mobil

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Arayüz ve tasarım](moduller/ui_core.md) | Tasarım sistemi, ana panel, komut paleti, bildirimler, masaüstü uygulaması, graf/zaman çizelgesi. | 10 | açık |

## Arama ve beyin

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Beyin dizini](moduller/brain.md) | Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler | 20 | açık |
| [Arama ve cevaplar](moduller/search.md) | Karma arama, kaynaklı cevap, doğal dil süzgeçleri, kayıtlı aramalar, araştırma. | 12 | açık |

## Verimlilik ve iletişim

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [İletişim yardımcıları](moduller/comms.md) | Mail taslağı, zincir özeti, takip, kişiye özel ton, ilişki sağlığı. | 10 | açık |
| [Kopya geçmişi (Pano)](moduller/pano.md) | Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez. | 8 | kapalı |
| [Görev ve planlama](moduller/tasks_plan.md) | Kanban, günlük plan, alışkanlık, OKR, haftalık gözden geçirme, toplantı hazırlığı. | 14 | açık |

## Kariyer ve yaşam

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Kariyer ve iş](moduller/career.md) | Mini CRM, teklif/fatura, saat takibi, başvuru, CV, portfolyo. | 12 | açık |
| [Kişisel yaşam](moduller/life.md) | Harcama, abonelik, seyahat, sağlık hatırlatma, tarif, günlük. | 9 | açık |

## Gizlilik ve kalite

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Gizlilik ve güvenlik](moduller/privacy.md) | Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek. | 8 | açık |
| [Kalite ve gözlemlenebilirlik](moduller/quality.md) | Uçtan uca test, çökme raporu, performans panosu, Yenilikler ekranı. | 4 | açık |

## Veri kaynakları

| Modül | Ne yapar | Madde | Varsayılan |
|---|---|---|---|
| [Mesaj içe aktarmaları](moduller/imports_comm.md) | Outlook, iCloud, Telegram, Discord, Slack arşivleri. | 5 | açık |
| [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları. | 10 | açık |
| [Medya ve okuma içe aktarmaları](moduller/imports_media.md) | Kindle, Pocket/Raindrop, YouTube, Spotify, RSS. | 5 | açık |
| [Not ve görev içe aktarmaları](moduller/imports_notes.md) | Notion, Keep, Apple Notlar, OneNote, Evernote, Todoist, Trello, Jira, Linear. | 5 | açık |
