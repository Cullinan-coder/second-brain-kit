# Sabah özeti maili

> Her gün özet maili ve günlük not

| | |
|---|---|
| Modül kimliği | `digest` |
| Kategori | Mail ve takvim |
| Varsayılan | açık |
| Madde sayısı | 0 |
| Ne ister | hesap: [E-posta (IMAP)](../03-hesaplar.md#hesap-imap); alan: Özet maili alıcısı (`notify_to`) |

## Ne işe yarar

Her gün özet maili ve günlük not.

Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Sabah özeti maili`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on digest` açar, `sb features --off digest` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [E-posta (IMAP)](../03-hesaplar.md#hesap-imap)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Özet maili alıcısı (`notify_to`) | e-posta adresi | hayır | Sabah özetinin gideceği adres. |

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Girişimci, Satış / CRM seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb daily`](../14-komut-referansi.md#sb-daily), [`sb weekly`](../14-komut-referansi.md#sb-weekly), [`sb notify-test`](../14-komut-referansi.md#sb-notify-test) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.
