# Kurulum paneli ve ürünleşme

> Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.

| | |
|---|---|
| Modül kimliği | `setup` |
| Kategori | Kurulum ve model |
| Varsayılan | açık |
| Madde sayısı | 22 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.

Bu modül özellik kataloğundan **22 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Kurulum paneli ve ürünleşme`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Minimal, Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Çalışmaya başla**, **Uygulama ayarları** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs), [`sb whatsnew`](../14-komut-referansi.md#sb-whatsnew) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [1](#madde-1) | Tek satırla kurulum (irm\|iex, curl\|sh) | hazır | 0.9.0 |
| [2](#madde-2) | Tarayıcıda açılan yerel kurulum paneli | hazır | 0.9.0 |
| [3](#madde-3) | Özellik kataloğu (features.yaml) ve özellik anahtarları | hazır | 0.4.0 |
| [4](#madde-4) | Hazır seçimler: Tam, Bulut, Minimal, Öğrenci, Ajans | hazır | 0.9.0 |
| [5](#madde-5) | Her özellik için açıklama ve gereksinim etiketi | hazır | 0.4.0 |
| [6](#madde-6) | Donanım tarayıcı ve model/hazır seçim önerisi | hazır | 0.9.0 |
| [7](#madde-7) | Panelde bilgi girişi; şifreler işletim sistemi kasasına | hazır | 0.9.0 |
| [8](#madde-8) | Canlı kurulum günlüğü ve ilerleme | hazır | 0.9.0 |
| [9](#madde-9) | Bağlantıyı test et düğmeleri | hazır | 0.9.0 |
| [10](#madde-10) | Kurulum profilini dışa/içe aktarma | hazır | 0.9.0 |
| [11](#madde-11) | Komut satırından sessiz kurulum (preset/config) | hazır | 0.9.0 |
| [12](#madde-12) | Seçili özellikleri geri alma | hazır | 0.9.0 |
| [13](#madde-13) | İlk 10 dakika turu | hazır | 0.9.0 |
| [14](#madde-14) | Google Cloud kurulum sihirbazı | hazır | 0.9.0 |
| [15](#madde-15) | Spotify, Telegram, Tailscale sihirbazları | hazır | 0.9.0 |
| [16](#madde-16) | Güncelleme sekmesi | hazır | 0.9.0 |
| [17](#madde-17) | Temiz kaldırma | hazır | 0.9.0 |
| [18](#madde-18) | Çok dilli panel (TR/EN) | hazır | 0.9.0 |
| [19](#madde-19) | Yarıda kalan kurulumu sürdürme | hazır | 0.9.0 |
| [20](#madde-20) | Sistem sağlığı sekmesi | hazır | 0.9.0 |
| [21](#madde-21) | İmzalı sürüm paketi ve SHA-256 | hazır | 0.9.0 |
| [22](#madde-22) | Kurumsal toplu kurulum | hazır | 0.9.0 |

<a id="madde-1"></a>

### 1. Tek satırla kurulum (irm|iex, curl|sh)

- **Ne işe yarar:** «Tek satırla kurulum (irm|iex, curl|sh)» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-2"></a>

### 2. Tarayıcıda açılan yerel kurulum paneli

- **Ne işe yarar:** «Tarayıcıda açılan yerel kurulum paneli» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-3"></a>

### 3. Özellik kataloğu (features.yaml) ve özellik anahtarları

- **Ne işe yarar:** «Özellik kataloğu (features.yaml) ve özellik anahtarları» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-4"></a>

### 4. Hazır seçimler: Tam, Bulut, Minimal, Öğrenci, Ajans

- **Ne işe yarar:** «Hazır seçimler: Tam, Bulut, Minimal, Öğrenci, Ajans» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-5"></a>

### 5. Her özellik için açıklama ve gereksinim etiketi

- **Ne işe yarar:** «Her özellik için açıklama ve gereksinim etiketi» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-6"></a>

### 6. Donanım tarayıcı ve model/hazır seçim önerisi

- **Ne işe yarar:** «Donanım tarayıcı ve model/hazır seçim önerisi» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-7"></a>

### 7. Panelde bilgi girişi; şifreler işletim sistemi kasasına

- **Ne işe yarar:** «Panelde bilgi girişi; şifreler işletim sistemi kasasına» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-8"></a>

### 8. Canlı kurulum günlüğü ve ilerleme

- **Ne işe yarar:** «Canlı kurulum günlüğü ve ilerleme» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-9"></a>

### 9. Bağlantıyı test et düğmeleri

- **Ne işe yarar:** «Bağlantıyı test et düğmeleri» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-10"></a>

### 10. Kurulum profilini dışa/içe aktarma

- **Ne işe yarar:** «Kurulum profilini dışa/içe aktarma» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-11"></a>

### 11. Komut satırından sessiz kurulum (preset/config)

- **Ne işe yarar:** «Komut satırından sessiz kurulum (preset/config)» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-12"></a>

### 12. Seçili özellikleri geri alma

- **Ne işe yarar:** «Seçili özellikleri geri alma» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-13"></a>

### 13. İlk 10 dakika turu

- **Ne işe yarar:** «İlk 10 dakika turu» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-14"></a>

### 14. Google Cloud kurulum sihirbazı

- **Ne işe yarar:** «Google Cloud kurulum sihirbazı» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-15"></a>

### 15. Spotify, Telegram, Tailscale sihirbazları

- **Ne işe yarar:** «Spotify, Telegram, Tailscale sihirbazları» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-16"></a>

### 16. Güncelleme sekmesi

- **Ne işe yarar:** «Güncelleme sekmesi» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-17"></a>

### 17. Temiz kaldırma

- **Ne işe yarar:** «Temiz kaldırma» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-18"></a>

### 18. Çok dilli panel (TR/EN)

- **Ne işe yarar:** «Çok dilli panel (TR/EN)» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-19"></a>

### 19. Yarıda kalan kurulumu sürdürme

- **Ne işe yarar:** «Yarıda kalan kurulumu sürdürme» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-20"></a>

### 20. Sistem sağlığı sekmesi

- **Ne işe yarar:** «Sistem sağlığı sekmesi» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-21"></a>

### 21. İmzalı sürüm paketi ve SHA-256

- **Ne işe yarar:** «İmzalı sürüm paketi ve SHA-256» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).

<a id="madde-22"></a>

### 22. Kurumsal toplu kurulum

- **Ne işe yarar:** «Kurumsal toplu kurulum» (Kurulum paneli ve ürünleşme kategorisi), «Kurulum paneli ve ürünleşme» modülünün parçasıdır. Modülün amacı: Tek satır kurulum, kurulum paneli, hazır seçimler, profil, güncelleme, sağlık.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Kurulum paneli ve ürünleşme» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Çalışmaya başla**, **Uygulama ayarları**; komut: [`sb doctor`](../14-komut-referansi.md#sb-doctor), [`sb update`](../14-komut-referansi.md#sb-update), [`sb version`](../14-komut-referansi.md#sb-version), [`sb features`](../14-komut-referansi.md#sb-features), [`sb roadmap`](../14-komut-referansi.md#sb-roadmap), [`sb logs`](../14-komut-referansi.md#sb-logs).
