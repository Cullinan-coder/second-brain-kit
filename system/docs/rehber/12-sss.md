# 12 · Sık sorulan sorular

Kısa cevaplar; ayrıntı için bağlantılara bak.

## Genel

**Second Brain ücretli mi?**
Uygulamanın kendisi için bu rehberde bir ücret yoktur. Ama kullandığın **bulut yapay zekâ sağlayıcıları** (OpenAI, Anthropic, Gemini…) kullanıma göre faturalar ([API anahtarları](04-api-anahtarlari.md)); Claude Code için Claude aboneliği gerekir; Spotify doğrudan çalma için Spotify Premium gerekir. Tam yerel kullanımda bulut ücreti yoktur.

**İnternet olmadan çalışır mı?**
Kurulumdan ve modeller indirildikten sonra **yerel modelle** büyük kısmı çalışır (notlar, arama, asistan). Mail/takvim çekmek, güncelleme ve bulut modeller internet ister.

**Verilerim bir yere gönderiliyor mu?**
Hayır. Notlar ve arşiv bilgisayarında kalır; Second Brain'in kendi sunucusu yoktur. Bulut model kullanırsan yalnız o isteğin (süzülmüş) metni sağlayıcıya gider; «Tam yerel»de hiçbir şey gitmez ([Güvenlik ve gizlilik](10-guvenlik-gizlilik.md)).

**Mailimi silebilir mi?**
Hayır. Mail erişimi salt okunurdur; silme/gönderme yapılamaz ([Başlangıç](00-baslangic.md#mail-salt-okunur-garantisi)).

**Hangi işletim sistemlerinde çalışır?**
Windows 10/11 ve macOS 13+. Windows'ta günlük kullanımda sınanmıştır; macOS desteği yazılmıştır ama sınırlı denenmiştir.

**Zayıf bir bilgisayarda kullanabilir miyim?**
Evet: sihirbazda donanım olarak **Zayıf laptop / bulut** seç; ağır özellikler (görüntü, ekran izleme, uyandırma sözcüğü, ses) kapanır, asistan bulut API ile çalışır. Ya da «Tam yerel + küçük model» (kalite düşer). Bkz. [Modeller ve ses](05-modeller-ses.md).

**Birden fazla bilgisayarda kullanabilir miyim?**
Her bilgisayara ayrı kurulum yaparsın. Kasa klasörünü Syncthing ya da git ile eşitleyebilirsin ama `.secondbrain` (mail arşivi, anahtarlar) bilgisayara özeldir ve eşitlenmez.

**Birden fazla kişi aynı kasayı kullanabilir mi?**
Şu an **tek kullanıcı** için tasarlanmıştır. Çok kullanıcı ve roller şirket ürünü yönü olarak planlanmıştır ([Sektör paketleri](20-sektor-paketleri.md)).

## Kurulum

**Kurulum ne kadar sürer?**
Sihirbaz ~10–20 dakika (kararlarına bağlı); Google bağlama ~10 dakika; model indirme internete ve boyuta bağlı (birkaç GB). Kur adımında Python ortamı en uzun adımlardan biridir.

**Her adımı doldurmam gerekiyor mu?**
Hayır. Her adım atlanabilir; atlananlar sonra Ayarlar'dan yapılır.

**Sihirbazı kapatsam ne olur?**
Yarım kalan kurulum kaydedilir; yeniden açınca **Kaldığın yerden devam et** çıkar. Sırlar kaydedilmez, yeniden girersin.

**Kasa klasörünü sonra taşıyabilir miyim?**
Kasa bir klasördür; taşıyabilirsin ama ayar dosyalarındaki yolun güncellenmesi gerekir. En sağlıklısı kurulumu yeni konumla yeniden yapmak ve eski notları kopyalamaktır. Kasayı OneDrive/Google Drive içinde tutma.

**Kurulumu geri alabilir miyim?**
Evet: Ayarlar → **Kaldır**. Önce plan gösterir; onay verirsen zamanlanmış görevleri kaldırır, kodu çöp kutusuna taşır. **Kasa notlarına dokunmaz.**

**Hata mesajı çıktı, ne yapmalıyım?**
[Sorun giderme](11-sorun-giderme.md); hata kartında «Nasıl düzeltilir» yazar, sonra **Yeniden dene**.

## Hesaplar ve anahtarlar

**Google'a neden kendi «uygulama»mı oluşturuyorum?**
Böylece izinleri yalnız sen kontrol edersin ve üçüncü bir tarafın aracılığı olmaz; hesabın yalnız senin projene izin verir ([Hesaplar → Google](03-hesaplar.md#hesap-google)).

**Google Cloud ücretli mi?**
Bu işlem için ücretsizdir; kart bilgisi istenmez. İstenirse yanlış bir sayfadasın.

**Normal şifremle IMAP olmuyor.**
Gmail, iCloud, Outlook gibi sağlayıcılar uygulama şifresi ister ([Hesaplar → IMAP](03-hesaplar.md#hesap-imap)).

**API anahtarı zorunlu mu?**
Hayır. Yalnız bulut model kullanmak istersen ([API anahtarları](04-api-anahtarlari.md)).

**Anahtarlarım nerede duruyor?**
İşletim sistemi şifre kasasında (Windows Kimlik Bilgisi Yöneticisi / macOS Anahtar Zinciri). Dosyalara yazılmaz.

## Kullanım

**Çalışmaya başla düğmesi ne yapıyor, her gün basmak zorunda mıyım?**
Güncelleme, sağlık, günlük işler ve model ısıtmayı sırayla yapar. Zamanlayıcı kuruluysa günlük işler kendiliğinden çalışır; yine de güncel olmak için günde bir basman önerilir ([Uygulama turu](08-uygulama-turu.md#calismaya-basla)).

**Asistan yanlış bilgi verdi.**
Yerel modeller hata yapabilir. Cevaptaki kaynak numaralarına tıklayıp notu kendin kontrol et. Yanlış bir not değişikliği olduysa `sb asistan-undo` ya da git geçmişi.

**Asistan takvime kendi kendine bir şey ekledi mi?**
Hayır. Takvim işlemleri her profilde **onay kartı** ister.

**Bir bilgiyi nasıl unuttururum?**
`/unut <konu>` yaz, çıkan onay kartını onayla ([Güvenlik ve gizlilik](10-guvenlik-gizlilik.md#unutma-bir-bilgiyi-silme-istegi)).

**Bir modülü kapatırsam verilerim silinir mi?**
Hayır. Kapatınca o iş çalışmaz; var olan notlar kalır.

**Obsidian şart mı?**
Hayır. Asistan ve uygulama Obsidian'sız çalışır. Obsidian notları görsel gezmek ve düzenlemek içindir.

**Telefonda nasıl kullanırım?**
Tailscale + eşleme: [Telefon](08-uygulama-turu.md#telefon).

## Gizlilik

**Hangi veriler buluta gider?**
Yalnız bulut sağlayıcı seçtiğin görevlerde, süzülmüş metin. Gizli notlar hiç gitmez. Gizlilik ekranındaki **Buluta giden** kartı sayıyı gösterir.

**Hassas bir notu nasıl korurum?**
Başına `visibility: private` yaz; ek olarak istersen `sb vault-encrypt` ile şifrele ([Güvenlik ve gizlilik](10-guvenlik-gizlilik.md)).

**Bilgisayarım çalınırsa?**
Disk şifreleme (BitLocker/FileVault) aç. Şifreler işletim sistemi kasasındadır ve oturum açmadan okunamaz. Tailscale'den cihazı çıkar, Google'da erişimi iptal et.

## Maliyet ve sınırlar

**Bulut kullanımı çok pahalı olabilir mi?**
`config/llm.yaml` bütçe sınırı (günlük/aylık) bulut çağrısını durdurur; sağlayıcı panelinde de limit koy ([API anahtarları](04-api-anahtarlari.md#maliyeti-kontrol-altinda-tut)).

**Dosya yükleme sınırı?**
Veri yüklemede dosya başına **2 GB**.

**Kaç özellik var?**
250 madde, 50 modül altında ([Özellik kataloğu](17-ozellik-katalogu.md)). Bazıları henüz yapım aşamasındadır; durumu kataloğun «Durum» sütununda yazar.

## Hâlâ sorum var

[Sorun giderme](11-sorun-giderme.md) ve [Sözlük](13-sozluk.md) sayfalarına bak; çözülmezse ürünün sahibine `sb logs --bundle` paketini gönder.
