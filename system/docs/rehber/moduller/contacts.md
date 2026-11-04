# Google Rehber

> Kişi notları

| | |
|---|---|
| Modül kimliği | `contacts` |
| Kategori | Mail ve takvim |
| Varsayılan | açık |
| Madde sayısı | 1 |
| Ne ister | hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`) |

## Ne işe yarar

Kişi notları.

Bu modül özellik kataloğundan **1 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Google Rehber`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on contacts` açar, `sb features --off contacts` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).
4. Ek kurulum belgesi: `docs/google-cloud-kurulum.md` (kitin `docs` klasöründe; rehberdeki karşılığı için [Hesaplar](../03-hesaplar.md#hesap-google)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Google](../03-hesaplar.md#hesap-google)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Ana Gmail adresi (`gmail`) | e-posta adresi | evet | Google ile giriş yapılacak hesap. |
| Google client_secret.json yolu (`client_secret`) | dosya ya da klasör yolu | hayır | Google Cloud'da OAuth istemcisi oluşturup indir (docs/google-cloud-kurulum.md). |

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Girişimci, Satış / CRM seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Kişi** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb contacts-sync`](../14-komut-referansi.md#sb-contacts-sync), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [186](#madde-186) | Doğum günü ve önemli tarihler | hazır | 0.7.0 |

<a id="madde-186"></a>

### 186. Doğum günü ve önemli tarihler

- **Ne işe yarar:** «Doğum günü ve önemli tarihler» (İletişim kategorisi), «Google Rehber» modülünün parçasıdır. Modülün amacı: Kişi notları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Google Rehber» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kişi**; komut: [`sb contacts-sync`](../14-komut-referansi.md#sb-contacts-sync), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kişi**; komut: [`sb contacts-sync`](../14-komut-referansi.md#sb-contacts-sync), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people).
