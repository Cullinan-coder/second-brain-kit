# WhatsApp sohbetleri

> Sohbet dışa aktarımı (.txt/.zip) → mesajlar.

| | |
|---|---|
| Kaynak kimliği | `whatsapp` |
| Dosya biçimi | `.txt`, `.zip` |
| Bağlayıcı | `whatsapp` |
| Bağlı modül | [WhatsApp](../moduller/whatsapp.md) |
| Ne ister | alan: Sohbetlerde senin adın (`me`) |

## Başlamadan önce

- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.
- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).
- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.

## Dışa aktarma adımları

1. Telefonda WhatsApp'ı aç ve dışa aktarmak istediğin sohbeti aç (her sohbet ayrı dışa aktarılır).
2. Android: sağ üstte ⋮ (üç nokta) → Diğer → Sohbeti dışa aktar → 'Medyasız' seç. iPhone: sohbetin üstündeki kişi/grup adına dokun → aşağı kaydır → Sohbeti dışa aktar → 'Medya olmadan'.
3. Paylaşım menüsünden dosyayı kendine kaydet: Google Drive'a, kendine e-postaya ya da Dosyalar'a (iPhone) gönder. Çıkan dosya .txt (ya da .zip içinde .txt) olur.
4. Dosyayı bilgisayara indir. Dil/saat biçimi (gg.aa.yyyy, 12/24 saat) otomatik algılanır; Android ve iPhone biçimleri desteklenir.
5. Önizlemede mesaj sayısı ve tarih aralığını kontrol et, 'Sen' alanına WhatsApp'taki kendi adını yaz (hangi mesajların senin olduğu bu şekilde anlaşılır), sonra içe aktar.
6. Birden çok sohbet için her birini ayrı dışa aktarıp aynı klasöre koy; klasör olarak da yüklenebilir.



## Sihirbazda yükleme (9. adım: Veri yükleme)

1. 9. adımda kaynak kartını bul (seçimin için gerekenler üstte; öbürleri **Bütün kaynakları göster** ile açılır).
2. Kartın içindeki **Bu dosyayı nasıl alırsın?** bölümü yukarıdaki adımların aynısını gösterir.
3. Dosyayı kutuya **sürükle-bırak** ya da **Dosya seç** ile seç. Üstte `Yükleniyor: <ad> (<MB> MB)…` yazar, bitince `Yüklendi: <ad>`.
4. **Önizle**'ye bas: dosyaya dokunmadan kaç kayıt okunacağı, tarih aralığı ve örnek başlıklar gösterilir. Sayı 0 ya da beklediğinden çok farklıysa yanlış dosyayı seçmiş olabilirsin.
5. Sorun yoksa **İçe aktar**'a bas; ilerleme altta görünür, bitince `N kayıt içe aktarıldı` ve **Yapılan içe aktarmalar** listesine düşer.



## Komut satırından

`sb import whatsapp <dosya> --dry-run` — önce yazmadan say (kayıt sayısı, tarih aralığı, 3 örnek başlık); sorun yoksa `--dry-run` olmadan çalıştır. `--me "Adın"` ekle: senin mesajların `me` olarak işaretlenir.

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
