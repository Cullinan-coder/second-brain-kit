# Telegram botu

> Telegram'dan not alma ve özet

| | |
|---|---|
| Modül kimliği | `telegram` |
| Kategori | Telefon ve mesaj |
| Varsayılan | açık |
| Madde sayısı | 0 |
| Ne ister | hesap: [Telegram](../03-hesaplar.md#hesap-telegram); gizli değer: Telegram bot belirteci (`telegram_token`) |

## Ne işe yarar

Telegram'dan not alma ve özet.

Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Telegram botu`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on telegram` açar, `sb features --off telegram` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).
4. Ek kurulum belgesi: `docs/telegram-kurulum.md` (kitin `docs` klasöründe; rehberdeki karşılığı için [Telegram](../03-hesaplar.md#hesap-telegram)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Telegram](../03-hesaplar.md#hesap-telegram)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Telegram bot belirteci (`telegram_token`) | gizli değer (yalnız şifre kasasına yazılır) | evet | @BotFather ile bot oluştur (docs/telegram-kurulum.md). |

Gizli değerler (`telegram_token`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Girişimci seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb telegram`](../14-komut-referansi.md#sb-telegram) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.
