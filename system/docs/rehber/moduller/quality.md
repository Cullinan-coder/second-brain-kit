# Kalite ve gözlemlenebilirlik

> Uçtan uca test, çökme raporu, performans panosu, Yenilikler ekranı.

| | |
|---|---|
| Modül kimliği | `quality` |
| Kategori | Gizlilik ve kalite |
| Varsayılan | açık |
| Madde sayısı | 4 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Uçtan uca test, çökme raporu, performans panosu, Yenilikler ekranı.

Bu modül özellik kataloğundan **4 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Kalite ve gözlemlenebilirlik`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [247](#madde-247) | Gerçek veriyle uçtan uca test paketi | hazır | 0.4.0 |
| [248](#madde-248) | Hata ve çökme raporlama | hazır | 0.4.0 |
| [249](#madde-249) | Performans panosu | hazır | 0.4.0 |
| [250](#madde-250) | Sürüm içi Yenilikler ekranı | hazır | 0.4.0 |

<a id="madde-247"></a>

### 247. Gerçek veriyle uçtan uca test paketi

- **Ne işe yarar:** «Gerçek veriyle uçtan uca test paketi» (Kalite, test ve gözlemlenebilirlik kategorisi), «Kalite ve gözlemlenebilirlik» modülünün parçasıdır. Modülün amacı: Uçtan uca test, çökme raporu, performans panosu, Yenilikler ekranı.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Kalite ve gözlemlenebilirlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor).

<a id="madde-248"></a>

### 248. Hata ve çökme raporlama

- **Ne işe yarar:** «Hata ve çökme raporlama» (Kalite, test ve gözlemlenebilirlik kategorisi), «Kalite ve gözlemlenebilirlik» modülünün parçasıdır. Modülün amacı: Uçtan uca test, çökme raporu, performans panosu, Yenilikler ekranı.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Kalite ve gözlemlenebilirlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor).

<a id="madde-249"></a>

### 249. Performans panosu

- **Ne işe yarar:** «Performans panosu» (Kalite, test ve gözlemlenebilirlik kategorisi), «Kalite ve gözlemlenebilirlik» modülünün parçasıdır. Modülün amacı: Uçtan uca test, çökme raporu, performans panosu, Yenilikler ekranı.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Kalite ve gözlemlenebilirlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor).

<a id="madde-250"></a>

### 250. Sürüm içi Yenilikler ekranı

- **Ne işe yarar:** «Sürüm içi Yenilikler ekranı» (Kalite, test ve gözlemlenebilirlik kategorisi), «Kalite ve gözlemlenebilirlik» modülünün parçasıdır. Modülün amacı: Uçtan uca test, çökme raporu, performans panosu, Yenilikler ekranı.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Kalite ve gözlemlenebilirlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb perf`](../14-komut-referansi.md#sb-perf), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb e2e`](../14-komut-referansi.md#sb-e2e), [`sb doctor`](../14-komut-referansi.md#sb-doctor).
