# ClipBoardLine (kopya geçmişi)

> Hazır açık kaynak (MIT) uygulama; kopyaladığın metin, bağlantı ve görselleri (görsellerde OCR ile) saklar. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve içeriğini (parola, anahtar, kart, IBAN gibi sırlar hariç) beynine okur.

| | |
|---|---|
| Modül kimliği | `clipboardline` |
| Kategori | Hazır uygulamalar |
| Varsayılan | açık |
| Madde sayısı | 4 |
| Ne ister | program: clipboardline |

## Ne işe yarar

Hazır açık kaynak (MIT) uygulama; kopyaladığın metin, bağlantı ve görselleri (görsellerde OCR ile) saklar. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve içeriğini (parola, anahtar, kart, IBAN gibi sırlar hariç) beynine okur.

Bu modül özellik kataloğundan **4 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`ClipBoardLine (kopya geçmişi)`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on clipboardline` açar, `sb features --off clipboardline` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Bilgisayarda kurulu olması gereken programlar:** clipboardline


## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb apps`](../14-komut-referansi.md#sb-apps) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Bağlı veri kaynakları

- [ClipBoardLine kütüphanesi](../kaynaklar/clipboardline.md): ClipBoardLine'ın library.json dosyası → metin, bağlantı ve görsel OCR kayıtları (sır içerenler atlanır).

## Sağlık testi

Çalışıp çalışmadığını `sb apps status clipboardline` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [251](#madde-251) | Hazır uygulamalar — katalog, SHA-256 doğrulamalı indirme ve sürüm denetimi (sb apps) | hazır | 0.11.0 |
| [252](#madde-252) | ClipBoardLine — resmî Windows/macOS sürümünün kurulumu, açılışı ve durum denetimi | hazır | 0.11.0 |
| [254](#madde-254) | Uygulama başlangıcı — bilgisayar açılınca / Çalışmaya başla ile / başlamasın (kurulumda sorulur) | hazır | 0.11.0 |
| [255](#madde-255) | ClipBoardLine → beyin — metin, bağlantı, görsel OCR metni, etiket ve klasörler (sır içeren kayıt atlanır) | hazır | 0.11.0 |

<a id="madde-251"></a>

### 251. Hazır uygulamalar — katalog, SHA-256 doğrulamalı indirme ve sürüm denetimi (sb apps)

- **Ne işe yarar:** «Hazır uygulamalar — katalog, SHA-256 doğrulamalı indirme ve sürüm denetimi (sb apps)» (Görev, takvim ve verimlilik kategorisi), «ClipBoardLine (kopya geçmişi)» modülünün parçasıdır. Modülün amacı: Hazır açık kaynak (MIT) uygulama; kopyaladığın metin, bağlantı ve görselleri (görsellerde OCR ile) saklar. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve içeriğini (parola, anahtar, kart, IBAN gibi sırlar hariç) beynine okur.
- **Durum:** hazır (sürüm 0.11.0).
- **Nasıl açılır:** «ClipBoardLine (kopya geçmişi)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: clipboardline.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps).

<a id="madde-252"></a>

### 252. ClipBoardLine — resmî Windows/macOS sürümünün kurulumu, açılışı ve durum denetimi

- **Ne işe yarar:** «ClipBoardLine — resmî Windows/macOS sürümünün kurulumu, açılışı ve durum denetimi» (Görev, takvim ve verimlilik kategorisi), «ClipBoardLine (kopya geçmişi)» modülünün parçasıdır. Modülün amacı: Hazır açık kaynak (MIT) uygulama; kopyaladığın metin, bağlantı ve görselleri (görsellerde OCR ile) saklar. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve içeriğini (parola, anahtar, kart, IBAN gibi sırlar hariç) beynine okur.
- **Durum:** hazır (sürüm 0.11.0).
- **Nasıl açılır:** «ClipBoardLine (kopya geçmişi)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: clipboardline.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps).

<a id="madde-254"></a>

### 254. Uygulama başlangıcı — bilgisayar açılınca / Çalışmaya başla ile / başlamasın (kurulumda sorulur)

- **Ne işe yarar:** «Uygulama başlangıcı — bilgisayar açılınca / Çalışmaya başla ile / başlamasın (kurulumda sorulur)» (Görev, takvim ve verimlilik kategorisi), «ClipBoardLine (kopya geçmişi)» modülünün parçasıdır. Modülün amacı: Hazır açık kaynak (MIT) uygulama; kopyaladığın metin, bağlantı ve görselleri (görsellerde OCR ile) saklar. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve içeriğini (parola, anahtar, kart, IBAN gibi sırlar hariç) beynine okur.
- **Durum:** hazır (sürüm 0.11.0).
- **Nasıl açılır:** «ClipBoardLine (kopya geçmişi)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: clipboardline.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps).

<a id="madde-255"></a>

### 255. ClipBoardLine → beyin — metin, bağlantı, görsel OCR metni, etiket ve klasörler (sır içeren kayıt atlanır)

- **Ne işe yarar:** «ClipBoardLine → beyin — metin, bağlantı, görsel OCR metni, etiket ve klasörler (sır içeren kayıt atlanır)» (Görev, takvim ve verimlilik kategorisi), «ClipBoardLine (kopya geçmişi)» modülünün parçasıdır. Modülün amacı: Hazır açık kaynak (MIT) uygulama; kopyaladığın metin, bağlantı ve görselleri (görsellerde OCR ile) saklar. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve içeriğini (parola, anahtar, kart, IBAN gibi sırlar hariç) beynine okur.
- **Durum:** hazır (sürüm 0.11.0).
- **Nasıl açılır:** «ClipBoardLine (kopya geçmişi)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: clipboardline.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps).
