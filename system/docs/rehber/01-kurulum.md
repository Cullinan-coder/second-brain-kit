# 01 · Kurulum

Bu bölüm Second Brain'i bilgisayarına **indirip açmaya** kadar olan adımları anlatır. Sonrasında açılan kurulum sihirbazı [02 · Sihirbaz adım adım](02-sihirbaz-adim-adim.md) bölümünde anlatılır.

## Başlamadan önce kontrol listesi

| Gerekli mi? | Ne | Neden |
|---|---|---|
| Zorunlu | Windows 10/11 ya da macOS 13 ve üstü | Desteklenen sistemler. Windows'ta günlük kullanımda sınanmıştır; macOS desteği yazılmıştır ama gerçek Mac'te sınırlı denenmiştir |
| Zorunlu | İnternet bağlantısı | İndirme, Python paketleri, modeller |
| Zorunlu | Boş disk alanı | Yerel model seçersen indirme boyutu: güçlü profil ≈ 15,4 GB, orta ≈ 8,5 GB, küçük ≈ 2,6 GB, bulut profili ≈ 1,4 GB (sihirbaz kendisi gösterir) |
| Zorunlu | **Gizli depoya erişim** (aşağıda) | Depo herkese açık değil; yalnız seçilen kişiler erişir |
| Önerilen | [Obsidian](https://obsidian.md) | Kasanı görsel olarak gezmek için (ücretsiz) |
| Önerilen | Claude Code (Pro/Max abonelik) | Derin derleme, MCP ve oturum hafızası için |
| İsteğe bağlı | Ollama ve ekran kartı | Yerel yapay zekâ modeli. Sihirbaz kurulumunu da yapar ([Modeller ve ses](05-modeller-ses.md)) |
| İsteğe bağlı | Google hesabı | Gmail/Takvim/Rehber/Drive için ([Hesaplar](03-hesaplar.md)) |

> **Önemli (Windows):** Kasayı **kısa bir klasör yoluna** koy (ör. `C:\SB`) ve **OneDrive içine koyma**. Uzun yol Windows'un 260 karakter sınırına takılır, OneDrive ise dosyaları kilitleyebilir. Sihirbaz bu iki durumda seni uyarır. Bkz. [Sorun giderme](11-sorun-giderme.md#yol-uzunlugu-260).

## Adım 1 — Depoya erişim al (gizli depo)

Second Brain'in kurulum dosyaları **gizli (private) bir GitHub deposunda** durur; herkes indiremez. Ürünün sahibi erişim verdiği kişileri «collaborator» olarak ekler.

1. https://github.com adresinde ücretsiz bir hesabın yoksa **Sign up** ile aç. (E-posta doğrulaması gerekir.)
2. GitHub **kullanıcı adını** ürünün sahibine ilet.
3. Sahibi seni depoya ekleyince GitHub'dan **e-posta daveti** gelir. E-postadaki **View invitation** → **Accept invitation** düğmesine bas. (Davet e-postası gelmezse https://github.com/notifications ya da profil menüsünden davetleri kontrol et. Düğme adları GitHub'ın arayüzüne göre değişebilir.)
4. Daveti kabul ettikten sonra depo sayfasını görebiliyorsan erişimin tamamdır.



<a id="gh-auth-login"></a>

## Adım 2 — GitHub ile oturum aç (`gh auth login`)

Gizli depodan indirme yapabilmek için bilgisayarda GitHub'a giriş yapılmış olmalıdır. İki yöntemden birini kullan:

### Yöntem A (önerilen): GitHub CLI

1. Windows'ta **PowerShell** aç (Başlat'a `PowerShell` yaz → **Windows PowerShell**). macOS'ta **Terminal**.
2. GitHub CLI'ı kur:
   - Windows: `winget install GitHub.cli` (kurulum bitince PowerShell'i kapatıp yeniden aç)
   - macOS: `brew install gh` (Homebrew kuruluysa)
3. `gh auth login` yaz → Enter. Sorulara şunları seç (oklarla gezip Enter):
   - *What account do you want to log into?* → **GitHub.com**
   - *What is your preferred protocol for Git operations?* → **HTTPS**
   - *Authenticate Git with your GitHub credentials?* → **Yes**
   - *How would you like to authenticate GitHub CLI?* → **Login with a web browser**
4. Ekranda 8 karakterli bir **tek kullanımlık kod** çıkar → Enter'a basınca tarayıcı açılır → kodu yapıştır → **Authorize** de.
5. Terminalde `✓ Logged in as <kullanıcı adın>` görünce bitti. Doğrulamak için: `gh auth status`.

(Soru metinleri `gh` sürümüne göre biraz farklı olabilir; resmi yardım: https://cli.github.com/manual/gh_auth_login)

### Yöntem B: kişisel erişim belirteci (`SB_GH_TOKEN`)

`gh` kurmak istemiyorsan GitHub'da **Settings → Developer settings → Personal access tokens** bölümünden **yalnız depo okuma izinli** bir belirteç üretebilirsin (menü adları sürüme göre değişebilir). Sonra komutu çalıştırmadan önce belirteci ortam değişkenine koy:

- Windows PowerShell: `$env:SB_GH_TOKEN = "<belirteç>"`
- macOS/Linux: `export SB_GH_TOKEN="<belirteç>"`

(`GITHUB_TOKEN` adı da kabul edilir.) **Belirteci kimseyle paylaşma, sohbete yapıştırma, bir dosyaya kaydetme.** Kurulum bitince belirteci GitHub'dan silebilirsin.

## Adım 3 — Tek satırlık komutu çalıştır

Tam komut (depo adresi gizli olduğu için) ürünün sahibi tarafından sana verilir; şu biçimdedir.

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/<hesap>/second-brain-kit/main/install.ps1 | iex
```

**macOS (Terminal):**

```bash
curl -fsSL https://raw.githubusercontent.com/<hesap>/second-brain-kit/main/install.sh | sh
```

(`<hesap>` yerine sana verilen GitHub hesap adı gelir.) Betik sırayla şunu yapar:

1. `gh` kuruluysa **son sürümü** onunla indirir; değilse `SB_GH_TOKEN`/`GITHUB_TOKEN` ile GitHub API'yi dener.
2. Windows'ta kurulum dosyasını **masaüstüne** `Second Brain Setup.exe` adıyla koyar ve açar. macOS'ta `Second Brain Setup.app` masaüstüne kopyalanır ve açılır.
3. İkisi de yoksa ne yapman gerektiğini yazar (aşağıdaki «Olmazsa»).



### Olmazsa (indirme yapılamadı)

Betik `Setup indirilemedi` benzeri bir mesaj verirse üç yol sunar:

1. GitHub CLI kur ve giriş yap, sonra komutu yeniden çalıştır (Adım 2, Yöntem A).
2. Belirteçle: `$env:SB_GH_TOKEN='...'` yazıp komutu yeniden çalıştır (Adım 2, Yöntem B).
3. Elle indir: depo sayfasında **Releases → Latest** altından `Second-Brain-Setup...exe` (macOS için `.zip`) dosyasını indir. İndirdiğin dosyayı masaüstüne koyup çift tıkla.

Bu üçü de olmuyorsa betik **kaynak koddan kurulum** (uv + panel) denemesine geçebilir; bu ileri düzeydir, [Sorun giderme](11-sorun-giderme.md) bölümüne bak.

Gelişmiş betik seçenekleri (çoğu kullanıcı için gerekmez): `--source` (kaynak koddan panel), `--cli` (eski soru-cevap kurucusu). Ortam değişkenleri: `SB_REPO`, `SB_GH_TOKEN`, `SB_DIR`.

<a id="ilk-acilis-uyarilari"></a>

## Adım 4 — İlk açılış uyarıları

Kurulum dosyası **imzasızdır** (kod imzalama sertifikası alınmamıştır). Bu yüzden işletim sistemi ilk açılışta uyarır; bu **beklenen ve normal** bir durumdur. Dosyayı yalnız ürünün sahibinin verdiği yoldan indirdiysen devam et.

### Windows: «Windows bilgisayarınızı korudu»

1. Mavi bir pencere çıkar: **Windows bilgisayarınızı korudu** (Microsoft Defender SmartScreen).
2. Pencerede **Ek bilgi** (More info) yazısına tıkla.
3. Altta **Yine de çalıştır** (Run anyway) düğmesi belirir → tıkla.
4. Kullanıcı Hesabı Denetimi (UAC) sorarsa **Evet**. (Kurulum yönetici yetkisi gerektirmeyebilir; sorarsa vermen yeterli.)



Düğme hiç görünmüyorsa: dosyaya sağ tık → **Özellikler** → altta **Engellemeyi kaldır** (Unblock) kutusunu işaretle → **Uygula**. Antivirüs yazılımı dosyayı karantinaya aldıysa dosyayı güvenilir olarak işaretle (yazılıma göre değişir).

### macOS: «açılamıyor» uyarısı (Gatekeeper)

Betik macOS'ta karantina işaretini kaldırmaya çalışır; yine de uyarı çıkarsa:

1. `Second Brain Setup.app` üzerine **sağ tık (ya da Control + tık) → Aç**.
2. Çıkan pencerede yine **Aç**'a bas.
3. Hâlâ açılmıyorsa: **Sistem Ayarları → Gizlilik ve Güvenlik** → aşağıda «Second Brain Setup engellendi» satırındaki **Yine de Aç** düğmesi. (Menü adları macOS sürümüne göre değişir; Apple yardımı: https://support.apple.com/102445)



## Adım 5 — Sihirbaz açıldı

Birkaç saniye içinde **Second Brain Kurulum** adlı pencere (1100×760) açılır. Pencere açılmazsa kurulum adresini tarayıcıda açar; terminalde adres yazar ve «Kapatmak için Ctrl+C» der. Panel yalnız bu bilgisayarda (127.0.0.1) çalışır ve oturuma özel bir jetonla korunur; başka bir cihazdan erişilemez.

Sonrası: [02 · Sihirbaz adım adım](02-sihirbaz-adim-adim.md).

## Deneme kipi (gerçek sisteme dokunmadan dene)

Sihirbazı **önce denemek** istersen: şifreler, zamanlanmış görevler, kısayollar, otomatik başlatma, MCP, Ollama ve Google girişi **gerçek sisteme dokunmadan** ayrı bir klasöre yazılır. Üstte **DENEME KİPİ — gerçek sisteme dokunulmuyor** çubuğu görünür ve özette «deneme» yazar.

- Setup uygulamasını komut satırından aç: `"Second Brain Setup.exe" --sandbox C:\sb-deneme` (macOS'ta aşağıdaki ortam değişkeni yolunu kullan).
- Ya da **ortam değişkeni**: `SB_SETUP_SANDBOX=C:\sb-deneme` (PowerShell: `$env:SB_SETUP_SANDBOX = "C:\sb-deneme"`; sonra uygulamayı aynı pencereden aç).
- Deneme bitince o klasörü silmen yeter; sisteminde iz kalmaz.

Deneme kipinde sihirbazın her ekranını gerçek kurulumla aynı şekilde gezebilirsin; sadece gerçek hesaplara bağlanılmaz.

<a id="kurulum-sirasinda-ne-olur-adim-12de"></a>

## Kurulum sırasında ne olur? (Adım 12'de)

Son adımda **Kur**'a basınca motor şu işleri sırayla yapar ve canlı ilerleme gösterir:

| Sıra | Adım | Ne yapar |
|---|---|---|
| 1 | Kasa ve kod | Kasa klasörünü şablondan oluşturur, kodu kopyalar |
| 2 | Ayarlar | Ayar dosyalarını yazar (profil, hesaplar, özellikler) |
| 3 | Sırlar (şifre kasası) | Girdiğin şifre/anahtarları işletim sistemi şifre kasasına yazar |
| 4 | Python ortamı | `uv` ile Python ortamını kurar (en uzun adımlardan biri) |
| 5 | Claude Code bağlantısı | MCP ve hafıza kancalarını bağlar |
| 6 | Yerel model | Seçtiğin modeli indirir |
| 7 | Zamanlayıcı | Günlük/haftalık görevleri (yalnız sorduğunda) kurar |
| 8 | Kasa git deposu | Kasayı sürümlemek için git deposu açar |
| 9 | Kontrol | `sb doctor` ile her şeyi denetler |
| 10 | Kısayollar | Masaüstü/Başlat menüsü kısayolları |

Bir adım hata verirse kırmızı bir **Kurulum durdu** kartı çıkar: **Ne oldu** ve **Nasıl düzeltilir** yazar. Düzelttikten sonra **Yeniden dene**'ye bas: biten adımlar tekrarlanmaz, kurulum kaldığı yerden sürer. Her hatanın çözümü: [Sorun giderme](11-sorun-giderme.md).

## Kurulumdan sonra

1. Sihirbazın son ekranında **Uygulamayı aç** → ana pencere açılır. **Turu göster** ile 5 adımlık hızlı tura bak.
2. Masaüstündeki **Second Brain** kısayolundan istediğin zaman açarsın.
3. Her gün **Çalışmaya başla** düğmesine bas ([Uygulama turu](08-uygulama-turu.md)).
4. İstersen kasa klasörünü Obsidian'da aç: Obsidian → **Open folder as vault** (Kasa olarak klasör aç) → kasa klasörünü seç.

<a id="kaldirma"></a>

## Kaldırma

Sihirbazın/ayarların **Kaldır** sekmesi önce bir **plan** gösterir (ne silinecek), sen onay kutusunu işaretleyip **Temiz kaldır**'a basana kadar hiçbir şey yapılmaz. Zamanlanmış görevler kaldırılır, kod çöp kutusuna taşınır; **kasa notlarına dokunulmaz**. Sırların listesi de gösterilir.
