# Google Takeout

> Gemini sohbetleri, etkinlik, Chrome, Keep, YouTube, Play → kasa.

| | |
|---|---|
| Kaynak kimliği | `takeout` |
| Dosya biçimi | `.zip` |
| Bağlayıcı | özel yol (aşağıya bak) |
| Bağlı modül | [Yaşam ve akademik içe aktarmalar](../moduller/imports_life.md) |
| Ne ister | hesap: [Google](../03-hesaplar.md#hesap-google) |

## Başlamadan önce

- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.
- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).
- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.

## Dışa aktarma adımları

1. takeout.google.com adresine git ve Google hesabınla giriş yap.
2. 'Tümünün seçimini kaldır' de, sonra yalnız şunları işaretle: Etkinliğim (My Activity), Chrome, Keep, YouTube ve YouTube Music, (isteğe bağlı) Play Store. Gemini sohbetleri 'Etkinliğim' içinde 'Gemini Uygulamaları' olarak gelir.
3. Etkinliğim ve YouTube için 'Tüm etkinlik verileri / Biçimler' düğmesinden biçimi JSON yap (varsayılan HTML'dir; JSON daha güvenilir okunur). YouTube'da yalnız 'geçmiş' ve 'abonelikler' yeterli.
4. Sonraki adım → Aktarım yöntemi: e-postayla bağlantı gönder; Sıklık: bir kez dışa aktar; Dosya türü: .zip; Boyut: 2 GB (büyükse birden çok zip çıkar).
5. 'Dışa aktarma oluştur'a bas. Hazır olunca e-posta gelir (dakikalar-günler); bağlantıdan zip'leri 7 gün içinde indir.
6. Zip'leri AÇMADAN Veri yükleme ekranına bırak (ya da `sb takeout <zip> ...`); önce 'dry-run' ile ne alınacağı sayılır. Fotoğraflar ve posta (mbox) bilerek alınmaz.

> Adımlar sağlayıcı tarafında zamanla değişebilir; takılırsan resmi yardım sayfasına bak: https://support.google.com/accounts/answer/3024190



## Sihirbazda yükleme (9. adım: Veri yükleme)

1. 9. adımda kaynak kartını bul (seçimin için gerekenler üstte; öbürleri **Bütün kaynakları göster** ile açılır).
2. Kartın içindeki **Bu dosyayı nasıl alırsın?** bölümü yukarıdaki adımların aynısını gösterir.
3. Dosyayı kutuya **sürükle-bırak** ya da **Dosya seç** ile seç. Üstte `Yükleniyor: <ad> (<MB> MB)…` yazar, bitince `Yüklendi: <ad>`.
4. **Önizle**'ye bas: dosyaya dokunmadan kaç kayıt okunacağı, tarih aralığı ve örnek başlıklar gösterilir. Sayı 0 ya da beklediğinden çok farklıysa yanlış dosyayı seçmiş olabilirsin.
5. Sorun yoksa **İçe aktar**'a bas; ilerleme altta görünür, bitince `N kayıt içe aktarıldı` ve **Yapılan içe aktarmalar** listesine düşer.



## Komut satırından

`sb takeout <zip> --dry-run` — yazmadan say; gerçek aktarım için `--dry-run` olmadan.

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
