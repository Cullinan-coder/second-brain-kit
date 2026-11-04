# ChatGPT / Claude / Gemini sohbet geçmişi

> Eski yapay zeka sohbetleri → aylık sohbet notları.

| | |
|---|---|
| Kaynak kimliği | `history-import` |
| Dosya biçimi | `.zip`, `.json`, `klasör` |
| Bağlayıcı | özel yol (aşağıya bak) |
| Bağlı modül | [Yaşam ve akademik içe aktarmalar](../moduller/imports_life.md) |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## Başlamadan önce

- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.
- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).
- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.

## Dışa aktarma adımları

1. ChatGPT: chatgpt.com → profil → Ayarlar → Veri kontrolleri (Data controls) → Verileri dışa aktar (Export data) → Dışa aktarmayı onayla. E-postayla gelen bağlantıdan zip'i indir (bağlantı kısa süre geçerlidir); içinde `conversations.json` bulunur.
2. Claude.ai: claude.ai → profil/ayarlar → Gizlilik (Privacy) → Verileri dışa aktar (Export data); e-postayla gelen bağlantıdan zip'i indir (içinde `conversations.json`). Menü adı değişirse resmi yardım: https://support.claude.com
3. Gemini: Google Takeout'tan 'Etkinliğim → Gemini Uygulamaları' seç (Google Takeout kaynağına bak).
4. Dosyayı Veri yükleme ekranına bırak. ÖNCE önizleme: kaç sohbetin hangi aylara gideceği gösterilir, hiçbir şey yazılmaz (onay kapısı).
5. Hassas konuları 'hariç tut' kelimeleriyle ya da tarih aralığıyla ele; özel sohbetleri 'özel' işaretle (bağlama girmez). Onaylayınca `40-Kaynaklar/Sohbet geçmişi/` altında ay başına bir not oluşur.
6. İstersen sonra Claude'a 'geçmişi bilgiye damıt' de (gecmis-import skill'i kavram notları çıkarır).

> Dışa aktarım yalnız yerelde okunur, hiçbir yere gönderilmez.



## Sihirbazda yükleme (9. adım: Veri yükleme)

1. 9. adımda kaynak kartını bul (seçimin için gerekenler üstte; öbürleri **Bütün kaynakları göster** ile açılır).
2. Kartın içindeki **Bu dosyayı nasıl alırsın?** bölümü yukarıdaki adımların aynısını gösterir.
3. Dosyayı kutuya **sürükle-bırak** ya da **Dosya seç** ile seç. Üstte `Yükleniyor: <ad> (<MB> MB)…` yazar, bitince `Yüklendi: <ad>`.
4. **Önizle**'ye bas: dosyaya dokunmadan kaç kayıt okunacağı, tarih aralığı ve örnek başlıklar gösterilir. Sayı 0 ya da beklediğinden çok farklıysa yanlış dosyayı seçmiş olabilirsin.
5. Sorun yoksa **İçe aktar**'a bas; ilerleme altta görünür, bitince `N kayıt içe aktarıldı` ve **Yapılan içe aktarmalar** listesine düşer.



## Komut satırından

`sb history-import <dosya>` — önizleme (hiçbir şey yazmaz); gerçekten içe aktarmak için sonuna `--apply` ekle.

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
