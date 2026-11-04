# 07 · Veri yükleme (içe aktarma)

Bu bölüm sihirbazın **9. adımını** (Ayarlar → **Veri yükleme** sekmesi) anlatır: başka hizmetlerden indirdiğin dışa aktarma dosyalarını Second Brain'e nasıl alacağını. **39 kaynak** vardır; her birinin ayrı bir sayfası var (dışa aktarma adımları + yükleme + sorun giderme): [Veri kaynakları listesi](18-veri-kaynaklari.md).

## Kavramlar

- **Dışa aktarma (export):** bir hizmetin («Verilerimi indir» düğmesiyle) sana verdiği zip/CSV/JSON dosyası. Hizmetin kendi sitesinde yapılır.
- **İçe aktarma (import):** bu dosyayı Second Brain'in okuyup **kasaya not ve kayıt** olarak çevirmesi.
- **Bağlayıcı (connector):** bir kaynağın dosya biçimini bilen küçük okuyucu (ör. `whatsapp`, `spotify`). Her kaynağın sayfasında adı yazar.
- **Önizleme (dry-run):** hiçbir şey yazmadan «şu kadar kayıt okunacak, şu tarih aralığında, işte 3 örnek» demek. **Her zaman önce önizle.**

> **Gizlilik:** dosya yalnız bu bilgisayarda okunur, hiçbir yere gönderilmez. Yüklediğin dosya geçici olarak `.secondbrain/import_staging/<kaynak>/` altında durur. İçe aktarma bittikten sonra bu geçici kopyayı silebilirsin; kasadaki notlar kalır.

## Adım adım: bir dosyayı içe aktarmak

1. **Dosyayı edin.** İlgili kaynağın sayfasındaki «Dışa aktarma adımları»nı izle (ör. [WhatsApp](kaynaklar/whatsapp.md), [Google Takeout](kaynaklar/takeout.md)). Bu adımlar sağlayıcıların sitelerinde yapılır; **menü adları değişebilir**, takılırsan sağlayıcının resmî yardım sayfasına bak (adım listesinde adres varsa yazılıdır).
2. **Sihirbazda/Ayarlar'da 9. adımı aç.** Seçimine göre gereken kaynaklar üstte görünür. Bütün kaynakları görmek için **Bütün kaynakları göster (39)** kutusunu işaretle.
3. **Kaynak kartını bul.** Kartta **Bu dosyayı nasıl alırsın?** (adımlar), **Biçim: …** (kabul edilen uzantılar) ve **Bağlayıcı: …** yazar.
4. **Dosyayı kutuya bırak** («Dosyayı buraya bırak ya da seçmek için tıkla») ya da **Dosya seç**. Zip'leri **açmadan** olduğu gibi yükle (aksi söylenmedikçe).
5. Yükleme sırasında «**Yükleniyor: ad (MB)…**», bitince «**Yüklendi: ad**».
6. **Önizle.** Sonuçta okunan kayıt sayısı, tarih aralığı ve örnek başlıklar çıkar: «Önizleme hazır; sorun yoksa içe aktar.» Sayılar mantıklı değilse **içe aktarma**; dosyayı ve adımları kontrol et.
7. **İçe aktar.** «İçe aktarma başlatılıyor…» → «İçe aktarılıyor; ilerleme aşağıda.» → «**İçe aktarma bitti.**» ve «**N kayıt içe aktarıldı**».
8. Alttaki **Yapılan içe aktarmalar** listesinde işlem **başarılı** / **başarısız** olarak görünür. Henüz yoksa «Henüz içe aktarma yok.»



## Ne kadar büyük dosya?

Yükleme sınırı **2 GB**'dır. Daha büyükse «dosya çok büyük (en çok 2 GB)» der. Çözüm: dışa aktarmayı daha dar tarih aralığıyla iste ya da komut satırından (`sb import <kaynak> <dosya>`) kullan. Çok büyük içe aktarmalar (ör. Google Takeout) uzun sürebilir; pencereyi kapatma.

## Komut satırından

Aynı işi terminalden de yaparsın:

```
sb import <kaynak> <dosya> --dry-run     # önce say
sb import <kaynak> <dosya>               # sonra aktar
```

- `--me "Adın"`: WhatsApp/Telegram/Instagram/Slack gibi sohbet kaynaklarında **senin mesajlarının** işaretlenmesi için.
- `--days N`: tarayıcı geçmişinde kaç gün geriye gidileceği (varsayılan 365).
- `--discover`: tarayıcı kaynağında bilgisayardaki profilleri listeler.
- Özel komutlar: `sb history-import <dosya>` (ChatGPT/Claude/Gemini sohbet geçmişi; **`--apply` olmadan hiçbir şey yazmaz**), `sb takeout <zip>`, `sb linkedin-import`, `sb sms-sync`.
- Ayrıntı: [Komut referansı → sb import](14-komut-referansi.md#sb-import).

## «Bağlayıcısı yok» ne demek?

Bir kaynağın içe aktarıcısı henüz yazılmamışsa Önizle şunu der: «**Bu kaynağın içe aktarıcısı henüz yok; dosya hazır bekliyor.**» Dosya yüklenmiş kalır, ama kasaya bir şey yazılmaz. Böyle bir durumda kaynağın sayfasındaki bağlayıcı bilgisine bak.

## Kaynaklar (kısa liste)

### Not ve görev uygulamaları

[Apple Notlar](kaynaklar/apple-notlar.md) · [Evernote](kaynaklar/evernote.md) · [Google Keep](kaynaklar/keep.md) · [Notion](kaynaklar/notion.md) · [OneNote](kaynaklar/onenote.md) · [Jira](kaynaklar/jira.md) · [Linear](kaynaklar/linear.md) · [Microsoft To Do](kaynaklar/mstodo.md) · [TickTick](kaynaklar/ticktick.md) · [Todoist](kaynaklar/todoist.md) · [Trello](kaynaklar/trello.md)

### Mesajlaşma ve mail

[WhatsApp sohbetleri](kaynaklar/whatsapp.md) · [Telegram arşivi](kaynaklar/telegram.md) · [Discord](kaynaklar/discord.md) · [Slack](kaynaklar/slack.md) · [SMS ve aramalar](kaynaklar/sms.md) · [Outlook / Microsoft 365 mail](kaynaklar/outlook.md) · [iCloud](kaynaklar/icloud.md) · [LinkedIn](kaynaklar/linkedin.md)

### Yaşam, akademik ve geçmiş

[ChatGPT / Claude / Gemini sohbet geçmişi](kaynaklar/history-import.md) · [Google Takeout](kaynaklar/takeout.md) · [Google Fotoğraflar](kaynaklar/gphotos.md) · [Google Haritalar](kaynaklar/gmaps.md) · [Instagram](kaynaklar/instagram.md) · [X (Twitter)](kaynaklar/x.md) · [Banka ekstresi](kaynaklar/bank.md) · [Ekran süresi](kaynaklar/screentime.md) · [arXiv](kaynaklar/arxiv.md) · [BibTeX](kaynaklar/bibtex.md) · [Zotero](kaynaklar/zotero.md) · [Coursera](kaynaklar/coursera.md) · [Udemy](kaynaklar/udemy.md)

### Medya ve okuma

[Spotify](kaynaklar/spotify.md) · [YouTube](kaynaklar/youtube.md) · [Kindle](kaynaklar/kindle.md) · [Pocket](kaynaklar/pocket.md) · [Raindrop.io](kaynaklar/raindrop.md) · [RSS](kaynaklar/rss.md) · [Tarayıcı geçmişi](kaynaklar/browser.md)

<a id="yaygin-hatalar"></a>

## Yaygın hatalar

| Belirti | Çözüm |
|---|---|
| «dosya çok büyük (en çok 2 GB)» | Daha dar aralıkla yeniden dışa aktar |
| «geçersiz dosya adı» | Dosyayı kısa, sade bir adla kaydet |
| «yükleme yarım kaldı» | Yeniden yükle |
| «dosya yüklenmemiş: önce yükle» | Önce dosyayı kutuya bırak, sonra Önizle |
| Önizlemede 0 kayıt | Yanlış dosya/biçim; kaynağın adımlarını baştan izle |
| «içe aktarma başarısız (kod N)» | **Günlük** sekmesine / `sb logs`'a bak; sorun sürerse [Sorun giderme](11-sorun-giderme.md) |
| Zip açılmıyor | Dosya indirme sırasında bozulmuştur; yeniden indir. Zip bombasına karşı bir güvenlik sınırı da vardır |
| Hizmette «Verilerimi indir» bulunamıyor | Menü adı sürüme göre değişir; «export your data» + hizmet adını arat, kaynak sayfasındaki resmî adrese bak |

## Verim ipuçları

- Önce **küçük bir dosya** ile dene.
- Aynı dosyayı iki kez içe aktarmadan önce **Yapılan içe aktarmalar** listesine bak.
- Önemli verileri içe aktarmadan önce kasanın yedeğini al ([Güvenlik ve gizlilik → Yedek](10-guvenlik-gizlilik.md#yedek-ve-geri-yukleme)); kasa ayrıca git ile sürümlenir, yanlış bir içe aktarma geri alınabilir.
- Sohbet geçmişi (ChatGPT/Claude) içe aktarmada **önizleme bir onay kapısıdır**: hassas konuları hariç tut, özel sohbetleri «özel» işaretle.
