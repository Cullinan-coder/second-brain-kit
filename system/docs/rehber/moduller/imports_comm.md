# Mesaj içe aktarmaları

> Outlook, iCloud, Telegram, Discord, Slack arşivleri.

| | |
|---|---|
| Modül kimliği | `imports_comm` |
| Kategori | Veri kaynakları |
| Varsayılan | açık |
| Madde sayısı | 5 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

Outlook, iCloud, Telegram, Discord, Slack arşivleri.

Bu modül özellik kataloğundan **5 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Mesaj içe aktarmaları`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb import`](../14-komut-referansi.md#sb-import) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Bağlı veri kaynakları

- [Discord veri paketi](../kaynaklar/discord.md): Discord 'verilerimi iste' paketi → mesajlar.
- [iCloud mail, takvim, kişiler](../kaynaklar/icloud.md): iCloud IMAP + CalDAV/CardDAV.
- [Outlook / Microsoft 365 mail](../kaynaklar/outlook.md): Outlook posta ve takvim (IMAP + yayımlı takvim bağlantısı).
- [Slack dışa aktarımı](../kaynaklar/slack.md): Slack çalışma alanı dışa aktarımı → mesajlar.
- [Telegram arşivi](../kaynaklar/telegram.md): Telegram Desktop dışa aktarımı (result.json) → mesajlar.

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [88](#madde-88) | Outlook / Microsoft 365 | hazır | 0.5.0 |
| [89](#madde-89) | iCloud mail, takvim, kişiler | hazır | 0.5.0 |
| [90](#madde-90) | Telegram mesaj arşivi | hazır | 0.5.0 |
| [91](#madde-91) | Discord arşivi | hazır | 0.8.0 |
| [92](#madde-92) | Slack | hazır | 0.8.0 |

<a id="madde-88"></a>

### 88. Outlook / Microsoft 365

- **Ne işe yarar:** «Outlook / Microsoft 365» (Yeni veri kaynakları kategorisi), «Mesaj içe aktarmaları» modülünün parçasıdır. Modülün amacı: Outlook, iCloud, Telegram, Discord, Slack arşivleri.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Mesaj içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-89"></a>

### 89. iCloud mail, takvim, kişiler

- **Ne işe yarar:** «iCloud mail, takvim, kişiler» (Yeni veri kaynakları kategorisi), «Mesaj içe aktarmaları» modülünün parçasıdır. Modülün amacı: Outlook, iCloud, Telegram, Discord, Slack arşivleri.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Mesaj içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-90"></a>

### 90. Telegram mesaj arşivi

- **Ne işe yarar:** «Telegram mesaj arşivi» (Yeni veri kaynakları kategorisi), «Mesaj içe aktarmaları» modülünün parçasıdır. Modülün amacı: Outlook, iCloud, Telegram, Discord, Slack arşivleri.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «Mesaj içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-91"></a>

### 91. Discord arşivi

- **Ne işe yarar:** «Discord arşivi» (Yeni veri kaynakları kategorisi), «Mesaj içe aktarmaları» modülünün parçasıdır. Modülün amacı: Outlook, iCloud, Telegram, Discord, Slack arşivleri.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Mesaj içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).

<a id="madde-92"></a>

### 92. Slack

- **Ne işe yarar:** «Slack» (Yeni veri kaynakları kategorisi), «Mesaj içe aktarmaları» modülünün parçasıdır. Modülün amacı: Outlook, iCloud, Telegram, Discord, Slack arşivleri.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Mesaj içe aktarmaları» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** ek hesap, anahtar ya da program gerekmez.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb import`](../14-komut-referansi.md#sb-import). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb import`](../14-komut-referansi.md#sb-import).
