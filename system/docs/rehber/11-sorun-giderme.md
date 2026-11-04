# 11 · Sorun giderme

Bu bölümdeki her kayıt **gerçek bir hata mesajına ya da durumuna** dayanır; mesajlar kodda geçtiği gibi alıntılanmıştır. Her kayıtta **Belirti → Neden → Çözüm** vardır.

## Önce şunu dene (30 saniye)

1. **Çalışmaya başla** düğmesine bas; **Sağlık kontrolü** adımı sorunun çoğunu «Nasıl düzeltilir» ile yazar.
2. Terminalde `sb doctor` çalıştır. ✓ hazır · ! isteğe bağlı/eksik (sistem çalışır) · ✗ çalışması için gerekli. Her ✗/! satırın sonunda ne yapılacağı yazar (aşağıda tablo).
3. Hâlâ takıldıysan `sb logs` son günlüğü ya da çökme raporunu gösterir; `sb logs --bundle` paylaşılabilir (sırları maskelenmiş) paket üretir.
4. Kurulum sırasında takıldıysan sihirbazın **Günlük** sekmesine bak.

## İçindekiler

- **Kurulum:** 1 SmartScreen · 2 macOS Gatekeeper · 3 Antivirüs · 4 İndirilemedi (gizli depo) · 5 gh girişi/davet · [6 Yol 260](#yol-uzunlugu-260) · 7 OneDrive · 8 Kasa kodun içinde · 9 Kasa yazılamıyor · 10 uv sync · 11 uv yok · 12 Şifre kasası · 13 Claude Code · 14 Model indirilemedi · 15 Zamanlayıcı · 16 Git · 17 Kısayol
- **Sihirbaz/uygulama:** 18 Oturum jetonu · 19 Sunucuya ulaşılamadı · 20 Başka iş sürüyor · 21 Pencere yerine tarayıcı · [22 Asistan açılmıyor](#asistan-acilmiyor) · 23 Port 8765 dolu
- **Hesaplar:** [24 Google giriş reddi](#google-giris-reddi) · 25 İstemci dosyası yok · 26 Yanlış hesap · 27 Giriş yok · [28 IMAP hataları](#imap-hata-mesajlari) · 29 Okul sistemi
- **Modeller/ses:** 30 Ollama · [31 Whisper GPU](#whisper-gpu) · 32 Bütçe doldu
- **Güncelleme:** 33 Yarım güncelleme · 34 git pull · 35 kit.json yok
- **Diğer:** 36 Telefon · 37 Sabah özeti · 38 Obsidian · 39 Beyne at kısayolu · 40 SMS yedeği eski · 41 Türkçe karakter · 42 İçe aktarma · 43 MCP · 44 Mac'te zamanlayıcı

---

## Kurulum sorunları

### 1. «Windows bilgisayarınızı korudu» (SmartScreen)

- **Neden:** Kurulum dosyası imzasız; Windows bilmediği yayıncıyı uyarır.
- **Çözüm:** **Ek bilgi → Yine de çalıştır.** Düğme yoksa dosyaya sağ tık → **Özellikler → Engellemeyi kaldır → Uygula**. Ayrıntı: [Kurulum](01-kurulum.md#ilk-acilis-uyarilari).

### 2. macOS: uygulama açılmıyor (Gatekeeper)

- **Çözüm:** Uygulamaya sağ tık → **Aç** → tekrar **Aç**. Olmazsa **Sistem Ayarları → Gizlilik ve Güvenlik → Yine de Aç**. Terminal yolu: `xattr -dr com.apple.quarantine "<uygulama yolu>"` (yalnız güvendiğin uygulama için).

### 3. Antivirüs dosyayı sildi/karantinaya aldı

- **Neden:** İmzasız yeni programlar yanlış alarm üretebilir.
- **Çözüm:** Antivirüsün karantina listesinden dosyayı geri al, klasörü istisna listesine ekle ya da dosyayı yeniden indir. Kaynağından emin değilsen çalıştırma; `SHA256SUMS` ile doğrula: `python setup/engine.py --verify <dosya> <sha256>`.

### 4. «Setup indirilemedi» (depo gizli)

- **Neden:** Betik GitHub'a giriş yapılmadığı için gizli depodan indiremedi.
- **Çözüm:** Üç yoldan biri: (1) `gh auth login` ([Kurulum → Adım 2](01-kurulum.md#gh-auth-login)); (2) `SB_GH_TOKEN` ortam değişkeni; (3) depo sayfasında **Releases → Latest**'ten dosyayı elle indir.

### 5. `gh auth status` «not logged in» ya da depo 404 veriyor

- **Neden:** Giriş yapılmamış ya da **collaborator davetini kabul etmemişsin** (GitHub gizli depoyu bulunamadı gibi gösterir).
- **Çözüm:** E-postadaki daveti kabul et (https://github.com/notifications); `gh auth login` ile doğru hesapla giriş yap; `gh auth status` ile doğrula.

### <a id="yol-uzunlugu-260"></a>6. Yol çok uzun (Windows 260 karakter) — «os error 3» / «path too long»

- **Belirti:** Python ortamı kurulurken `uv sync` hatası: `os error 3`, `failed to persist`, `path too long`. Sihirbaz: «Kasa yolu uzun (… karakter): Windows 260 karakter sınırı Python paketlerinin kurulumunu bozabilir.»
- **Neden:** Windows'un klasik yol sınırı. Python paketlerinin iç içe uzun dosya yolları, kasa uzun bir yolda olunca sınırı aşar.
- **Çözüm:** **Kişisel bilgiler** adımına dön, **Kısa yolu kullan** düğmesine bas (ör. `C:\SB`) ya da kasayı kısa bir klasöre kendin yaz; sonra **Yeniden dene**. Uzun yolları açmak istersen (yönetici gerekir): kayıt defteri `LongPathsEnabled` — ama kısa yol daha güvenlidir.

### 7. Kasa OneDrive içinde — kurulum yavaş/bozuk

- **Belirti:** «Kasa OneDrive klasörünün içinde: eşitleme dosyaları kilitleyebilir ve kurulumu yavaşlatır/bozar.»
- **Çözüm:** Kasayı OneDrive dışına (`C:\SB` gibi) al; kurulum hatası aldıysan **Yeniden dene**. Google Drive masaüstü senkronu için de aynı.

### 8. «Kasa kodun/kurulum paketinin içinde olamaz»

- **Neden:** Kasa klasörü olarak kurulum paketinin ya da kodun içindeki bir klasörü seçtin.
- **Çözüm:** Kişisel bilgilerde ayrı bir klasör seç (ör. belgelerin altında yeni klasör). Aynı kural «Deneme kasası kodun içinde olamaz» ve «Kasa kurulum paketinin içine kurulamaz» için geçerli.

### 9. «Kasa klasörüne yazılamıyor» (adım: Kasa ve kod / Ayarlar)

- **Neden:** Klasör yok, yazma iznin yok ya da disk dolu.
- **Çözüm:** Klasörün var ve yazılabilir olduğunu, diskte yer olduğunu kontrol et; gerekirse başka klasör seç; **Yeniden dene**.

### 10. «Python ortamı kurulamadı» / «uv sync başarısız»

- **Belirti:** Adım 4 (Python ortamı) hata verir; günlükte `uv sync başarısız: …`.
- **Nedenler ve çözümler:**
  - İnternet yok / VPN-proxy engeli → bağlantıyı kontrol et, VPN'i kapat. («İnternete ulaşılamadı» ipucu.)
  - Disk dolu → yer aç.
  - Yol çok uzun / OneDrive → bkz. 6 ve 7.
  - Kurumsal ağda paket indirme engeli → ağ yöneticisine sor ya da başka ağdan dene.
  - Antivirüs paket dosyalarını kilitliyor → klasörü istisna yap.
- **Sonra:** **Yeniden dene** (biten adımlar tekrarlanmaz).

### 11. «`uv` bulunamadı»

- **Neden:** Paketli kurulumda uv gömülüdür; kaynak koddan kurulumda sistemde uv yok.
- **Çözüm:** uv'yi kur (https://docs.astral.sh/uv/) ya da kurulum paketini yeniden indir; **Yeniden dene**.

### 12. «Şifre kasasına (keyring) yazılamadı» / «keyring yok»

- **Belirti:** Adım «Sırlar (şifre kasası)» hata verir. Mesaj: `keyring yok: sırlar dosyaya yazılmaz; uv sync sonrası bu adımı yeniden çalıştır`. MCP'de: «şifre kasası (keyring) yok».
- **Neden:** İşletim sistemi şifre kasası kullanılamıyor (Windows'ta Kimlik Bilgisi Yöneticisi servisi, macOS'ta Anahtar Zinciri kilitli, Linux'ta anahtar halkası yok). Sırlar **bilerek** düz dosyaya yazılmaz.
- **Çözüm:** Windows: `Windows Credential Manager`/`VaultSvc` servisinin açık olduğunu kontrol et; macOS: Anahtar Zinciri Erişimi'nde oturum anahtarlığını aç. Sorun sürerse sırları kurulumdan sonra uygulamadan gir; **Yeniden dene**.

### 13. «Claude Code bağlantısı kurulamadı»

- **Neden:** `claude` komutu yok (Claude Code kurulu değil) ya da MCP ekleme hatası.
- **Çözüm:** Claude Code'u kur (https://claude.com/code), terminali yeniden aç, **Yeniden dene**. Bu adım zorunlu değildir; sonra **MCP** sekmesinden de yapılır.

### 14. «Yerel model indirilemedi»

- **Neden:** Ollama kurulu/çalışır değil ya da internet yok.
- **Çözüm:** [Modeller ve ses](05-modeller-ses.md) bölümüne göre Ollama'yı kur/aç; modeli sonra **Modeller** sekmesinden indir.

### 15. «Zamanlayıcı kurulamadı» / `sb doctor`: «Zamanlanmış görev SecondBrain-Daily» !

- **Belirti:** Doctor `Zamanlanmış görev SecondBrain-Daily/Weekly/Chat` satırlarını ! gösterir; günlük işler kendiliğinden çalışmaz.
- **Neden:** Görev zamanlayıcıya görev eklenmemiş ya da izin verilmemiş (kurulumda sorulur; seçmediysen eklenmez).
- **Çözüm (Windows):** PowerShell'de `powershell -ExecutionPolicy Bypass -File <kasa>\_system\tools\schedule.ps1`. Görevler: `SecondBrain-Daily` (oturum açılışında + her gün 13:00), `SecondBrain-Weekly` (pazar 15:00), `SecondBrain-Chat` (asistan sunucusu, oturum açılışında). Görev Zamanlayıcı'yı (`taskschd.msc`) açıp görevleri kontrol edebilirsin. Yönetici izni gerekebilir.
- **Çözüm (macOS):** `python3 _system/tools/schedule_macos.py` (launchd görevleri `com.secondbrain.daily/weekly/chat`).
- Zamanlayıcıya hiç gerek yoksa **Çalışmaya başla** düğmesi günlük işleri kullanıcı açınca çalıştırır.

### 16. «Kasa git deposu oluşturulamadı»

- **Neden:** `git` kurulu değil. Zorunlu değildir.
- **Çözüm:** git'i kur (https://git-scm.com), **Yeniden dene**; ya da atla (geri alma için git önerilir).

### 17. «Kısayol oluşturulamadı»

- **Çözüm:** Masaüstü/Başlat menüsü klasörlerine yazma iznini kontrol et; **Yeniden dene**. Uygulamayı yine de kurulum klasöründen açabilirsin.

---

## Sihirbaz ve uygulama

### 18. «Oturum jetonu eksik: paneli kurulum penceresinden aç.»

- **Neden:** Sihirbaz adresini jetonsuz (ya da eski jetonla) tarayıcıda açtın.
- **Çözüm:** Sihirbazı yalnız **Second Brain Setup** penceresinden aç; adres `?t=` ile biten jetonu içerir.

### 19. «Kurulum sunucusuna ulaşılamadı.»

- **Neden:** Kurulum penceresi kapanmış ya da sunucu durmuş.
- **Çözüm:** Setup uygulamasını yeniden aç; yarım kalan kurulum varsa **Kaldığın yerden devam et**.

### 20. «Başka bir iş sürüyor; ilerlemeyi Günlük sekmesinde izle.»

- **Neden:** Aynı anda ikinci bir uzun iş (model indirme, kurulum…) başlatılamaz.
- **Çözüm:** Mevcut işin bitmesini bekle (**Günlük** sekmesi).

### 21. Pencere değil tarayıcı açıldı

- **Neden:** `pywebview` yoksa panel/uygulama varsayılan tarayıcıda açılır.
- **Çözüm:** Normal çalışır; adres sayfasını kapatma. Pencere istersen paketli uygulamayı kullan.

### <a id="asistan-acilmiyor"></a>22. Asistan açılmıyor / «Asistan sunucusu 30 sn içinde açılmadı»

- **Belirti:** Uygulama penceresi boş; `RuntimeError: Asistan sunucusu 30 sn içinde açılmadı`; `sb doctor`: «Asistan sunucusu (127.0.0.1:8765)» !.
- **Nedenler ve çözümler:**
  1. Python ortamı eksik/bozuk → `sb doctor`; kurulumu **Yeniden dene** ya da güncellemeyi `sb update --recover` ile tamamla.
  2. Port 8765 başka programda → bkz. 23.
  3. Yarım kalan güncelleme → `sb update --recover`.
  4. Elle başlat: terminalde `sb chat`; hata mesajını oku.
  5. Antivirüs/güvenlik duvarı yerel sunucuyu engelliyor → `python`/uygulamaya izin ver (yalnız 127.0.0.1 üzerinden).
- Sunucu açıldıktan sonra tarayıcıdan `http://127.0.0.1:8765/` adresini deneyebilirsin.

### 23. Port 8765 dolu

- **Belirti:** Sunucu başlamıyor; başka bir program 8765'i kullanıyor (ya da eski bir Second Brain süreci takılı kaldı).
- **Çözüm:** Windows: `netstat -ano | findstr :8765` → son sütundaki PID'yi `taskkill /PID <pid> /F` ile kapat (kendi `python.exe`/`pythonw.exe` Second Brain süreciyse). macOS: `lsof -i :8765` → `kill <pid>`. Sonra uygulamayı yeniden aç. Tek örnek koruması için kullanılan 8767 portu da doluysa uygulama «zaten açık» sanır; bilgisayarı yeniden başlatmak en hızlı çözümdür.

---

## Hesaplar

### <a id="google-giris-reddi"></a>24. Google giriş reddi

| Mesaj/belirti | Neden | Çözüm |
|---|---|---|
| Tarayıcıda **Erişim engellendi: Second Brain doğrulama sürecini tamamlamadı** (*access_denied*) | Uygulama «Testing» ve adresin **Test users** listesinde yok | Google Cloud → **Audience → Test users → Add users**; ya da **Publish app** |
| Her hafta yeniden giriş istiyor | Uygulama «Testing» durumunda (7 günde düşer) | **Publish app** |
| **Google bu uygulamayı doğrulamadı** | Normal; kendi uygulaman | **Gelişmiş → Second Brain'e git (güvenli değil)** |
| **redirect_uri_mismatch** | İstemci türü yanlış | **Desktop app** istemci oluştur, yeni JSON indir |
| **invalid_client** / **unauthorized_client** | JSON dosyası bozuk/yanlış proje | `client_secret.json`'u yeniden indir ve yükle |
| «API … has not been used in project / disabled» | Gmail/Takvim/People/Drive API etkin değil | **APIs & Services → Library**'den **Enable** |
| Giriş tamam ama «Bağlantı hatası» | Tarayıcı geri dönüşü engellendi | Yerel adres (`127.0.0.1`) engelleyen eklentiyi/VPN'i kapat, tekrar dene |
| `invalid_grant` / belirteç iptal | Parola değişti ya da erişim iptal edildi | `sb login <takma-ad>` ile yeniden giriş yap |

Google'ın hata metinleri ve menüleri zamanla değişir; anahtar sözcük (ör. *access_denied*) aynı kalır. Ayrıntı: [Hesaplar → Google](03-hesaplar.md#hesap-google).

### 25. «İstemci dosyası yok: …client_secret.json»

- **Neden:** Google için `client_secret.json` yüklenmemiş.
- **Çözüm:** Sihirbazda **Dosya seç…** ile yükle ya da dosyayı `.secondbrain/secrets/client_secret.json` olarak koy. (Mesajdaki «Rehber» bu rehberin Google bölümüdür.)

### 26. «Yanlış hesap: X ile giriş yapıldı, beklenen Y. Token kaydedilmedi.»

- **Neden:** Tarayıcıda başka bir Google hesabı açıkken izin verdin.
- **Çözüm:** Tarayıcıda doğru hesaba geç ya da gizli pencere kullan; `sb login <takma-ad>`'yi tekrarla.

### 27. «<takma-ad> için giriş yok. Çalıştır: … sb login <takma-ad>»

- **Çözüm:** Komutu çalıştır; tarayıcıdan izin ver. Doctor'da «Google girişi: <ad>» ✗ olarak görünür.

### <a id="imap-hata-mesajlari"></a>28. IMAP hata mesajları

Sihirbazın **Test et ve kaydet** düğmesi ve `sb mail-fetch` şu mesajları verir:

| Mesaj | Anlamı | Çözüm |
|---|---|---|
| «Kimlik reddedildi: kullanıcı adı ya da şifre yanlış. Gmail, iCloud ve Outlook'ta normal şifre değil UYGULAMA ŞİFRESİ gerekir (önce 2 adımlı doğrulamayı aç, sonra hesap ayarlarından uygulama şifresi üret).» | Giriş reddedildi | Uygulama şifresi üret ([Hesaplar → IMAP](03-hesaplar.md#hesap-imap)); kullanıcı adının tam e-posta olduğundan emin ol |
| «Güvenli bağlantı kurulamadı (sunucu:port). IMAP için genellikle port 993 (SSL) kullanılır; sunucu ve portu kontrol et.» | SSL/TLS hatası | Port 993; 143/STARTTLS desteklenmez |
| «Sunucu bulunamadı: … Sunucu adının yazımını ve internet bağlantını kontrol et.» | DNS çözülemedi | Yazım hatası/internet |
| «Bağlanılamadı: sunucu:port zaman aşımına uğradı. Sunucu/port yanlış olabilir ya da bir güvenlik duvarı engelliyor.» | Zaman aşımı | Port, güvenlik duvarı, VPN (kurum sunucusu ise kurum ağı) |
| «Bağlanılamadı: sunucu:port bağlantıyı reddetti. Sunucu adı ve port (genelde 993) doğru mu?» | Port kapalı | Sunucu/port |
| «Bağlanılamadı: sunucu:port. İnternet bağlantını, sunucu adını ve portu kontrol et.» | Genel ağ hatası | Bağlantıyı kontrol et |
| «IMAP girişi başarısız oldu. Sunucu, port ve şifreyi kontrol et.» | Bilinmeyen | Bilgileri tekrar gir |
| «Sunucu, kullanıcı ve şifre gerekli.» | Boş alan | Üç alanı da doldur |
| `[takma-ad] IMAP girişi başarısız: … Outlook/Microsoft 365 girişi reddedildi…` | Outlook özel ipucu | Kişisel hesapta IMAP açık + uygulama şifresi; **kurumsal M365'te şifreyle IMAP çoğunlukla kapalıdır, OAuth2 gerekir ve bu henüz desteklenmiyor** |
| `… iCloud girişi reddedildi. iCloud normal Apple Kimliği şifresiyle çalışmaz…` | iCloud özel ipucu | Uygulamaya özel şifre |
| `<takma-ad> şifresi yok. Çalıştır: … sb set-secret imap-<takma-ad>` | Şifre kasasında yok | Komutu çalıştır ya da sihirbazdan hesabı yeniden ekle |

Gmail için ek: IMAP erişimi hesap ayarlarında kapalı olabilir; 2 adımlı doğrulama kapalıysa uygulama şifresi seçeneği görünmez.

### 29. Okul sistemi (ÖBS/LMS) bağlanmıyor

- **Çözüm:** Adres tam yazıldı mı (`https://…`), kullanıcı adı/şifre doğru mu, okul VPN'i gerekiyor mu kontrol et. Okulun sistemi iki adımlı doğrulama ya da captcha istiyorsa otomatik giriş çalışmayabilir; ders notlarını `sb obs-import` ile `_system/data/obs.yaml` dosyasından elle yükleyebilirsin.

---

## Modeller ve ses

### 30. Ollama kurulu değil / ulaşılamıyor / açılmadı

- **Mesajlar:** `Ollama kurulu değil`, `Ollama N sn içinde açılmadı`, «Ollama'ya ulaşılamadı (ollama.com'dan kur)». Doctor: «Ollama (yerel model)» !.
- **Çözüm:** Ollama'yı kur ([Modeller ve ses](05-modeller-ses.md)); Başlat menüsünden aç; tarayıcıda `http://localhost:11434` adresi «Ollama is running» demeli. Modeller eksikse doctor `ollama pull <model>` önerir.

### <a id="whisper-gpu"></a>31. Whisper / ses: GPU ve kütüphane sorunları

| Belirti | Çözüm |
|---|---|
| `pip install faster-whisper` ipucu / `available: false` | **Sesi kur** ya da `sb voice --setup` |
| Hatada «cuda», «cudnn», «cublas» ya da «.dll» geçiyor | NVIDIA kütüphaneleri eksik. **Sesi kur**'u **NVIDIA GPU kütüphanelerini de kur** işaretli çalıştır. Hiçbiri yoksa Second Brain otomatik **işlemciye (CPU)** düşer; sadece yavaş olur |
| Ses çok yavaş | GPU yok → CPU. Daha küçük Whisper modeli (`base`/`tiny`) kullan (`config/asistan.yaml → voice.stt_model`) |
| Mikrofon çalışmıyor | Tarayıcı/uygulama mikrofon iznini ver; işletim sistemi ayarlarından mikrofonu aç |
| Transkript Türkçe değil | Dil otomatik algılanır; kısa/gürültülü kayıtta hata olabilir; sessiz ortamda tekrar dene |

### 32. «günlük bütçe doldu» / «aylık bütçe doldu»

- **Neden:** `config/llm.yaml` bütçe sınırı aşıldı; bulut çağrıları durur (yerel modeller etkilenmez).
- **Çözüm:** Sınırı artır ya da 0 yaz (sınırsız); iş yerel modele düşsün istiyorsan `fallback_to_local` açık olmalı. `sb usage` harcamayı gösterir.

---

## Güncelleme

### 33. `sb doctor`: «Yarım kalan güncelleme» ✗

- **Çözüm:** `sb update --recover` (kodu kitten yeniden kurar) ya da `sb update --rollback` (güncelleme öncesi yedeğe dön).

### 34. «git pull başarısız (kit klasöründe elle değişiklik mi var?)»

- **Çözüm:** Mesajın söylediği gibi `git -C <kit> status` ile bak; elle değiştirdiğin dosyaları geri al ya da yedekle.

### 35. «Bu kurulum kitten yapılmamış (kit.json yok)»

- **Neden:** Kaynak kasadan çalışıyorsun; güncelleme yalnız kit kurulumlarında geçerli.
- **Çözüm:** Normal kullanıcıysan setup ile yeniden kur; geliştiriciysen kiti `tools/build_kit.py` ile üret.

---

## Diğer sorunlar

### 36. Telefon bağlanamıyor

| Belirti | Çözüm |
|---|---|
| Telefon eşleme düğmesi yok | Asistan sunucusu çalışmıyor ya da Tailscale bağlı değil; bilgisayarda uygulama açık, Tailscale **bağlı** olmalı |
| Sayfa açılmıyor | İki cihazda da **aynı** Tailscale hesabı ve «bağlı» durum; adres doğru mu (`http://…:8765`) |
| «telefon dinleyicisi açılamadı: …» (günlük) | Telefon portu doluysa ya da Tailscale adresi değiştiyse; uygulamayı yeniden başlat |
| Ana ekrana ekle/bildirim çalışmıyor | HTTPS gerekir: `tailscale serve --https=443 …` ve Tailscale panelinde HTTPS Certificates |
| Eşleme kodu yanlış | Bilgisayardaki sayfada güncel kodu oku; kod yenilenmiş olabilir |
| `sb doctor`: «Telefon erişimi (isteğe bağlı, Tailscale)» ! | Henüz eşlenmemiş; [Telefon](08-uygulama-turu.md#telefon) |

### 37. Sabah özeti maili gelmiyor

- **Neden:** Özet maili isteğe bağlıdır; `accounts.yaml` içinde `notify.to` ve SMTP tanımlı değilse özet yalnız kasada (günlük notta) kalır. Doctor: «Sabah özeti maili» !.
- **Çözüm:** Tanımla; `sb notify-test` yalnız kendi adresine deneme mailidir. Zamanlayıcı yoksa özet **Çalışmaya başla** ile üretilir (bkz. 15).

### 38. Obsidian kasayı görmüyor

- **Çözüm:** Obsidian → **Open folder as vault** (Kasa olarak klasör aç) → kasa klasörünü seç. Doctor: «Obsidian kasası» !.

### 39. «Beyne at» kısayolu (Ctrl+Alt+B) çalışmıyor

- **Çözüm:** Windows: `powershell -ExecutionPolicy Bypass -File <kasa>\_system\tools\hotkey.ps1` (Başlat menüsüne «Beyne at» kısayolu ekler; kısayol tuşu o kısayola bağlıdır). Başka bir program aynı kısayolu kullanıyor olabilir.

### 40. SMS'ler eski

- **Neden:** Telefondaki yedekleme uygulaması durmuş (pil kısıtlaması, Drive oturumu düşmüş).
- **Çözüm:** [SMS kaynağı](kaynaklar/sms.md): telefonda **SMS Backup & Restore** zamanlanmış yedeği, pil tasarrufu «kısıtlama yok» ve otomatik başlatma açık olsun; `sb sms-sync` sonrası son SMS tarihi 2 günden eskiyse yedek durmuştur.

### 41. Türkçe karakterler bozuk (terminal)

- **Çözüm:** PowerShell'de `chcp 65001` yaz; `sb` komutları zaten UTF-8 çıktı üretir. Çıktıyı dosyaya alırken `-Encoding utf8` kullan.

### 42. İçe aktarma hataları

- Bkz. [Veri yükleme → Yaygın hatalar](07-veri-yukleme.md#yaygin-hatalar) ve ilgili kaynağın sayfasındaki **Sorun giderme** tablosu.

### 43. MCP hataları

- Bkz. [MCP → Sorun giderme](06-mcp.md#sorun-giderme).

### 44. macOS'ta zamanlayıcı çalışmıyor

- **Çözüm:** `python3 _system/tools/schedule_macos.py` ile `launchd` görevlerini kur; `launchctl list | grep secondbrain` ile `com.secondbrain.daily/weekly/chat` görünmeli.

---

## `sb doctor` satırları ne demek?

| Satır | Durum | Çözüm |
|---|---|---|
| Profil (config/profile.yaml) | ✗ | Kurulumu çalıştır / örnek dosyayı kopyala |
| Hesaplar (config/accounts.yaml) | ✗ | Sihirbazda hesap ekle |
| Ayar mail_rules / llm / local_files / course_files | ! | `*.example.yaml` dosyasından kopyala |
| Obsidian kasası | ! | Obsidian'da klasörü kasa olarak aç |
| Google OAuth istemcisi (client_secret.json) | ✗ | [Google rehberi](03-hesaplar.md#hesap-google) |
| Google girişi: <ad> | ✗ | `sb login <ad>` |
| IMAP şifresi: <ad> | ✗ | `sb set-secret imap-<ad>` |
| Yerel arşiv (mail.db) | ! | İlk `sb daily` ya da `sb mail-fetch <ad>` oluşturur |
| Ollama / Model … | ! | Ollama'yı kur; `ollama pull <model>` |
| API anahtarı: <sağlayıcı> | ! | `sb set-secret api-<sağlayıcı>` |
| Claude Code / MCP: second-brain / hafıza kancaları | ! | Claude Code'u kur; MCP'yi bağla; kurulumu yeniden çalıştır |
| Zamanlanmış görev … | ! | Bkz. 15 |
| Beyne at kısayolu | ! | Bkz. 39 |
| Asistan sunucusu (127.0.0.1:8765) | ! | Bkz. 22 |
| Spotify doğrudan çalma / Telefon erişimi / Codex / Kasa git deposu | ! | İsteğe bağlı |
| Yarım kalan güncelleme | ✗ | Bkz. 33 |

## Hâlâ çözülmediyse

1. `sb logs --bundle` ile paylaşılabilir paket üret (sırlar maskelenir).
2. Ürünün sahibine paketi, ne yapmaya çalıştığını ve hata mesajını ilet. **Şifre, anahtar ya da `client_secret.json` gönderme.**
3. Bu rehberde bulamadığın mesajlar için [Sık sorulanlar](12-sss.md) ve [Sözlük](13-sozluk.md) sayfalarına bak.
