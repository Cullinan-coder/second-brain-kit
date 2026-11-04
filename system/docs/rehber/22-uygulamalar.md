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

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| «SHA-256 uyuşmuyor» | İndirme bozulmuş ya da sürüm değişmiş; dosya silindi. `sb apps install <id>` ile yeniden dene. Tekrarlarsa kurma |
| ClipBoardLine kurulmadı, kurulum penceresi açıldı | Pencerede kurulumu bitir, sonra `sb apps status clipboardline` |
| `sb apps sync` «veri klasörü yok» diyor | Uygulama henüz hiç açılmamış; bir kez aç (`sb apps start <id>`) |
| Senkron «0 kayıt» diyor | ClipBoardLine'da metin/görsel toplama kapalı olabilir (yukarıya bak); Nashi bir dosya işlemediyse kayıt boştur |
| «kilitli, sonraki turda denenecek» | Uygulama dosyayı yazıyordu; kendiliğinden geçer |
| «sır içerdiği için atlanan» sayısı beklenenden çok | Metinde parola benzeri bir kalıp, 4-8 haneli kod ya da kart/IBAN benzeri sayı var; bilerek atlanır |
| Nashi güncellemesi «çalışıyor» diyor | Nashi'yi kapat, sonra `sb apps install nashi --force` |
| macOS | Kurulum, açma ve başlangıç komutları yazıldı ama macOS'ta denenmedi; veri okuma yalnız Windows biçimini destekler. Gatekeeper ilk açılışta onay isteyebilir |

Bu bölümle ilgili modüller: [ClipBoardLine](moduller/clipboardline.md), [Nashi](moduller/nashi.md). Komut: [`sb apps`](14-komut-referansi.md#sb-apps).
