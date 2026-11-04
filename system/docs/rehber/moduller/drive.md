# Google Drive

> Drive dosya listesi ve notları

| | |
|---|---|
| Modül kimliği | `drive` |
| Kategori | Mail ve takvim |
| Varsayılan | açık |
| Madde sayısı | 0 |
| Ne ister | hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`) |

## Ne işe yarar

Drive dosya listesi ve notları.

Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Google Drive`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on drive` açar, `sb features --off drive` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).
4. Ek kurulum belgesi: `docs/google-cloud-kurulum.md` (kitin `docs` klasöründe; rehberdeki karşılığı için [Hesaplar](../03-hesaplar.md#hesap-google)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Google](../03-hesaplar.md#hesap-google)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Ana Gmail adresi (`gmail`) | e-posta adresi | evet | Google ile giriş yapılacak hesap. |
| Google client_secret.json yolu (`client_secret`) | dosya ya da klasör yolu | hayır | Google Cloud'da OAuth istemcisi oluşturup indir (docs/google-cloud-kurulum.md). |

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Akademisyen, Girişimci, İçerik üreticisi, Araştırmacı seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb drive-sync`](../14-komut-referansi.md#sb-drive-sync), [`sb drive-index`](../14-komut-referansi.md#sb-drive-index) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.
