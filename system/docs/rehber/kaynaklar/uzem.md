# Okul ders sitesi (UZEM / Moodle)

> Moodle haftalık konular, duyurular, ödevler ve ders dosyaları → ders notları ve 40-Kaynaklar/UZEM.

| | |
|---|---|
| Kaynak kimliği | `uzem` |
| Dosya biçimi | `hesap` |
| Bağlayıcı | özel yol (aşağıya bak) |
| Bağlı modül | [Okul (ÖBS/LMS)](../moduller/courses.md) |
| Ne ister | hesap: [Okul (ÖBS / LMS)](../03-hesaplar.md#hesap-okul) |

## Başlamadan önce

- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.
- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).
- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.

- Bu kaynak bir **dosya değil bir hesaptır**: sihirbazın 5. adımında e-posta (IMAP) hesabı olarak eklenir.

## Dışa aktarma adımları

1. Kurulum sihirbazının «Okul» adımında öğrenci numaranı ve UZEM şifreni kaydet (şifre yalnız işletim sistemi şifre kasasına gider).
2. `sb uzem sync --dry-run` ile önce ne alınacağına bak (giriş yapar, hiçbir şey yazmaz).
3. `sb uzem sync` derslerin haftalık konularını ders notlarına yazar, dosyaları 40-Kaynaklar/UZEM altına indirir (git, telefon dışı).

> Giriş yalnız GET istekleriyle yapılır; yanlış şifrede hesabı kilitlememek için tekrar denenmez.



## Sihirbazda yükleme (9. adım: Veri yükleme)

1. Sihirbazın **5. adımına (Hesaplar)** git, **E-posta (IMAP)** bölümünde ilgili hazır sunucuyu seç ([Hesaplar](../03-hesaplar.md#hesap-imap)).
2. Takma ad, e-posta ve uygulama şifresini gir → **Test et ve kaydet**.
3. 9. adımda bu kaynak yalnız bilgi olarak görünür; arşivleme günlük işlerle (`sb daily`) ya da `sb mail-fetch <takma-ad>` ile yapılır.



## Komut satırından

Bu kaynağın ayrı bir komutu yoktur; sihirbazdan ya da uygulamadan yüklenir.

Genel komut açıklaması: [`sb import`](../14-komut-referansi.md#sb-import).

## Sorun giderme

| Belirti | Neden olabilir | Ne yap |
|---|---|---|
| `dosya çok büyük (en çok 2 GB)` | Yükleme sınırı 2 GB | Dışa aktarmayı daha dar bir tarih aralığıyla yeniden iste ya da komut satırından `sb import` kullan |
| `geçersiz dosya adı` | Ad boş ya da yasak karakter içeriyor | Dosyayı kısa, sade bir adla kaydet (harf, rakam, boşluk, nokta, tire) |
| `yükleme yarım kaldı` | Bağlantı/disk sorunu | Dosyayı yeniden yükle |
| Önizlemede 0 kayıt | Yanlış dosya ya da boş dışa aktarma | Yukarıdaki adımları baştan izle; zip'in içeriğini kontrol et |
| `Bu kaynağın içe aktarıcısı henüz yok; dosya hazır bekliyor.` | Bu kaynak için bağlayıcı yazılmamış | Dosya `import_staging` klasöründe bekler; bağlayıcı eklenince içe aktarılır |
| Sağlayıcıda menü bulunamıyor | Menü adları sürüme göre değişir | Adım listesindeki resmi yardım adresine ya da sağlayıcının yardım sayfasında «verilerimi indir» aramasına bak |

Genel sorunlar: [Sorun giderme](../11-sorun-giderme.md) · Veri yükleme genel rehberi: [Veri yükleme](../07-veri-yukleme.md).
