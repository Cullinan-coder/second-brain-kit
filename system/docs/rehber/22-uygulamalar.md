# 22 · Uygulamalar: ClipBoardLine ve Nashi

Second Brain iki hazır, açık kaynak (MIT) uygulamayı **olduğu gibi** kurup beynine bağlayabilir. Biz bu uygulamaları yeniden yazmadık; yazarlarının **resmî sürümleri** indirilir, doğrulanır ve kurulur. İstersen hiç kurma: bölüm tamamen isteğe bağlıdır.

| Uygulama | Ne işe yarar | Boyut | Veri nerede? |
|---|---|---|---|
| **ClipBoardLine** | Kopya geçmişi: kopyaladığın metin, bağlantı ve görseller raflarda durur; ara, sabitle, etiketle, klasörle; görsellerdeki yazı OCR ile okunur | ~520 MB | Windows: `%APPDATA%\ClipBoardLine\library.json` |
| **Nashi** | Dosya dönüştürme, sıkıştırma ve düzenleme araçları; son 50 dışa aktarımın kaydı tutulur | ~91 MB | Windows: `%LOCALAPPDATA%\Nashi\library.json` |

Kaynak kodları (değiştirilmemiş kopya, lisansları ve kaynak commit'iyle) kit deposunda `apps/clipboardline/` ve `apps/nashi/` klasörlerindedir; her birinde `UPSTREAM.md` vardır.

## Kurulum

1. Kurulum sihirbazında **Başlangıç** adımına gel (ya da Ayarlar'da **Başlangıç** sekmesine). Uygulama içindeki **Çalışmaya başla** görünümünün altındaki **Uygulamalar** kartı durumu gösterir; kurulumu sihirbaz ya da komut yapar.
2. **Hazır uygulamalar** bölümünde uygulamanın kartındaki **Kur** düğmesine tıkla. İlerleme çubuğu altta görünür.
3. Arka planda şunlar olur: resmî sürüm GitHub'dan (yalnız `github.com/orkunisitmak/...` adresinden) indirilir → sürümdeki `SHA256SUMS` dosyasıyla **SHA-256 karşılaştırılır** (uyuşmazsa dosya silinir ve kurulum durur) → ClipBoardLine sessiz kurulumla (`/S`, yalnız senin kullanıcın için) kurulur; Nashi'nin taşınabilir zip'i güvenli biçimde `%LOCALAPPDATA%\Programs\Nashi` altına açılır.
4. ClipBoardLine'ın sessiz kurulumu çalışmazsa normal kurulum penceresi açılır; kurulumu sen bitirirsin.

Komutla: `sb apps install clipboardline` ve `sb apps install nashi`. Durum: `sb apps status`. Yeni sürüm var mı: `sb apps update clipboardline`.

> Deneme kipinde (`SB_SETUP_SANDBOX`) hiçbir şey indirilmez ya da kurulmaz; günlükte `[deneme] atlandı` yazar.

## Ne zaman başlasınlar?

Her uygulama için kurulumda sorulur. Varsayılan **bilgisayar açılınca**.

| Seçim | Ne olur | Komut |
|---|---|---|
| Bilgisayar açılınca başlasın (varsayılan) | Windows oturum açılışında başlayacak bir kayıt (`HKCU\...\Run`, ad: `SecondBrain-ClipBoardLine` / `SecondBrain-Nashi`) yazılır. Uygulamanın kendi «oturumda başla» ayarına dokunulmaz | `sb apps autostart <id> login` |
| Second Brain «Çalışmaya başla» ile başlasın | Kayıt yazılmaz; **Çalışmaya başla** düğmesine bastığında uygulama arka planda açılır | `sb apps autostart <id> startup` |
| Başlamasın | Kayıt silinir | `sb apps autostart <id> off` |

Kaydı geri almak için `off` yeterlidir. Uygulamayı elle açmak için: `sb apps start <id>` (Nashi için `--background` tepsiye alır) ya da kartın **Aç** düğmesi.

## Beyne neler girer?

Günlük çalışmada (`sb daily`), **Çalışmaya başla** adımında ve asistan açıkken **5 dakikada bir** hafif bir senkron çalışır; elle: `sb apps sync clipboardline`, `sb apps sync nashi`, `sb apps sync all --dry-run` (yazmadan sayar). Kayıtlar mail arşivindeki ortak kayıt tablosuna girer, `sb search` ve asistan aramasında bulunur.

**ClipBoardLine:** metinler, bağlantılar (adres ve sayfa başlığı), görsellerde uygulamanın bulduğu **OCR metni**, kayıt adı, etiketler, klasörler, not ve sabitlenmiş olma bilgisi. Çöpe attığın kayıt beyne alınmaz; daha önce alınmışsa arşivden de kaldırılır.

**Nashi:** son 50 dışa aktarımın işlem adı, dosya yolu, türü ve zamanı. Dosya hâlâ yerinde ise pdf, docx, pptx, xlsx, txt/md/csv gibi desteklenen türlerde içeriği de okunur; görsellerde OCR yapılır.

## Gizlilik

- **Sır içeren kayıt atlanır:** parola, API anahtarı, kart numarası, IBAN, TCKN, tek kullanımlık kod gibi görünen bir şey içeren ClipBoardLine kaydı beyne **hiç alınmaz** (maskelenip alınmaz, tamamen atlanır). Sayısı senkron çıktısında ve Uygulamalar kartında «sır içerdiği için atlanan» olarak görünür; içeriği hiçbir yere yazılmaz. Nashi'de sır içeren dosya içeriği satıra eklenmez (yol ve zaman kalır).
- **Uygulamaların verisine yazılmaz.** Second Brain `library.json` dosyasını yalnız okur: geçici bir kopya alıp kopyayı okur; dosya kilitliyse sonraki turda yeniden dener.
- ClipBoardLine'ın kendi ayarlarına dokunulmaz. **Metin toplama** ClipBoardLine'da varsayılan olarak **kapalıdır**: uygulamayı açıp Ayarlar'dan kendin açmalısın (varsayılan olarak yalnız bağlantılar toplanır). Kapalıysa beyne girecek metin olmaz.
- Veri bu bilgisayardan çıkmaz; senkron yalnız yerel dosyaları okur. Ağa yalnız kurulum ve sürüm denetiminde, yalnız GitHub'a çıkılır.

## ClipBoardLine nasıl kullanılır

Kopyaladığın her şey ekranın üstünde üç rafta durur: **Görseller**, **Metinler**, **Linkler**.

**İlk iş:** `Ctrl+Alt+T` → `Ctrl+K` → «Settings» yaz → **Sources** → metin ve görsel toplamayı aç. Açmazsan yalnız linkler toplanır ve beyne yalnız onlar girer.

| Kısayol (Windows) | Ne yapar |
|---|---|
| `Ctrl+Alt+T` | Rafları aç / kapat (başka bir uygulamadayken de çalışır) |
| `Ctrl+Alt+S` | Rafları arama kutusu odakta açar |
| `Ctrl+Alt+A` | İmlecin olduğu ekranın görüntüsünü alır, kırpmada açar |
| `← → ↑ ↓` | Kartlar ve raflar arasında gez |
| `Tab` / `Shift+Tab` | Etkin rafı değiştir |
| `1`–`9` | Görünen sayfadaki numaralı kartı seç |
| `Enter` | Seçileni kopyala, rafı kapat, önceki uygulamaya dön |
| `Ctrl+C` | Kopyala, raf açık kalsın |
| `Ctrl+Enter` | Önceki uygulamadaki yazı alanına doğrudan yapıştır |
| `Space` | Önizle (`←`/`→` ile önizlemede gez) |
| `P` | Sabitle: sabitlenen kayıt süresi dolunca silinmez |
| `Shift+P` / `Alt+P` | Klasöre ekleyerek sabitle / ad vererek sabitle |
| `Ctrl+Shift+T` | Etiket ekle |
| `F` | Yalnız sabitlenenleri göster |
| `Shift+S` | Raflarda ara (görsellerin içindeki yazı dahil) |
| `S` / `Backspace` | Raftan kaldır / son kaldırmayı geri al |
| `Delete` | Onayla Çöp Kutusu'na taşı |
| `L` | Kütüphaneyi aç (`Ctrl+F` ara, `Ctrl+1/2/3` görsel/metin/link süzgeci) |
| `Ctrl+K` | Tüm komutlar ve ayarlar |
| `Ctrl+Shift+C` | Görseldeki yazıyı kopyala (OCR, Türkçe/İngilizce) |
| `E` | Metin önizlemesini düzenle |
| `M` / `C` | Görselde işaretleme (kalem, ok, dikdörtgen, metin) / kırpma |
| `Ctrl+O` | Seçili linki tarayıcıda aç |
| `Ctrl+Shift+E` | Seçilenleri bir klasöre dışa aktar |
| `Esc` | Önizlemeyi, aramayı, sonra rafları kapat |

Tüm kısayollar ClipBoardLine'da `Ctrl+K` → Settings → Keyboard shortcuts'tan değiştirilebilir. Ayrıntılı liste: `apps/clipboardline/README.tr.md`.

## Nashi nasıl kullanılır

Dosyayı Nashi penceresine bırak (ya da `Ctrl+O`), çıkan çarktan ne yapacağını seç. Çıktılar **Kütüphane**'ye (`Ctrl+2`) düşer ve oradan beyne alınır.

| Kısayol (Windows) | Ne yapar |
|---|---|
| Dosyayı sürüklerken **Shift** | Dönüştürme çarkı (PDF → JPG/PNG/TXT/MD/DOCX…, video → MP4/MP3/GIF…) |
| Sürüklerken **Ctrl** | Araçlar (sıkıştır, böl, sayfaları düzenle, birleştir, kırp, kolaj, QR, metadata) |
| Sürüklerken **Alt** | Dosya işlemleri (paylaş, kopyala, taşı, yolu kopyala, terminal) |
| `Ctrl+O` | Dosya seç |
| `Ctrl+V` | Kopyalanan dosya, metin, görsel ya da linki içeri al |
| `Ctrl+Space` | Seçili dosyaların çarkı → **Convert** |
| `Ctrl+Shift+D` | Kopyaladığın herkese açık video/ses linkini indir |
| `Ctrl+1` / `Ctrl+2` | Ana sayfa / Kütüphane (son 50 çıktı) |
| `Ctrl+F` | Kütüphanede ara |
| `Ctrl+U` | Güncelleme denetle |
| Video/ses: `Space`, `←`/`→`, `Shift+←`/`→`, `I`/`O`, `Shift+Space` | Oynat/durdur, 1 sn ileri/geri, kare kare, aralık başı/sonu, aralığı oynat |
| Kırpma: sürükle, `Shift`, `Enter` | Seç, oranı kilitle, kaydet |

**Gereken ek araçlar** (Nashi ilk açılışta sorar, sonra **Finish setup**): video/ses ve link indirme için **media tools** (FFmpeg, yt-dlp, Deno, ~180 MB); Word/Excel/PowerPoint/EPUB dönüştürme için **office tools** (LibreOffice, ~360 MB).

> **Bilinen hata (Nashi 0.7.14):** dosyayı **Windows masaüstünden** Shift/Ctrl ile sürükleyince çark yalnız «Download Video / Download Audio» gösterir; Explorer penceresinden sürükleyince doğru çalışır. Geçici çözüm: `Win+E` → Masaüstü klasörü → oradan sürükle, ya da dosyayı Nashi penceresine bırak. Düzeltme Nashi'de incelemede: [orkunisitmak/nashi-app#96](https://github.com/orkunisitmak/nashi-app/issues/96).

## Komut satırı

Kurulum `sb` komutunu terminale ekler (Windows: `%USERPROFILE%\.secondbrain\bin\sb.cmd`, kullanıcı PATH'inde; macOS: `~/.local/bin/sb`). **Yeni açılan** her terminalde, hangi klasörde olursan ol:

```bash
sb apps status          # kurulu mu, çalışıyor mu, başlangıç, son senkron
sb apps sync all        # kütüphaneleri şimdi beyne al
sb apps start nashi
sb apps autostart clipboardline login   # login | startup | off
sb apps update          # yeni sürüm var mı
```

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| Nashi Başlat menüsünde yok | 0.11.1 öncesi kurulumda kısayol oluşmuyordu: `sb apps install nashi --force` |
| Sürüklerken çark yalnız «Download Video / Download Audio» gösteriyor | Yukarıdaki bilinen hata: masaüstünden değil Explorer penceresinden sürükle |
| `sb` komutu bulunamadı | Terminali kapatıp yeniden aç (PATH yeni terminalde geçerli olur). Olmazsa kurulumu ayarlar kipinde yeniden çalıştır |
| «SHA-256 uyuşmuyor» | İndirme bozulmuş ya da sürüm değişmiş; dosya silindi. `sb apps install <id>` ile yeniden dene. Tekrarlarsa kurma |
| ClipBoardLine kurulmadı, kurulum penceresi açıldı | Pencerede kurulumu bitir, sonra `sb apps status clipboardline` |
| `sb apps sync` «veri klasörü yok» diyor | Uygulama henüz hiç açılmamış; bir kez aç (`sb apps start <id>`) |
| Senkron «0 kayıt» diyor | ClipBoardLine'da metin/görsel toplama kapalı olabilir (yukarıya bak); Nashi bir dosya işlemediyse kayıt boştur |
| «kilitli, sonraki turda denenecek» | Uygulama dosyayı yazıyordu; kendiliğinden geçer |
| «sır içerdiği için atlanan» sayısı beklenenden çok | Metinde parola benzeri bir kalıp, 4-8 haneli kod ya da kart/IBAN benzeri sayı var; bilerek atlanır |
| Nashi güncellemesi «çalışıyor» diyor | Nashi'yi kapat, sonra `sb apps install nashi --force` |
| macOS | Kurulum, açma ve başlangıç komutları yazıldı ama macOS'ta denenmedi; veri okuma yalnız Windows biçimini destekler. Gatekeeper ilk açılışta onay isteyebilir |

Bu bölümle ilgili modüller: [ClipBoardLine](moduller/clipboardline.md), [Nashi](moduller/nashi.md). Komut: [`sb apps`](14-komut-referansi.md#sb-apps).
