# Gece koşusu

> İstenince gece işlerini Claude Code'a sırayla yaptırır

| | |
|---|---|
| Modül kimliği | `night` |
| Kategori | Asistan ve hafıza |
| Varsayılan | açık |
| Madde sayısı | 1 |
| Ne ister | program: Claude Code |

## Ne işe yarar

İstenince gece işlerini Claude Code'a sırayla yaptırır.

Bu modül özellik kataloğundan **1 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Gece koşusu`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on night` açar, `sb features --off night` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Bilgisayarda kurulu olması gereken programlar:** Claude Code


## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Yazılımcı seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb night`](../14-komut-referansi.md#sb-night) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [228](#madde-228) | Gece koşusu raporu ve sabah onayı | hazır | 0.8.0 |

<a id="madde-228"></a>

### 228. Gece koşusu raporu ve sabah onayı

- **Ne işe yarar:** «Gece koşusu raporu ve sabah onayı» (Ajanlar ve otomasyon kategorisi), «Gece koşusu» modülünün parçasıdır. Modülün amacı: İstenince gece işlerini Claude Code'a sırayla yaptırır.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gece koşusu» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: Claude Code.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb night`](../14-komut-referansi.md#sb-night). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb night`](../14-komut-referansi.md#sb-night).
