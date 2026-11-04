# Beyin dizini

> Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler

| | |
|---|---|
| Modül kimliği | `brain` |
| Kategori | Arama ve beyin |
| Varsayılan | açık |
| Madde sayısı | 20 |
| Ne ister | donanım: bellek (RAM) ≥ 8 GB |

## Ne işe yarar

Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.

Bu modül özellik kataloğundan **20 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Beyin dizini`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on brain` açar, `sb features --off brain` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Donanım:** bellek (RAM) en az 8 GB.


## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Yazılımcı, Akademisyen, Araştırmacı seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Bilgi grafı** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters), [`sb suggest-links`](../14-komut-referansi.md#sb-suggest-links), [`sb analyze`](../14-komut-referansi.md#sb-analyze), [`sb graph-style`](../14-komut-referansi.md#sb-graph-style), [`sb find`](../14-komut-referansi.md#sb-find), [`sb answer`](../14-komut-referansi.md#sb-answer), [`sb similar`](../14-komut-referansi.md#sb-similar) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [118](#madde-118) | Derin yeniden aktarım modu | hazır | 0.5.0 |
| [119](#madde-119) | Varlık çıkarımı (kişi, kurum, proje, yer, tarih, para) | hazır | 0.5.0 |
| [120](#madde-120) | Kişi birleştirme | hazır | 0.5.0 |
| [121](#madde-121) | Yapay zekayla kümeleme ve küme notları | hazır | 0.5.0 |
| [122](#madde-122) | Anlam tabanlı arama dizini (yerel gömme) | hazır | 0.5.0 |
| [123](#madde-123) | Otomatik bağlantı önerisi (onayla/reddet) | hazır | 0.5.0 |
| [124](#madde-124) | Konu zaman çizelgesi | hazır | 0.5.0 |
| [125](#madde-125) | Proje ilişki haritası | hazır | 0.5.0 |
| [126](#madde-126) | Belge sınıflandırma | hazır | 0.5.0 |
| [127](#madde-127) | Tekrar belge tespiti | hazır | 0.5.0 |
| [128](#madde-128) | Yaşlanan bilgi politikası | hazır | 0.5.0 |
| [129](#madde-129) | Bilgi tazeliği kontrolü | hazır | 0.5.0 |
| [130](#madde-130) | Çelişki tespiti | hazır | 0.5.0 |
| [131](#madde-131) | Yetenek profili | hazır | 0.5.0 |
| [132](#madde-132) | Kişisel sözlük | hazır | 0.5.0 |
| [133](#madde-133) | Etiket düzenleyici | hazır | 0.5.0 |
| [134](#madde-134) | Not kalite puanı | hazır | 0.5.0 |
| [135](#madde-135) | Kaynak güven puanı | hazır | 0.5.0 |
| [136](#madde-136) | Görsel küme haritası | hazır | 0.5.0 |
| [137](#madde-137) | Veri hattı panosu | hazır | 0.5.0 |

<a id="madde-118"></a>

### 118. Derin yeniden aktarım modu

- **Ne işe yarar:** «Derin yeniden aktarım modu» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-119"></a>

### 119. Varlık çıkarımı (kişi, kurum, proje, yer, tarih, para)

- **Ne işe yarar:** «Varlık çıkarımı (kişi, kurum, proje, yer, tarih, para)» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-120"></a>

### 120. Kişi birleştirme

- **Ne işe yarar:** «Kişi birleştirme» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-121"></a>

### 121. Yapay zekayla kümeleme ve küme notları

- **Ne işe yarar:** «Yapay zekayla kümeleme ve küme notları» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-122"></a>

### 122. Anlam tabanlı arama dizini (yerel gömme)

- **Ne işe yarar:** «Anlam tabanlı arama dizini (yerel gömme)» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-123"></a>

### 123. Otomatik bağlantı önerisi (onayla/reddet)

- **Ne işe yarar:** «Otomatik bağlantı önerisi (onayla/reddet)» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-124"></a>

### 124. Konu zaman çizelgesi

- **Ne işe yarar:** «Konu zaman çizelgesi» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-125"></a>

### 125. Proje ilişki haritası

- **Ne işe yarar:** «Proje ilişki haritası» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-126"></a>

### 126. Belge sınıflandırma

- **Ne işe yarar:** «Belge sınıflandırma» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-127"></a>

### 127. Tekrar belge tespiti

- **Ne işe yarar:** «Tekrar belge tespiti» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-128"></a>

### 128. Yaşlanan bilgi politikası

- **Ne işe yarar:** «Yaşlanan bilgi politikası» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-129"></a>

### 129. Bilgi tazeliği kontrolü

- **Ne işe yarar:** «Bilgi tazeliği kontrolü» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-130"></a>

### 130. Çelişki tespiti

- **Ne işe yarar:** «Çelişki tespiti» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-131"></a>

### 131. Yetenek profili

- **Ne işe yarar:** «Yetenek profili» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-132"></a>

### 132. Kişisel sözlük

- **Ne işe yarar:** «Kişisel sözlük» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-133"></a>

### 133. Etiket düzenleyici

- **Ne işe yarar:** «Etiket düzenleyici» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-134"></a>

### 134. Not kalite puanı

- **Ne işe yarar:** «Not kalite puanı» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-135"></a>

### 135. Kaynak güven puanı

- **Ne işe yarar:** «Kaynak güven puanı» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-136"></a>

### 136. Görsel küme haritası

- **Ne işe yarar:** «Görsel küme haritası» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).

<a id="madde-137"></a>

### 137. Veri hattı panosu

- **Ne işe yarar:** «Veri hattı panosu» (Beyni yeniden kurma kategorisi), «Beyin dizini» modülünün parçasıdır. Modülün amacı: Bütün kaynaklarda anlam araması, kişi bağlantıları, kümeleme, analizler.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Beyin dizini» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Bilgi grafı**; komut: [`sb index`](../14-komut-referansi.md#sb-index), [`sb mentions`](../14-komut-referansi.md#sb-mentions), [`sb chat-links`](../14-komut-referansi.md#sb-chat-links), [`sb merge-people`](../14-komut-referansi.md#sb-merge-people), [`sb search2`](../14-komut-referansi.md#sb-search2), [`sb clusters`](../14-komut-referansi.md#sb-clusters).
