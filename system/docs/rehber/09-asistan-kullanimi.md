# 09 · Asistanı kullanmak: sohbet, / komutları, onay kartları, ses, telefon

Asistan, kasanı ve arşivini bilen yerel bir sohbet yardımcısıdır. Obsidian yan panelinde, uygulama penceresinde ve telefonda aynı asistan çalışır. Bu bölüm nasıl konuşacağını, hangi komutların olduğunu ve onay kartlarının nasıl işlediğini anlatır.

## İlk soru

Uygulamayı aç (ya da [kurulum turundaki](02-sihirbaz-adim-adim.md) 5 adımı izle):

1. Alttaki mesaj kutusuna yaz: `bugün neyim var?`
2. **Enter**. Asistan takvimine ve notlarına bakıp cevaplar. Cevabın altında kaynak notlar listelenebilir; tıklayarak açarsın.
3. Devam etmek için aynı sohbette yazmaya devam et; asistan bağlamı hatırlar.



## Doğal dille ne isteyebilirsin?

Asistan yalnız **açık olan modüllerin** işlerini yapar. Örnekler (kendi verinle çalışır):

| Alan | Örnek istek | İlgili modül |
|---|---|---|
| Soru-cevap | `son gelen mail neydi?` · `geçen ay kimden fatura geldi?` · `proje X'te en son ne yaptık?` | [Arama ve cevaplar](moduller/search.md), [Gmail](moduller/gmail.md), [Beyin dizini](moduller/brain.md) |
| Takvim | `cuma 15:00 doktor ekle` · `yarın neyim var?` · `perşembe toplantısını sil` | [Google Takvim](moduller/calendar.md) (onay kartıyla) |
| Notlar | `şu başvuru kabul edildi, notu güncelle` · `bu notu arşivle` | [Yerel asistan](moduller/assistant.md) |
| Hızlı not/görev | `not: yarın dilekçeyi yazdır` · `görev ekle: rapor taslağı` | [Not kutusu](moduller/inbox.md), [Görev ve planlama](moduller/tasks_plan.md) |
| Bilgisayar | `hesap makinesini aç` · `sistem bilgisi` · `sesi kıs` | [Bilgisayar kontrolü](moduller/computer.md) |
| Müzik/video | `Spotify'da X çal` · `YouTube'da Y aç` | [Spotify ve YouTube](moduller/media.md) |
| Ekran/kamera | `ekranımda ne var?` | [Ekran ve kamera](moduller/vision.md) |
| WhatsApp | `Ayşe'ye "geç kalacağım" taslağı hazırla` | [WhatsApp](moduller/whatsapp.md) (taslak + onay) |
| Plan | `bugünü planla` · `haftamı planla` | [Görev ve planlama](moduller/tasks_plan.md) |
| Web | `... için web'de ara` | [Bilgisayar kontrolü](moduller/computer.md) |

Hangi isteğin hangi modüle bağlı olduğu bilinmiyorsa [Özellik kataloğu](17-ozellik-katalogu.md)na bak. Bir modül kapalıysa asistan o aracı kullanamaz ve söyler.

### İyi soru sormanın ipuçları

- **Zaman süzgeçleri** anlar: `geçen ay`, `ekimde`, `hocadan gelen mailler`.
- Kaynak göster demene gerek yok: cevaplar **kaynak numaralıdır** ([1], [2]); numaraya tıkla.
- Belirsizse asistan tahmin etmek yerine sorar ya da onaya sunar (özellikle tarih ve silme işlerinde).
- Uzun işler (ör. büyük belge özeti) yerel modelle birkaç dakika sürebilir.
- Yanlış bir şey yaptıysa son kasa değişikliğini `sb asistan-undo` ile geri alabilirsin; kasa ayrıca git ile sürümlüdür.

## / komutları

Mesaj kutusuna **/** yazınca komut listesi açılır: ok tuşlarıyla gez, **Enter** ya da **Tab** ile seç. Esc kapatır.

| Komut | Yazım | Ne yapar |
|---|---|---|
| `/yeni` | `/yeni` | Yeni sohbet başlatır |
| `/ara` | `/ara fatura nisan` | Kasada ve arşivde arar; ilk 8 sonucu tür ve özetle listeler |
| `/not` | `/not yarın dilekçe` | Gelen kutusuna (`00-Inbox`) hızlı not düşer |
| `/gorev` | `/gorev rapor taslağı` | Yeni görev ekler (en çok 120 karakter) |
| `/ozet` | `/ozet` | Bu sohbeti 5 maddede özetler (konu, kararlar, açık işler) |
| `/hatirla` | `/hatirla kahveyi sütsüz içerim` | Kalıcı bilgi hatırlar (hafızaya yazar) |
| `/unut` | `/unut kahve tercihi` | Bir konuyu unutma isteği: eşleşmeleri bulur, **onay kartı** çıkarır; onaylarsan siler (arşive taşır) |
| `/bugun` | `/bugun` | Yaklaşan teslim/sınav/başvuru tarihleri ve onay bekleyen takvim adayları |
| `/kisi` | `/kisi Ayşe Yılmaz` | **Kişi** görünümünü açar |
| `/proje` | `/proje second-brain` | **Proje** görünümünü açar |
| `/kart` | `/kart` | **Bilgi kartları** tekrar oturumunu açar |

Metin gereken komutlar (`/ara`, `/not`, `/gorev`, `/hatirla`, `/unut`, `/kisi`, `/proje`) metinsiz yazılırsa «/komut için metin gerekli» der. Bilinmeyen komutta «bilinmeyen komut: /…». Bu komutlara metin olarak yazdığın şey **gizli veri maskelemesinden geçer** (kart numarası vb. kaydedilmez).

<a id="onay-kartlari"></a>

## Onay kartları

Bazı işler **kendiliğinden yapılmaz**; asistan önce bir kart çıkarır:

- **Takvime ekle/sil** — Takvim · onay gerekli
- **Komut çalıştır** — Komut · onay gerekli (sınıflama aşağıda)
- **Bir konuyu unut / sil** — Unutma / Silme
- **WhatsApp mesajı**, **SMS**, **Mail taslağı** — taslak hazırlanır, **gönderilmez**
- **Not güncelleme/arşivleme, kural ekleme, hafızaya yazma** — izin profiline göre (aşağıda)

Kartın yapısı: üstte tür etiketi («Takvim · onay gerekli»), altında ne yapılacağı, altta **Onayla** ve **İptal**. Onaylayınca satır «Onaylandı — mesaj», iptalde «İptal edildi» olur. Birden çok bekleyen varsa çip «Onayla (N bekliyor)» yazar. Pano'daki **Onay bekleyen** bölümü ve **Otomasyonlar → Bekleyen onaylar** aynı kartları toplar.



**Kurallar:**

1. Takvim ve WhatsApp **her izin profilinde** onaylıdır.
2. Riskli/yazan komutlar (paket kurma, sistem yükseltme, dal silme, ortam değişkeni okuma, dosyaya yazdırma, ağ paylaşımı, kasa dışı dosya okuma…) her zaman onaylıdır.
3. **Komut** ve **WhatsApp** kartları yalnız **bilgisayardan** onaylanır, telefondan değil.
4. Bir mail/SMS/belge içinde yazan «şunu yap» yönergeleri komut sayılmaz; «kural ekle», «hafızaya yaz», «URL çek» gibi işler yalnız **senin yazdığın** mesajda o istek varsa onaysız ilerler ([Güvenlik ve gizlilik](10-guvenlik-gizlilik.md)).
5. Kalıcı silme yoktur; silinen her şey arşive taşınır.

## Sesli kullanım

1. **Mikrofon düğmesi** (mesaj kutusunun yanında, **Sesle konuş**): bas, konuş, tekrar bas. Konuşman yerel **Whisper** ile yazıya çevrilir ve mesaj kutusuna düşer. Ses modülü açık ve **Sesi kur** yapılmış olmalı ([Modeller ve ses](05-modeller-ses.md)).
2. **Sesli cevap:** **Ayarlar** görünümünde **Cevapları sesli oku** kutusunu aç; **Ses** listesinden ses seç; **Dene** ile dinle.
3. **Uyandırma sözcüğü:** **Ayarlar → Uyandırma sözcüğü** kutusu. Ses modülüne bağlıdır ve **yalnız sekme açıkken** dinler. Varsayılan kapalıdır.
4. **Sesli not ve toplantı/ders kaydı:** kayıt dökümü `40-Kaynaklar/Toplantılar` altına not olur; ses dosyası `.secondbrain/audio`'da kalır.
5. Mikrofon izni sorarsa **İzin ver** (tarayıcı/uygulama ayarlarından değiştirilebilir).

## Telefondan kullanım

[Uygulama turu → Telefon](08-uygulama-turu.md#telefon) bölümündeki eşlemeyi yaptıktan sonra aynı arayüz telefonda açılır. Farklar: izin profilini değiştiremezsin, komut ve WhatsApp kartlarını onaylayamazsın, bağlantı yoksa mesajlar kuyruğa girer, Android'de **Paylaş → İkinci Beyin** ile metin/bağlantı gönderebilirsin.

## Claude Code ile birlikte kullanım

- **Hafıza:** Claude Code her oturumun başında kurallarını, hafızanı, açık konularını ve son oturum kartlarını görür ([Claude Code hafızası](moduller/claude_hooks.md)).
- **Oturum sonu:** önemli bir iş bitince Claude `Son oturum.md`e kart yazar; kalıcı öğrenimler `sb concept`, makbuzlar `sb receipt`, görevler `sb task` ile kaydedilir ([Komut referansı](14-komut-referansi.md#sb-receipt)).
- **MCP araçları:** Claude `brain_search`, `brain_project`, `brain_today` gibi araçlarla kasanı okur ([MCP](06-mcp.md#second-brain-mcpsi)).
- **Gece koşusu:** `00-Inbox/Gece işleri.md` maddelerini `sb night` Claude Code'a sırayla yaptırır ([Gece koşusu](moduller/night.md)).
- **Hafıza modu:** `sb mode normal | ekonomik | manuel` hafıza kancalarının ne kadar bağlam eklediğini ayarlar.

## Sınırlar ve beklentiler

- Yerel model, büyük bulut modellerinden küçüktür; karmaşık sorularda hata yapabilir. Önemli kararlarda kaynağı kendin kontrol et.
- Asistan veri yoksa bilmediğini söyler; kaynağı olmayan bilgiyi doğrulamaz.
- Mail/arşiv salt okunur olduğu için «bu maili sil/cevapla» gibi istekler **taslak** üretir ya da yapılamaz.
