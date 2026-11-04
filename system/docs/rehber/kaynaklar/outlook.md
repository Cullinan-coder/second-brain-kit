# Outlook / Microsoft 365 mail

> Outlook posta ve takvim (IMAP + yayımlı takvim bağlantısı).

| | |
|---|---|
| Kaynak kimliği | `outlook` |
| Dosya biçimi | `hesap` |
| Bağlayıcı | özel yol (aşağıya bak) |
| Bağlı modül | [Mesaj içe aktarmaları](../moduller/imports_comm.md) |
| Ne ister | hesap: [Outlook](../03-hesaplar.md#hesap-outlook), [E-posta (IMAP)](../03-hesaplar.md#hesap-imap); gizli değer: IMAP şifresi (uygulama şifresi) (`imap_password`); alan: IMAP takma adı (ör. is) (`imap_alias`), IMAP e-posta (`imap_email`) |

## Başlamadan önce

- Bu kaynak için **hiçbir veri bulutta işlenmez**: aldığın dosya yalnız bu bilgisayarda okunur ve kasaya notlara/kayıtlara çevrilir.
- Dışa aktarma adımları sağlayıcının kendi sitesinde yapılır; **menü adları sürüme göre değişebilir**. Aşağıdaki adımlar manifestten gelir, takılırsan sağlayıcının resmi yardım sayfasına bak (varsa adım listesinde adresi var).
- Boş disk alanı bırak: dışa aktarma dosyaları büyük olabilir; sihirbaz en çok 2 GB'lık dosya yükler.

- Bu kaynak bir **dosya değil bir hesaptır**: sihirbazın 5. adımında e-posta (IMAP) hesabı olarak eklenir.

## Dışa aktarma adımları

1. Kişisel Outlook.com hesabı: outlook.com → Ayarlar → Posta → E-postayı eşitle → POP ve IMAP'ta IMAP erişimine izin ver.
2. Hesabında iki adımlı doğrulama açıksa microsoft hesap güvenliği sayfasından bir 'uygulama parolası' oluştur ve onu kullan.
3. Sunucu: outlook.office365.com, bağlantı noktası 993 (SSL). Kurulumda hesap ön ayarı olarak 'outlook' seçilir.
4. Takvim için: Outlook web → Ayarlar → Takvim → Paylaşılan takvimler → Takvimi yayımla → ICS bağlantısını kopyala; bağlantıyı hesap ayarına yapıştır (`sb caldav-sync outlook`).
5. Kurumsal Microsoft 365'te IMAP genellikle yönetici tarafından kapalıdır ve parola yerine OAuth gerekir; bu durumda BT yöneticine sor. Resmi yardım: https://support.microsoft.com/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353



## Sihirbazda yükleme (9. adım: Veri yükleme)

1. Sihirbazın **5. adımına (Hesaplar)** git, **E-posta (IMAP)** bölümünde ilgili hazır sunucuyu seç ([Hesaplar](../03-hesaplar.md#hesap-imap)).
2. Takma ad, e-posta ve uygulama şifresini gir → **Test et ve kaydet**.
3. 9. adımda bu kaynak yalnız bilgi olarak görünür; arşivleme günlük işlerle (`sb daily`) ya da `sb mail-fetch <takma-ad>` ile yapılır.



## Komut satırından

`sb mail-fetch <takma-ad>` — IMAP hesabı eklendikten sonra; takvim için `sb caldav-sync` (Outlook ICS).

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
