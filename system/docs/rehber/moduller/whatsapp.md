# WhatsApp

> Onaylı mesaj gönderimi (kartı onaylayınca mesaj gönderilir)

| | |
|---|---|
| Modül kimliği | `whatsapp` |
| Kategori | Telefon ve mesaj |
| Varsayılan | açık |
| Madde sayısı | 2 |
| Ne ister | hesap: [WhatsApp](../03-hesaplar.md#hesap-whatsapp); program: WhatsApp Desktop |

## Ne işe yarar

Onaylı mesaj gönderimi (kartı onaylayınca mesaj gönderilir).

Bu modül özellik kataloğundan **2 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`WhatsApp`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on whatsapp` açar, `sb features --off whatsapp` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [WhatsApp](../03-hesaplar.md#hesap-whatsapp)

**Bilgisayarda kurulu olması gereken programlar:** WhatsApp Desktop


## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Girişimci, Satış / CRM seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb import`](../14-komut-referansi.md#sb-import) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Bağlı veri kaynakları

- [WhatsApp sohbetleri](../kaynaklar/whatsapp.md): Sohbet dışa aktarımı (.txt/.zip) → mesajlar.

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [87](#madde-87) | WhatsApp mesaj arşivi | hazır | 0.5.0 |
| [184](#madde-184) | WhatsApp taslak → onaylı gönderme (gelişmiş) | hazır | 0.7.0 |

<a id="madde-87"></a>

### 87. WhatsApp mesaj arşivi

- **Ne işe yarar:** «WhatsApp mesaj arşivi» (Yeni veri kaynakları kategorisi), «WhatsApp» modülünün parçasıdır. Modülün amacı: Onaylı mesaj gönderimi (kartı onaylayınca mesaj gönderilir).
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «WhatsApp» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [WhatsApp](../03-hesaplar.md#hesap-whatsapp); program: WhatsApp Desktop.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-184"></a>

### 184. WhatsApp taslak → onaylı gönderme (gelişmiş)

- **Ne işe yarar:** «WhatsApp taslak → onaylı gönderme (gelişmiş)» (İletişim kategorisi), «WhatsApp» modülünün parçasıdır. Modülün amacı: Onaylı mesaj gönderimi (kartı onaylayınca mesaj gönderilir).
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «WhatsApp» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [WhatsApp](../03-hesaplar.md#hesap-whatsapp); program: WhatsApp Desktop.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).
