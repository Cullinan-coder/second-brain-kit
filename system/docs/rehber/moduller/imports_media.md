# Medya ve okuma içe aktarmaları

> Kindle, Pocket/Raindrop, YouTube, Spotify, RSS.

| | |
|---|---|
| Modül kimliği | `imports_media` |
| Kategori | Veri kaynakları |
| Varsayılan | açık |
| Madde sayısı | 5 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Kindle, Pocket/Raindrop, YouTube, Spotify, RSS.

Bu modül özellik kataloğundan **5 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Medya ve okuma içe aktarmaları`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Akademisyen, İçerik üreticisi, Araştırmacı seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb import`](../14-komut-referansi.md#sb-import) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Bağlı veri kaynakları

- [Kindle vurguları](../kaynaklar/kindle.md): Kindle 'My Clippings.txt' → vurgu/not kayıtları.
- [Pocket](../kaynaklar/pocket.md): Pocket okuma listesi (ril_export.html/CSV) → bağlantı kayıtları.
- [Raindrop.io yer imleri](../kaynaklar/raindrop.md): Raindrop dışa aktarımı (CSV) → bağlantı kayıtları.
- [RSS ve haber bültenleri](../kaynaklar/rss.md): RSS/Atom akışları (config/rss.yaml) → makale kayıtları. Ağ kullanan tek bağlayıcı.
- [Spotify teknik günlük paketi](../kaynaklar/spotify-teknik.md): Spotify 'Technical Log Information' (my_spotify_data.zip) → aramalar, beğeniler, tekrar dinlenenler, sözüne bakılanlar + "Müzik zevki" notu. Cihaz/ağ günlükleri alınmaz.
- [Spotify dinleme geçmişi](../kaynaklar/spotify.md): Spotify 'Extended streaming history' → dinleme kayıtları.
- [YouTube izleme geçmişi](../kaynaklar/youtube.md): İzleme geçmişi ve abonelikler (Takeout) → kayıtlar.

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [101](#madde-101) | Kindle / e-kitap vurguları | hazır | 0.5.0 |
| [102](#madde-102) | Okuma listesi (Pocket, Raindrop) | hazır | 0.8.0 |
| [103](#madde-103) | YouTube izleme geçmişi ve abonelikler | hazır | 0.5.0 |
| [104](#madde-104) | Spotify dinleme geçmişi | hazır | 0.5.0 |
| [112](#madde-112) | RSS ve haber bültenleri | hazır | 0.5.0 |

<a id="madde-101"></a>

### 101. Kindle / e-kitap vurguları

- **Ne işe yarar:** «Kindle / e-kitap vurguları» (Yeni veri kaynakları kategorisi), «Medya ve okuma içe aktarmaları» modülünün parçasıdır. Modülün amacı: Kindle, Pocket/Raindrop, YouTube, Spotify, RSS.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Medya ve okuma içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-102"></a>

### 102. Okuma listesi (Pocket, Raindrop)

- **Ne işe yarar:** «Okuma listesi (Pocket, Raindrop)» (Yeni veri kaynakları kategorisi), «Medya ve okuma içe aktarmaları» modülünün parçasıdır. Modülün amacı: Kindle, Pocket/Raindrop, YouTube, Spotify, RSS.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Medya ve okuma içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-103"></a>

### 103. YouTube izleme geçmişi ve abonelikler

- **Ne işe yarar:** «YouTube izleme geçmişi ve abonelikler» (Yeni veri kaynakları kategorisi), «Medya ve okuma içe aktarmaları» modülünün parçasıdır. Modülün amacı: Kindle, Pocket/Raindrop, YouTube, Spotify, RSS.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Medya ve okuma içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-104"></a>

### 104. Spotify dinleme geçmişi

- **Ne işe yarar:** «Spotify dinleme geçmişi» (Yeni veri kaynakları kategorisi), «Medya ve okuma içe aktarmaları» modülünün parçasıdır. Modülün amacı: Kindle, Pocket/Raindrop, YouTube, Spotify, RSS.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Medya ve okuma içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-112"></a>

### 112. RSS ve haber bültenleri

- **Ne işe yarar:** «RSS ve haber bültenleri» (Yeni veri kaynakları kategorisi), «Medya ve okuma içe aktarmaları» modülünün parçasıdır. Modülün amacı: Kindle, Pocket/Raindrop, YouTube, Spotify, RSS.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Medya ve okuma içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).
