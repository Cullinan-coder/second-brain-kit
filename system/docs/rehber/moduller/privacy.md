# Gizlilik ve güvenlik

> Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.

| | |
|---|---|
| Modül kimliği | `privacy` |
| Kategori | Gizlilik ve kalite |
| Varsayılan | açık |
| Madde sayısı | 8 |
| Ne ister | gizli değer: Kasa şifreleme parolası (`vault_key`) |

## Ne işe yarar

Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.

Bu modül özellik kataloğundan **8 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Gizlilik ve güvenlik`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.

## Hangi hesap, veri ya da anahtar ister


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Kasa şifreleme parolası (`vault_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | Kaybedersen kasa açılamaz; yedeğini sakla. |

Gizli değerler (`vault_key`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Hazır seçimlerde

- **Yoğunluk:** Minimal, Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Gizlilik** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [239](#madde-239) | Gizlilik paneli | hazır | 0.8.0 |
| [240](#madde-240) | Bulut gönderim süzgeci (maskeleme) | hazır | 0.8.0 |
| [241](#madde-241) | Kasa şifreleme (isteğe bağlı) | hazır | 0.8.0 |
| [242](#madde-242) | Denetim günlüğü arayüzü | hazır | 0.8.0 |
| [243](#madde-243) | İzin profilleri | hazır | 0.8.0 |
| [244](#madde-244) | Yedek ve geri yükleme sihirbazı | hazır | 0.8.0 |
| [245](#madde-245) | Veri dışa aktarma ve silme | hazır | 0.8.0 |
| [246](#madde-246) | İstem enjeksiyonu kalkanı testleri | hazır | 0.8.0 |

<a id="madde-239"></a>

### 239. Gizlilik paneli

- **Ne işe yarar:** «Gizlilik paneli» (Güvenlik ve gizlilik kategorisi), «Gizlilik ve güvenlik» modülünün parçasıdır. Modülün amacı: Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gizlilik ve güvenlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** gizli değer: Kasa şifreleme parolası (`vault_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test).

<a id="madde-240"></a>

### 240. Bulut gönderim süzgeci (maskeleme)

- **Ne işe yarar:** «Bulut gönderim süzgeci (maskeleme)» (Güvenlik ve gizlilik kategorisi), «Gizlilik ve güvenlik» modülünün parçasıdır. Modülün amacı: Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gizlilik ve güvenlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** gizli değer: Kasa şifreleme parolası (`vault_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test).

<a id="madde-241"></a>

### 241. Kasa şifreleme (isteğe bağlı)

- **Ne işe yarar:** «Kasa şifreleme (isteğe bağlı)» (Güvenlik ve gizlilik kategorisi), «Gizlilik ve güvenlik» modülünün parçasıdır. Modülün amacı: Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gizlilik ve güvenlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** gizli değer: Kasa şifreleme parolası (`vault_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test).

<a id="madde-242"></a>

### 242. Denetim günlüğü arayüzü

- **Ne işe yarar:** «Denetim günlüğü arayüzü» (Güvenlik ve gizlilik kategorisi), «Gizlilik ve güvenlik» modülünün parçasıdır. Modülün amacı: Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gizlilik ve güvenlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** gizli değer: Kasa şifreleme parolası (`vault_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test).

<a id="madde-243"></a>

### 243. İzin profilleri

- **Ne işe yarar:** «İzin profilleri» (Güvenlik ve gizlilik kategorisi), «Gizlilik ve güvenlik» modülünün parçasıdır. Modülün amacı: Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gizlilik ve güvenlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** gizli değer: Kasa şifreleme parolası (`vault_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test).

<a id="madde-244"></a>

### 244. Yedek ve geri yükleme sihirbazı

- **Ne işe yarar:** «Yedek ve geri yükleme sihirbazı» (Güvenlik ve gizlilik kategorisi), «Gizlilik ve güvenlik» modülünün parçasıdır. Modülün amacı: Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gizlilik ve güvenlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** gizli değer: Kasa şifreleme parolası (`vault_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test).

<a id="madde-245"></a>

### 245. Veri dışa aktarma ve silme

- **Ne işe yarar:** «Veri dışa aktarma ve silme» (Güvenlik ve gizlilik kategorisi), «Gizlilik ve güvenlik» modülünün parçasıdır. Modülün amacı: Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gizlilik ve güvenlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** gizli değer: Kasa şifreleme parolası (`vault_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test).

<a id="madde-246"></a>

### 246. İstem enjeksiyonu kalkanı testleri

- **Ne işe yarar:** «İstem enjeksiyonu kalkanı testleri» (Güvenlik ve gizlilik kategorisi), «Gizlilik ve güvenlik» modülünün parçasıdır. Modülün amacı: Gizlilik paneli, bulut maskeleme, kasa şifreleme, denetim günlüğü, izin profilleri, yedek.
- **Durum:** hazır (sürüm 0.8.0).
- **Nasıl açılır:** «Gizlilik ve güvenlik» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** gizli değer: Kasa şifreleme parolası (`vault_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Gizlilik**; komut: [`sb vault-encrypt`](../14-komut-referansi.md#sb-vault-encrypt), [`sb vault-decrypt`](../14-komut-referansi.md#sb-vault-decrypt), [`sb vault-key`](../14-komut-referansi.md#sb-vault-key), [`sb restore`](../14-komut-referansi.md#sb-restore), [`sb security-test`](../14-komut-referansi.md#sb-security-test).
