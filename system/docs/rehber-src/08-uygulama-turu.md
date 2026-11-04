# 08 · Uygulama turu: Second Brain penceresi, ekranlar, ayarlar, tepsi, telefon

Bu bölüm kurulumdan sonra günlük kullandığın **Second Brain uygulamasını** ekran ekran anlatır.

## Uygulamayı açmak

- **Masaüstü / Başlat menüsü kısayolu:** `Second Brain` (Windows `Second Brain.exe`, macOS `Second Brain.app`).
- Pencere 1280×820 boyutunda açılır, başlığı **Second Brain**'dir. İçinde yerel asistan sayfası (`http://127.0.0.1:8765/`) gösterilir.
- Açılışta asistan sunucusu çalışmıyorsa uygulama onu **kendi alt süreci** olarak başlatır; uygulamadan çıkınca durdurur. Zamanlanmış görevin zaten çalışan sunucusuna dokunmaz. 30 saniyede açılmazsa hata verir ([Sorun giderme](11-sorun-giderme.md#asistan-acilmiyor)).
- **Tek örnek:** uygulamayı ikinci kez açarsan yeni pencere açılmaz; açık olan öne gelir.
- Bilgisayar açılınca otomatik başlasın istiyorsan: **Ayarlar → Başlangıç** ([Sihirbaz Adım 11](02-sihirbaz-adim-adim.md)). Simge durumunda başlatma `--minimized` ile yapılır.

![Ana pencere: kenar çubuğu, sohbet alanı, üst çubuk](img/uygulama-ana-pencere.png)

## Tepsi simgesi

Pencereyi kapatınca uygulama **kapanmaz, tepside kalır** (tepsi kütüphanesi yüklüyse; yoksa kapanır). Simgeye sağ tıkla:

| Menü | Ne yapar |
|---|---|
| **Aç** (çift tık) | Pencereyi öne getirir |
| **Çalışmaya başla** | Güncelleme–sağlık–günlük iş sırasını başlatır ve pencereyi açar |
| **Ayarlar** | Ayarlar penceresini açar (1100×760) |
| **Çık** | Uygulamayı tamamen kapatır |

Windows'ta simge görev çubuğunun sağındaki gizli simgeler (⌃) içinde olabilir.

<a id="calismaya-basla"></a>

## Çalışmaya başla

Her gün (ya da bilgisayarı açınca) bir kez bas. Üst çubukta **Çalışmaya başla** düğmesi vardır (kenar çubuğundaki **Görünümler** menüsünde de **Çalışmaya başla** görünümü). Beş adım sırayla çalışır, her birinin süresi ve sonucu yazılır:

| Adım | Ne yapar |
|---|---|
| 1. **Güncelleme denetimi** | Yeni sürüm var mı bakar. Varsa «Güncelleme var: 0.9.8 → 0.9.9» kartı çıkar; **otomatik güncelle** ayarı açıksa kendisi (yedekli) günceller |
| 2. **Sağlık kontrolü** | `sb doctor` testlerini çalıştırır; sorun varsa «**Nasıl düzeltilir:**» ile çözümü yazar |
| 3. **Günlük işler** | Bugün çalışmadıysa arka planda günlük işleri çalıştırır (mail çekme, indeksleme, tarih çıkarma, özet…) |
| 4. **Modelleri ısıt** | Yerel modeli (Ollama, 30 dk bellekte tutulur) ve Whisper'ı belleğe yükler; ilk soru hızlı gelsin |
| 5. **Hazır** | Her şey tamam |

Durum işaretleri: **○** bekliyor · **…** çalışıyor · **✓** tamam · **!** uyarı · **✗** hata · **–** atlandı. Alt satır: «Çalışıyor…», «Bitti.» ya da «Bitti; sorunlar var.»

![Çalışmaya başla ekranı: beş adım ve durumları](img/uygulama-calismaya-basla.png)

## Ana ekran: sol kenar çubuğu

| Öğe | Ne yapar |
|---|---|
| **Yeni sohbet** | Boş bir sohbet açar (`/yeni` ile de) |
| **Sohbetlerde ara** | Eski sohbetleri süzer |
| **Sohbetler / Arşiv** sekmeleri | Aktif ve arşivlenmiş sohbetler |
| Sohbet listesi | Tıkla aç; sohbetler **Arşiv** sekmesine taşınabilir |
| **Görünümler** (açılır menü) | Aşağıdaki bütün ekranlar |
| **Görünüm ve cihazlar** | Tema, vurgu rengi, yazı boyutu, telefon eşleme, sunucu bilgisi |

Dar ekranda (telefon) kenar çubuğu menü düğmesiyle (☰) açılır/kapanır.

## Üst çubuk

| Düğme | Ne yapar |
|---|---|
| ← (Sohbete dön) | Bir görünümdeysen sohbete döner |
| Sohbet başlığı ve alt başlık | Konuşma adı, ne yaptığı |
| **Komut paleti (Ctrl+K)** | Not, kişi, proje, komut ya da sohbet ara (aşağıya bak) |
| **Telefon eşleme** | Eşleme kodu ve adresi gösterir (telefon erişimi açıksa) |
| **Tema** | Açık/koyu/sistem arasında geçer |
| **Bildirimler** (zil) | Bildirim listesi; **Hepsini okundu yap** |
| **Çalışmaya başla** | Yukarıdaki sıra |

## Komut paleti (Ctrl+K)

Ctrl+K (macOS: Cmd+K) → arama kutusu: «Not, kişi, proje, komut ya da sohbet ara...» Yazdıkça sonuçlar çıkar (ok tuşlarıyla gez, Enter ile aç, Esc ile kapat). **Yeni sohbet** gibi komutlar da burada.

## Sohbet alanı

- Mesaj kutusu: «Sor ya da söyle ( / komutlar )». Enter gönderir, Shift+Enter yeni satır.
- **/** yazınca komutlar listesi açılır (bkz. [Asistan kullanımı](09-asistan-kullanimi.md)).
- Kutunun solunda **Dosya ekle** (ataş) ve sağında **Sesle konuş** (mikrofon) ile **Gönder**.
- Dosyayı pencereye **sürükleyip bırak**: «Dosyayı bırak, mesaja eklensin».
- Giriş kutusu dışında **/** tuşu kutuya odaklanır.
- Cevabın altında **hızlı cevap çipleri** çıkabilir.

## Görünümler (ekranlar)

Kenar çubuğunda **Görünümler** menüsünden açılır. Her ekran bir modülün parçasıdır; modül kapalıysa o ekran görünmez/boş kalır.

| Ekran | Ne gösterir | Modül |
|---|---|---|
| **Pano** | «Bugün» (takvim), **Yaklaşan**, **Görevler**, **Son notlar**, **Durum** (gelen kutusu, sayılar), **Onay bekleyen**, öneriler | [Arayüz ve tasarım](moduller/ui_core.md) |
| **Bilgi grafı** | Notların birbirine bağlantı grafiği | [Arayüz ve tasarım](moduller/ui_core.md) |
| **Zaman çizelgesi** | Olayların zamansal akışı | [Arayüz ve tasarım](moduller/ui_core.md) |
| **Kişi**, **Proje** | Bir kişinin/projenin birleşik görünümü (`/kisi`, `/proje` ile) | [Arayüz ve tasarım](moduller/ui_core.md) |
| **Bilgi kartları** | Aralıklı tekrar kartları (`/kart`) | [Bilgi kartları](moduller/cards.md) |
| **Öğrenme yolları** | Öğrenme yolları ekranı (konu bazlı çalışma akışı) | [Arayüz ve tasarım](moduller/ui_core.md) |
| **Ortak günlük** | Senin ve asistanın ortak günlüğü | [Hafıza ve kişilik](moduller/memory_ui.md) |
| **Hafıza** | Asistanın hakkında bildikleri; düzenle/sil (silinen arşive taşınır); «Öğrendiğim aday tercihler» | [Hafıza ve kişilik](moduller/memory_ui.md) |
| **Ayarlar** | Görünüm, ses, asistan kişiliği | [Arayüz ve tasarım](moduller/ui_core.md) |
| **Hata panosu** | Çalışma hataları | [Arayüz ve tasarım](moduller/ui_core.md) |
| **Bugün planı** | «En önemli 3 iş», takvim boşluklarına bloklar, uyarılar, **Pomodoro**, «Bugün nasılsın?» | [Görev ve planlama](moduller/tasks_plan.md) |
| **Görev panosu** | Yapılacak / yapılıyor / bitti | [Görev ve planlama](moduller/tasks_plan.md) |
| **Dersler** | Ders listesi, notlar, sınav/teslim, **GANO** ve «Senaryo (ya olursa)» | [Okul](moduller/courses.md) |
| **Çalışma planı** | Sınav/teslimlere göre çalışma programı | [Okul](moduller/courses.md) |
| **Kariyer** | **Başvuru panosu**, gelir/gider ve vergi, müşteriler, saat takibi, sözleşmeler | [Kariyer ve iş](moduller/career.md) |
| **Çalışma araçları** | Kaynakça (APA/IEEE) ve çalışma yardımcıları | [Kariyer ve iş](moduller/career.md) |
| **İletişim** | **Cevap bekleyenler**, uzun süredir konuşulmayanlar, önemli tarihler, son aramalar, bülten temizliği önerisi (yalnız öneri) | [İletişim yardımcıları](moduller/comms.md) |
| **Taslaklar** | Mail taslağı (**gönderilmez**), mail zinciri özeti, çeviri | [İletişim yardımcıları](moduller/comms.md) |
| **Yaşam** | Harcama, hediye fikirleri, okuma/izleme listesi, ruh hali, sağlık (yalnız yerel), öneriler | [Kişisel yaşam](moduller/life.md) |
| **Otomasyonlar** | Kurallar (her X olduğunda Y), **Yeni kural**, **Bekleyen onaylar** | [Otomasyonlar ve ajanlar](moduller/automation.md) |
| **Ajanlar**, **Ajan izleme** | Hazır ajanlar, çalışmalar, onay bekleyen değişiklikler, **Gece raporu**, kod ajanı (yalnız gece listesine ekler) | [Otomasyonlar ve ajanlar](moduller/automation.md) |
| **Gizlilik** | **Veri nerede?**, **Buluta giden**, **İzin profili**, **Denetim günlüğü**, **Yedekler** | [Gizlilik ve güvenlik](moduller/privacy.md) |
| **Çalışmaya başla** | Yukarıdaki beş adım | [Kurulum paneli](moduller/setup.md) |
| **Uygulama ayarları** | **Ayarları aç** düğmesi → Ayarlar penceresi | [Kurulum paneli](moduller/setup.md) |

> Ekran içerikleri sürümle gelişir; yukarıdakiler sürüm 0.9.x kodundan alınan başlıklardır.

## Görünüm ve cihazlar (kenar çubuğunun altı)

Açılır pencere: **Tema** (Sistem/Açık/Koyu), **Vurgu rengi** (Mavi, Yeşil, Turuncu, Mor, Kırmızı), **Yazı boyutu** (Küçük, Orta, Büyük, Çok büyük), **Telefon** (eşleme bilgisi), **Sunucu** (adres bilgisi). **Ayarlar** görünümünde ayrıca **Cevapları sesli oku**, **Ses** listesi, **Uyandırma sözcüğü** ve **Asistan kişiliği** bulunur.

## Ayarlar penceresi (Uygulama ayarları)

Açılış: **Uygulama ayarları → Ayarları aç** (ya da tepsi → **Ayarlar**). Ayrı pencere açılır. Sekmeler:

| Sekme | İçeriği |
|---|---|
| **Özellikler** | Modül ve madde aç/kapa (sihirbaz 3. adımın aynısı) |
| **Hesaplar** | Google, IMAP, okul, diğer hizmetler; bağlı hesaplar ve **Kaldır** |
| **Anahtarlar** | Bulut API anahtarları |
| **Modeller** | Donanım, Ollama, model indirme, ses |
| **MCP** | Hazır MCP'ler, kendi MCP'n |
| **Veri yükleme** | Dışa aktarma dosyalarını içe aktar |
| **Telefon** | Tailscale durumu, adres, eşleme kodu |
| **Başlangıç** | Otomatik açılış, simge durumunda başlatma |
| **Güncelle** | **Mevcut sürüm**, **Son sürüm**, **Denetle**, **Güncelle**; «Güncelsin.» / «Yeni sürüm var.» |
| **Sağlık** | **Sağlık kontrolü** düğmesi; her testin ✓/!/✗ sonucu ve ipucu |
| **Kaldır** | Önce plan, sonra onay, sonra **Temiz kaldır** (kasa notlarına dokunmaz) |
| **Günlük** | Kurulum/işlem günlüğü; **Yenile** |

![Ayarlar penceresi sekmeleri](img/uygulama-ayarlar.png)

## Onay kartları

Takvime etkinlik eklemek, komut çalıştırmak, bir şeyi unutmak, WhatsApp taslağı, mail/SMS taslağı gibi **dış etkili** işlerde sohbette bir **onay kartı** çıkar: üstte tür («Takvim · onay gerekli», «Komut · onay gerekli», «Unutma», «Silme», «Mail», «WhatsApp», «SMS», «Not»), altında ne yapılacağı ve **Onayla** / **İptal** düğmeleri. Onaylayınca «Onaylandı», iptalde «İptal edildi». Beklenen birden çok onay varsa çipte «Onayla (3 bekliyor)» yazar. Ayrıntı: [Asistan kullanımı](09-asistan-kullanimi.md#onay-kartlari).

<a id="telefon"></a>
## Telefon

Telefondan aynı asistana bağlanırsın; veri internete açılmaz.

### 1) Tailscale ile bağlan

[Tailscale kurulumu](03-hesaplar.md#hesap-tailscale)nu yap. Sonra bilgisayarda uygulamada üst çubuktaki **Telefon eşleme** düğmesi **Asistan adresi** ve 6 haneli **eşleme kodu** gösterir (düğme asistan sunucusu çalışırken görünür).

### 2) Telefonda aç ve eşle

1. Telefon tarayıcısında asistan adresini aç.
2. Eşleme kodunu gir. Bu cihaz «eşlenmiş» olur (cihaz çerezi).
3. Tarayıcı menüsü → **Ana ekrana ekle** (iOS: Paylaş → **Ana Ekrana Ekle**). Uygulama gibi açılır; arayüz çevrimdışı kabuk olarak önbelleğe alınır. **API yanıtları önbelleğe alınmaz** (özel veri).

### 3) HTTPS ve bildirimler (isteğe bağlı)

Ana ekran kurulumu ve anlık bildirim için **HTTPS** gerekir: Tailscale yönetim panelinde **MagicDNS** ve **HTTPS Certificates**'ı aç, bilgisayarda `tailscale serve --https=443 http://127.0.0.1:<sb-portu>` çalıştır; adres `https://<makine>.<tailnet>.ts.net` olur. Bildirim için sunucuda `pywebpush` kurulu olmalı (yoksa uygulama içi bildirim merkezi geçerlidir). iOS'ta bildirim yalnız ana ekrana eklenmiş uygulamada (iOS 16.4+) çalışır.

### 4) Telefondan paylaşma ve çevrimdışı kuyruk

- Android'de herhangi bir uygulamanın **Paylaş** menüsünde «İkinci Beyin» çıkar → metin/bağlantı önizleme sayfasına gider → **Beyne at**'a basmadan **kaydedilmez** (siteler arası form saldırısına karşı).
- iOS'ta **Kestirmeler** uygulamasıyla paylaşım hedefi kurulur (adres: `https://<adres>/share?text=<metin>`).
- Bağlantı yokken gönderilen mesaj ve paylaşımlar telefonda **kuyruğa** alınır («Kuyrukta N»), bağlantı gelince sırayla gönderilir.

### 5) Telefon güvenliği

- Telefondan gelen her **bilgisayar eylemi** onaya düşer.
- **İzin profili telefondan değiştirilemez**; **komut** ve **WhatsApp** kartları yalnız bilgisayardan onaylanır.
- Telefonu kaybedersen: eşleme kodunu yenile / Tailscale yönetim panelinden cihazı çıkar.

### 6) Kasayı telefonda Obsidian ile açmak (isteğe bağlı)

Kasa telefonda Obsidian ile açılıp okunabilir/düzenlenebilir. Ücretsiz yöntem **Syncthing**: bilgisayar açıkken cihazlar arası doğrudan eşitleme. Kısaca: Syncthing'i iki cihaza kur → cihazları kimlikle/QR ile eşle → kasa klasörünü paylaş → telefonda Obsidian ile **Kasayı klasör olarak aç**. Git klasörü ve Python ortamı eşitlemeye alınmaz. Aynı notu iki cihazda aynı anda düzenlersen `*.sync-conflict-*` dosyası oluşur; birleştirip birini sil. (Bu ileri düzey bir ek özelliktir; menü adları Syncthing'in sürümüne göre değişir: https://docs.syncthing.net)

### 7) SMS ve arama kayıtları (Android)

Android'de **SMS Backup & Restore** uygulaması mesajları Drive'a düzenli yedekler; Second Brain oradan okur. Adımlar: [SMS ve aramalar](kaynaklar/sms.md).

### 8) Dış erişim (Cloudflare Tunnel) — ileri düzey

Tailscale yerine internet üzerinden erişim isteyenler için hazırlanmış bir **plan** vardır; tünel kendiliğinden **başlamaz** ve **e-posta doğrulamalı erişim politikası** olmadan açılmaz. Ayrıntı: `docs/telefon-pwa.md`. Çoğu kullanıcı için gerekmez.

## Obsidian ile birlikte

Kasayı Obsidian'da aç (Obsidian → **Open folder as vault** → kasa klasörü). Obsidian'da yan panel eklentisi ve «Beyne at» için `_system/integrations` altındaki eklentiler elle kurulabilir. Obsidian Git eklentisi kasayı belirli aralıkla commit eder (10 dakika önerilir). Bu isteğe bağlıdır.

## Beyne at (Ctrl+Alt+B)

Panodaki bir bağlantı ya da metni (ya da ekran görüntüsünü) **Ctrl+Alt+B** ile kasaya kaydedersin (`sb capture`). Windows'ta bu kısayol kurulumda eklenen «Beyne at» kısayoluyla çalışır; yoksa `sb doctor` «Beyne at kısayolu» satırı ! gösterir. Ayrıca Gönder menüsünden **Beyne At**, tarayıcı eklentisi ve telefonda **Paylaş** kullanılabilir.
