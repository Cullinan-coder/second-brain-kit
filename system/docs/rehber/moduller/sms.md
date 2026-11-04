# SMS ve aramalar

> Telefon yedeğinden SMS/arama

| | |
|---|---|
| Modül kimliği | `sms` |
| Kategori | Telefon ve mesaj |
| Varsayılan | açık |
| Madde sayısı | 1 |
| Ne ister | hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`); program: SMS Backup & Restore (Android) |

## Ne işe yarar

Telefon yedeğinden SMS/arama.

Bu modül özellik kataloğundan **1 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`SMS ve aramalar`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on sms` açar, `sb features --off sms` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).
4. Ek kurulum belgesi: `docs/telefon-sms-kurulum.md` (kitin `docs` klasöründe; rehberdeki karşılığı için [SMS kaynağı](../kaynaklar/sms.md)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Google](../03-hesaplar.md#hesap-google)

**Bilgisayarda kurulu olması gereken programlar:** SMS Backup & Restore (Android)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Ana Gmail adresi (`gmail`) | e-posta adresi | evet | Google ile giriş yapılacak hesap. |
| Google client_secret.json yolu (`client_secret`) | dosya ya da klasör yolu | hayır | Google Cloud'da OAuth istemcisi oluşturup indir (docs/google-cloud-kurulum.md). |

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Satış / CRM seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb sms-sync`](../14-komut-referansi.md#sb-sms-sync) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Bağlı veri kaynakları

- [SMS ve aramalar](../kaynaklar/sms.md): Android SMS/arama yedeği (XML, Drive üzerinden) → mesajlar.

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [76](#madde-76) | Android SMS/arama otomatik eşitleme | hazır | 0.5.0 |

<a id="madde-76"></a>

### 76. Android SMS/arama otomatik eşitleme

- **Ne işe yarar:** «Android SMS/arama otomatik eşitleme» (Mobil kategorisi), «SMS ve aramalar» modülünün parçasıdır. Modülün amacı: Telefon yedeğinden SMS/arama.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «SMS ve aramalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`); program: SMS Backup & Restore (Android).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb sms-sync`](../14-komut-referansi.md#sb-sms-sync). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb sms-sync`](../14-komut-referansi.md#sb-sms-sync).
