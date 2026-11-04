# 03 · Hesapları bağlama

Bu bölüm her hesap türü için **ne işe yaradığını, ne istediğini ve nasıl bağlanacağını** adım adım anlatır. Hesapları sihirbazın **5. adımında** (ve kurulumdan sonra **Ayarlar → Hesaplar** sekmesinde) bağlarsın.

> **Üçüncü taraf menüleri hakkında:** Google, Microsoft, Apple, Spotify, Telegram ve GitHub arayüzlerini kendileri değiştirir. Aşağıdaki menü adları yazıldığı andaki hâlidir; farklı görürsen her bölümün sonundaki **resmi yardım adresine** bak. Second Brain'in kendi ekranlarındaki adlar koddan doğrulanmıştır.

> **Tüm hesaplar için genel kural:** şifreler ve anahtarlar yalnız işletim sisteminin şifre kasasına yazılır. Hiçbirini sohbete, e-postaya ya da bir dosyaya yapıştırma. Hiçbir hesap zorunlu değildir; yalnız seçtiğin özelliklerin istediği hesapları bağla ([Hangi özellik ne ister](21-ne-ister.md)).

## Hangi hesabı ne zaman bağlarım?

| Hesap | Ne için | Zorunlu mu |
|---|---|---|
| [Google](#hesap-google) | Gmail arşivi, Takvim, Rehber, Drive, SMS yedeği | Mail/takvim istiyorsan evet |
| [E-posta (IMAP)](#hesap-imap) | Outlook, iCloud, Yandex, okul/şirket maili | İstersen |
| [Okul (ÖBS/LMS)](#hesap-okul) | Ders notları ve dosyaları | İstersen |
| [Tailscale](#hesap-tailscale) | Telefondan erişim | İstersen |
| [Spotify](#hesap-spotify) | Doğrudan şarkı çalma | İstersen |
| [Telegram](#hesap-telegram) | Bot ile not alma ve bildirim | İstersen |
| [GitHub](#hesap-github) | Proje ve GitHub kayıtları | İstersen |
| [WhatsApp](#hesap-whatsapp), [LinkedIn](#hesap-linkedin) | Hesap değil, **dosya** içe aktarma | İstersen |
| API anahtarları | Bulut modeller | [Ayrı bölüm](04-api-anahtarlari.md) |

---

<a id="hesap-google"></a>
## Google hesabı (Gmail, Takvim, Rehber, Drive)

### Ne işe yarar?

Second Brain Google'a **kendi OAuth istemcinle** bağlanır: sen Google Cloud'da (ücretsiz) küçük bir «uygulama» tanımlarsın, yalnız kendi hesabın bu uygulamaya izin verir. Böylece:

- **Gmail** (`gmail.readonly`): mailler **salt okunur** arşivlenir, kategorilere ayrılır.
- **Takvim** (`calendar.events`): takvim kasaya alınır; etkinlik ekleme/silme **onayla** yapılır.
- **Rehber** (`contacts.readonly`): kişi notları.
- **Drive** (`drive.readonly`): dosya listesi ve son dönem Docs metni; SMS yedeği de Drive'dan okunur.

Bu işlem **bir kerelik, yaklaşık 10 dakika** sürer ve ücretsizdir. Para ödeme bilgisi istenmez (istenirse dur: yanlış bir ürüne gidiyorsundur).

### Önce hazırla

- Bağlayacağın Google hesabının e-postası (bu rehberde örnek: `ornek@gmail.com`).
- Tarayıcıda o hesapla oturum açık olsun. Birden çok hesabın varsa **doğru hesabın** seçili olduğunu sağ üst avatardan kontrol et.
- Sihirbazın 5. adımındaki **7 ekranlık** rehber aşağıdakinin kısa halidir; aynı sırayı izler.

### Adım adım

**Ekran 1 — Proje oluştur**

1. https://console.cloud.google.com adresini aç; doğru Google hesabıyla giriş yap. (İlk girişte kullanım şartlarını kabul etmen istenebilir.)
2. Üstteki **proje seçici**ye (sol üstte, «Google Cloud» yazısının yanı) tıkla.
3. Açılan pencerede sağ üstte **New project** (Yeni proje).
4. **Project name:** `second-brain` yaz. (Organization/Location alanları boş kalabilir.) → **Create**.
5. Birkaç saniye sonra bildirimde proje oluşur → proje seçiciden `second-brain` projesini **seç**. Üst çubukta adı görünmeli.



**Ekran 2 — API'leri aç**

1. Sol üst **☰ menü → APIs & Services → Library** (ya da arama kutusuna `Library` yaz).
2. Arama kutusuna sırayla şunları yaz, sonuca tıkla, **Enable** (Etkinleştir) düğmesine bas:
   - **Gmail API**
   - **Google Calendar API**
   - **People API** (rehber için)
   - **Google Drive API**
3. Her biri için «API enabled» (ya da Manage düğmesi) görünce geri dön.



**Ekran 3 — İzin ekranı (Google Auth Platform)**

1. Sol menüde **Google Auth Platform** (eski arayüzde *APIs & Services → OAuth consent screen*) → **Get started**.
2. **App name:** `Second Brain`. **User support email:** kendi adresin → **Next**.
3. **Audience:** **External** → **Next**.
4. **Contact information:** kendi e-postan → **Next**.
5. Kullanım şartı kutusunu işaretle → **Continue** → **Create**.



**Ekran 4 — Test kullanıcıları ve yayınla**

1. **Audience** sekmesine git.
2. **Test users → Add users**: bağlayacağın Google adres(ler)ini ekle → **Save**.
3. Aynı sekmede **Publish app** → **Confirm**. (**Neden?** Uygulama «Testing»de kalırsa giriş her **7 günde bir** düşer, yeniden giriş istenir. Yayınlayınca sürer. «Doğrulanmamış uygulama» uyarısı çıkacak; bu **senin kendi uygulaman** olduğu için normaldir.)



**Ekran 5 — İzinler (scopes)**

1. Sol menü **Data Access → Add or remove scopes**.
2. Şu dört izni bul ve işaretle (listede arayabilirsin):
   - `.../auth/gmail.readonly`
   - `.../auth/calendar.events`
   - `.../auth/contacts.readonly`
   - `.../auth/drive.readonly`
3. **Update** → sayfanın altında **Save**.



**Ekran 6 — İstemci (client) oluştur**

1. Sol menü **Clients → Create client**.
2. **Application type:** **Desktop app**. **Name:** `sb-desktop` → **Create**.
3. Açılan pencerede **Download JSON** düğmesine bas. Bir `client_secret_....json` dosyası iner.



> `client_secret.json` dosyası **gizlidir**: kimseye gönderme, depoya koyma, ekran görüntüsünü paylaşma.

**Ekran 7 — Dosyayı yerleştir ve bağlan**

1. Sihirbazda **Google ile bağlan** kutusuna in. **Takma ad** (varsayılan `ana`) ve **Google e-posta adresi**ni yaz.
2. **OAuth istemci dosyası (client_secret.json)** altındaki **Dosya seç…** düğmesine bas → indirdiğin JSON'u seç. Rozet **client_secret.json yüklendi ✓** olur. (Dosya `.secondbrain/secrets/client_secret.json` olarak kasa dışına konur; elle taşımak istersen oraya koyabilirsin.)
3. Vermek istediğin izinleri işaretle (**Gmail**, **Takvim**, **Rehber**, **Drive**; Gmail varsayılan olarak işaretlidir).
4. **Google ile bağlan**'a bas → «Tarayıcıda Google girişini tamamla…» yazar, tarayıcı açılır.
5. Hesabını seç. **«Google bu uygulamayı doğrulamadı» (Google hasn't verified this app)** uyarısı çıkarsa: **Gelişmiş (Advanced)** → **Second Brain'e git (güvenli değil) (Go to Second Brain (unsafe))**. Bu senin kendi uygulamandır.
6. İzin sayfasında istenen izinleri işaretle → **Devam (Continue)**.
7. «Bağlantı tamam» benzeri bir sayfa görünce tarayıcıyı kapat. Sihirbaz **Bağlandı: ornek@gmail.com** yazar.



### Komutla bağlama

`sb login <takma-ad>` (ör. `sb login ana`) tarayıcıyı açar, aynı izin akışını yürütür ve giriş belirtecini şifre kasasına yazar. Sonra `sb mail-fetch ana` ilk mail çekimini yapar. Bkz. [Komut referansı](14-komut-referansi.md#sb-login).

### Birden fazla Google hesabı

Her hesap için farklı **takma ad** kullanarak **Google ile bağlan**'ı tekrarla (ör. `ana`, `okul`). Aynı `client_secret.json` hepsinde kullanılır. Test kullanıcıları listesine her adresi eklemeyi unutma.

### Sık hatalar

| Belirti | Çözüm |
|---|---|
| «Google ile bağlanmak için önce client_secret.json dosyasını yükle.» | Önce **Dosya seç…** ile JSON'u yükle |
| «Geçerli bir Google e-posta adresi yaz.» | `ornek@gmail.com` biçiminde yaz |
| Tarayıcıda **Erişim engellendi / access_denied** | Adresi **Test users** listesine ekle ya da uygulamayı **Publish app** ile yayınla |
| Giriş birkaç günde düşüyor | Uygulama «Testing» durumunda; **Publish app** |
| **redirect_uri_mismatch** | İstemci türü **Desktop app** olmalı; web istemcisi oluşturduysan silip Desktop ile yeniden oluştur |
| «API has not been used in project … / disabled» | Ekran 2'deki dört API'nin **Enable** olduğunu kontrol et |
| Yanlış hesapla bağlandın | Hesaplar listesinde **Kaldır**, sonra doğru hesapla tekrar bağlan |

Daha fazlası: [Sorun giderme → Google giriş reddi](11-sorun-giderme.md#google-giris-reddi).

Resmî yardım: https://support.google.com/cloud/answer/6158849 (OAuth izin ekranı) ve https://developers.google.com/workspace/guides/create-credentials

---

<a id="hesap-imap"></a>
## E-posta (IMAP): Gmail uygulama şifresi, Outlook, iCloud, Yandex, okul/şirket

### Ne işe yarar?

IMAP, mailini okuyan standart protokoldür. Google ile bağlamak istemediğin ya da Google olmayan hesapları (Outlook, iCloud, Yandex, okul veya şirket sunucusu) **salt okunur** arşivlemek için kullanılır. Birden çok hesap ekleyebilirsin.

### Sihirbazda ekleme (5. adım → E-posta (IMAP))

1. **Takma ad:** kısa bir ad (`is`, `okul`, `icloud`). Küçük harf/rakam/`_`/`-`.
2. **Hazır sunucu:** Gmail · Outlook / Microsoft 365 · iCloud · Yandex · Diğer.
3. **Kullanıcı / e-posta** ve **Şifre / uygulama şifresi** (aşağıda nasıl alınır).
4. **Test et ve kaydet.** Başarılıysa «✓ IMAP girişi başarılı»; şifre şifre kasasına yazılır.

Hazır sunucuların değerleri:

| Hazır sunucu | Sunucu | Kapı | Sağlayıcıya özel ipucu |
|---|---|---|---|
| Gmail | `imap.gmail.com` | 993 | IMAP açık ve uygulama şifresi gerekir (2 adımlı doğrulama) |
| Outlook / Microsoft 365 | `outlook.office365.com` | 993 | Kişisel Outlook: IMAP açık + uygulama şifresi |
| iCloud | `imap.mail.me.com` | 993 | appleid/Apple hesabından uygulamaya özel şifre |
| Yandex | `imap.yandex.com` | 993 | Ayarlarda IMAP'i aç, uygulama şifresi üret |
| Diğer | kendin yaz | genelde 993 (SSL) | Sağlayıcının yardım sayfasında yazar |

### Uygulama şifresi nedir, neden gerekir?

Bazı sağlayıcılar, iki adımlı doğrulama açıkken harici programların **normal şifrenle** girmesine izin vermez. Bunun yerine «yalnız bu program için» geçerli, tek kullanımlık görünen ayrı bir şifre üretirsin. İstediğin zaman iptal edebilirsin ve ana şifrene dokunmaz. Sihirbazın hata mesajı da bunu söyler: «Kimlik reddedildi: kullanıcı adı ya da şifre yanlış. Gmail, iCloud ve Outlook'ta normal şifre değil UYGULAMA ŞİFRESİ gerekir.»

### Gmail'i IMAP olarak bağlamak (Google yöntemi yerine)

Çoğu kişi için [Google hesabı](#hesap-google) yöntemi daha iyidir. IMAP ile bağlamak istersen:

1. https://myaccount.google.com → **Güvenlik (Security)**.
2. **2 Adımlı Doğrulama**'yı aç (kapalıysa).
3. Arama kutusuna `Uygulama şifreleri` (App passwords) yaz ya da **2 Adımlı Doğrulama** sayfasının altındaki **Uygulama şifreleri** bağlantısına git. (Hesap türüne göre bu seçenek görünmeyebilir.)
4. Bir ad ver (`Second Brain`) → **Oluştur**. Çıkan **16 karakterli** şifreyi kopyala (boşluksuz da kabul edilir).
5. Gmail web → ⚙ → **Tüm ayarları gör → Yönlendirme ve POP/IMAP** → IMAP erişimi **etkin** (güncel Gmail'de IMAP çoğunlukla zaten açıktır).
6. Sihirbazda **Hazır sunucu: Gmail**, kullanıcı = tam Gmail adresin, şifre = az önceki 16 karakter.

Resmî yardım: https://support.google.com/accounts/answer/185833

<a id="hesap-outlook"></a>
### Outlook / Microsoft 365

1. Kişisel Outlook.com: web'de **Ayarlar → Posta → E-postayı eşitle → POP ve IMAP** bölümünde IMAP erişimine izin ver.
2. İki adımlı doğrulama açıksa Microsoft hesap **güvenlik sayfasından** bir **uygulama parolası** oluştur ve onu kullan.
3. Sihirbazda **Hazır sunucu: Outlook / Microsoft 365** (`outlook.office365.com`, 993).
4. **Kurumsal/okul Microsoft 365'te** IMAP genellikle yönetici tarafından kapalıdır ve parola yerine OAuth gerekir; bu durumda BT yöneticine sor.
5. Takvim için Outlook web → **Ayarlar → Takvim → Paylaşılan takvimler → Takvimi yayımla** → ICS bağlantısını kopyala; `sb caldav-sync outlook` ile çekilir.

Resmî yardım: https://support.microsoft.com/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353

<a id="hesap-icloud"></a>
### iCloud

1. Apple hesabında **iki faktörlü kimlik doğrulama** açık olmalı.
2. https://account.apple.com (eski adı appleid.apple.com) → **Oturum açma ve güvenlik → Uygulamaya özel parolalar** → yeni parola oluştur (ör. `Second Brain`).
3. Sihirbazda **Hazır sunucu: iCloud** (`imap.mail.me.com`, 993); kullanıcı adı iCloud adresin.
4. Takvim ve kişiler için aynı uygulama parolasıyla CalDAV (`https://caldav.icloud.com`) ve CardDAV (`https://contacts.icloud.com`) kullanılır: `sb caldav-sync icloud`.

Resmî yardım: https://support.apple.com/102654

### Yandex

1. Yandex Mail web → ⚙ **Tüm ayarlar → E-posta programları** bölümünde **IMAP ile** erişimi aç. (Menü adları Yandex'in arayüzüne göre değişir.)
2. Yandex ID güvenlik ayarlarından **uygulama şifresi** oluştur (Posta için).
3. Sihirbazda **Hazır sunucu: Yandex** (`imap.yandex.com`, 993).

Yandex yardımı: https://yandex.com/support/mail/

### Okul veya şirket mail sunucusu

1. Sağlayıcının (okul BT birimi / şirket yöneticisi) yardım sayfasında **IMAP sunucu adresini** ve kapıyı bul (ör. `mail.ornek.com.tr`, 993).
2. Sihirbazda **Hazır sunucu: Diğer (elle gir)** → **Sunucu** ve **Kapı**yı yaz; kullanıcı genelde tam e-posta adresindir.
3. Şifre için uygulama şifresi gerekip gerekmediğini BT'ye sor.

### Güvenlik duvarı / VPN

Okul-şirket sunucuları bazen yalnız kurum ağından erişilebilir; hata «Bağlanılamadı … zaman aşımına uğradı» olur. Kurum VPN'ine bağlan.

IMAP hata mesajlarının tam listesi: [Sorun giderme](11-sorun-giderme.md#imap-hata-mesajlari).

---

<a id="hesap-okul"></a>
## Okul (ÖBS / LMS)

**Ne işe yarar:** ders notları, ders dosyaları ve dönem planı için okul sistemini bağlar (modül: [Okul (ÖBS/LMS)](moduller/courses.md)).

**Adımlar (5. adım → Okul):**

1. **Okul sistemi adresi:** okulunun öğrenci bilgi sisteminin/LMS'in adresini yaz (örnek metin `obs.okul.edu.tr`).
2. **Kullanıcı adı / öğrenci no:** giriş adın.
3. **Okul şifresi:** şifren yalnız şifre kasasına yazılır (`svc-school-password`).
4. **Adres ve kullanıcıyı kaydet** → «Okul bilgileri kaydedildi.»

**Notlar:** Her okulun sistemi farklıdır; adres ve kullanıcı bilgisi yalnız kaydedilir. Not geçmişi gibi bazı veriler `_system/data/obs.yaml` dosyasından elle de yüklenebilir (`sb obs-import`). Okulunun sistemi iki adımlı doğrulama istiyorsa okul BT'sinin yardım sayfasına bak.

---

<a id="hesap-tailscale"></a>
## Tailscale (telefondan erişim)

**Ne işe yarar:** bilgisayarın ve telefonun arasında kapalı, özel bir ağ kurar. Asistana telefondan, **veriyi internete açmadan** bağlanırsın. Ücretsiz plan kişisel kullanım için yeterlidir (planlar değişebilir: https://tailscale.com/pricing).

1. Bilgisayarında https://tailscale.com/download adresinden Tailscale'i kur ve **Log in** ile giriş yap (Google/Microsoft/Apple/GitHub hesabıyla).
2. Telefonuna Tailscale uygulamasını kur (App Store / Google Play); **aynı hesapla** giriş yap.
3. İki cihazda da Tailscale'in «bağlı» olduğunu gör.
4. Sihirbazın 10. adımında (**Telefon**) **Tailscale kurulu** ve **Tailscale bağlı** göstergeleri yeşil olmalı; **Asistan adresi** ve **Eşleme kodu** görünür.
5. Telefonda tarayıcıdan **Asistan adresi**ni aç, eşleme kodunu gir, sonra tarayıcı menüsünden **Ana ekrana ekle** (PWA).
6. Doğrulama: `sb doctor` → «Telefon erişimi (isteğe bağlı, Tailscale)» satırı ✓ olur.

Ayrıntılar (HTTPS, bildirim, çevrimdışı kuyruk): [Uygulama turu → Telefon](08-uygulama-turu.md#telefon).

Resmî yardım: https://tailscale.com/kb

---

<a id="hesap-spotify"></a>
## Spotify (doğrudan şarkı çalma)

**Ne işe yarar:** asistan «X şarkısını çal» dediğinde Spotify'da doğrudan çalar. **Spotify Premium hesabı gerekir** (şarkı açma için). Listeleme/dinleme geçmişi içe aktarma için Premium şart değildir ([Spotify dinleme geçmişi](kaynaklar/spotify.md)).

1. https://developer.spotify.com/dashboard adresine git, Spotify hesabınla giriş yap (şartları kabul etmen istenebilir).
2. **Create app** de. Ad ve açıklama yaz (ör. `Second Brain`).
3. **Redirect URI** olarak tam şunu yaz: `http://127.0.0.1:8888/callback` → **Add** → kaydet. (Adres birebir aynı olmalı; yanlışsa giriş döner ve hata verir.)
4. Uygulamanın **Settings** sayfasından **Client ID**'yi kopyala; **View client secret** ile **Client Secret**'ı da kopyala.
5. Sihirbazın 5. adımında **Diğer hizmetler** altına **Spotify Client ID** ve **Spotify Client Secret**'ı yapıştır → **Kaydet ve test et**.
6. Spotify ilk kullanımda izin isterse kabul et (ekranlar Spotify'a göre değişir).

Hata durumunda: `redirect_uri` hatası → 3. adımdaki adresi kontrol et. «Premium gerekli» → hesabın Premium olmalı. Kontrol: `sb doctor` → «Spotify doğrudan çalma (isteğe bağlı)».

Resmî yardım: https://developer.spotify.com/documentation/web-api

---

<a id="hesap-telegram"></a>
## Telegram botu

**Ne işe yarar:** kendi botuna yazdığın her şey kasanın `00-Inbox` klasörüne **not** olarak düşer; sabah özeti ve hata uyarıları telefonuna Telegram'dan gelebilir. Bot yalnız **senin sohbet kimliğinden** gelen mesajları işler; başkası yazarsa yok sayılır.

1. Telegram'da **@BotFather**'ı bul (mavi tikli resmî hesap) → **Start**.
2. `/newbot` yaz.
3. Bot için bir **ad** (istediğin) ve **kullanıcı adı** (`bot` ile bitmeli, alınmışsa başka dene) seç.
4. BotFather sana bir **belirteç (token)** verir (`123456789:AA...` biçiminde uzun bir yazı). Kopyala. **Kimseyle paylaşma.**
5. Sihirbazın 5. adımında **Telegram bot belirteci** alanına yapıştır → **Kaydet ve test et**. (Komutla: `sb set-secret telegram-bot`.)
6. Telegram'da yeni botunu bul (BotFather'ın verdiği bağlantı) → **Start**, sonra `merhaba` yaz.
7. Botu sana bağlamak için `sb telegram setup` çalıştır; «bağlandı» yazınca deneme mesajı telefonuna gelir. Bota yazılanları kasaya çekmek için `sb telegram pull`.

Sık sorun: bot cevap vermiyor → bota **Start** demedin ya da belirteç yanlış; belirteci BotFather'dan `/token` ile yeniden alabilirsin (eskisi geçersiz olur).

Resmî yardım: https://core.telegram.org/bots/tutorial

---

<a id="hesap-github"></a>
## GitHub

**Ne işe yarar:** projelerin GitHub kayıtlarını (issue, PR, commit, release) kasaya alır; GitHub MCP'sini de besler. Bunun için bilgisayarda **`gh`** (GitHub CLI) girişi ya da bir **kişisel erişim belirteci (PAT)** gerekir.

**`gh` ile (önerilen):**

1. `winget install GitHub.cli` (macOS: `brew install gh`).
2. `gh auth login` → GitHub.com → HTTPS → tarayıcıyla giriş ([ayrıntı](01-kurulum.md#gh-auth-login)).

**Belirteçle (PAT):**

1. GitHub → profil → **Settings → Developer settings → Personal access tokens** (menü adları sürüme göre değişir).
2. **Yeni belirteç üret**; yalnız gereken izinleri ver (kod okuma, issue/PR okuma). Gereğinden fazla izin verme.
3. Belirteci kopyala (bir daha gösterilmez).
4. Sihirbazda **GitHub kişisel erişim belirteci** alanına yapıştır → kaydet. GitHub kullanıcı adını da yaz (modül alanı `github_user`).

Güvenlik: belirteci süreli (örn. 90 gün) yap; sızdığını düşünürsen GitHub'da hemen **Revoke** et.

Resmî yardım: https://docs.github.com/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

---

<a id="hesap-whatsapp"></a>
## WhatsApp

WhatsApp için **hesap bağlanmaz**; sohbet dışa aktarma **dosyası** içe aktarılır ve (isteğe bağlı) WhatsApp Masaüstü ile **onaylı mesaj gönderimi** yapılır. Sohbeti dışa aktarmanın ve içe aktarmanın adımları: [WhatsApp sohbetleri](kaynaklar/whatsapp.md). Asistan WhatsApp mesajını **onaysız göndermez**: önce mesajın tam metniyle onay kartı çıkar; kartı (yalnız bilgisayardan) onaylarsan mesaj **gönderilir**.

<a id="hesap-linkedin"></a>
## LinkedIn

LinkedIn için de hesap bağlanmaz; **veri arşivi** (zip) içe aktarılır: [LinkedIn veri arşivi](kaynaklar/linkedin.md).

---

<a id="hesabi-kaldirma"></a>

## Hesabı kaldırma

- **Ayarlar → Hesaplar → Kaldır** (onay sorar). Bağlantı kaldırılır; **arşivlenmiş veriler silinmez**.
- Google erişimini Google tarafında da iptal etmek için: Google Hesabın → **Güvenlik → Hesabına erişimi olan üçüncü taraf uygulamalar** → *Second Brain* → **Erişimi kaldır** (menü adı sürüme göre değişebilir).
- Şifre kasasındaki kayıtları silmek için kaldırma sihirbazının **sırlar listesi**ni kullan ([Kurulum → Kaldırma](01-kurulum.md#kaldirma)).
