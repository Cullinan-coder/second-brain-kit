# RSS ve haber bültenleri

> RSS/Atom akışları (config/rss.yaml) → makale kayıtları. Ağ kullanan tek bağlayıcı.

| | |
|---|---|
| Kaynak kimliği | `rss` |
| Dosya biçimi | `config/rss.yaml` |
| Bağlayıcı | `rss` |
| Bağlı modül | [Medya ve okuma içe aktarmaları](../moduller/imports_media.md) |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Başlamadan önce

- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.
- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).
- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.

## Dışa aktarma adımları

1. Dosya gerekmez: izlemek istediğin akışların adreslerini `config/rss.yaml` dosyasına yaz (kurulum paneli de bu dosyayı yazar).
2. Bir sitenin RSS adresini bulmak için sayfanın kaynağında 'rss' ya da 'atom' ara, ya da sitenin /feed ve /rss.xml adreslerini dene.
3. `sb import rss` akışları çeker ve yeni makaleleri kaydeder; ilk çalıştırmada `--dry-run` ile ne geleceğini gör.



## Sihirbazda yükleme (9. adım: Veri yükleme)

1. Dosya yüklemen gerekmez; adım listesindeki ayar dosyasını düzenle (kurulum paneli de bu dosyayı yazar).
2. 9. adımdaki kaynak kartında **Önizle** ile ne geleceğini gör, sonra **İçe aktar**.



## Komut satırından

`sb import rss <dosya> --dry-run` — önce yazmadan say (kayıt sayısı, tarih aralığı, 3 örnek başlık); sorun yoksa `--dry-run` olmadan çalıştır.

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
