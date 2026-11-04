# Sektör paketleri

Sektör paketi = çekirdek + bir tanım (modül/kaynak/MCP listesi, hazır seçim, roller, rapor şablonları, terimler). Kod değişmeden yeni sektör eklenir. Bu bir **şirket ürünü** yönüdür; kişisel kullanımda gerekmez.

## Kişisel (varsayılan)

Tek kişilik kullanım: öğrenci/çalışan/girişimci kendi verisiyle. Varsayılan sektör paketi.

- **Kimlik:** `kisisel`
- **Hazır seçim:** Donanım = Orta (8-14 GB VRAM), Gizlilik = Karma, Yoğunluk = Günlük hayat
- **Modüller:** [Gmail](moduller/gmail.md), [Google Takvim](moduller/calendar.md), [Tarih çıkarma](moduller/dates.md), [Google Rehber](moduller/contacts.md), [Sabah özeti maili](moduller/digest.md), [Beyin dizini](moduller/brain.md), [Yerel asistan](moduller/assistant.md), [Hafıza ve kişilik](moduller/memory_ui.md), [Beyne at](moduller/capture.md), [Not kutusu](moduller/inbox.md), [Claude Code hafızası](moduller/claude_hooks.md), [Oturum özetleri](moduller/flush.md), [Telefon erişimi](moduller/phone.md), [Arama ve cevaplar](moduller/search.md), [Gizlilik ve güvenlik](moduller/privacy.md)
- **Veri kaynakları:** [WhatsApp sohbetleri](kaynaklar/whatsapp.md), [Google Takeout](kaynaklar/takeout.md), [ChatGPT / Claude / Gemini sohbet geçmişi](kaynaklar/history-import.md)
- **MCP'ler:** [Second Brain (kendi MCP'miz)](mcp/second-brain.md)

### Roller

| Rol | Raporlar |
|---|---|
| Sahip |  |

### Rapor şablonları

| Rapor | Sıklık | Kaynaklar | Not |
|---|---|---|---|

### Not

Tek kullanıcı varsayımı: roller yalnız tanımdır, uygulamada tek rol vardır.

## Tekstil — Şirket Asistanı (Kyass pilotu)

Tekstil firması için firma sunucusunda çalışan, rol bazlı rapor veren asistan: satış, gelir-gider, mail özeti; üretim/defo modülü yakında.

- **Kimlik:** `tekstil`
- **Hazır seçim:** Meslek = Girişimci, Donanım = Orta (8-14 GB VRAM), Gizlilik = Tam yerel, Yoğunluk = Günlük hayat
- **Modüller:** [Gmail](moduller/gmail.md), [Şirket/okul maili (IMAP)](moduller/imap.md), [Google Takvim](moduller/calendar.md), [Tarih çıkarma](moduller/dates.md), [Google Drive](moduller/drive.md), [Fatura ve kargo](moduller/derived.md), [Sabah özeti maili](moduller/digest.md), [Bilgisayar dosyaları](moduller/local_files.md), [Beyin dizini](moduller/brain.md), [Arama ve cevaplar](moduller/search.md), [Kariyer ve iş](moduller/career.md), [İletişim yardımcıları](moduller/comms.md), [Otomasyonlar ve ajanlar](moduller/automation.md), [WhatsApp](moduller/whatsapp.md), [Yerel asistan](moduller/assistant.md), [Hafıza ve kişilik](moduller/memory_ui.md), [Gizlilik ve güvenlik](moduller/privacy.md), [Görev ve planlama](moduller/tasks_plan.md)
- **Veri kaynakları:** [Banka ekstresi (CSV)](kaynaklar/bank.md), [WhatsApp sohbetleri](kaynaklar/whatsapp.md), [Outlook / Microsoft 365 mail](kaynaklar/outlook.md)
- **MCP'ler:** [Second Brain (kendi MCP'miz)](mcp/second-brain.md), [Dosya sistemi](mcp/filesystem.md)

### Roller

| Rol | Raporlar |
|---|---|
| Patron | Satış raporu, Gelir-gider raporu, Mail özeti, Üretim özeti |
| Muhasebe | Gelir-gider raporu, Mail özeti |
| Satış | Satış raporu, Mail özeti |
| Üretim | Üretim özeti |

### Rapor şablonları

| Rapor | Sıklık | Kaynaklar | Not |
|---|---|---|---|
| Satış raporu | haftalik | gmail, imap, derived | Sayıları kod hesaplar, model yalnız yorumlar. |
| Gelir-gider raporu | aylik | bank, derived | Banka CSV'sinden numarasız özet; tutarları kod toplar. |
| Mail özeti | gunluk | gmail, imap | Cevap bekleyenler ve teslim tarihleri öne çıkar. |
| Üretim özeti | gunluk | — | yakında |

### Terimler

- **musteri:** müşteri / marka
- **siparis:** sipariş / iş emri
- **defo:** defo (iğne/platin izi vb. kumaş kusuru)
- **makine:** örgü makinesi

### Yakında

- **Üretim ve defo tespiti:** Seamless örgü makinesinde akustik iğne/platin izi tespiti; üretim hattı verisi. Henüz kodlanmadı.

### Not

Çok kullanıcı ve rol zorlaması bu pakette YOK: roller yalnız tanımdır; yetki ileride veri katmanında uygulanacak (docs/v1-plan.md, Uyarlanabilirlik ilkesi). Veri firma sunucusunda yerel kalır.
