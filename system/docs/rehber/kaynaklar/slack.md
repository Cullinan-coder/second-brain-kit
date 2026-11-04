# Slack dışa aktarımı

> Slack çalışma alanı dışa aktarımı → mesajlar.

| | |
|---|---|
| Kaynak kimliği | `slack` |
| Dosya biçimi | `.zip`, `klasör` |
| Bağlayıcı | `slack` |
| Bağlı modül | [Mesaj içe aktarmaları](../moduller/imports_comm.md) |
| Ne ister | alan: Sohbetlerde senin adın (`me`) |

## Başlamadan önce

- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.
- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).
- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.

## Dışa aktarma adımları

1. Çalışma alanı sahibi/yöneticisi olarak giriş yap (normal üye tüm çalışma alanını dışa aktaramaz).
2. Slack'te çalışma alanı adı → Ayarlar ve yönetim (Settings & administration) → Çalışma alanı ayarları → İçe/Dışa veri aktarma (Import/Export Data) → Dışa aktar (Export).
3. Dışa aktarma aralığını seç ve başlat; hazır olunca Slack e-posta atar, oradan zip'i indir. Ücretsiz ve standart planlarda yalnız herkese açık kanallar çıkar; özel mesajlar için plana göre Slack'ten talep gerekir.
4. Zip'i (içinde kanal klasörleri ve users.json) Veri yükleme ekranına bırak; 'Sen' alanına Slack görünen adını yaz.

> Adımlar sağlayıcı tarafında zamanla değişebilir; takılırsan resmi yardım sayfasına bak: https://slack.com/help/articles/201658943



## Sihirbazda yükleme (9. adım: Veri yükleme)

1. 9. adımda kaynak kartını bul (seçimin için gerekenler üstte; öbürleri **Bütün kaynakları göster** ile açılır).
2. Kartın içindeki **Bu dosyayı nasıl alırsın?** bölümü yukarıdaki adımların aynısını gösterir.
3. Dosyayı kutuya **sürükle-bırak** ya da **Dosya seç** ile seç. Üstte `Yükleniyor: <ad> (<MB> MB)…` yazar, bitince `Yüklendi: <ad>`.
4. **Önizle**'ye bas: dosyaya dokunmadan kaç kayıt okunacağı, tarih aralığı ve örnek başlıklar gösterilir. Sayı 0 ya da beklediğinden çok farklıysa yanlış dosyayı seçmiş olabilirsin.
5. Sorun yoksa **İçe aktar**'a bas; ilerleme altta görünür, bitince `N kayıt içe aktarıldı` ve **Yapılan içe aktarmalar** listesine düşer.



## Komut satırından

`sb import slack <dosya> --dry-run` — önce yazmadan say (kayıt sayısı, tarih aralığı, 3 örnek başlık); sorun yoksa `--dry-run` olmadan çalıştır. `--me "Adın"` ekle: senin mesajların `me` olarak işaretlenir.

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
