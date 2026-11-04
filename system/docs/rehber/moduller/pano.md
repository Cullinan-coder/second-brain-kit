# Kopya geçmişi (Pano)

> Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.

| | |
|---|---|
| Modül kimliği | `pano` |
| Kategori | Verimlilik ve iletişim |
| Varsayılan | kapalı (isteğe bağlı özellik) |
| Madde sayısı | 8 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.

Bu modül özellik kataloğundan **8 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Kopya geçmişi (Pano)`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on pano` açar, `sb features --off pano` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** hiçbir yoğunluk seçiminde kendiliğinden açılmaz; elle açarsın.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Kopya geçmişi (Görünümler menüsü; kısayol: /)** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** bu modülün kendine ait komutu yoktur; asistan ya da uygulama üzerinden çalışır.
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb pano status` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [251](#madde-251) | Kopya geçmişi — metin, bağlantı ve görsel toplama (yerel izleyici, varsayılan kapalı) | hazır | 0.10.1 |
| [252](#madde-252) | Kopya geçmişi — görsel, metin ve bağlantı için üç raf | hazır | 0.10.1 |
| [253](#madde-253) | Kopya geçmişi — sabitleme, klasör ve etiket | hazır | 0.10.1 |
| [254](#madde-254) | Kopya geçmişi — arama ve görsellerde OCR | hazır | 0.10.1 |
| [255](#madde-255) | Kopya geçmişi — tutma süresi seçimi ve çöp kutusu | hazır | 0.10.1 |
| [256](#madde-256) | Kopya geçmişi — sır süzgeci (parola, anahtar, IBAN, kart numarası kaydedilmez) | hazır | 0.10.1 |
| [257](#madde-257) | Kopya geçmişi — uygulama kara listesi (parola yöneticileri) ve boyut sınırları | hazır | 0.10.1 |
| [258](#madde-258) | Kopya geçmişi — klavyeyle gezinme, tek tuşla geri kopyalama ve sb pano komutu | hazır | 0.10.1 |

<a id="madde-251"></a>

### 251. Kopya geçmişi — metin, bağlantı ve görsel toplama (yerel izleyici, varsayılan kapalı)

- **Ne işe yarar:** «Kopya geçmişi — metin, bağlantı ve görsel toplama (yerel izleyici, varsayılan kapalı)» (Görev, takvim ve verimlilik kategorisi), «Kopya geçmişi (Pano)» modülünün parçasıdır. Modülün amacı: Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.
- **Durum:** hazır (sürüm 0.10.1).
- **Nasıl açılır:** «Kopya geçmişi (Pano)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**.

<a id="madde-252"></a>

### 252. Kopya geçmişi — görsel, metin ve bağlantı için üç raf

- **Ne işe yarar:** «Kopya geçmişi — görsel, metin ve bağlantı için üç raf» (Görev, takvim ve verimlilik kategorisi), «Kopya geçmişi (Pano)» modülünün parçasıdır. Modülün amacı: Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.
- **Durum:** hazır (sürüm 0.10.1).
- **Nasıl açılır:** «Kopya geçmişi (Pano)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**.

<a id="madde-253"></a>

### 253. Kopya geçmişi — sabitleme, klasör ve etiket

- **Ne işe yarar:** «Kopya geçmişi — sabitleme, klasör ve etiket» (Görev, takvim ve verimlilik kategorisi), «Kopya geçmişi (Pano)» modülünün parçasıdır. Modülün amacı: Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.
- **Durum:** hazır (sürüm 0.10.1).
- **Nasıl açılır:** «Kopya geçmişi (Pano)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**.

<a id="madde-254"></a>

### 254. Kopya geçmişi — arama ve görsellerde OCR

- **Ne işe yarar:** «Kopya geçmişi — arama ve görsellerde OCR» (Görev, takvim ve verimlilik kategorisi), «Kopya geçmişi (Pano)» modülünün parçasıdır. Modülün amacı: Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.
- **Durum:** hazır (sürüm 0.10.1).
- **Nasıl açılır:** «Kopya geçmişi (Pano)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**.

<a id="madde-255"></a>

### 255. Kopya geçmişi — tutma süresi seçimi ve çöp kutusu

- **Ne işe yarar:** «Kopya geçmişi — tutma süresi seçimi ve çöp kutusu» (Görev, takvim ve verimlilik kategorisi), «Kopya geçmişi (Pano)» modülünün parçasıdır. Modülün amacı: Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.
- **Durum:** hazır (sürüm 0.10.1).
- **Nasıl açılır:** «Kopya geçmişi (Pano)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**.

<a id="madde-256"></a>

### 256. Kopya geçmişi — sır süzgeci (parola, anahtar, IBAN, kart numarası kaydedilmez)

- **Ne işe yarar:** «Kopya geçmişi — sır süzgeci (parola, anahtar, IBAN, kart numarası kaydedilmez)» (Görev, takvim ve verimlilik kategorisi), «Kopya geçmişi (Pano)» modülünün parçasıdır. Modülün amacı: Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.
- **Durum:** hazır (sürüm 0.10.1).
- **Nasıl açılır:** «Kopya geçmişi (Pano)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**.

<a id="madde-257"></a>

### 257. Kopya geçmişi — uygulama kara listesi (parola yöneticileri) ve boyut sınırları

- **Ne işe yarar:** «Kopya geçmişi — uygulama kara listesi (parola yöneticileri) ve boyut sınırları» (Görev, takvim ve verimlilik kategorisi), «Kopya geçmişi (Pano)» modülünün parçasıdır. Modülün amacı: Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.
- **Durum:** hazır (sürüm 0.10.1).
- **Nasıl açılır:** «Kopya geçmişi (Pano)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**.

<a id="madde-258"></a>

### 258. Kopya geçmişi — klavyeyle gezinme, tek tuşla geri kopyalama ve sb pano komutu

- **Ne işe yarar:** «Kopya geçmişi — klavyeyle gezinme, tek tuşla geri kopyalama ve sb pano komutu» (Görev, takvim ve verimlilik kategorisi), «Kopya geçmişi (Pano)» modülünün parçasıdır. Modülün amacı: Kopyaladığın metin, bağlantı ve görselleri yerelde geçmiş olarak saklar; ara, sabitle, klasörle. Parola, anahtar, IBAN ve kart numarası gibi görünenler hiç kaydedilmez.
- **Durum:** hazır (sürüm 0.10.1).
- **Nasıl açılır:** «Kopya geçmişi (Pano)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Kopya geçmişi (Görünümler menüsü; kısayol: /)**.
