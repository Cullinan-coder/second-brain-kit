# Uyandırma sözcüğü

> 'Hey <asistan>' ile dinlemeye başlar (yalnız sekme açıkken)

| | |
|---|---|
| Modül kimliği | `wake_word` |
| Kategori | Bilgisayar ve ses |
| Varsayılan | kapalı (isteğe bağlı özellik) |
| Madde sayısı | 1 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

'Hey <asistan>' ile dinlemeye başlar (yalnız sekme açıkken).

Bu modül özellik kataloğundan **1 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Uyandırma sözcüğü`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on wake_word` açar, `sb features --off wake_word` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** hiçbir yoğunluk seçiminde kendiliğinden açılmaz; elle açarsın.
- **Donanım nedeniyle kapanır:** Orta (8-14 GB VRAM), Zayıf laptop / bulut, Mac (Apple Silicon).

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Ayarlar (Uyandırma sözcüğü kutusu)** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** bu modülün kendine ait komutu yoktur; asistan ya da uygulama üzerinden çalışır.
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [40](#madde-40) | Uyandırma sözcüğü | hazır | 0.6.0 |

<a id="madde-40"></a>

### 40. Uyandırma sözcüğü

- **Ne işe yarar:** «Uyandırma sözcüğü» (Ses ve çok kipli kullanım kategorisi), «Uyandırma sözcüğü» modülünün parçasıdır. Modülün amacı: 'Hey <asistan>' ile dinlemeye başlar (yalnız sekme açıkken).
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Uyandırma sözcüğü» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Ayarlar (Uyandırma sözcüğü kutusu)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Ayarlar (Uyandırma sözcüğü kutusu)**.
