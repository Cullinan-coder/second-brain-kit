# Şirket/okul maili (IMAP)

> IMAP hesaplarını salt okunur arşivler

| | |
|---|---|
| Modül kimliği | `imap` |
| Kategori | Mail ve takvim |
| Varsayılan | açık |
| Madde sayısı | 0 |
| Ne ister | hesap: [E-posta (IMAP)](../03-hesaplar.md#hesap-imap); gizli değer: IMAP şifresi (uygulama şifresi) (`imap_password`); alan: IMAP takma adı (ör. is) (`imap_alias`), IMAP e-posta (`imap_email`), IMAP sunucusu (`imap_host`) |

## Ne işe yarar

IMAP hesaplarını salt okunur arşivler.

Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Şirket/okul maili (IMAP)`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on imap` açar, `sb features --off imap` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [E-posta (IMAP)](../03-hesaplar.md#hesap-imap)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| IMAP takma adı (ör. is) (`imap_alias`) | metin | hayır | Hesabı kısa adla tanır. |
| IMAP e-posta (`imap_email`) | e-posta adresi | evet | — |
| IMAP sunucusu (`imap_host`) | metin | evet | Ör. mail.sirketim.com; sağlayıcının yardım sayfasında yazar. |
| IMAP şifresi (uygulama şifresi) (`imap_password`) | gizli değer (yalnız şifre kasasına yazılır) | evet | Yalnız işletim sistemi şifre kasasına yazılır. |

Gizli değerler (`imap_password`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Girişimci, Satış / CRM seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb mail-fetch`](../14-komut-referansi.md#sb-mail-fetch) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.
