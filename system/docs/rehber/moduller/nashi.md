# Nashi (dosya dönüştürücü)

> Hazır açık kaynak (MIT) uygulama; dosya dönüştürme, sıkıştırma ve düzenleme araçları. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve dışa aktardığı dosyaların kaydını (desteklenen türlerde içeriğiyle) beynine okur.

| | |
|---|---|
| Modül kimliği | `nashi` |
| Kategori | Hazır uygulamalar |
| Varsayılan | açık |
| Madde sayısı | 4 |
| Ne ister | program: nashi |

## Ne işe yarar

Hazır açık kaynak (MIT) uygulama; dosya dönüştürme, sıkıştırma ve düzenleme araçları. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve dışa aktardığı dosyaların kaydını (desteklenen türlerde içeriğiyle) beynine okur.

Bu modül özellik kataloğundan **4 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Nashi (dosya dönüştürücü)`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on nashi` açar, `sb features --off nashi` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Bilgisayarda kurulu olması gereken programlar:** nashi


## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb apps`](../14-komut-referansi.md#sb-apps) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Bağlı veri kaynakları

- [Nashi dışa aktarım kaydı](../kaynaklar/nashi.md): Nashi'nin library.json dosyası → dışa aktarılan dosyaların yolu, zamanı ve (desteklenen türlerde) içeriği.

## Sağlık testi

Çalışıp çalışmadığını `sb apps status nashi` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [253](#madde-253) | Nashi — taşınabilir Windows/macOS sürümünün kurulumu, açılışı ve durum denetimi | hazır | 0.11.0 |
| [256](#madde-256) | Nashi → beyin — dışa aktarılan dosyaların kaydı ve desteklenen türlerde içeriği | hazır | 0.11.0 |
| [257](#madde-257) | Kurulum sihirbazında Uygulamalar bölümü ve asistanda Uygulamalar kartı | hazır | 0.11.0 |
| [258](#madde-258) | Uygulamalar günlük çalışmada, Çalışmaya başla adımında ve asistan açıkken 5 dakikada bir senkron | hazır | 0.11.0 |

<a id="madde-253"></a>

### 253. Nashi — taşınabilir Windows/macOS sürümünün kurulumu, açılışı ve durum denetimi

- **Ne işe yarar:** «Nashi — taşınabilir Windows/macOS sürümünün kurulumu, açılışı ve durum denetimi» (Görev, takvim ve verimlilik kategorisi), «Nashi (dosya dönüştürücü)» modülünün parçasıdır. Modülün amacı: Hazır açık kaynak (MIT) uygulama; dosya dönüştürme, sıkıştırma ve düzenleme araçları. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve dışa aktardığı dosyaların kaydını (desteklenen türlerde içeriğiyle) beynine okur.
- **Durum:** hazır (sürüm 0.11.0).
- **Nasıl açılır:** «Nashi (dosya dönüştürücü)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: nashi.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps).

<a id="madde-256"></a>

### 256. Nashi → beyin — dışa aktarılan dosyaların kaydı ve desteklenen türlerde içeriği

- **Ne işe yarar:** «Nashi → beyin — dışa aktarılan dosyaların kaydı ve desteklenen türlerde içeriği» (Görev, takvim ve verimlilik kategorisi), «Nashi (dosya dönüştürücü)» modülünün parçasıdır. Modülün amacı: Hazır açık kaynak (MIT) uygulama; dosya dönüştürme, sıkıştırma ve düzenleme araçları. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve dışa aktardığı dosyaların kaydını (desteklenen türlerde içeriğiyle) beynine okur.
- **Durum:** hazır (sürüm 0.11.0).
- **Nasıl açılır:** «Nashi (dosya dönüştürücü)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: nashi.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps).

<a id="madde-257"></a>

### 257. Kurulum sihirbazında Uygulamalar bölümü ve asistanda Uygulamalar kartı

- **Ne işe yarar:** «Kurulum sihirbazında Uygulamalar bölümü ve asistanda Uygulamalar kartı» (Görev, takvim ve verimlilik kategorisi), «Nashi (dosya dönüştürücü)» modülünün parçasıdır. Modülün amacı: Hazır açık kaynak (MIT) uygulama; dosya dönüştürme, sıkıştırma ve düzenleme araçları. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve dışa aktardığı dosyaların kaydını (desteklenen türlerde içeriğiyle) beynine okur.
- **Durum:** hazır (sürüm 0.11.0).
- **Nasıl açılır:** «Nashi (dosya dönüştürücü)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: nashi.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps).

<a id="madde-258"></a>

### 258. Uygulamalar günlük çalışmada, Çalışmaya başla adımında ve asistan açıkken 5 dakikada bir senkron

- **Ne işe yarar:** «Uygulamalar günlük çalışmada, Çalışmaya başla adımında ve asistan açıkken 5 dakikada bir senkron» (Görev, takvim ve verimlilik kategorisi), «Nashi (dosya dönüştürücü)» modülünün parçasıdır. Modülün amacı: Hazır açık kaynak (MIT) uygulama; dosya dönüştürme, sıkıştırma ve düzenleme araçları. Second Brain onu kurar, istersen bilgisayar açılınca başlatır ve dışa aktardığı dosyaların kaydını (desteklenen türlerde içeriğiyle) beynine okur.
- **Durum:** hazır (sürüm 0.11.0).
- **Nasıl açılır:** «Nashi (dosya dönüştürücü)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** program: nashi.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla (Uygulamalar kartı)**, **Uygulama ayarları → Başlangıç sekmesi (Hazır uygulamalar)**; komut: [`sb apps`](../14-komut-referansi.md#sb-apps).
