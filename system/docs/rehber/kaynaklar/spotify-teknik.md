# Spotify teknik günlük paketi

> Spotify 'Technical Log Information' (my_spotify_data.zip) → aramalar, beğeniler, tekrar dinlenenler, sözüne bakılanlar + "Müzik zevki" notu. Cihaz/ağ günlükleri alınmaz.

| | |
|---|---|
| Kaynak kimliği | `spotify-teknik` |
| Dosya biçimi | `.zip`, `klasör` |
| Bağlayıcı | `spotify-teknik` |
| Bağlı modül | [Medya ve okuma içe aktarmaları](../moduller/imports_media.md) |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Başlamadan önce

- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.
- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).
- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.

## Dışa aktarma adımları

1. Spotify web: spotify.com/account/privacy (Hesap → Gizlilik ayarları) adresine git ve giriş yap.
2. 'Verilerini indir' bölümünde 'Teknik günlük bilgileri' (Technical log information) kutusunu işaretle ve 'Veri iste'ye bas.
3. E-postadaki onay bağlantısına tıkla; hazırlanması günler sürebilir, hazır olunca indirme bağlantısı gelir.
4. İnen `my_spotify_data.zip` dosyasını açmadan Veri yükleme ekranına bırak (ya da `sb import spotify-teknik <zip>`).

> Bu paket dinleme geçmişi İÇERMEZ (o "Genişletilmiş akış geçmişi" ile gelir, bkz. Spotify dinleme geçmişi). Şarkı adları, daha önce yüklenmiş dinleme geçmişinden ya da Spotify bağlıysa Spotify API'den bulunur. Dosya yalnız bu bilgisayarda okunur.



## Sihirbazda yükleme (9. adım: Veri yükleme)

1. 9. adımda kaynak kartını bul (seçimin için gerekenler üstte; öbürleri **Bütün kaynakları göster** ile açılır).
2. Kartın içindeki **Bu dosyayı nasıl alırsın?** bölümü yukarıdaki adımların aynısını gösterir.
3. Dosyayı kutuya **sürükle-bırak** ya da **Dosya seç** ile seç. Üstte `Yükleniyor: <ad> (<MB> MB)…` yazar, bitince `Yüklendi: <ad>`.
4. **Önizle**'ye bas: dosyaya dokunmadan kaç kayıt okunacağı, tarih aralığı ve örnek başlıklar gösterilir. Sayı 0 ya da beklediğinden çok farklıysa yanlış dosyayı seçmiş olabilirsin.
5. Sorun yoksa **İçe aktar**'a bas; ilerleme altta görünür, bitince `N kayıt içe aktarıldı` ve **Yapılan içe aktarmalar** listesine düşer.



## Komut satırından

`sb import spotify-teknik <dosya> --dry-run` — önce yazmadan say (kayıt sayısı, tarih aralığı, 3 örnek başlık); sorun yoksa `--dry-run` olmadan çalıştır.

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
