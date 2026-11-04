# Tarih çıkarma

> Mail/SMS'ten teslim ve randevu tarihlerini çıkarıp onaya sunar

| | |
|---|---|
| Modül kimliği | `dates` |
| Kategori | Mail ve takvim |
| Varsayılan | açık |
| Madde sayısı | 1 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Mail/SMS'ten teslim ve randevu tarihlerini çıkarıp onaya sunar.

Bu modül özellik kataloğundan **1 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Tarih çıkarma`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on dates` açar, `sb features --off dates` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Öğrenci, Ajans / Freelancer seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Pano (Onay bekleyen)** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb extract-dates`](../14-komut-referansi.md#sb-extract-dates), [`sb approve`](../14-komut-referansi.md#sb-approve), [`sb housekeep`](../14-komut-referansi.md#sb-housekeep) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [174](#madde-174) | Teslim risk uyarısı | hazır | 0.7.0 |

<a id="madde-174"></a>

### 174. Teslim risk uyarısı

- **Ne işe yarar:** «Teslim risk uyarısı» (Görev, takvim ve verimlilik kategorisi), «Tarih çıkarma» modülünün parçasıdır. Modülün amacı: Mail/SMS'ten teslim ve randevu tarihlerini çıkarıp onaya sunar.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Tarih çıkarma» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Pano (Onay bekleyen)**; komut: [`sb extract-dates`](../14-komut-referansi.md#sb-extract-dates), [`sb approve`](../14-komut-referansi.md#sb-approve), [`sb housekeep`](../14-komut-referansi.md#sb-housekeep). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Pano (Onay bekleyen)**; komut: [`sb extract-dates`](../14-komut-referansi.md#sb-extract-dates), [`sb approve`](../14-komut-referansi.md#sb-approve), [`sb housekeep`](../14-komut-referansi.md#sb-housekeep).
