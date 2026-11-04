# Ses

> Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı

| | |
|---|---|
| Modül kimliği | `voice` |
| Kategori | Bilgisayar ve ses |
| Varsayılan | açık |
| Madde sayısı | 10 |
| Ne ister | donanım: bellek (RAM) ≥ 8 GB |

## Ne işe yarar

Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.

Bu modül özellik kataloğundan **10 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Ses`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on voice` açar, `sb features --off voice` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Donanım:** bellek (RAM) en az 8 GB.


## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Öğrenci, Akademisyen, İçerik üreticisi, Araştırmacı seçimlerinde ayrıca eklenir.
- **Donanım nedeniyle kapanır:** Zayıf laptop / bulut.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb voice`](../14-komut-referansi.md#sb-voice) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [38](#madde-38) | Konuşmayı yazıya çevirme (Whisper, yerel) | hazır | 0.6.0 |
| [39](#madde-39) | Sesli cevap (TTS) ve ses seçimi | hazır | 0.6.0 |
| [41](#madde-41) | Bas-konuş kısayolu ve mikrofon düğmesi | hazır | 0.6.0 |
| [42](#madde-42) | Telefonda sesli not | hazır | 0.6.0 |
| [43](#madde-43) | Toplantı/ders kaydı: döküm, özet, görev, karar | hazır | 0.6.0 |
| [44](#madde-44) | Video ve podcast dökümü | hazır | 0.6.0 |
| [50](#madde-50) | Konuşma kesme (barge-in) | hazır | 0.6.0 |
| [51](#madde-51) | Çok dilli ses | hazır | 0.6.0 |
| [52](#madde-52) | Telaffuz ve konuşma koçu | hazır | 0.6.0 |
| [84](#madde-84) | Saat üzerinden sesli not | planlandı (henüz yok) | 0.9.0 |

<a id="madde-38"></a>

### 38. Konuşmayı yazıya çevirme (Whisper, yerel)

- **Ne işe yarar:** «Konuşmayı yazıya çevirme (Whisper, yerel)» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-39"></a>

### 39. Sesli cevap (TTS) ve ses seçimi

- **Ne işe yarar:** «Sesli cevap (TTS) ve ses seçimi» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-41"></a>

### 41. Bas-konuş kısayolu ve mikrofon düğmesi

- **Ne işe yarar:** «Bas-konuş kısayolu ve mikrofon düğmesi» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-42"></a>

### 42. Telefonda sesli not

- **Ne işe yarar:** «Telefonda sesli not» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-43"></a>

### 43. Toplantı/ders kaydı: döküm, özet, görev, karar

- **Ne işe yarar:** «Toplantı/ders kaydı: döküm, özet, görev, karar» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-44"></a>

### 44. Video ve podcast dökümü

- **Ne işe yarar:** «Video ve podcast dökümü» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-50"></a>

### 50. Konuşma kesme (barge-in)

- **Ne işe yarar:** «Konuşma kesme (barge-in)» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-51"></a>

### 51. Çok dilli ses

- **Ne işe yarar:** «Çok dilli ses» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-52"></a>

### 52. Telaffuz ve konuşma koçu

- **Ne işe yarar:** «Telaffuz ve konuşma koçu» (Ses ve çok kipli kullanım kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** hazır (sürüm 0.6.0).
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).

<a id="madde-84"></a>

### 84. Saat üzerinden sesli not

- **Ne işe yarar:** «Saat üzerinden sesli not» (Mobil kategorisi), «Ses» modülünün parçasıdır. Modülün amacı: Konuşmayı yazıya çevirme (yerel Whisper), sesli cevap, sesli not, toplantı/ders kaydı.
- **Durum:** planlandı (henüz yok); yol haritasında Faz 5 / sürüm 0.9.0 için yer alır. Şu an tam çalışmasını bekleme.
- **Nasıl açılır:** «Ses» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** donanım: bellek (RAM) ≥ 8 GB.
- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.
- **İlgili ekran/komut:** ekran: **Sohbet kutusundaki mikrofon düğmesi**, **Ayarlar (Cevapları sesli oku, Ses)**; komut: [`sb voice`](../14-komut-referansi.md#sb-voice).
