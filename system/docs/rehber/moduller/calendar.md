# Google Takvim

> Takvimi kasaya alır; onaylı ekleme ve silme

| | |
|---|---|
| Modül kimliği | `calendar` |
| Kategori | Mail ve takvim |
| Varsayılan | açık |
| Madde sayısı | 2 |
| Ne ister | hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`) |

## Ne işe yarar

Takvimi kasaya alır; onaylı ekleme ve silme.

Bu modül özellik kataloğundan **2 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Google Takvim`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on calendar` açar, `sb features --off calendar` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).
4. Ek kurulum belgesi: `docs/google-cloud-kurulum.md` (kitin `docs` klasöründe; rehberdeki karşılığı için [Hesaplar](../03-hesaplar.md#hesap-google)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Google](../03-hesaplar.md#hesap-google)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Ana Gmail adresi (`gmail`) | e-posta adresi | evet | Google ile giriş yapılacak hesap. |
| Google client_secret.json yolu (`client_secret`) | dosya ya da klasör yolu | hayır | Google Cloud'da OAuth istemcisi oluşturup indir (docs/google-cloud-kurulum.md). |

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Öğrenci, Ajans / Freelancer, Girişimci, Satış / CRM seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Pano (Bugün)**, **Bugün planı** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb approve`](../14-komut-referansi.md#sb-approve), [`sb sync-gcal`](../14-komut-referansi.md#sb-sync-gcal), [`sb import-gcal`](../14-komut-referansi.md#sb-import-gcal), [`sb add-event`](../14-komut-referansi.md#sb-add-event), [`sb extract-dates`](../14-komut-referansi.md#sb-extract-dates) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [164](#madde-164) | Zaman bloklama (onaylı) | hazır | 0.7.0 |
| [177](#madde-177) | Takvim çakışma tespiti | hazır | 0.7.0 |

<a id="madde-164"></a>

### 164. Zaman bloklama (onaylı)

- **Ne işe yarar:** «Zaman bloklama (onaylı)» (Görev, takvim ve verimlilik kategorisi), «Google Takvim» modülünün parçasıdır. Modülün amacı: Takvimi kasaya alır; onaylı ekleme ve silme.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Google Takvim» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Pano (Bugün)**, **Bugün planı**; komut: [`sb approve`](../14-komut-referansi.md#sb-approve), [`sb sync-gcal`](../14-komut-referansi.md#sb-sync-gcal), [`sb import-gcal`](../14-komut-referansi.md#sb-import-gcal), [`sb add-event`](../14-komut-referansi.md#sb-add-event), [`sb extract-dates`](../14-komut-referansi.md#sb-extract-dates). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Pano (Bugün)**, **Bugün planı**; komut: [`sb approve`](../14-komut-referansi.md#sb-approve), [`sb sync-gcal`](../14-komut-referansi.md#sb-sync-gcal), [`sb import-gcal`](../14-komut-referansi.md#sb-import-gcal), [`sb add-event`](../14-komut-referansi.md#sb-add-event), [`sb extract-dates`](../14-komut-referansi.md#sb-extract-dates).

<a id="madde-177"></a>

### 177. Takvim çakışma tespiti

- **Ne işe yarar:** «Takvim çakışma tespiti» (Görev, takvim ve verimlilik kategorisi), «Google Takvim» modülünün parçasıdır. Modülün amacı: Takvimi kasaya alır; onaylı ekleme ve silme.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Google Takvim» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Google](../03-hesaplar.md#hesap-google); alan: Ana Gmail adresi (`gmail`), Google client_secret.json yolu (`client_secret`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Pano (Bugün)**, **Bugün planı**; komut: [`sb approve`](../14-komut-referansi.md#sb-approve), [`sb sync-gcal`](../14-komut-referansi.md#sb-sync-gcal), [`sb import-gcal`](../14-komut-referansi.md#sb-import-gcal), [`sb add-event`](../14-komut-referansi.md#sb-add-event), [`sb extract-dates`](../14-komut-referansi.md#sb-extract-dates). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Pano (Bugün)**, **Bugün planı**; komut: [`sb approve`](../14-komut-referansi.md#sb-approve), [`sb sync-gcal`](../14-komut-referansi.md#sb-sync-gcal), [`sb import-gcal`](../14-komut-referansi.md#sb-import-gcal), [`sb add-event`](../14-komut-referansi.md#sb-add-event), [`sb extract-dates`](../14-komut-referansi.md#sb-extract-dates).
