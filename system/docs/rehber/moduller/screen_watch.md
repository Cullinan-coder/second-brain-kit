# Ekran izleme

> İzin verilince belirli süre ekranı okuyup gün özeti çıkarır (görüntü saklanmaz)

| | |
|---|---|
| Modül kimliği | `screen_watch` |
| Kategori | Bilgisayar ve ses |
| Varsayılan | kapalı (isteğe bağlı özellik) |
| Madde sayısı | 1 |
| Ne ister | donanım: ekran kartı belleği (VRAM) ≥ 8 GB |

## Ne işe yarar

İzin verilince belirli süre ekranı okuyup gün özeti çıkarır (görüntü saklanmaz).

Bu modül özellik kataloğundan **1 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Ekran izleme`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on screen_watch` açar, `sb features --off screen_watch` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Donanım:** ekran kartı belleği (VRAM) en az 8 GB.


## Hazır seçimlerde

- **Yoğunluk:** hiçbir yoğunluk seçiminde kendiliğinden açılmaz; elle açarsın.
- **Donanım nedeniyle kapanır:** Orta (8-14 GB VRAM), Zayıf laptop / bulut, Mac (Apple Silicon).

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
| [47](#madde-47) | Ekran izleme modu (izinli) | hazır | 0.6.0 |

<a id="madde-47"></a>

### 47. Ekran izleme modu (izinli)

- **Ne işe yarar:** «Ekran izleme modu (izinli)» (Ses ve çok kipli kullanım kategorisi), «Ekran izleme» modülünün parçasıdır. Modülün amacı: İzin verilince belirli süre ekranı okuyup gün özeti çıkarır (görüntü saklanmaz).
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ekran izleme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: ekran kartı belleği (VRAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa arka planda ya da asistan üzerinden çalışır. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** yok (altyapı).
