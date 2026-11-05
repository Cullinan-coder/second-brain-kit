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

![Veri yükleme: kaynak kartı, yükleme, önizleme](img/veri-yukleme-kart.png)

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

<a id="izlenen-klasor-ve-kaynak-tazeligi"></a>

## İzlenen klasör ve kaynak tazeliği

**İzlenen klasör:** kasadaki `00-Inbox/İçe aktar/` klasörüne bir dışa aktarma dosyasını (zip, json, csv, txt…) ya da klasörünü bırakman yeter. Günlük çalışma ve asistan açıkken 10 dakikada bir klasöre bakar:

1. Dosya hâlâ yazılıyorsa (boyutu ya da son değişiklik zamanı değişiyorsa) dokunmaz, sonraki turu bekler.
2. Çok büyük dosyayı ve zip bombasını (sıkıştırma oranı, dosya sayısı, açılmış boyut sınırı) reddeder.
3. Aynı içerik daha önce alındıysa (içerik SHA-256 karması) **ikinci kez içe aktarmaz**; «zaten alınmıştı» der ve dosyayı taşır.
4. Kaynağı tanır ve içe aktarır; başarılıysa dosya `_işlendi/<tarih>/` altına **taşınır (silinmez)**.
5. Tanınmazsa (ya da okunamazsa) dosya `_tanınmadı/` altına taşınır ve **Onaylar**'a «bu dosya tanınmadı, kaynağını seç» kartı düşer. Kaynağı sen seçince: `sb import-inbox --assign "dosya.zip" whatsapp`.

Klasör git'e girmez (ilk oluşturulurken kasa `.gitignore` dosyasına eklenir). Elle çalıştırmak için: `sb import-inbox`.

**Kaynak tazeliği:** her kaynağın son başarılı içe aktarma zamanı `~/.secondbrain/freshness.json` içinde tutulur. Her kaynak manifestindeki `refresh:` alanı ne kadar sürede eskiyeceğini ve nasıl güncelleneceğini söyler:

| Alan | Anlamı |
|---|---|
| `mode` | `auto` günlük çalışan bağlayıcı (Gmail, takvim, Drive…) · `export` dışa aktarma dosyası (WhatsApp 30 gün, Takeout 60, Spotify 180…) · `manual` elle (RSS) |
| `every_days` | eşik: yaş bu değeri aşınca «eskiyor», iki katını aşınca «bayat» (otomatik kaynaklarda +0,5 gün hoşgörü) |
| `hint` | «nasıl güncellenir» tek cümle (`tr`, `en`) |

Yalnız **kullandığın** kaynaklar raporlanır: bir kez içe aktardığın ya da hesabı bağlı otomatik kaynaklar. Hiç kullanmadığın kaynak bayat diye uyarmaz. İlk çalıştırmada geçmiş kayıtlardan (`mail.db`) tohumlanır.
`sb freshness` tabloyu, `sb today` günün özetini gösterir; `sb doctor` bayat kaynak sayısını yazar, sabah özeti «Eskiyen kaynaklar» bölümü ekler.

### Arayüz için JSON (`GET /api/v2/today`, `GET /api/v2/freshness`)

İkisi de salt okunur; telefon da çağırabilir (telefonda mail konusu/gönderen, onay ayrıntısı, dosya adı ve adım çıktısı çıkarılır). Durumlar: `taze`, `eskiyor`, `bayat`, `hiç`.

```json
// GET /api/v2/today   (sb today --json aynı gövdeyi verir)
{
  "generated": "2026-11-05T09:30:00+03:00", "date": "2026-11-05", "remote": false,
  "deadlines": {
    "today": [{"date": "2026-11-05", "time": "10:00", "title": "Vize", "type": "sinav", "kind": null, "status": "aktif", "days_left": 0}],
    "week":  [{"date": "2026-11-05", "time": "10:00", "title": "Vize", "type": "sinav", "kind": null, "status": "aktif", "days_left": 0}]
  },
  "approvals": {"count": 4, "oldest": [{"id": "a1b2c3d4", "kind": "takvim", "title": "Toplantı ekle", "created": "2026-11-03T08:00:00+03:00", "detail": "…"}]},
  "mail": {"count": 2, "by_category": {"okul": 1, "finans": 1},
           "items": [{"category": "okul", "subject": "Vize yeri", "from": "Hoca", "date": "2026-11-04 09:12"}]},
  "stale_sources": {"total": 1, "items": [{"source": "bank", "name": {"tr": "Banka hareketleri", "en": "Bank transactions"}, "mode": "export",
                    "state": "bayat", "age_days": 71.0, "threshold_days": 30, "hint": {"tr": "…", "en": "…"}}]},
  "last_failed_step": {"name": "drive", "ts": "2026-11-05T01:10:00+03:00", "rc": 1, "tail": "invalid_grant"}
}
```

```json
// GET /api/v2/freshness
{
  "generated": "2026-11-05T09:30:00+03:00", "seeded": true,
  "counts": {"taze": 5, "eskiyor": 1, "bayat": 1, "hiç": 0}, "stale": 2,
  "sources": [{"source": "bank", "name": {"tr": "…", "en": "…"}, "mode": "export", "last": "2026-08-26T10:00:00+03:00",
               "age_days": 71.0, "threshold_days": 30, "state": "bayat", "hint": {"tr": "…", "en": "…"},
               "records": 120, "last_new": 14, "data_max": "2026-08-25", "via": "ingest",
               "file": {"name": "ekstre.csv", "size": 20480, "sha256": "9f2c…", "at": "2026-08-26T10:00:00+03:00", "read": 14, "new": 14},
               "last_fail": null}]
}
```

## Verim ipuçları

- Önce **küçük bir dosya** ile dene.
- Aynı dosyayı iki kez içe aktarmadan önce **Yapılan içe aktarmalar** listesine bak.
- Önemli verileri içe aktarmadan önce kasanın yedeğini al ([Güvenlik ve gizlilik → Yedek](10-guvenlik-gizlilik.md#yedek-ve-geri-yukleme)); kasa ayrıca git ile sürümlenir, yanlış bir içe aktarma geri alınabilir.
- Sohbet geçmişi (ChatGPT/Claude) içe aktarmada **önizleme bir onay kapısıdır**: hassas konuları hariç tut, özel sohbetleri «özel» işaretle.
