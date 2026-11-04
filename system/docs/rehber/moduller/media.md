# Spotify ve YouTube

> Şarkı/video açma

| | |
|---|---|
| Modül kimliği | `media` |
| Kategori | Bilgisayar ve ses |
| Varsayılan | açık |
| Madde sayısı | 0 |
| Ne ister | hesap: [Spotify](../03-hesaplar.md#hesap-spotify); gizli değer: Spotify client secret (`spotify_client_secret`); alan: Spotify client id (`spotify_client_id`) |

## Ne işe yarar

Şarkı/video açma.

Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Spotify ve YouTube`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on media` açar, `sb features --off media` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Spotify](../03-hesaplar.md#hesap-spotify)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Spotify client id (`spotify_client_id`) | metin | hayır | developer.spotify.com'da uygulama oluştur. |
| Spotify client secret (`spotify_client_secret`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | Aynı uygulamanın sayfasında. |

Gizli değerler (`spotify_client_secret`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** İçerik üreticisi seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** bu modülün kendine ait komutu yoktur; asistan ya da uygulama üzerinden çalışır.
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.
