# Telefon erişimi

> Asistana telefondan Tailscale ile erişim

| | |
|---|---|
| Modül kimliği | `phone` |
| Kategori | Telefon ve mesaj |
| Varsayılan | açık |
| Madde sayısı | 8 |
| Ne ister | hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale |

## Ne işe yarar

Asistana telefondan Tailscale ile erişim.

Bu modül özellik kataloğundan **8 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Telefon erişimi`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on phone` açar, `sb features --off phone` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).
4. Ek kurulum belgesi: `docs/telefon-pwa.md` (kitin `docs` klasöründe; rehberdeki karşılığı için [Telefon](../08-uygulama-turu.md#telefon)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Tailscale](../03-hesaplar.md#hesap-tailscale)

**Bilgisayarda kurulu olması gereken programlar:** Tailscale


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Tailscale cihaz adı (`tailscale_name`) | metin | hayır | tailscale status çıktısındaki bilgisayar adı. |

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Telefon eşleme (üst çubuktaki telefon simgesi)** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** bu modülün kendine ait komutu yoktur; asistan ya da uygulama üzerinden çalışır.
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [75](#madde-75) | Telefon uygulaması (PWA iyileştirme) | hazır | 0.9.0 |
| [78](#madde-78) | Telefon push bildirimleri | hazır | 0.9.0 |
| [79](#madde-79) | Telefon widget'ı | planlandı (henüz yok) | 0.9.0 |
| [80](#madde-80) | Çevrimdışı kuyruk | hazır | 0.9.0 |
| [81](#madde-81) | Konum tabanlı hatırlatma | planlandı (henüz yok) | 0.9.0 |
| [82](#madde-82) | Obsidian mobil eşitleme kurulumu | hazır | 0.9.0 |
| [83](#madde-83) | iOS Kestirmeler / Android Tasker | hazır | 0.9.0 |
| [86](#madde-86) | Güvenli tünel seçeneği (Cloudflare Tunnel) | hazır | 0.9.0 |

<a id="madde-75"></a>

### 75. Telefon uygulaması (PWA iyileştirme)

- **Ne işe yarar:** «Telefon uygulaması (PWA iyileştirme)» (Mobil kategorisi), «Telefon erişimi» modülünün parçasıdır. Modülün amacı: Asistana telefondan Tailscale ile erişim.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Telefon erişimi» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**.

<a id="madde-78"></a>

### 78. Telefon push bildirimleri

- **Ne işe yarar:** «Telefon push bildirimleri» (Mobil kategorisi), «Telefon erişimi» modülünün parçasıdır. Modülün amacı: Asistana telefondan Tailscale ile erişim.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Telefon erişimi» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**.

<a id="madde-79"></a>

### 79. Telefon widget'ı

- **Ne işe yarar:** «Telefon widget'ı» (Mobil kategorisi), «Telefon erişimi» modülünün parçasıdır. Modülün amacı: Asistana telefondan Tailscale ile erişim.
- **Durum:** planlandı (henüz yok); yol haritasında Faz 5 / sürüm 0.9.0 için yer alır. Şu an tam çalışmasını bekleme.
- **Nasıl açılır:** «Telefon erişimi» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale.
- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.
- **İlgili ekran/komut:** ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**.

<a id="madde-80"></a>

### 80. Çevrimdışı kuyruk

- **Ne işe yarar:** «Çevrimdışı kuyruk» (Mobil kategorisi), «Telefon erişimi» modülünün parçasıdır. Modülün amacı: Asistana telefondan Tailscale ile erişim.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Telefon erişimi» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**.

<a id="madde-81"></a>

### 81. Konum tabanlı hatırlatma

- **Ne işe yarar:** «Konum tabanlı hatırlatma» (Mobil kategorisi), «Telefon erişimi» modülünün parçasıdır. Modülün amacı: Asistana telefondan Tailscale ile erişim.
- **Durum:** planlandı (henüz yok); yol haritasında Faz 5 / sürüm 0.9.0 için yer alır. Şu an tam çalışmasını bekleme.
- **Nasıl açılır:** «Telefon erişimi» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale.
- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.
- **İlgili ekran/komut:** ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**.

<a id="madde-82"></a>

### 82. Obsidian mobil eşitleme kurulumu

- **Ne işe yarar:** «Obsidian mobil eşitleme kurulumu» (Mobil kategorisi), «Telefon erişimi» modülünün parçasıdır. Modülün amacı: Asistana telefondan Tailscale ile erişim.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Telefon erişimi» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**.

<a id="madde-83"></a>

### 83. iOS Kestirmeler / Android Tasker

- **Ne işe yarar:** «iOS Kestirmeler / Android Tasker» (Mobil kategorisi), «Telefon erişimi» modülünün parçasıdır. Modülün amacı: Asistana telefondan Tailscale ile erişim.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Telefon erişimi» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**.

<a id="madde-86"></a>

### 86. Güvenli tünel seçeneği (Cloudflare Tunnel)

- **Ne işe yarar:** «Güvenli tünel seçeneği (Cloudflare Tunnel)» (Mobil kategorisi), «Telefon erişimi» modülünün parçasıdır. Modülün amacı: Asistana telefondan Tailscale ile erişim.
- **Durum:** hazır (sürüm 0.9.0).
- **Nasıl açılır:** «Telefon erişimi» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Tailscale](../03-hesaplar.md#hesap-tailscale); alan: Tailscale cihaz adı (`tailscale_name`); program: Tailscale.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**. Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Telefon eşleme (üst çubuktaki telefon simgesi)**.
