# Not kutusu

> 00-Inbox/Dump notlarını yerine dağıtır

| | |
|---|---|
| Modül kimliği | `inbox` |
| Kategori | Asistan ve hafıza |
| Varsayılan | açık |
| Madde sayısı | 0 |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Ne işe yarar

00-Inbox/Dump notlarını yerine dağıtır.

Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Not kutusu`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on inbox` açar, `sb features --off inbox` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Hazır seçimlerde

- **Yoğunluk:** Minimal, Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **İletişim** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb inbox-process`](../14-komut-referansi.md#sb-inbox-process) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.
