# GitHub derin

> Issue, PR, commit ve release kayıtları

| | |
|---|---|
| Modül kimliği | `github` |
| Kategori | Okul ve proje |
| Varsayılan | açık |
| Madde sayısı | 2 |
| Ne ister | hesap: [GitHub](../03-hesaplar.md#hesap-github); alan: GitHub kullanıcı adı (`github_user`); program: gh |

## Ne işe yarar

Issue, PR, commit ve release kayıtları.

Bu modül özellik kataloğundan **2 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`GitHub derin`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. **Komutla:** `sb features --on github` açar, `sb features --off github` kapatır, `sb features` durumu listeler (bkz. [`sb features`](../14-komut-referansi.md#sb-features)).

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [GitHub](../03-hesaplar.md#hesap-github)

**Bilgisayarda kurulu olması gereken programlar:** gh


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| GitHub kullanıcı adı (`github_user`) | metin | hayır | github.com/<ad> adresindeki ad. |

## Hazır seçimlerde

- **Yoğunluk:** Güç kullanıcısı seçildiğinde açıktır.
- **Meslek:** Ajans / Freelancer, Yazılımcı seçimlerinde ayrıca eklenir.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekran:** bu modülün ayrı bir ekranı yoktur; sonuçları asistanın cevaplarında, Obsidian notlarında ve Pano'da görürsün ([Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb github-deep`](../14-komut-referansi.md#sb-github-deep) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [98](#madde-98) | GitHub derin (issue, PR, yorum, commit, release) | hazır | 0.5.0 |
| [99](#madde-99) | GitLab, Bitbucket | planlandı (henüz yok) | 0.8.0 |

<a id="madde-98"></a>

### 98. GitHub derin (issue, PR, yorum, commit, release)

- **Ne işe yarar:** «GitHub derin (issue, PR, yorum, commit, release)» (Yeni veri kaynakları kategorisi), «GitHub derin» modülünün parçasıdır. Modülün amacı: Issue, PR, commit ve release kayıtları.
- **Durum:** hazır (sürüm 0.5.0).
- **Nasıl açılır:** «GitHub derin» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [GitHub](../03-hesaplar.md#hesap-github); alan: GitHub kullanıcı adı (`github_user`); program: gh.
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: komut: [`sb github-deep`](../14-komut-referansi.md#sb-github-deep). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** komut: [`sb github-deep`](../14-komut-referansi.md#sb-github-deep).

<a id="madde-99"></a>

### 99. GitLab, Bitbucket

- **Ne işe yarar:** «GitLab, Bitbucket» (Yeni veri kaynakları kategorisi), «GitHub derin» modülünün parçasıdır. Modülün amacı: Issue, PR, commit ve release kayıtları.
- **Durum:** planlandı (henüz yok); yol haritasında Faz 4 / sürüm 0.8.0 için yer alır. Şu an tam çalışmasını bekleme.
- **Nasıl açılır:** «GitHub derin» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [GitHub](../03-hesaplar.md#hesap-github); alan: GitHub kullanıcı adı (`github_user`); program: gh.
- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.
- **İlgili ekran/komut:** komut: [`sb github-deep`](../14-komut-referansi.md#sb-github-deep).
