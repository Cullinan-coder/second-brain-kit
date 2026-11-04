# 02 · Kurulum sihirbazı: 12 adım, adım adım

Sihirbaz (**Second Brain Kurulum**) 12 adımdan oluşur. Her ekranı, alanı ve düğmeyi burada bulursun. Hesap ve anahtar alma ayrıntıları ayrı bölümlerde: [Hesaplar](03-hesaplar.md), [API anahtarları](04-api-anahtarlari.md), [Modeller ve ses](05-modeller-ses.md), [MCP](06-mcp.md), [Veri yükleme](07-veri-yukleme.md).

## Sihirbazın genel kuralları

- **Her adım atlanabilir.** Atladıklarını kurulumdan sonra uygulamanın **Ayarlar** bölümünden yaparsın; özet ekranında «atlandı — sonra uygulamadan» olarak listelenir.
- **İleri / Geri** düğmeleri altta; adım göstergesi **Adım n/12** yazar. Üstteki şeritte **Kurulum %…** ilerlemesi görünür.
- **Dil:** sağ üstte **Dil: Türkçe / English** anahtarı. **Tema:** **Koyu / açık tema** anahtarı.
- **Yarıda kalan kurulum:** pencereyi kapatıp yeniden açarsan ilk ekranda **Yarım kalmış bir kurulum var.** yazar ve **Kaldığın yerden devam et** düğmesi çıkar (adım numarası da yazılır: «Yarım kalan kurulum sürdürüldü (adım n)»). Sıfırdan başlamak için **Baştan başla**.
- **Sırlar** (şifre, anahtar, belirteç) asla sihirbazın kaydına yazılmaz; yalnız işletim sistemi şifre kasasına gider. Yarım kalan kurulumda sırları yeniden girmen gerekebilir.
- Hata olursa kırmızı **Kurulum durdu** kartı: **Ne oldu / Nasıl düzeltilir** ve **Yeniden dene** ([Sorun giderme](11-sorun-giderme.md)).



---

## Adım 1 — Hoş geldin

**Amaç:** dil seçmek ve verinin nasıl korunduğunu görmek.

Ekranda:

- **Dil** anahtarı (Türkçe / English).
- **Gizlilik** başlığı altında dört madde:
  1. Notların ve verilerin bu bilgisayarda kalır; kasa senin klasörün.
  2. Şifreler ve API anahtarları yalnız işletim sistemi kasasında (keyring) saklanır.
  3. Mail salt okunur; silme ve gönderme her zaman senin onayınla olur.
  4. Bulut modeli kullanmak tamamen isteğe bağlıdır; tam yerel çalışabilirsin.
- **Lisans notu:** devam ederek yazılımı kendi sorumluluğunda kullanmayı kabul edersin; imzasız uygulama uyarısı ilk açılışta normaldir.
- «Her adım atlanabilir; atladıklarını sonra uygulamadaki Ayarlar'dan yaparsın.»

**Yapacağın:** dili seç → **İleri**.



---

<a id="adim-2-hazir-secim"></a>

## Adım 2 — Hazır seçim

**Amaç:** dört eksenle başlangıç özellik listesini çıkarmak. Sonra 3. adımda tek tek değiştirirsin.

Dört kart grubu vardır (her kartın altında açıklaması yazar):

| Eksen | Seçenekler | Ne belirler |
|---|---|---|
| **Meslek** — «Sana uygun özellik paketi.» | Öğrenci · Ajans / Freelancer · Yazılımcı · Akademisyen · Girişimci · Satış / CRM · İçerik üreticisi · Araştırmacı | O mesleğe uygun modülleri **ekler** |
| **Donanım** — «Bilgisayarın ne kadar yerel model kaldırır.» | Güçlü ekran kartı (14 GB+ VRAM) · Orta (8–14 GB VRAM) · Zayıf laptop / bulut · Mac (Apple Silicon) | Model boyutunu seçer, ağır özellikleri kapatır |
| **Gizlilik** — «Verinin nerede işleneceği.» | Tam yerel · Karma · Bulut öncelikli | Verinin buluta gidip gitmeyeceğini, izin profilini ve maskelemeyi belirler |
| **Yoğunluk** — «Kaç özellik açılsın.» | Minimal · Günlük hayat · Güç kullanıcısı | Temel modül listesini verir |

- Sihirbaz bilgisayarını tarar ve **Donanım** kartlarından birini **önerilen** diye işaretler (GPU belleğine göre). Öneriyi değiştirebilirsin.
- Varsayılanlar: Donanım = Orta, Gizlilik = Karma, Yoğunluk = Günlük hayat; Meslek seçili değildir.
- Alttaki sonuç satırı seçimin sonucunu yazar: «Bu seçim **M modül** ve **I madde** açar. Üçüncü adımda değiştirebilirsin.»
- Seçimlerin birbirini nasıl kısıtladığı: [Hazır seçimler](15-hazir-secimler.md). Örneğin Zayıf laptop seçersen görüntü, ekran izleme, uyandırma sözcüğü ve ses kapanır; Tam yerel seçersen görsel üretme kapanır ve bulut anahtarı gerekmez.
- Uyarı çıkabilir: «Tam yerel gizlilik + zayıf donanım: küçük yerel model kullanılır, kalite düşebilir».

**Yapacağın:** her eksenden bir kart seç → **İleri**. Emin değilsen: Meslek = sana en yakın olan, Donanım = önerilen, Gizlilik = Karma, Yoğunluk = Günlük hayat.



---

## Adım 3 — Bütün özellikler

**Amaç:** 250 maddelik kataloğu (50 modül altında gruplu) tek tek açıp kapatmak.

Ekranın üstündeki denetimler:

| Denetim | Ne yapar |
|---|---|
| **Ara: ad ya da açıklama** kutusu | Modül/madde adına ya da açıklamaya göre süzer |
| **Kategori** listesi (**Bütün kategoriler**) | Tek bir kategoriye indirger |
| **Yalnız seçilileri göster** kutusu | Yalnız işaretli olanları listeler |
| **Hepsini aç / Hepsini kapat** | Tüm modül kartlarını genişletir/daraltır |
| Her modülde **Maddeleri göster/gizle** | O modülün maddelerini açar |

Her **modül** bir kutudur; altında **maddeleri** (her biri kendi kutusuyla) bulunur. Modül kutusunu kapatırsan altındaki maddeler de kapanır. Her modülde ve maddede **gereksinim rozetleri** görünür:

| Rozet | Anlamı |
|---|---|
| **hesap** | Bir hesap gerekir (Google, IMAP, Spotify…) |
| **anahtar** | Bir API anahtarı/gizli değer gerekir |
| **GPU** | Belirli ekran kartı belleği gerekir |
| **gerekir** | Başka bir ön koşul (ör. program) |

Altta sayaçlar: «**n/m seçili**» (modülde) ve «**M/Mt modül · I/It madde seçili**» (genel). Eşleşme yoksa **Eşleşen madde yok.**

Bazı modüller başkasına bağlıdır: ses kapanırsa uyandırma sözcüğü, görsel model kapanırsa ekran izleme kapanır; Gmail **ve** IMAP ikisi de kapanırsa sabah özeti kapanır.

**Yapacağın:** ilgilenmediğin modülleri kapat; emin değilsen varsayılan listeyle devam et (sonradan **Ayarlar → Özellikler**'den değiştirirsin). Her modülün ne yaptığı: [Modüller](16-moduller.md).



---

## Adım 4 — Kişisel bilgiler

**Amaç:** asistanın seni tanıması için temel bilgiler. «Bu bilgiler yalnız bu bilgisayarda, kasanın ayar dosyasında tutulur.»

| Alan | Ne yazılır | Notlar |
|---|---|---|
| **Adın** | Asistanın sana nasıl hitap edeceği | Zorunlu: «Devam etmek için adını yaz (ya da adımı atla)» |
| **Tam adın** | Resmî ad soyad | İsteğe bağlı |
| **Kasa klasörü** | Notlarının duracağı klasör | Boş bırakırsan varsayılan konum kullanılır («boşsa varsayılan konum»). **Gözat…** düğmesi klasör seçtirir (yalnız masaüstü pencerede). **Kısa yolu kullan** düğmesi önerilen kısa yolu yazar |
| **Saat dilimi** | Listeden seç ya da yaz | Ör. `Europe/Istanbul`, `GMT+3`, `Türkiye` de anlaşılır |
| **Okul / iş yeri** | Kurum adı | İsteğe bağlı |
| **Rol / bölüm** | Öğrenci, mühendis, … | İsteğe bağlı |

**Kasa yolu uyarıları** (yazarken anında çıkar):

- **Uzun yol (Windows):** «Kasa yolu uzun (… karakter): Windows 260 karakter sınırı Python paketlerinin kurulumunu bozabilir. Daha kısa bir klasör seç.» → `C:\SB` gibi kısa bir yola al.
- **OneDrive içi:** «Kasa OneDrive klasörünün içinde: eşitleme dosyaları kilitleyebilir ve kurulumu yavaşlatır/bozar.» → OneDrive dışına al.

Uyarılar engellemez ama kurulumu bozabilir; dinlemen önerilir.



---

## Adım 5 — Hesaplar

**Amaç:** Google, e-posta (IMAP) ve diğer hizmetleri bağlamak. «Şifreler yalnız işletim sistemi kasasına gider.»

Üstte seçimine göre **gereken hesaplar** yazılır («Seçimin için gereken hesaplar: …»); her hesabın yanında nasıl bağlanacağı belirtilir (aşağıdaki bölümlerin bağlantısı). Tüm hesapları şimdi bağlamak zorunda değilsin.

Ekranın bölümleri:

### 5a · Bağlı hesaplar

**Bağlı hesaplar** listesi. Henüz yoksa «Henüz bağlı hesap yok.» Her hesapta tür (Google / E-posta (IMAP)), **yetkili / yetki yok** durumu ve **Kaldır** düğmesi (onay sorar: «'…' hesabının bağlantısı kaldırılsın mı? (Arşivlenmiş veriler silinmez.)»).

### 5b · Google hesabı (adım adım)

Başlık: **Google hesabı (adım adım)**. Giriş: «Google'ın Gmail, Takvim, Rehber ve Drive'ına salt okunur erişmek için bir kerelik OAuth istemcisi oluşturulur (~10 dk). Ekranları sırayla izle.»

7 ekran vardır (**Ekran n/7**; **Önceki ekran / Sonraki ekran** düğmeleri):

1. **Proje oluştur** 2. **API'leri aç** 3. **İzin ekranı** 4. **Test kullanıcıları ve yayınla** 5. **İzinler (scopes)** 6. **İstemci oluştur** 7. **Dosyayı yerleştir ve bağlan**

Her ekranın ayrıntısı ve ekran görüntüsü yerleri: [Hesaplar → Google](03-hesaplar.md#hesap-google).

Sonra **Google ile bağlan** kutusu:

| Alan/Düğme | Ne yapar |
|---|---|
| **Takma ad** (varsayılan `ana`) | Hesabın kısa adı; küçük harf/rakam/`_`/`-`, en çok 30 karakter |
| **Google e-posta adresi** | Giriş yapacağın Gmail adresi. Geçersizse «Geçerli bir Google e-posta adresi yaz.» |
| **OAuth istemci dosyası (client_secret.json)** → **Dosya seç…** | Google Cloud'dan indirdiğin JSON'u yükler. Başarılıysa «client_secret.json yüklendi ✓»; yoksa «Henüz yüklenmedi» |
| Onay kutuları | **Gmail (salt okunur)**, **Takvim**, **Rehber**, **Drive (salt okunur)** — hangi izinleri vereceğin; seçimine göre önceden işaretlenir |
| **Google ile bağlan** | Önce dosya yüklenmeli («Google ile bağlanmak için önce client_secret.json dosyasını yükle.»). Basınca tarayıcı açılır; «Tarayıcıda Google girişini tamamla…». Bitince «Bağlandı: …» |

### 5c · E-posta (IMAP)

Başlık **E-posta (IMAP)** → **IMAP hesabı ekle**. «Gmail, Outlook, iCloud, Yandex ya da kendi sunucun. Birden çok hesap ekleyebilirsin; salt okunur arşivlenir. Gmail/iCloud için uygulama şifresi gerekir.»

| Alan | Açıklama |
|---|---|
| **Takma ad** | Kısa ad (ör. `is`, `okul`) |
| **Hazır sunucu** | Gmail · Outlook / Microsoft 365 · iCloud · Yandex · Diğer (elle gir). Seçince sunucu ve kapı kendiliğinden dolar: `imap.gmail.com`, `outlook.office365.com`, `imap.mail.me.com`, `imap.yandex.com`; hepsi **993** |
| **Sunucu**, **Kapı (port)** | «Diğer»de elle gir |
| **Kullanıcı / e-posta** | Giriş adı (genelde e-posta adresin) |
| **Şifre / uygulama şifresi** | Normal şifre değil **uygulama şifresi** ([nasıl alınır](03-hesaplar.md#hesap-imap)) |
| **Test et ve kaydet** | Sunucuya bağlanıp giriş dener; başarılıysa kaydeder (şifre, şifre kasasına yazılır). Eksikse «Sunucu, kullanıcı ve şifre gerekli.» |

Hata mesajları Türkçe ve ne yapacağını söyler (ör. «Kimlik reddedildi: kullanıcı adı ya da şifre yanlış…»); tam liste: [Sorun giderme](11-sorun-giderme.md#imap-hata-mesajlari).

### 5d · Okul (ÖBS / LMS)

**Okul (ÖBS / LMS):** okul sisteminin adresi ve kullanıcı adın hesaplara yazılır, şifre yalnız şifre kasasına gider. Alanlar: **Okul sistemi adresi** (örnek metin `obs.okul.edu.tr`), **Kullanıcı adı / öğrenci no**, **Okul şifresi**; düğme **Adres ve kullanıcıyı kaydet** → «Okul bilgileri kaydedildi.»

### 5e · Diğer hizmetler

Başlık **Diğer hizmetler**: **Spotify Client ID** ve **Spotify Client Secret**, **Telegram bot belirteci**, **GitHub kişisel erişim belirteci**. Altlarında Spotify, Telegram, Tailscale ve GitHub için kısa adım adım rehberler vardır ([Spotify](03-hesaplar.md#hesap-spotify), [Telegram](03-hesaplar.md#hesap-telegram), [Tailscale](03-hesaplar.md#hesap-tailscale), [GitHub](03-hesaplar.md#hesap-github)). Gizli alanların yanındaki **Kaydet ve test et** düğmesi değeri şifre kasasına yazar ve («Deneniyor…») sonucu gösterir.



---

## Adım 6 — API anahtarları

**Amaç:** bulut yapay zekâ sağlayıcılarının anahtarlarını girmek. **Tümü isteğe bağlıdır.** «Tam yerel» seçtiysen ekranda «Tam yerel seçtin: hiçbir şey buluta gitmez, bu yüzden bulut API anahtarları gerekmez.» yazar ve anahtarlar «isteğe bağlı» görünür.

Sağlayıcılar: **OpenAI, Anthropic, Gemini, OpenRouter, Groq, DeepSeek, Mistral**. Her satırda:

- Gizli bir alan (yazdığın görünmez). Önceden kaydedilmişse yer tutucu «**kayıtlı (değiştirmek için yaz)**» der; durum rozeti **kayıtlı / yok**.
- **Kaydet ve test et** düğmesi: anahtarı şifre kasasına yazar ve sağlayıcıya küçük bir sorgu gönderir («Anahtar kaydedilince sağlayıcıya küçük bir test isteği gönderilebilir; değer ekranda tutulmaz.»). Sonuç **Kaydedildi.** ya da hata. Alan boşsa «Önce anahtarı yaz.»
- Altta «**Seçimin için gereken diğer sırlar**» (ör. Spotify, Telegram) listelenebilir.

Anahtarı nereden alacağın, maliyet ve limit uyarıları: [API anahtarları](04-api-anahtarlari.md).



---

## Adım 7 — Yerel modeller

**Amaç:** yerel yapay zekâ modelini ve sesi kurmak.

- **Donanım kartı:** **Bellek**, **İşlemci** (çekirdek), **Ekran kartı**, **Disk** bilgileri ve **Önerilen model profili**. **Yeniden tara** düğmesi taramayı tazeler; bilgi alınamazsa «Donanım bilgisi alınamadı.»
- **Ollama (yerel model çalıştırıcı):** kuruluysa «Ollama kurulu.» (✓); değilse «Ollama kurulu değil.» ve **Ollama'yı kur** düğmesi (resmî kurucu indirilir ve çalıştırılır; ilerleme altta görünür).
- **Kurulu modeller:** liste ya da «Henüz model indirilmemiş.» Önerilen model **Önerilen:** satırında yazar. **model adı** kutusuna (örn. `qwen2.5:7b`) yazıp **Modeli indir** diyerek istediğini çekersin; «… indiriliyor…» ilerlemesi görünür.
- **Ses (Whisper):** «Konuşmayı yazıya çeviren yerel faster-whisper kurulur.» **NVIDIA GPU kütüphanelerini de kur** kutusu ve **Sesi kur** düğmesi.

Hangi profilin ne zaman seçileceği, indirme boyutları, GPU kütüphaneleri: [Modeller ve ses](05-modeller-ses.md).



---

## Adım 8 — MCP

**Amaç:** Claude Code/Desktop'a Second Brain'in kendi MCP'sini ve istediğin hazır MCP'leri bağlamak. «MCP sunucuları Claude'a ek araçlar verir. Gereken alanları doldurup kur; gizli değerler yalnız kasaya yazılır.»

- **Katalog kartları:** 18 hazır MCP ([MCP kataloğu](19-mcp-katalogu.md)). Seçimin için gerekenler önce, **önerilen** rozetiyle gelir. Her kartta açıklama, gereken alanlar (gizliler parola kutusu), **Kur ve bağla**, **Belge** bağlantısı. Kuruluysa **kurulu** rozeti ve **Kaldır**.
- Elle kurulan MCP'lerde (uzak sunucular) yalnız belge görünür: «Elle kurulum: belgeye bak.»
- **Kendi MCP'ni ekle:** «Bir komut (stdio) ile çalışan MCP sunucusu.» Alanlar: **Ad**, **Komut**, **Bağımsız değişkenler (boşlukla)**, **Ortam değişkenleri (her satır ANAHTAR=değer)**; **Ekle** düğmesi. Eksikse «Ad ve komut gerekli.»

Ayrıntı: [MCP](06-mcp.md).



---

## Adım 9 — Veri yükleme

**Amaç:** başka hizmetlerden aldığın dışa aktarma dosyalarını içe aktarmak (WhatsApp, Takeout, ChatGPT/Claude geçmişi, Spotify, LinkedIn, banka, Notion, Evernote…). 39 kaynak vardır ([Veri kaynakları](18-veri-kaynaklari.md)).

Her kaynak kartında:

1. **Bu dosyayı nasıl alırsın?** — adım adım anlatım.
2. «**Dosyayı buraya bırak ya da seçmek için tıkla**» alanı veya **Dosya seç**; **Biçim: …** ve **Bağlayıcı: …** bilgisi.
3. **Yükleniyor: ad (MB)…** → **Yüklendi: ad**.
4. **Önizle** → **Önizleme hazır; sorun yoksa içe aktar.** (hiçbir şey yazılmaz).
5. **İçe aktar** → «İçe aktarılıyor; ilerleme aşağıda.» → **İçe aktarma bitti.** / «N kayıt içe aktarıldı».

Üstte «Her kaynak için dosyayı nasıl alacağını oku, dosyayı kutuya bırak, önizle, içe aktar. Dosya yalnız bu bilgisayarda okunur.» yazar. Seçimin için gereken kaynak yoksa «Seçimin için gereken kaynak yok.»; **Bütün kaynakları göster (n)** kutusu hepsini açar. Altta **Yapılan içe aktarmalar** listesi (başarılı / başarısız). Yükleme sınırı **2 GB**.

Ayrıntı: [Veri yükleme](07-veri-yukleme.md).



---

## Adım 10 — Telefon

**Amaç:** telefondan asistana Tailscale ile bağlanmak. «Telefondan asistana Tailscale üzerinden bağlanırsın; veri internete açılmaz.»

Ekranda göstergeler: **Tailscale kurulu**, **Tailscale bağlı**, **Asistan adresi**, **Eşleme kodu**. Asistan sunucusu çalışmıyorsa «Asistan sunucusu çalışmıyor; adres ve kod uygulama açıkken görünür.» yazar. **Yenile** durumu tazeler. Adım adım Tailscale kurulumu: [Hesaplar → Tailscale](03-hesaplar.md#hesap-tailscale); telefonu eşleme ve PWA: [Uygulama turu → Telefon](08-uygulama-turu.md#telefon).



---

## Adım 11 — Başlangıç

**Amaç:** bilgisayar açılınca Second Brain açılsın mı? «Uygulama bilgisayar açılınca kendiliğinden başlayabilir. Bu yalnız senin onayınla yapılır.»

| Kutu | Anlamı |
|---|---|
| **Bilgisayar açılınca Second Brain açılsın** | Windows'ta Başlangıç klasörüne, macOS'ta oturum açma öğelerine kısayol eklenir |
| **Simge durumunda (tepside) başlasın** | Pencere açılmadan tepsi simgesinde başlar |

**Kaydet** → «Başlangıç ayarı kaydedildi.» «Seçmezsen hiçbir şey eklenmez; sonra Ayarlar'dan değiştirebilirsin.» Sistem desteklemiyorsa «Bu sistemde otomatik başlatma desteklenmiyor.»

Günlük işlerin (güncelleme, mail çekme vb.) saati zamanlayıcı kurulurken belirlenir: Windows'ta günlük görev oturum açılışında ve **13:00**'te, haftalık denetim **pazar 15:00**'te çalışır (`SecondBrain-Daily`, `SecondBrain-Weekly`, `SecondBrain-Chat`). Zamanlanmış görevler kurulum adımında yalnız sen izin verirsen eklenir.



---

## Adım 12 — Özet ve kurulum

**Amaç:** seçimleri gözden geçirip **Kur**'a basmak.

Özet ekranı şunları listeler: **Ad**, **Kasa** (deneme kipindeyse «deneme»), **Saat dilimi**, **Modül** ve **Madde** sayıları, **Otomatik açılış**, **Bağlı hesaplar**, **Kasadaki sırlar** («N sır kasada (yalnız adlar)»), **Yerel modeller** (kurulu / kurulacak), **MCP**, **İçe aktarılanlar**, **Atlanan adımlar**. **Neler kurulacak** bölümü ayrıntı verir; boşsa «bir şey eklenmedi». Atlananlar için not: «Atlanan adımları kurulumdan sonra uygulamanın Ayarlar bölümünden yapabilirsin.»

**Kur** → canlı ilerleme (10 adım, [Kurulum](01-kurulum.md#kurulum-sirasinda-ne-olur-adim-12de)). Bitince:

- **Hazırsın** — «Second Brain kuruldu. Uygulamayı açıp ilk turu izleyebilirsin.» Düğmeler: **Uygulamayı aç**, **Turu göster**.
- Hata olursa «Kurulum bir hatayla durdu; günlüğe bak, sonra tekrar dene.» ve **Kurulum durdu** kartı (**Yeniden dene**, **Kişisel bilgilere dön**).



---

## Kurulumdan sonra aynı ekranlar: Ayarlar

Sihirbazın sayfaları uygulamanın **Ayarlar** penceresinde sekme olarak durur: **Özellikler · Hesaplar · Anahtarlar · Modeller · MCP · Veri yükleme · Telefon · Başlangıç · Güncelle · Sağlık · Kaldır · Günlük**. Açılış: uygulamada **Uygulama ayarları → Ayarları aç** ya da tepsi simgesinde **Ayarlar**. Ayrıntı: [Uygulama turu](08-uygulama-turu.md).
