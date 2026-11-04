# Hazır seçimler

Sihirbazın 2. adımı dört ekseni birlikte seçtirir. Sonuç, 3. adımda tek tek değiştirebileceğin bir başlangıç listesidir.

**Birleştirme sırası:** önce *yoğunluk* temel modül listesini verir → *meslek* modül ekler → *gizlilik* ve *donanım* kısıtlar (modül kapatır, model profili belirler). Bir modül kapanırsa ona bağlı olan da kapanır (ör. ses kapanınca uyandırma sözcüğü; Gmail ve IMAP ikisi de kapanınca sabah özeti).

Varsayılan seçimler: Donanım = **Orta (8-14 GB VRAM)**, Gizlilik = **Karma**, Yoğunluk = **Günlük hayat**; meslek varsayılan olarak seçili değildir.

## Yoğunluk

### Minimal

Yalnız kasa + Obsidian + asistan.

**Açılan modüller (7):** [Yerel asistan](moduller/assistant.md), [Beyne at](moduller/capture.md), [Not kutusu](moduller/inbox.md), [Claude Code hafızası](moduller/claude_hooks.md), [Kurulum paneli ve ürünleşme](moduller/setup.md), [Gizlilik ve güvenlik](moduller/privacy.md), [Model katmanı](moduller/models.md)

### Günlük hayat

Mail, takvim, arama, hafıza ve plan; ağır özellikler kapalı.

**Açılan modüller (24):** [Yerel asistan](moduller/assistant.md), [Beyne at](moduller/capture.md), [Not kutusu](moduller/inbox.md), [Claude Code hafızası](moduller/claude_hooks.md), [Kurulum paneli ve ürünleşme](moduller/setup.md), [Gizlilik ve güvenlik](moduller/privacy.md), [Model katmanı](moduller/models.md), [Gmail](moduller/gmail.md), [Google Takvim](moduller/calendar.md), [Tarih çıkarma](moduller/dates.md), [Google Rehber](moduller/contacts.md), [Sabah özeti maili](moduller/digest.md), [Fatura ve kargo](moduller/derived.md), [Hafıza ve kişilik](moduller/memory_ui.md), [Beyin dizini](moduller/brain.md), [Oturum özetleri](moduller/flush.md), [Claude Code oturumları](moduller/sessions.md), [Projeler ve GitHub](moduller/projects.md), [Bilgisayar dosyaları](moduller/local_files.md), [Telefon erişimi](moduller/phone.md), [Arama ve cevaplar](moduller/search.md), [Arayüz ve tasarım](moduller/ui_core.md), [Görev ve planlama](moduller/tasks_plan.md), [Bilgi kartları](moduller/cards.md)

### Güç kullanıcısı

Her şey açık (ek özellikler hariç: uyandırma sözcüğü, ekran izleme, görsel üretme).

**Açılan modüller (49):** [Yerel asistan](moduller/assistant.md), [Otomasyonlar ve ajanlar](moduller/automation.md), [Beyin dizini](moduller/brain.md), [Tarayıcı geçmişi](moduller/browser.md), [Google Takvim](moduller/calendar.md), [Beyne at](moduller/capture.md), [Bilgi kartları](moduller/cards.md), [Kariyer ve iş](moduller/career.md), [Claude Code hafızası](moduller/claude_hooks.md), [ClipBoardLine (kopya geçmişi)](moduller/clipboardline.md), [İletişim yardımcıları](moduller/comms.md), [Bilgisayar kontrolü](moduller/computer.md), [Google Rehber](moduller/contacts.md), [Okul (ÖBS/LMS)](moduller/courses.md), [Tarih çıkarma](moduller/dates.md), [Fatura ve kargo](moduller/derived.md), [Sabah özeti maili](moduller/digest.md), [Google Drive](moduller/drive.md), [Oturum özetleri](moduller/flush.md), [GitHub derin](moduller/github.md), [Gmail](moduller/gmail.md), [Şirket/okul maili (IMAP)](moduller/imap.md), [Mesaj içe aktarmaları](moduller/imports_comm.md), [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md), [Medya ve okuma içe aktarmaları](moduller/imports_media.md), [Not ve görev içe aktarmaları](moduller/imports_notes.md), [Not kutusu](moduller/inbox.md), [Kişisel yaşam](moduller/life.md), [LinkedIn arşivi](moduller/linkedin.md), [Bilgisayar dosyaları](moduller/local_files.md), [Spotify ve YouTube](moduller/media.md), [Hafıza ve kişilik](moduller/memory_ui.md), [Model katmanı](moduller/models.md), [Nashi (dosya dönüştürücü)](moduller/nashi.md), [Gece koşusu](moduller/night.md), [Telefon erişimi](moduller/phone.md), [Gizlilik ve güvenlik](moduller/privacy.md), [Projeler ve GitHub](moduller/projects.md), [Kalite ve gözlemlenebilirlik](moduller/quality.md), [Arama ve cevaplar](moduller/search.md), [Claude Code oturumları](moduller/sessions.md), [Kurulum paneli ve ürünleşme](moduller/setup.md), [SMS ve aramalar](moduller/sms.md), [Görev ve planlama](moduller/tasks_plan.md), [Telegram botu](moduller/telegram.md), [Arayüz ve tasarım](moduller/ui_core.md), [Ekran ve kamera](moduller/vision.md), [Ses](moduller/voice.md), [WhatsApp](moduller/whatsapp.md)

## Meslek

### Öğrenci

Okul, ders, kartlar, sınav planı.

**Eklenen modüller (9):** [Gmail](moduller/gmail.md), [Google Takvim](moduller/calendar.md), [Tarih çıkarma](moduller/dates.md), [Okul (ÖBS/LMS)](moduller/courses.md), [Bilgi kartları](moduller/cards.md), [Görev ve planlama](moduller/tasks_plan.md), [Hafıza ve kişilik](moduller/memory_ui.md), [Ses](moduller/voice.md), [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md)

### Ajans / Freelancer

CRM, mail, projeler, teklif ve saat takibi.

**Eklenen modüller (14):** [Gmail](moduller/gmail.md), [Şirket/okul maili (IMAP)](moduller/imap.md), [Google Takvim](moduller/calendar.md), [Tarih çıkarma](moduller/dates.md), [Google Rehber](moduller/contacts.md), [Google Drive](moduller/drive.md), [Fatura ve kargo](moduller/derived.md), [Sabah özeti maili](moduller/digest.md), [Projeler ve GitHub](moduller/projects.md), [GitHub derin](moduller/github.md), [Otomasyonlar ve ajanlar](moduller/automation.md), [WhatsApp](moduller/whatsapp.md), [Kariyer ve iş](moduller/career.md), [İletişim yardımcıları](moduller/comms.md)

### Yazılımcı

Projeler, GitHub, Claude Code hafızası, gece koşusu.

**Eklenen modüller (10):** [Projeler ve GitHub](moduller/projects.md), [GitHub derin](moduller/github.md), [Claude Code oturumları](moduller/sessions.md), [Claude Code hafızası](moduller/claude_hooks.md), [Oturum özetleri](moduller/flush.md), [Gece koşusu](moduller/night.md), [Otomasyonlar ve ajanlar](moduller/automation.md), [Tarayıcı geçmişi](moduller/browser.md), [Beyin dizini](moduller/brain.md), [Arama ve cevaplar](moduller/search.md)

### Akademisyen

Ders, kaynakça, arama, akademik kaynaklar.

**Eklenen modüller (9):** [Okul (ÖBS/LMS)](moduller/courses.md), [Bilgi kartları](moduller/cards.md), [Google Drive](moduller/drive.md), [Bilgisayar dosyaları](moduller/local_files.md), [Beyin dizini](moduller/brain.md), [Arama ve cevaplar](moduller/search.md), [Ses](moduller/voice.md), [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md), [Medya ve okuma içe aktarmaları](moduller/imports_media.md)

### Girişimci

Mail, CRM, otomasyon, finans ve yaşam düzeni.

**Eklenen modüller (13):** [Gmail](moduller/gmail.md), [Şirket/okul maili (IMAP)](moduller/imap.md), [Google Takvim](moduller/calendar.md), [Google Rehber](moduller/contacts.md), [Google Drive](moduller/drive.md), [Fatura ve kargo](moduller/derived.md), [Sabah özeti maili](moduller/digest.md), [Otomasyonlar ve ajanlar](moduller/automation.md), [WhatsApp](moduller/whatsapp.md), [Telegram botu](moduller/telegram.md), [Kariyer ve iş](moduller/career.md), [İletişim yardımcıları](moduller/comms.md), [Kişisel yaşam](moduller/life.md)

### Satış / CRM

Kişi, mail, WhatsApp, LinkedIn, takip hatırlatmaları.

**Eklenen modüller (12):** [Gmail](moduller/gmail.md), [Şirket/okul maili (IMAP)](moduller/imap.md), [Google Rehber](moduller/contacts.md), [Google Takvim](moduller/calendar.md), [WhatsApp](moduller/whatsapp.md), [LinkedIn arşivi](moduller/linkedin.md), [SMS ve aramalar](moduller/sms.md), [Fatura ve kargo](moduller/derived.md), [Sabah özeti maili](moduller/digest.md), [Otomasyonlar ve ajanlar](moduller/automation.md), [Kariyer ve iş](moduller/career.md), [İletişim yardımcıları](moduller/comms.md)

### İçerik üreticisi

Yakalama, medya, LinkedIn gönderisi, ses ve görsel üretim.

**Eklenen modüller (8):** [Spotify ve YouTube](moduller/media.md), [Tarayıcı geçmişi](moduller/browser.md), [LinkedIn arşivi](moduller/linkedin.md), [Google Drive](moduller/drive.md), [Ses](moduller/voice.md), [Görsel üretme](moduller/image_gen.md), [Medya ve okuma içe aktarmaları](moduller/imports_media.md), [İletişim yardımcıları](moduller/comms.md)

### Araştırmacı

Derin arama, tarayıcı geçmişi, kartlar, akademik kaynaklar.

**Eklenen modüller (11):** [Beyin dizini](moduller/brain.md), [Arama ve cevaplar](moduller/search.md), [Tarayıcı geçmişi](moduller/browser.md), [Bilgisayar dosyaları](moduller/local_files.md), [Google Drive](moduller/drive.md), [Bilgi kartları](moduller/cards.md), [Ses](moduller/voice.md), [Ekran ve kamera](moduller/vision.md), [Otomasyonlar ve ajanlar](moduller/automation.md), [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md), [Medya ve okuma içe aktarmaları](moduller/imports_media.md)

## Gizlilik

### Tam yerel

Hiçbir istek buluta gitmez; yalnız yerel model.

**Kapatılan modüller:** [Görsel üretme](moduller/image_gen.md)
**Model ayarı:** `local_model` = `True`, `cloud` = `False`
**Gizlilik profili:** `mode` = `tam_yerel`, `permission_profile` = `sıkı`, `cloud_send` = `never`, `mask` = `True`

### Karma

Özel notlar yerelde; genel işler buluta gidebilir, maskeleme açık.

**Kapatılan modül:** yok.
**Model ayarı:** `cloud` = `True`
**Gizlilik profili:** `mode` = `karma`, `permission_profile` = `normal`, `cloud_send` = `masked`, `mask` = `True`

### Bulut öncelikli

Bulut modeller öncelikli; gizli etiketli notlar yine yerelde.

**Kapatılan modül:** yok.
**Model ayarı:** `cloud` = `True`, `prefer_cloud` = `True`
**Gizlilik profili:** `mode` = `bulut`, `permission_profile` = `normal`, `cloud_send` = `masked`, `mask` = `True`

## Donanım

### Güçlü ekran kartı (14 GB+ VRAM)

14B yazı + 8B görüntü modeli yerelde.

**Kapatılan modül:** yok.
**Model ayarı:** `profile` = `full`, `local_model` = `True`

### Orta (8-14 GB VRAM)

8B yazı + 4B görüntü modeli; ağır izleme kapalı.

**Kapatılan modüller:** [Ekran izleme](moduller/screen_watch.md), [Uyandırma sözcüğü](moduller/wake_word.md)
**Model ayarı:** `profile` = `medium`, `local_model` = `True`

### Zayıf laptop / bulut

Ekran kartı yok ya da < 4 GB: asistan bulut API ile.

**Kapatılan modüller:** [Ekran ve kamera](moduller/vision.md), [Ekran izleme](moduller/screen_watch.md), [Uyandırma sözcüğü](moduller/wake_word.md), [Ses](moduller/voice.md)
**Model ayarı:** `profile` = `cloud`, `local_model` = `False`

### Mac (Apple Silicon)

Birleşik bellek; 16 GB altında orta profil, 32 GB+ güçlü profil önerilir.

**Kapatılan modüller:** [Uyandırma sözcüğü](moduller/wake_word.md), [Ekran izleme](moduller/screen_watch.md)
**Model ayarı:** `profile` = `medium`, `local_model` = `True`, `profile_if_ram_gb_ge` = `{'32': 'full'}`

## Modül × yoğunluk tablosu

| Modül | Minimal | Günlük hayat | Güç kullanıcısı |
|---|---|---|---|
| [Yerel asistan](moduller/assistant.md) | ● | ● | ● |
| [Otomasyonlar ve ajanlar](moduller/automation.md) |  |  | ● |
| [Beyin dizini](moduller/brain.md) |  | ● | ● |
| [Tarayıcı geçmişi](moduller/browser.md) |  |  | ● |
| [Google Takvim](moduller/calendar.md) |  | ● | ● |
| [Beyne at](moduller/capture.md) | ● | ● | ● |
| [Bilgi kartları](moduller/cards.md) |  | ● | ● |
| [Kariyer ve iş](moduller/career.md) |  |  | ● |
| [Claude Code hafızası](moduller/claude_hooks.md) | ● | ● | ● |
| [ClipBoardLine (kopya geçmişi)](moduller/clipboardline.md) |  |  | ● |
| [İletişim yardımcıları](moduller/comms.md) |  |  | ● |
| [Bilgisayar kontrolü](moduller/computer.md) |  |  | ● |
| [Google Rehber](moduller/contacts.md) |  | ● | ● |
| [Okul (ÖBS/LMS)](moduller/courses.md) |  |  | ● |
| [Tarih çıkarma](moduller/dates.md) |  | ● | ● |
| [Fatura ve kargo](moduller/derived.md) |  | ● | ● |
| [Sabah özeti maili](moduller/digest.md) |  | ● | ● |
| [Google Drive](moduller/drive.md) |  |  | ● |
| [Oturum özetleri](moduller/flush.md) |  | ● | ● |
| [GitHub derin](moduller/github.md) |  |  | ● |
| [Gmail](moduller/gmail.md) |  | ● | ● |
| [Görsel üretme](moduller/image_gen.md) |  |  |  |
| [Şirket/okul maili (IMAP)](moduller/imap.md) |  |  | ● |
| [Mesaj içe aktarmaları](moduller/imports_comm.md) |  |  | ● |
| [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) |  |  | ● |
| [Medya ve okuma içe aktarmaları](moduller/imports_media.md) |  |  | ● |
| [Not ve görev içe aktarmaları](moduller/imports_notes.md) |  |  | ● |
| [Not kutusu](moduller/inbox.md) | ● | ● | ● |
| [Kişisel yaşam](moduller/life.md) |  |  | ● |
| [LinkedIn arşivi](moduller/linkedin.md) |  |  | ● |
| [Bilgisayar dosyaları](moduller/local_files.md) |  | ● | ● |
| [Spotify ve YouTube](moduller/media.md) |  |  | ● |
| [Hafıza ve kişilik](moduller/memory_ui.md) |  | ● | ● |
| [Model katmanı](moduller/models.md) | ● | ● | ● |
| [Nashi (dosya dönüştürücü)](moduller/nashi.md) |  |  | ● |
| [Gece koşusu](moduller/night.md) |  |  | ● |
| [Telefon erişimi](moduller/phone.md) |  | ● | ● |
| [Gizlilik ve güvenlik](moduller/privacy.md) | ● | ● | ● |
| [Projeler ve GitHub](moduller/projects.md) |  | ● | ● |
| [Kalite ve gözlemlenebilirlik](moduller/quality.md) |  |  | ● |
| [Ekran izleme](moduller/screen_watch.md) |  |  |  |
| [Arama ve cevaplar](moduller/search.md) |  | ● | ● |
| [Claude Code oturumları](moduller/sessions.md) |  | ● | ● |
| [Kurulum paneli ve ürünleşme](moduller/setup.md) | ● | ● | ● |
| [SMS ve aramalar](moduller/sms.md) |  |  | ● |
| [Görev ve planlama](moduller/tasks_plan.md) |  | ● | ● |
| [Telegram botu](moduller/telegram.md) |  |  | ● |
| [Arayüz ve tasarım](moduller/ui_core.md) |  | ● | ● |
| [Ekran ve kamera](moduller/vision.md) |  |  | ● |
| [Ses](moduller/voice.md) |  |  | ● |
| [Uyandırma sözcüğü](moduller/wake_word.md) |  |  |  |
| [WhatsApp](moduller/whatsapp.md) |  |  | ● |

● = o yoğunlukta açık.

## Modül × meslek tablosu

| Modül | Öğrenci | Ajans / Freelancer | Yazılımcı | Akademisyen | Girişimci | Satış / CRM | İçerik üreticisi | Araştırmacı |
|---|---|---|---|---|---|---|---|---|
| [Yerel asistan](moduller/assistant.md) |  |  |  |  |  |  |  |  |
| [Otomasyonlar ve ajanlar](moduller/automation.md) |  | ● | ● |  | ● | ● |  | ● |
| [Beyin dizini](moduller/brain.md) |  |  | ● | ● |  |  |  | ● |
| [Tarayıcı geçmişi](moduller/browser.md) |  |  | ● |  |  |  | ● | ● |
| [Google Takvim](moduller/calendar.md) | ● | ● |  |  | ● | ● |  |  |
| [Beyne at](moduller/capture.md) |  |  |  |  |  |  |  |  |
| [Bilgi kartları](moduller/cards.md) | ● |  |  | ● |  |  |  | ● |
| [Kariyer ve iş](moduller/career.md) |  | ● |  |  | ● | ● |  |  |
| [Claude Code hafızası](moduller/claude_hooks.md) |  |  | ● |  |  |  |  |  |
| [ClipBoardLine (kopya geçmişi)](moduller/clipboardline.md) |  |  |  |  |  |  |  |  |
| [İletişim yardımcıları](moduller/comms.md) |  | ● |  |  | ● | ● | ● |  |
| [Bilgisayar kontrolü](moduller/computer.md) |  |  |  |  |  |  |  |  |
| [Google Rehber](moduller/contacts.md) |  | ● |  |  | ● | ● |  |  |
| [Okul (ÖBS/LMS)](moduller/courses.md) | ● |  |  | ● |  |  |  |  |
| [Tarih çıkarma](moduller/dates.md) | ● | ● |  |  |  |  |  |  |
| [Fatura ve kargo](moduller/derived.md) |  | ● |  |  | ● | ● |  |  |
| [Sabah özeti maili](moduller/digest.md) |  | ● |  |  | ● | ● |  |  |
| [Google Drive](moduller/drive.md) |  | ● |  | ● | ● |  | ● | ● |
| [Oturum özetleri](moduller/flush.md) |  |  | ● |  |  |  |  |  |
| [GitHub derin](moduller/github.md) |  | ● | ● |  |  |  |  |  |
| [Gmail](moduller/gmail.md) | ● | ● |  |  | ● | ● |  |  |
| [Görsel üretme](moduller/image_gen.md) |  |  |  |  |  |  | ● |  |
| [Şirket/okul maili (IMAP)](moduller/imap.md) |  | ● |  |  | ● | ● |  |  |
| [Mesaj içe aktarmaları](moduller/imports_comm.md) |  |  |  |  |  |  |  |  |
| [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | ● |  |  | ● |  |  |  | ● |
| [Medya ve okuma içe aktarmaları](moduller/imports_media.md) |  |  |  | ● |  |  | ● | ● |
| [Not ve görev içe aktarmaları](moduller/imports_notes.md) |  |  |  |  |  |  |  |  |
| [Not kutusu](moduller/inbox.md) |  |  |  |  |  |  |  |  |
| [Kişisel yaşam](moduller/life.md) |  |  |  |  | ● |  |  |  |
| [LinkedIn arşivi](moduller/linkedin.md) |  |  |  |  |  | ● | ● |  |
| [Bilgisayar dosyaları](moduller/local_files.md) |  |  |  | ● |  |  |  | ● |
| [Spotify ve YouTube](moduller/media.md) |  |  |  |  |  |  | ● |  |
| [Hafıza ve kişilik](moduller/memory_ui.md) | ● |  |  |  |  |  |  |  |
| [Model katmanı](moduller/models.md) |  |  |  |  |  |  |  |  |
| [Nashi (dosya dönüştürücü)](moduller/nashi.md) |  |  |  |  |  |  |  |  |
| [Gece koşusu](moduller/night.md) |  |  | ● |  |  |  |  |  |
| [Telefon erişimi](moduller/phone.md) |  |  |  |  |  |  |  |  |
| [Gizlilik ve güvenlik](moduller/privacy.md) |  |  |  |  |  |  |  |  |
| [Projeler ve GitHub](moduller/projects.md) |  | ● | ● |  |  |  |  |  |
| [Kalite ve gözlemlenebilirlik](moduller/quality.md) |  |  |  |  |  |  |  |  |
| [Ekran izleme](moduller/screen_watch.md) |  |  |  |  |  |  |  |  |
| [Arama ve cevaplar](moduller/search.md) |  |  | ● | ● |  |  |  | ● |
| [Claude Code oturumları](moduller/sessions.md) |  |  | ● |  |  |  |  |  |
| [Kurulum paneli ve ürünleşme](moduller/setup.md) |  |  |  |  |  |  |  |  |
| [SMS ve aramalar](moduller/sms.md) |  |  |  |  |  | ● |  |  |
| [Görev ve planlama](moduller/tasks_plan.md) | ● |  |  |  |  |  |  |  |
| [Telegram botu](moduller/telegram.md) |  |  |  |  | ● |  |  |  |
| [Arayüz ve tasarım](moduller/ui_core.md) |  |  |  |  |  |  |  |  |
| [Ekran ve kamera](moduller/vision.md) |  |  |  |  |  |  |  | ● |
| [Ses](moduller/voice.md) | ● |  |  | ● |  |  | ● | ● |
| [Uyandırma sözcüğü](moduller/wake_word.md) |  |  |  |  |  |  |  |  |
| [WhatsApp](moduller/whatsapp.md) |  | ● |  |  | ● | ● |  |  |

● = o meslek seçilince eklenir.

Sihirbazdaki ekranın tanıtımı: [Sihirbaz adım adım](02-sihirbaz-adim-adim.md#adim-2-hazir-secim).
