# Telefon: SMS ve arama kayıtlarını Drive'a yedekleme (Redmi 13 Pro 5G, ~5 dk)

Google Messages'ın dışarıya açık bir API'si yok. Bu yüzden telefondaki **SMS Backup & Restore**
uygulaması mesajları ve arama kaydını düzenli olarak Drive'a XML dosyası olarak yükler; Second Brain oradan okur.

1. Play Store → **SMS Backup & Restore** (geliştirici: *SyncTech Pty Ltd*) → Yükle.
2. Uygulamayı aç → istenen izinlere **İzin ver** (SMS, Kişiler, Telefon/Arama kaydı, Dosyalar).
3. **Yedekleme ayarla** (Set up a backup):
   - **Mesajlar** ✅ ve **Telefon görüşmeleri** ✅ açık olsun. (Mesajlar altında MMS/RCS seçeneği varsa açık kalabilir.)
   - İleri → **Google Drive** seç → **ornek@gmail.com** ile giriş → izin ver.
     (Klasör adını değiştirme; varsayılan `SMSBackupRestore` kalsın.)
   - İleri → **Zamanlanmış yedeklemeler** (Schedule recurring backups) açık:
     sıklık olarak sunulan **en kısa aralığı** seç (saatlik yoksa **Günlük**, saat **06:30** — sabah taramasından önce).
   - **Şimdi yedekle** (Back up now).
4. Yedek bitince Drive'da `SMSBackupRestore` klasöründe `sms-….xml` ve `calls-….xml` dosyalarını görmelisin.
5. Xiaomi'ye özel: Ayarlar → Uygulamalar → SMS Backup & Restore → **Pil tasarrufu: Kısıtlama yok** ve
   **Otomatik başlatma: Açık**. Yoksa MIUI zamanlanmış yedeği öldürür.

Bitince Claude'a "yedek tamam" yaz.

## Zamanlanmış yedek (otomatik) — kısa kontrol listesi

1. SMS Backup & Restore → sol menü **Yedekleme ve geri yükleme** → **Yedeklemeyi ayarla** (ya da **Zamanlanmış yedeklemeler**).
2. **Google Drive** hedefi seçili ve hesap `ornek@gmail.com` olsun.
3. **Zamanlama** açık: sıklık **Günlük** (ya da en kısa seçenek), saat **06:30**; **Mesajlar** ve **Telefon görüşmeleri** işaretli.
4. **Yalnız Wi-Fi'de yedekle** açıksa telefonun geceleri Wi-Fi'ye bağlı olduğundan emin ol.
5. **Şimdi yedekle** ile bir deneme yap; Drive'da yeni `sms-….xml` görünmeli.
6. Kontrol: `sb sms-sync` sonrası bilgisayarda `sms.freshness` son SMS tarihini gösterir; 2 günden eskiyse yedek durmuş demektir
   (pil kısıtlaması / Drive oturumu düşmüş olabilir).
