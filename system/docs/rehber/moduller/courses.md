# Okul (ÖBS/LMS)

> Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları

| | |
|---|---|
| Modül kimliği | `courses` |
| Kategori | Okul ve proje |
| Varsayılan | açık |
| Madde sayısı | 13 |
| Ne ister | hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`) |

## Ne işe yarar

Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.

Bu modül özellik kataloğundan **13 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Okul (ÖBS/LMS)`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on courses` açar, `sb features --off courses` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Okul sistemi adresi (ÖBS/LMS) (`school_url`) | web adresi | hayır | Girişin yapıldığı adres. |

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Öğrenci, Akademisyen seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Dersler**, **Çalışma planı** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Bağlı veri kaynakları

- [Okul ders sitesi (UZEM / Moodle)](../kaynaklar/uzem.md): Moodle haftalık konular, duyurular, ödevler ve ders dosyaları → ders notları ve 40-Kaynaklar/UZEM.

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [178](#madde-178) | Sınav takvimi ve çalışma planı | hazır | 0.7.0 |
| [192](#madde-192) | Ders panosu | hazır | 0.7.0 |
| [193](#madde-193) | Ders notu üretici | hazır | 0.7.0 |
| [194](#madde-194) | Sınav hazırlık modu | hazır | 0.7.0 |
| [195](#madde-195) | Ödev yardımcısı (öğretici kip) | hazır | 0.7.0 |
| [196](#madde-196) | Kaynakça yöneticisi | hazır | 0.7.0 |
| [197](#madde-197) | Tez/proje yazım asistanı | hazır | 0.7.0 |
| [198](#madde-198) | GANO hesaplama ve senaryo | hazır | 0.7.0 |
| [199](#madde-199) | Ders programı ve duyuru takibi | hazır | 0.7.0 |
| [200](#madde-200) | Hoca/asistan iletişim geçmişi | hazır | 0.7.0 |
| [201](#madde-201) | Grup projesi takibi | hazır | 0.7.0 |
| [202](#madde-202) | Burs, staj, yarışma takibi | hazır | 0.7.0 |
| [203](#madde-203) | Okul belgeleri arşivi | hazır | 0.7.0 |

<a id="madde-178"></a>

### 178. Sınav takvimi ve çalışma planı

- **Ne işe yarar:** «Sınav takvimi ve çalışma planı» (Görev, takvim ve verimlilik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-192"></a>

### 192. Ders panosu

- **Ne işe yarar:** «Ders panosu» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-193"></a>

### 193. Ders notu üretici

- **Ne işe yarar:** «Ders notu üretici» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-194"></a>

### 194. Sınav hazırlık modu

- **Ne işe yarar:** «Sınav hazırlık modu» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-195"></a>

### 195. Ödev yardımcısı (öğretici kip)

- **Ne işe yarar:** «Ödev yardımcısı (öğretici kip)» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-196"></a>

### 196. Kaynakça yöneticisi

- **Ne işe yarar:** «Kaynakça yöneticisi» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-197"></a>

### 197. Tez/proje yazım asistanı

- **Ne işe yarar:** «Tez/proje yazım asistanı» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-198"></a>

### 198. GANO hesaplama ve senaryo

- **Ne işe yarar:** «GANO hesaplama ve senaryo» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-199"></a>

### 199. Ders programı ve duyuru takibi

- **Ne işe yarar:** «Ders programı ve duyuru takibi» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-200"></a>

### 200. Hoca/asistan iletişim geçmişi

- **Ne işe yarar:** «Hoca/asistan iletişim geçmişi» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-201"></a>

### 201. Grup projesi takibi

- **Ne işe yarar:** «Grup projesi takibi» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-202"></a>

### 202. Burs, staj, yarışma takibi

- **Ne işe yarar:** «Burs, staj, yarışma takibi» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).

<a id="madde-203"></a>

### 203. Okul belgeleri arşivi

- **Ne işe yarar:** «Okul belgeleri arşivi» (Öğrenci ve akademik kategorisi), «Okul (ÖBS/LMS)» modülünün parçasıdır. Modülün amacı: Ders notları, ders dosyaları, ders derlemesi, UZEM/Moodle haftalık konular ve ders dosyaları.
- **Durum:** hazır (sürüm 0.7.0).
- **Nasıl açılır:** «Okul (ÖBS/LMS)» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul); alan: Okul sistemi adresi (ÖBS/LMS) (`school_url`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Dersler**, **Çalışma planı**; komut: [`sb course-files`](../14-komut-referansi.md#sb-course-files), [`sb course-deep`](../14-komut-referansi.md#sb-course-deep), [`sb obs-import`](../14-komut-referansi.md#sb-obs-import), [`sb courses`](../14-komut-referansi.md#sb-courses), [`sb gpa`](../14-komut-referansi.md#sb-gpa).
