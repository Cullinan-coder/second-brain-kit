# Yaşam ve akademik içe aktarmalar

> Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.

| | |
|---|---|
| Modül kimliği | `imports_life` |
| Kategori | Veri kaynakları |
| Varsayılan | açık |
| Madde sayısı | 10 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.

Bu modül özellik kataloğundan **10 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Yaşam ve akademik içe aktarmalar`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Öğrenci, Akademisyen, Araştırmacı seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Bağlı veri kaynakları

- [arXiv sorguları](../kaynaklar/arxiv.md): arXiv arama sorguları (config/rss.yaml `arxiv:`) → makale kayıtları.
- [Banka ekstresi (CSV)](../kaynaklar/bank.md): Banka hesap hareketleri CSV'si → işlem kayıtları. Hesap/kart numarası ve IBAN hiçbir yerde saklanmaz.
- [BibTeX dosyası](../kaynaklar/bibtex.md): BibTeX (.bib) → kaynak kayıtları.
- [Coursera ilerlemesi](../kaynaklar/coursera.md): Kurs ilerlemesi CSV/JSON → kurs kayıtları.
- [Google Haritalar zaman çizelgesi](../kaynaklar/gmaps.md): Konum geçmişi (zaman çizelgesi) → yer kayıtları.
- [Google Fotoğraflar meta verisi](../kaynaklar/gphotos.md): Fotoğraf yan dosyaları (JSON) → tarih/yer kayıtları; fotoğrafın kendisi okunmaz.
- [ChatGPT / Claude / Gemini sohbet geçmişi](../kaynaklar/history-import.md): Eski yapay zeka sohbetleri → aylık sohbet notları.
- [Instagram verileri](../kaynaklar/instagram.md): Instagram 'bilgilerini indir' (JSON) → DM'ler ve gönderiler.
- [Ekran süresi / uygulama kullanımı](../kaynaklar/screentime.md): ManicTime/RescueTime vb. CSV → kullanım kayıtları.
- [Google Takeout](../kaynaklar/takeout.md): Gemini sohbetleri, etkinlik, Chrome, Keep, YouTube, Play → kasa.
- [Udemy ilerlemesi](../kaynaklar/udemy.md): Kurs ilerlemesi CSV/JSON → kurs kayıtları.
- [X (Twitter) arşivi](../kaynaklar/x.md): X arşivi → gönderiler.
- [Zotero kütüphanesi](../kaynaklar/zotero.md): Zotero veritabanı (zotero.sqlite) → kaynak kayıtları.

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [105](#madde-105) | Google Fotoğraflar meta verisi | hazır | 0.8.0 |
| [106](#madde-106) | Google Haritalar zaman çizelgesi | hazır | 0.8.0 |
| [107](#madde-107) | Banka ekstresi CSV (numarasız özet) | hazır | 0.8.0 |
| [108](#madde-108) | e-Devlet / e-Okul belgeleri | planlandı (henüz yok) | 0.8.0 |
| [109](#madde-109) | Instagram, X arşivi | hazır | 0.8.0 |
| [110](#madde-110) | Sağlık uygulaması özeti (gizli) | planlandı (henüz yok) | 0.8.0 |
| [111](#madde-111) | Ekran süresi / uygulama kullanımı | hazır | 0.8.0 |
| [113](#madde-113) | Google Scholar, arXiv, Zotero | hazır | 0.5.0 |
| [114](#madde-114) | Coursera, Udemy ilerleme | hazır | 0.8.0 |
| [115](#madde-115) | İş ilanı takibi | planlandı (henüz yok) | 0.8.0 |

<a id="madde-105"></a>

### 105. Google Fotoğraflar meta verisi

- **Ne işe yarar:** «Google Fotoğraflar meta verisi» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-106"></a>

### 106. Google Haritalar zaman çizelgesi

- **Ne işe yarar:** «Google Haritalar zaman çizelgesi» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-107"></a>

### 107. Banka ekstresi CSV (numarasız özet)

- **Ne işe yarar:** «Banka ekstresi CSV (numarasız özet)» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-108"></a>

### 108. e-Devlet / e-Okul belgeleri

- **Ne işe yarar:** «e-Devlet / e-Okul belgeleri» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** planlandı (henüz yok); yol haritasında Faz 4 / sürüm 0.8.0 için yer alır. Şu an tam çalışmasını bekleme.
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-109"></a>

### 109. Instagram, X arşivi

- **Ne işe yarar:** «Instagram, X arşivi» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-110"></a>

### 110. Sağlık uygulaması özeti (gizli)

- **Ne işe yarar:** «Sağlık uygulaması özeti (gizli)» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** planlandı (henüz yok); yol haritasında Faz 4 / sürüm 0.8.0 için yer alır. Şu an tam çalışmasını bekleme.
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-111"></a>

### 111. Ekran süresi / uygulama kullanımı

- **Ne işe yarar:** «Ekran süresi / uygulama kullanımı» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-113"></a>

### 113. Google Scholar, arXiv, Zotero

- **Ne işe yarar:** «Google Scholar, arXiv, Zotero» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-114"></a>

### 114. Coursera, Udemy ilerleme

- **Ne işe yarar:** «Coursera, Udemy ilerleme» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).

<a id="madde-115"></a>

### 115. İş ilanı takibi

- **Ne işe yarar:** «İş ilanı takibi» (Yeni veri kaynakları kategorisi), «Yaşam ve akademik içe aktarmalar» modülünün parçasıdır. Modülün amacı: Fotoğraf, Haritalar, banka CSV, e-Devlet, sosyal, sağlık, ekran süresi, akademik kaynaklar, kurslar, iş ilanları.
- **Durum:** planlandı (henüz yok); yol haritasında Faz 4 / sürüm 0.8.0 için yer alır. Şu an tam çalışmasını bekleme.
- **Nasıl açılır:** «Yaşam ve akademik içe aktarmalar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import), [`sb history-import`](../14-komut-referansi.md#sb-history-import), [`sb takeout`](../14-komut-referansi.md#sb-takeout).
