# Görsel üretme

> Metinden görsel (bulut sağlayıcı anahtarı gerekir)

| | |
|---|---|
| Modül kimliği | `image_gen` |
| Kategori | Bilgisayar ve ses |
| Varsayılan | kapalı (isteğe bağlı özellik) |
| Madde sayısı | 1 |
| Ne ister | hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Gemini](../04-api-anahtarlari.md#anahtar-gemini); gizli değer: OpenAI API anahtarı (`openai_key`), Gemini API anahtarı (`gemini_key`) |

## Ne işe yarar

Metinden görsel (bulut sağlayıcı anahtarı gerekir).

Bu modül özellik kataloğundan **1 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Görsel üretme`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on image_gen` açar, `sb features --off image_gen` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Gemini](../04-api-anahtarlari.md#anahtar-gemini)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| OpenAI API anahtarı (`openai_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | platform.openai.com > API keys. |
| Gemini API anahtarı (`gemini_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | aistudio.google.com > Get API key. |

Gizli değerler (`openai_key`, `gemini_key`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Hazır seçimlerde

- **Yoğunluk:** hiçbir yoğunluk seçiminde kendiliğinden açılmaz; elle açarsın.
- **Meslek:** İçerik üreticisi seçimlerinde ayrıca eklenir.
- **Gizlilik nedeniyle kapanır:** Tam yerel.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** bu modülün kendine ait komutu yoktur; asistan ya da uygulama üzerinden çalışır.
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [49](#madde-49) | Görsel üretme | hazır | 0.6.0 |

<a id="madde-49"></a>

### 49. Görsel üretme

- **Ne işe yarar:** «Görsel üretme» (Ses ve çok kipli kullanım kategorisi), «Görsel üretme» modülünün parçasıdır. Modülün amacı: Metinden görsel (bulut sağlayıcı anahtarı gerekir).
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Görsel üretme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Gemini](../04-api-anahtarlari.md#anahtar-gemini); gizli değer: OpenAI API anahtarı (`openai_key`), Gemini API anahtarı (`gemini_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa arka planda ya da asistan üzerinden çalışır. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** yok (altyapı).
