# Fatura ve kargo

> Maillerden fatura ve kargo kayıtları

| | |
|---|---|
| Modül kimliği | `derived` |
| Kategori | Mail ve takvim |
| Varsayılan | açık |
| Madde sayısı | 3 |
| Ne ister | hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`) |

## Ne işe yarar

Maillerden fatura ve kargo kayıtları.

Bu modül özellik kataloğundan **3 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Fatura ve kargo`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on derived` açar, `sb features --off derived` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Google](../03-hesaplar.md#hesap-google)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Ana Gmail adresi (`gmail`) | e-posta adresi | evet | Google ile giriş yapılacak hesap. |

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Girişimci, Satış / CRM seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb derive`](../14-komut-referansi.md#sb-derive) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [116](#madde-116) | Fatura ve e-arşiv faturaları | hazır | 0.5.0 |
| [117](#madde-117) | Kargo takibi | hazır | 0.5.0 |
| [232](#madde-232) | Garanti ve fatura takibi | hazır | 0.8.0 |

<a id="madde-116"></a>

### 116. Fatura ve e-arşiv faturaları

- **Ne işe yarar:** «Fatura ve e-arşiv faturaları» (Yeni veri kaynakları kategorisi), «Fatura ve kargo» modülünün parçasıdır. Modülün amacı: Maillerden fatura ve kargo kayıtları.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Fatura ve kargo» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb derive`](../14-komut-referansi.md#sb-derive). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb derive`](../14-komut-referansi.md#sb-derive).

<a id="madde-117"></a>

### 117. Kargo takibi

- **Ne işe yarar:** «Kargo takibi» (Yeni veri kaynakları kategorisi), «Fatura ve kargo» modülünün parçasıdır. Modülün amacı: Maillerden fatura ve kargo kayıtları.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Fatura ve kargo» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb derive`](../14-komut-referansi.md#sb-derive). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb derive`](../14-komut-referansi.md#sb-derive).

<a id="madde-232"></a>

### 232. Garanti ve fatura takibi

- **Ne işe yarar:** «Garanti ve fatura takibi» (Kişisel yaşam kategorisi), «Fatura ve kargo» modülünün parçasıdır. Modülün amacı: Maillerden fatura ve kargo kayıtları.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Fatura ve kargo» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb derive`](../14-komut-referansi.md#sb-derive). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb derive`](../14-komut-referansi.md#sb-derive).
