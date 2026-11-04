# Projeler ve GitHub

> Kod projelerini tarar; proje dosyası derler

| | |
|---|---|
| Modül kimliği | `projects` |
| Kategori | Okul ve proje |
| Varsayılan | açık |
| Madde sayısı | 0 |
| Ne ister | hesap: [GitHub](../03-hesaplar.md#hesap-github); alan: Kod projeleri klasörü (`workspace`), GitHub kullanıcı adı (`github_user`) |

## Ne işe yarar

Kod projelerini tarar; proje dosyası derler.

Bu modülün katalog maddesi yoktur; altyapı ya da veri kaynağı modülüdür, işlevi yukarıdaki açıklamadır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Projeler ve GitHub`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on projects` açar, `sb features --off projects` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [GitHub](../03-hesaplar.md#hesap-github)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Kod projeleri klasörü (`workspace`) | dosya ya da klasör yolu | hayır | Git depolarının bulunduğu üst klasör. |
| GitHub kullanıcı adı (`github_user`) | metin | hayır | github.com/<ad> adresindeki ad. |

## Hazır seçimlerde

- **Yoğunluk:** Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Yazılımcı seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Proje** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb projects-sync`](../14-komut-referansi.md#sb-projects-sync), [`sb project-deep`](../14-komut-referansi.md#sb-project-deep) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.
