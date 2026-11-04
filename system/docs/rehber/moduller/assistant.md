# Yerel asistan

> Obsidian yan paneli ve telefondan sohbet

| | |
|---|---|
| Modül kimliği | `assistant` |
| Kategori | Asistan ve hafıza |
| Varsayılan | açık |
| Madde sayısı | 10 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Obsidian yan paneli ve telefondan sohbet.

Bu modül özellik kataloğundan **10 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Yerel asistan`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on assistant` açar, `sb features --off assistant` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Minimal, Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Sohbet ekranı (ana pencere)** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [54](#madde-54) | Sohbet geçmişi listesi, arama, sabitleme | hazır | 0.6.0 |
| [55](#madde-55) | Kaynak kartları (tıklanabilir dayanak) | hazır | 0.6.0 |
| [56](#madde-56) | Onay kartları yeniden tasarım | hazır | 0.6.0 |
| [59](#madde-59) | Eğik çizgi komutları | hazır | 0.6.0 |
| [60](#madde-60) | Mesaj düzenle, yeniden üret, nota çevir | hazır | 0.6.0 |
| [61](#madde-61) | Sohbete dosya sürükle-bırak | hazır | 0.6.0 |
| [64](#madde-64) | Mini sohbet balonu | hazır | 0.8.0 |
| [65](#madde-65) | Obsidian eklentisi | hazır | 0.8.0 |
| [73](#madde-73) | Ses + metin karışık sohbet | hazır | 0.6.0 |
| [74](#madde-74) | Hızlı tepki düğmeleri | hazır | 0.6.0 |

<a id="madde-54"></a>

### 54. Sohbet geçmişi listesi, arama, sabitleme

- **Ne işe yarar:** «Sohbet geçmişi listesi, arama, sabitleme» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-55"></a>

### 55. Kaynak kartları (tıklanabilir dayanak)

- **Ne işe yarar:** «Kaynak kartları (tıklanabilir dayanak)» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-56"></a>

### 56. Onay kartları yeniden tasarım

- **Ne işe yarar:** «Onay kartları yeniden tasarım» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-59"></a>

### 59. Eğik çizgi komutları

- **Ne işe yarar:** «Eğik çizgi komutları» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-60"></a>

### 60. Mesaj düzenle, yeniden üret, nota çevir

- **Ne işe yarar:** «Mesaj düzenle, yeniden üret, nota çevir» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-61"></a>

### 61. Sohbete dosya sürükle-bırak

- **Ne işe yarar:** «Sohbete dosya sürükle-bırak» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-64"></a>

### 64. Mini sohbet balonu

- **Ne işe yarar:** «Mini sohbet balonu» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-65"></a>

### 65. Obsidian eklentisi

- **Ne işe yarar:** «Obsidian eklentisi» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-73"></a>

### 73. Ses + metin karışık sohbet

- **Ne işe yarar:** «Ses + metin karışık sohbet» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).

<a id="madde-74"></a>

### 74. Hızlı tepki düğmeleri

- **Ne işe yarar:** «Hızlı tepki düğmeleri» (Asistan arayüzü ve deneyim kategorisi), «Yerel asistan» modülünün parçasıdır. Modülün amacı: Obsidian yan paneli ve telefondan sohbet.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Yerel asistan» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet ekranı (ana pencere)**; komut: [`sb chat`](../14-komut-referansi.md#sb-chat), [`sb ask`](../14-komut-referansi.md#sb-ask), [`sb asistan-undo`](../14-komut-referansi.md#sb-asistan-undo).
