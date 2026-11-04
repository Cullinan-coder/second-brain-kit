# Gmail

> Gmail hesaplarını salt okunur arşivler, kategorilere ayırır

| | |
|---|---|
| Modül kimliği | `gmail` |
| Kategori | Mail ve takvim |
| Varsayılan | açık |
| Madde sayısı | 0 |
| Ne ister | hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`) |

## Ne işe yarar

Gmail hesaplarını salt okunur arşivler, kategorilere ayırır.

Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Gmail`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on gmail` açar, `sb features --off gmail` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).
4. Ek kurulum belgesi: `docs/google-cloud-kurulum.md` (kitin `docs` klasöründe; rehberdeki karşılığı için [Hesaplar](../03-hesaplar.md#hesap-google)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Google](../03-hesaplar.md#hesap-google)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Ana Gmail adresi (`gmail`) | e-posta adresi | evet | Google ile giriş yapılacak hesap. |
| Google client_secret.json yolu (`client_secret`) | dosya ya da klasör yolu | hayır | Google Cloud'da OAuth istemcisi oluşturup indir (docs/google-cloud-kurulum.md). |

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Öğrenci, Ajans / Freelancer, Girişimci, Satış / CRM seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **İletişim**, **Pano** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb mail-categorize`](../14-komut-referansi.md#sb-mail-categorize), [`sb mail-index`](../14-komut-referansi.md#sb-mail-index), [`sb login`](../14-komut-referansi.md#sb-login), [`sb mail-fetch`](../14-komut-referansi.md#sb-mail-fetch), [`sb mail-ics-backfill`](../14-komut-referansi.md#sb-mail-ics-backfill) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.
