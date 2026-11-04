# 00 · Başlangıç: Second Brain nedir?

Bu bölüm ürünü tanıtır: ne işe yaradığını, verilerinin nerede durduğunu, nelere asla dokunmadığını ve rehberin nasıl okunacağını anlatır. Kurulum için [01 · Kurulum](01-kurulum.md) bölümüne geç.

## Tek cümleyle

**Second Brain, bilgisayarında çalışan, seni tanıyan bir «ikinci beyin» ve kişisel asistandır.** Mailini, takvimini, notlarını, belgelerini, mesajlarını, okul ve proje dosyalarını tek bir klasörde (**kasa**) toplar, birbirine bağlar ve her gün kendiliğinden günceller. Üstüne bir **sohbet asistanı** oturur: ona «bu hafta neyim var?», «geçen ay fatura mailleri hangileri?» ya da «cuma 15:00'e doktor randevusu ekle» dersin.

## Ne işe yarar? (somut örnekler)

| Sorun | Second Brain ne yapar |
|---|---|
| Mailler, SMS'ler, belgeler dağınık | Hepsini yerel bir arşive alır; tek aramayla bulursun |
| Teslim ve randevu tarihleri kaçıyor | Maillerden tarih çıkarır, emin olamadığını sana **onaya** sunar, onayladığını takvime ekler |
| «Bunu geçen ay kimle konuşmuştum?» | Kişi, proje ve konu notlarını birbirine bağlar; anlam araması yapar |
| Her sabah dağınık başlamak | Sabah özeti: takvim, yaklaşan teslimler, önemli mailler |
| Yapay zekâ asistanı her seferinde sıfırdan başlıyor | Claude Code'a **hafıza** verir: kurallarını, açık işlerini ve son oturum özetini her oturumun başında hatırlatır |
| Telefonda da erişmek | Telefondan aynı asistana güvenli bağlanırsın (Tailscale) |

Ürünün 250 maddelik özellik kataloğu vardır; bunların hepsi [Özellik kataloğu](17-ozellik-katalogu.md) sayfasında tek tek anlatılır. Özellikler **50 modülde** toplanır ([Modüller](16-moduller.md)); istemediğini kapatırsın.

## Kim için?

Öğrenci, ajans sahibi/freelancer, yazılımcı, akademisyen, girişimci, satış/CRM çalışanı, içerik üreticisi, araştırmacı. Kurulumdaki **hazır seçim** bu meslekler için uygun bir başlangıç listesi hazırlar ([Hazır seçimler](15-hazir-secimler.md)). Teknik bilgi gerekmez; bu rehber her adımı «şuna tıkla → şunu gör» biçiminde anlatır.

## Parçalar: neyi ne zaman göreceksin?

1. **Kurulum sihirbazı** (`Second Brain Setup.exe` / `.app`): bir kerelik, 12 adımlı kurulum. Bkz. [Sihirbaz adım adım](02-sihirbaz-adim-adim.md).
2. **Masaüstü uygulaması** (`Second Brain.exe` / `.app`): günlük kullandığın pencere. Sohbet, bütün ekranlar, ayarlar, **Çalışmaya başla** düğmesi. Bkz. [Uygulama turu](08-uygulama-turu.md).
3. **Kasa** (bir klasör): notların. Bunu **Obsidian** adlı ücretsiz not uygulamasıyla da açıp gezebilirsin (isteğe bağlı ama önerilir).
4. **Komut satırı** (`sb ...`): ileri kullanım ve sorun giderme için. Günlük kullanımda gerekmez. Bkz. [Komut referansı](14-komut-referansi.md).
5. **Claude Code / Claude Desktop bağlantısı (MCP)**: yapay zekâ asistanlarının kasanı okumasını sağlar. Bkz. [MCP](06-mcp.md).

## Gizlilik ilkeleri

Bunlar ürünün değişmez kurallarıdır:

1. **Verin bu bilgisayarda kalır.** Notlar kasa klasöründe, ham arşiv (mail, SMS, dizin) senin kullanıcı klasöründeki `.secondbrain` içinde durur. Hiçbir şey bir Second Brain sunucusuna gönderilmez; böyle bir sunucu yoktur.
2. **Şifreler ve API anahtarları yalnız işletim sisteminin şifre kasasında** (Windows Kimlik Bilgisi Yöneticisi, macOS Anahtar Zinciri; `keyring`) saklanır. Ayar dosyasında, kasada, günlükte ya da bu rehberde yer almaz.
3. **Mail salt okunurdur.** Aşağıda ayrıca anlatılıyor.
4. **Silme ve gönderme her zaman senin onayınladır.** Kalıcı silme yoktur: «silinen» her şey `90-Arşiv`e taşınır; kasa ayrıca git ile sürümlenir, geri alınabilir.
5. **Bulut modeli kullanmak tamamen isteğe bağlıdır.** «Tam yerel» seçersen hiçbir istek buluta gitmez ([API anahtarları](04-api-anahtarlari.md#tam-yerel-ne-demek)).
6. **Bulut kullansan bile süzgeç vardır:** API anahtarı, şifre, doğrulama kodu, kart/IBAN/TCKN buluta gitmeden maskelenir; `gizli` işaretli notlar hiç gitmez ([Güvenlik ve gizlilik](10-guvenlik-gizlilik.md)).
7. **Otomatik başlatma yalnız senin «evet»inle** kurulur. Sihirbazda sorulur; seçmezsen hiçbir şey eklenmez.

## Mail salt okunur garantisi

- **Gmail:** Google'a yalnız `gmail.readonly` izni istenir. Bu izinle mail **silinemez, gönderilemez, taşınamaz, okundu işaretlenemez**; teknik olarak yapılamaz.
- **IMAP hesapları** (Outlook, iCloud, Yandex, okul/şirket): yalnız okunup yerel arşive kopyalanır; sunucudaki posta kutuna yazılmaz.
- **Takvim:** `calendar.events` izni ile etkinlik eklenebilir; ama asistan bunu **her zaman onay kartıyla** yapar (hangi profil olursa olsun).
- **Sabah özeti maili:** isteğe bağlı; yalnız **senin kendi adresine** gönderilir (şirket SMTP'si tanımlıysa). Başkasına mail gönderen bir özellik yoktur.
- Bir mail içinde «şunu sil/şuna cevap yaz» gibi yönergeler olsa bile asistan bunları **komut olarak almaz** (istem enjeksiyonu kalkanı, bkz. [Güvenlik ve gizlilik](10-guvenlik-gizlilik.md)).

## Hangi veri nerede?

| Ne | Nerede | Not |
|---|---|---|
| Notların (Markdown) | **Kasa klasörü** (sihirbazda seçtiğin; varsayılan konum sihirbazda yazar) | Obsidian ile açılır, git ile sürümlenir |
| Mail/SMS/Drive ham arşivi, beyin dizini | Kullanıcı klasöründe **`.secondbrain`** (`mail.db`, `brain.db` …) | Git'e ve telefona girmez |
| Google istemci dosyası | `.secondbrain/secrets/client_secret.json` | Kasanın dışındadır, kasaya/GitHub'a gitmez |
| Şifreler, API anahtarları, belirteçler | İşletim sistemi şifre kasası (anahtarlık) | Hizmet adı `second-brain` |
| Yedekler | `.secondbrain/backups` | [Güvenlik ve gizlilik](10-guvenlik-gizlilik.md) |
| İçe aktarma dosyaları (geçici) | `.secondbrain/import_staging` | Yüklediğin dışa aktarma dosyaları |
| Günlükler / çökme raporları | `.secondbrain/logs`, `.secondbrain/crashes` | `sb logs` gösterir |
| Ses kayıtları | `.secondbrain/audio` | Notlara yalnız döküm (yazıya çevrilmiş metin) girer |

Kasanın klasörleri:

| Klasör | İçinde ne var |
|---|---|
| `00-Inbox` | İşlenmemiş her şey; `onay-bekleyenler.md` (emin olunamayan tarihler); `_imports` (dış arşivler) |
| `10-Dersler` | Her ders bir klasör; ders ve teslim notları |
| `20-Projeler` | Aktif/pasif projeler; «Proje dosyası» otomatik derlenir |
| `25-Görevler` | `sb task` ile açılan görevler |
| `30-Kariyer` | Başvurular ve görüşmeler |
| `40-Kaynaklar` | Mail/Drive indeksleri, içe aktarılan kaynaklar, kavram notları |
| `50-Günlük` | Günlük notlar (`YYYY-AA-GG.md`) |
| `60-Kişiler` | Kişi başına bir not |
| `90-Arşiv` | Biten/silinen her şey (silme yok, taşıma var) |
| `_templates`, `_system` | Şablonlar; motorun kendisi |

> Not: klasör adları kurulumda şablondan gelir; ürün sürümüne göre küçük farklar olabilir.

## Ne yapmaz?

- Başka biri adına mail/mesaj **göndermez** (WhatsApp ve takvim dahil her dış etkili eylem onay kartıyla gelir).
- Banka/hesap/kart numarası **saklamaz** (banka ekstresi içe aktarıcısı bunları dışarıda bırakır).
- Giriş/banka/e-Devlet sayfalarını tarayıcı geçmişinden **okumaz**.
- Bilgisayarında «kendi kendine» tehlikeli komut çalıştırmaz: komutlar sınıflanır, riskli olanlar yalnız bilgisayarda onayla çalışır.
- Telefon üzerinden güvenlik profilini **değiştiremezsin**; komut ve WhatsApp kartları yalnız bilgisayardan onaylanır.

<a id="surum-ve-guncelleme"></a>
## Sürüm ve güncelleme

- Kurulu sürüm: `sb version`. Yenilikler: `sb whatsnew`.
- Güncelleme: uygulamada **Çalışmaya başla** (ya da **Ayarlar → Güncelle**) yeni sürüm olup olmadığına bakar; komutla `sb update --check`, sonra `sb update`. Güncelleme notlarına ve ayarlarına **dokunmaz**; önce yedek alır; sorun olursa `sb update --rollback` ile geri dönersin.
- Bu rehber 1.0 sürümü içindir; üretici `tools/build_guide.py` rehberi manifestlerden yeniden çıkarır, böylece özellik listesi ile rehber birbirinden kopmaz.

## Bu rehberi nasıl okuyacaksın?

- Sırayla: 00 → 01 → 02 → 03 → … Kurulumdan önce sadece 00–02 yeter.
- **Sihirbazda bir ekranda takıldın:** [02 · Sihirbaz adım adım](02-sihirbaz-adim-adim.md) her alanı ve düğmeyi anlatır.
- **Bir hesap bağlayamıyorsun:** [03 · Hesaplar](03-hesaplar.md).
- **Hata mesajı aldın:** [11 · Sorun giderme](11-sorun-giderme.md) ve [12 · Sık sorulanlar](12-sss.md).
- **Bir kelimeyi bilmiyorsun:** [13 · Sözlük](13-sozluk.md).
- **Belirli bir özelliği arıyorsun:** [Özellik kataloğu](17-ozellik-katalogu.md) ya da [Modüller](16-moduller.md).

### Ekran görüntüleri ve üçüncü taraf menüleri

Rehberde `![açıklama](img/...)` biçimindeki yerler ekran görüntüsü içindir. Google, Notion, Apple, LinkedIn gibi **üçüncü tarafların arayüzleri sürümden sürüme değişir**; rehberdeki menü adları bunların yazıldığı andaki hâlidir. Menü farklıysa o hizmetin resmi yardım sayfasına bak (adresler ilgili bölümlerde verilmiştir). Second Brain'in kendi ekranları ise koddan doğrulanmıştır.
