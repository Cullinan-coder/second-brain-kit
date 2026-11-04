# Otomasyonlar ve ajanlar

> Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu

| | |
|---|---|
| Modül kimliği | `automation` |
| Kategori | Asistan ve hafıza |
| Varsayılan | açık |
| Madde sayısı | 10 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.

Bu modül özellik kataloğundan **10 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Otomasyonlar ve ajanlar`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on automation` açar, `sb features --off automation` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Yazılımcı, Girişimci, Satış / CRM, Araştırmacı seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Otomasyonlar**, **Ajanlar**, **Ajan izleme** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [216](#madde-216) | Otomasyon oluşturucu (her X olduğunda Y) | hazır | 0.8.0 |
| [217](#madde-217) | Ajan pazarı (hazır ajanlar) | hazır | 0.8.0 |
| [218](#madde-218) | Zamanlanmış rapor ajanları | hazır | 0.8.0 |
| [219](#madde-219) | Web araştırma ajanı | hazır | 0.8.0 |
| [222](#madde-222) | Ajan izleme paneli | hazır | 0.8.0 |
| [223](#madde-223) | Webhook ve e-posta tetikleyicileri | hazır | 0.8.0 |
| [224](#madde-224) | Zapier / n8n / Make | hazır | 0.8.0 |
| [225](#madde-225) | Ajan kum havuzu (izinler) | hazır | 0.8.0 |
| [226](#madde-226) | Çok ajanlı akış şablonları | hazır | 0.8.0 |
| [227](#madde-227) | Akış ortasında insan onayı | hazır | 0.8.0 |

<a id="madde-216"></a>

### 216. Otomasyon oluşturucu (her X olduğunda Y)

- **Ne işe yarar:** «Otomasyon oluşturucu (her X olduğunda Y)» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-217"></a>

### 217. Ajan pazarı (hazır ajanlar)

- **Ne işe yarar:** «Ajan pazarı (hazır ajanlar)» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-218"></a>

### 218. Zamanlanmış rapor ajanları

- **Ne işe yarar:** «Zamanlanmış rapor ajanları» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-219"></a>

### 219. Web araştırma ajanı

- **Ne işe yarar:** «Web araştırma ajanı» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-222"></a>

### 222. Ajan izleme paneli

- **Ne işe yarar:** «Ajan izleme paneli» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-223"></a>

### 223. Webhook ve e-posta tetikleyicileri

- **Ne işe yarar:** «Webhook ve e-posta tetikleyicileri» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-224"></a>

### 224. Zapier / n8n / Make

- **Ne işe yarar:** «Zapier / n8n / Make» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-225"></a>

### 225. Ajan kum havuzu (izinler)

- **Ne işe yarar:** «Ajan kum havuzu (izinler)» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-226"></a>

### 226. Çok ajanlı akış şablonları

- **Ne işe yarar:** «Çok ajanlı akış şablonları» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).

<a id="madde-227"></a>

### 227. Akış ortasında insan onayı

- **Ne işe yarar:** «Akış ortasında insan onayı» (Ajanlar ve otomasyon kategorisi), «Otomasyonlar ve ajanlar» modülünün parçasıdır. Modülün amacı: Kurallar (her X olduğunda Y), hazır ajanlar, onay kuyruğu.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Otomasyonlar ve ajanlar» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Otomasyonlar**, **Ajanlar**, **Ajan izleme**; komut: [`sb automation-tick`](../14-komut-referansi.md#sb-automation-tick).
