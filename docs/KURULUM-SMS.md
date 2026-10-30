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
