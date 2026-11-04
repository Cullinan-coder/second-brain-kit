# Komut referansı

Second Brain'in her işi bir komutla da yapılabilir. Uygulamayı kullanıyorsan çoğu zaman buna **gerek yoktur**; ama otomasyon, sorun giderme ve ileri kullanım için hepsi burada.

## Komutu nasıl çalıştırırım

1. **Terminali aç.** Windows'ta Başlat menüsüne `PowerShell` yaz → **Windows PowerShell**'e tıkla. macOS'ta Spotlight (Cmd+Boşluk) → `Terminal`.
2. Kurulumda `sb` kısayolu eklendiyse doğrudan `sb doctor` yaz → Enter. Kısayol yoksa (`sb` tanınmıyorsa) kasadaki `_system` klasöründen şunu çalıştır: `uv run python -m sb doctor`.
3. Bir komutun kendi yardımı: `sb <komut> --help`. Bütün komutlar: `sb --help`.
4. Windows'ta Türkçe karakterler bozuk görünürse: `chcp 65001` yaz, sonra komutu tekrar çalıştır.

> `--dry-run` olan komutlar önce **yazmadan sayar**; ilk seferde her zaman bununla dene. Kalıcı silme yapan komut yoktur; şifreleme/geri yükleme komutları `--confirm` ister ve önce yedek alır.

Aşağıdaki hesap takma adları (`<hesap>`) sihirbazda verdiğin adlardır; örneklerde uydurma `ana` kullanıldı.

## Kurulum, sağlık ve güncelleme

### sb doctor

**Ne yapar:** kurulumu kontrol et (eksikleri ve ne yapılacağını söyler).

```
sb doctor
```

**Örnek:** `sb doctor`

### sb update

**Ne yapar:** kit kurulumunu son sürüme getir (notlara ve ayarlara dokunmaz).

```
sb update [--check] [--rollback] [--recover] [--yes] [--tags-only]
```

| Seçenek | Anlamı |
|---|---|
| `--check` | yalnız yeni sürüm var mı bak |
| `--rollback` | son güncellemeden önceki yedeğe dön |
| `--recover` | yarım kalan güncellemeyi tamamla (kodu kitten yeniden kur) |
| `--yes` | gelen değişiklikleri sormadan çek |
| `--tags-only` | yalnız etiketli (v*) sürümlere güncelle |

**Örnek:** `sb update --check`

### sb version

**Ne yapar:** kurulu sürüm.

```
sb version
```

**Örnek:** `sb version`

### sb whatsnew

**Ne yapar:** son görmediğin sürüm yenilikleri.

```
sb whatsnew [--all]
```

| Seçenek | Anlamı |
|---|---|
| `--all` | tüm sürümleri göster |

**Örnek:** `sb whatsnew`

### sb features

**Ne yapar:** modülleri aç/kapat (config/features.yaml); listesiz çalıştırınca durumu gösterir.

```
sb features [--on ON] [--off OFF]
```

| Seçenek | Anlamı |
|---|---|
| `--on ON` | (açıklama yok) |
| `--off OFF` | (açıklama yok) |

**Örnek:** `sb features --on voice --off screen_watch`

### sb roadmap

**Ne yapar:** 250 maddelik yol haritasının ilerlemesi (features.yaml).

```
sb roadmap [--mark MARK] [--status STATUS]
```

| Seçenek | Anlamı |
|---|---|
| `--mark MARK` | ör. 3,5,23 |
| `--status STATUS` | (açıklama yok) |

**Örnek:** `sb roadmap`

### sb logs

**Ne yapar:** son günlük çalışma logu / çökme raporu; --bundle paylaşılabilir paket üretir.

```
sb logs [--n N] [--crash] [--bundle]
```

| Seçenek | Anlamı |
|---|---|
| `--n N` | (açıklama yok) |
| `--crash` | son çökme raporunu göster |
| `--bundle` | son 5 rapor + doctor çıktısını tek zip yap (hiçbir yere gönderilmez) |

**Örnek:** `sb logs --bundle`

### sb perf

**Ne yapar:** performans panosu (perf.jsonl): adım/sohbet süreleri, p95, hata oranı.

```
sb perf [--days DAYS]
```

| Seçenek | Anlamı |
|---|---|
| `--days DAYS` | (açıklama yok) |

**Örnek:** `sb perf`

### sb e2e

**Ne yapar:** gerçek kasada salt okunur uçtan uca testler; --live çalışan asistanı da dener.

```
sb e2e [--live]
```

| Seçenek | Anlamı |
|---|---|
| `--live` | (açıklama yok) |

**Örnek:** `sb e2e`

### sb models

**Ne yapar:** yerel model yöneticisi: donanım, öneri, profil, indirme/silme, kendi verinle sınav.

```
sb models [--apply APPLY] [--bench BENCH] [--n N] [--pull PULL] [--rm RM] [--yes]
```

| Seçenek | Anlamı |
|---|---|
| `--apply APPLY` | profili llm.yaml'a uygula: full\|medium\|small\|cloud (--yes olmadan yalnız fark) |
| `--bench BENCH` | virgüllü model listesi, ör. ollama:qwen3:14b,ollama:qwen3:4b |
| `--n N` | sınavda not sayısı |
| `--pull PULL` | Ollama'ya model indir (--yes gerekir) |
| `--rm RM` | Ollama'dan model sil (--yes gerekir) |
| `--yes` | (açıklama yok) |

**Örnek:** `sb models`

### sb apps

**Ne yapar:** hazır uygulamaları (ClipBoardLine, Nashi) yönetir: listele, durum, kur, başlat, başlangıç kipi, sürüm denetimi, beyne senkron. Ayrıntı: [Uygulamalar: ClipBoardLine ve Nashi](22-uygulamalar.md).

```
sb apps [--force] [--background] [--dry-run] {list,status,install,start,autostart,update,sync} [id] [{login,startup,off}]
```

| Değer | Anlamı |
|---|---|
| `action` | `list` katalog, `status` durum, `install` resmî sürümü indirip kur, `start` aç, `autostart` başlangıç kipi, `update` yeni sürüm var mı, `sync` beyne oku |
| `id` | `clipboardline` ya da `nashi` (`status` ve `sync` için `all` de olur) |
| `mode` | `autostart` için: `login` bilgisayar açılınca, `startup` Second Brain «Çalışmaya başla» ile, `off` başlamasın |

| Seçenek | Anlamı |
|---|---|
| `--force` | `install`: kuruluysa da yeniden kur |
| `--background` | `start`: arka planda başlat (Nashi tepsiye gider) |
| `--dry-run` | `sync`: yazmadan say |

**Örnek:** `sb apps install nashi` · `sb apps autostart clipboardline startup` · `sb apps sync all --dry-run`

### sb usage

**Ne yapar:** model kullanımı ve maliyet özeti (bütçeyle birlikte).

```
sb usage [--days DAYS]
```

| Seçenek | Anlamı |
|---|---|
| `--days DAYS` | (açıklama yok) |

**Örnek:** `sb usage`

### sb embed-test

**Ne yapar:** yapılandırılmış gömme modeliyle tek metni göm (boyut + ilk 5 değer).

```
sb embed-test text
```

| Değer | Anlamı |
|---|---|
| `text` | (zorunlu değer) |

**Örnek:** `sb embed-test`

### sb set-secret

**Ne yapar:** Gizli değeri (ör. claude-oauth) gizli girişle keyring'e kaydet.

```
sb set-secret {claude-oauth,telegram-bot,imap-<takma-ad>,api-openai,api-anthropic,api-gemini,api-openrouter,api-groq,api-deepseek,api-mistral}
```

**Örnek:** `sb set-secret api-openai`

### sb chat

**Ne yapar:** yerel Qwen asistanı (Obsidian'a gömülür).

```
sb chat [--port PORT]
```

| Seçenek | Anlamı |
|---|---|
| `--port PORT` | (açıklama yok) |

**Örnek:** `sb chat`

### sb daily

**Ne yapar:** günlük otomatik güncelleme ve sabah özeti (zamanlayıcı 13:00'te ve oturum açılışında çalıştırır).

```
sb daily [--force]
```

| Seçenek | Anlamı |
|---|---|
| `--force` | bugün zaten çalışmış olsa da çalıştır |

**Örnek:** `sb daily`

### sb weekly

**Ne yapar:** haftalık denetim ve özet (zamanlayıcı pazar günleri 15:00'te çalıştırır).

```
sb weekly
```

**Örnek:** `sb weekly`

### sb notify-test

**Ne yapar:** Deneme maili (şirket SMTP → sadece kullanıcının adresi).

```
sb notify-test
```

**Örnek:** `sb notify-test`

### sb restore

**Ne yapar:** yedekten geri yükle (önce mevcut durumun yedeği; <yedek> --confirm).

```
sb restore [--folder FOLDER] [--confirm] [rest ...]
```

| Değer | Anlamı |
|---|---|
| `rest` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--folder FOLDER` | (açıklama yok) |
| `--confirm` | (açıklama yok) |

**Örnek:** `sb restore vault-tum-20261104-150000.zip.enc` (şifreli yedek; düz `.zip` de okunur)

### sb backup

**Ne yapar:** şifreli kasa yedeği al (`~/.secondbrain/backups/vault-tum-*.zip.enc`); haftalık görev de alır, son 8 kalır. Şifreleme yoksa düz yedek ALMAZ.

```
sb backup
```

**Örnek:** `sb backup`

### sb encrypt

**Ne yapar:** `sb vault-encrypt` takma adı; ayrıca `--purge-history <klasör>` ile şifrelenmiş klasörün git geçmişindeki düz metni temizler (`--confirm` olmadan yalnız anlatır; önce tam şifreli yedek alır; uzak depoya ZORLA push gerekir).

```
sb encrypt [--folder FOLDER] [--confirm] [--purge-history PURGE_HISTORY] [rest ...]
```

**Örnek:** `sb encrypt --purge-history 30-Kariyer` (önizleme), `sb encrypt --purge-history 30-Kariyer --confirm`

### sb vault-encrypt

**Ne yapar:** klasörü şifrele (önce yedek; --folder <klasör> --confirm).

```
sb vault-encrypt [--folder FOLDER] [--confirm] [rest ...]
```

| Değer | Anlamı |
|---|---|
| `rest` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--folder FOLDER` | (açıklama yok) |
| `--confirm` | (açıklama yok) |

**Örnek:** `sb vault-encrypt --folder 90-Arşiv --confirm`

### sb vault-decrypt

**Ne yapar:** şifreli klasörü aç (--folder <klasör> --confirm).

```
sb vault-decrypt [--folder FOLDER] [--confirm] [rest ...]
```

| Değer | Anlamı |
|---|---|
| `rest` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--folder FOLDER` | (açıklama yok) |
| `--confirm` | (açıklama yok) |

**Örnek:** `sb vault-decrypt`

### sb vault-key

**Ne yapar:** kasa şifreleme anahtarını yedekle: --export <dosya>.

```
sb vault-key [--export EXPORT]
```

| Seçenek | Anlamı |
|---|---|
| `--export EXPORT` | (açıklama yok) |

**Örnek:** `sb vault-key`

### sb security-test

**Ne yapar:** istem enjeksiyonu kalkanı: yerel modelle senaryolar.

```
sb security-test [--folder FOLDER] [--confirm] [rest ...]
```

| Değer | Anlamı |
|---|---|
| `rest` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--folder FOLDER` | (açıklama yok) |
| `--confirm` | (açıklama yok) |

**Örnek:** `sb security-test`

## Hesaplar ve toplama

### sb login

**Ne yapar:** Google izni (tarayıcı); token keyring'e.

```
sb login <hesap>
```

| Değer | Anlamı |
|---|---|
| `<hesap>` | (zorunlu değer) |

**Örnek:** `sb login ana`

### sb mail-fetch

**Ne yapar:** mail hesabını (Gmail ya da IMAP) salt okunur olarak yerel arşive çeker; --full hepsini, --limit en çok N iletiyi alır.

```
sb mail-fetch [--full] [--limit LIMIT] <hesap>
```

| Değer | Anlamı |
|---|---|
| `<hesap>` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--full` | (açıklama yok) |
| `--limit LIMIT` | (açıklama yok) |

**Örnek:** `sb mail-fetch ana --limit 200`

### sb mail-ics-backfill

**Ne yapar:** Eski maillerdeki .ics eklerini okuyup tarih çıkarmaya yeniden aç.

```
sb mail-ics-backfill <hesap>
```

| Değer | Anlamı |
|---|---|
| `<hesap>` | (zorunlu değer) |

**Örnek:** `sb mail-ics-backfill`

### sb mail-categorize

**Ne yapar:** Kurallarla yeniden kategorile.

```
sb mail-categorize [--all]
```

| Seçenek | Anlamı |
|---|---|
| `--all` | (açıklama yok) |

**Örnek:** `sb mail-categorize`

### sb mail-index

**Ne yapar:** 40-Kaynaklar/Mail indeks notlarını güncelle.

```
sb mail-index [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb mail-index`

### sb contacts-sync

**Ne yapar:** Google Contacts → 60-Kişiler (salt okunur).

```
sb contacts-sync [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb contacts-sync`

### sb drive-sync

**Ne yapar:** Drive dosya listesi (+ son 120 gün Docs metni) → mail.db (salt okunur).

```
sb drive-sync
```

**Örnek:** `sb drive-sync`

### sb drive-index

**Ne yapar:** mail.db → 40-Kaynaklar/Drive üst klasör indeks notları.

```
sb drive-index [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb drive-index`

### sb sms-sync

**Ne yapar:** Drive'daki SMS Backup & Restore yedekleri → mail.db (sonra contacts-sync).

```
sb sms-sync [--sms SMS] [--calls CALLS]
```

| Seçenek | Anlamı |
|---|---|
| `--sms SMS` | test için yerel sms XML |
| `--calls CALLS` | test için yerel calls XML |

**Örnek:** `sb sms-sync`

### sb sync-gcal

**Ne yapar:** Takvim API → ders/teslim/akademik notları.

```
sb sync-gcal [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb sync-gcal`

### sb import-gcal

**Ne yapar:** Takvim JSON anlık görüntüsünden aynı aktarım.

```
sb import-gcal [--dry-run] [--vault VAULT] [--today TODAY] file
```

| Değer | Anlamı |
|---|---|
| `file` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |
| `--vault VAULT` | test için farklı kasa kökü |
| `--today TODAY` | test için bugünün tarihi (YYYY-MM-DD) |

**Örnek:** `sb import-gcal`

### sb caldav-sync

**Ne yapar:** iCloud CalDAV/CardDAV (ve Outlook ICS) takvim+kişileri → items.

```
sb caldav-sync alias
```

| Değer | Anlamı |
|---|---|
| `alias` | accounts.yaml imap takma adı |

**Örnek:** `sb caldav-sync`

### sb local-files

**Ne yapar:** Bu bilgisayardaki dosyalar → 40-Kaynaklar/Bilgisayar (link, kopya yok).

```
sb local-files [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb local-files`

### sb content-sync

**Ne yapar:** Belgelerin metnini çıkar (PDF/Word/PPT/Excel/ipynb/metin) → aranabilir arşiv.

```
sb content-sync [--limit LIMIT]
```

| Seçenek | Anlamı |
|---|---|
| `--limit LIMIT` | (açıklama yok) |

**Örnek:** `sb content-sync`

### sb projects-sync

**Ne yapar:** ~/Workspace/projects + GitHub → 20-Projeler (son çalışmalar, özet).

```
sb projects-sync [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb projects-sync`

### sb project-deep

**Ne yapar:** Claude (salt okunur) projeyi inceler → notta "Proje dosyası".

```
sb project-deep [--all] [--force] [--show-prompt] [folder]
```

| Değer | Anlamı |
|---|---|
| `folder` | ~/Workspace/projects altındaki klasör adı |

| Seçenek | Anlamı |
|---|---|
| `--all` | tüm projeler (değişmeyenler atlanır) |
| `--force` | değişiklik olmasa da yeniden derle |
| `--show-prompt` | Claude'a gidecek metni göster, çalıştırma |

**Örnek:** `sb project-deep`

### sb github-deep

**Ne yapar:** GitHub repolarında son N gün issue/PR/yorum/commit/release → items.

```
sb github-deep [--days DAYS] [--repo REPO] [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--days DAYS` | (açıklama yok) |
| `--repo REPO` | tek repo (ad ya da sahip/ad) |
| `--dry-run` | yalnız say, yazma |

**Örnek:** `sb github-deep`

### sb sessions-sync

**Ne yapar:** Claude Code oturumlarını özetle → proje notunda "Oturum günlüğü".

```
sb sessions-sync [--include-active] [--render-only]
```

| Seçenek | Anlamı |
|---|---|
| `--include-active` | son 60 dk içinde değişen oturumları da özetle |
| `--render-only` | Claude çağırmadan sadece notları yeniden yaz |

**Örnek:** `sb sessions-sync`

### sb derive

**Ne yapar:** mail/SMS'ten fatura ve kargo çıkar → items (kural tabanlı).

```
sb derive [--days DAYS] [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--days DAYS` | (açıklama yok) |
| `--dry-run` | yalnız say, yazma |

**Örnek:** `sb derive`

### sb extract-dates

**Ne yapar:** maillerden teslim ve randevu tarihlerini çıkarır; --apply olmadan takvime ya da dosyaya yazmaz.

```
sb extract-dates [--days DAYS] [--limit LIMIT] [--model MODEL] [--apply] [--today TODAY]
```

| Seçenek | Anlamı |
|---|---|
| `--days DAYS` | (açıklama yok) |
| `--limit LIMIT` | (açıklama yok) |
| `--model MODEL` | (açıklama yok) |
| `--apply` | (açıklama yok) |
| `--today TODAY` | (açıklama yok) |

**Örnek:** `sb extract-dates`

### sb approve

**Ne yapar:** onay-bekleyenler.md'de [x] işaretlileri takvime ekle.

```
sb approve [--apply]
```

| Seçenek | Anlamı |
|---|---|
| `--apply` | (açıklama yok) |

**Örnek:** `sb approve`

### sb add-event

**Ne yapar:** takvime kurallı etkinlik ekle.

```
sb add-event [--minutes MINUTES] [--note NOTE] [--apply] tag title date [time]
```

| Değer | Anlamı |
|---|---|
| `tag` | SINAV, SUNUM, ÖDEV, BAŞVURU, GÖRÜŞME, YOLCULUK, RANDEVU, |
| `title` | ör. "İzgaz – Gaz Açım" |
| `date` | YYYY-AA-GG |
| `time` | SS:DD (yoksa tüm gün) |

| Seçenek | Anlamı |
|---|---|
| `--minutes MINUTES` | süre (dk) |
| `--note NOTE` | açıklama |
| `--apply` | gerçekten ekle (yoksa deneme) |

**Örnek:** `sb add-event`

### sb housekeep

**Ne yapar:** süresi geçen/biten teslim, görüşme, başvuruları arşive taşı.

```
sb housekeep [--apply]
```

| Seçenek | Anlamı |
|---|---|
| `--apply` | gerçekten taşı (yoksa sadece listeler) |

**Örnek:** `sb housekeep`

### sb inbox-process

**Ne yapar:** 00-Inbox/Dump notlarını yerel modelle ilgili notlara dağıt.

```
sb inbox-process [--apply]
```

| Seçenek | Anlamı |
|---|---|
| `--apply` | gerçekten dağıt (yoksa yalnız kararları listeler) |

**Örnek:** `sb inbox-process`

## Veri içe aktarma

### sb import

**Ne yapar:** dışa aktarım dosyasından içe aktar (whatsapp, telegram, kindle, youtube, spotify, browser, rss, arxiv, zotero, bibtex, auto).

```
sb import [--me ME] [--days DAYS] [--dry-run] [--discover] source [path]
```

| Değer | Anlamı |
|---|---|
| `source` | (zorunlu değer) |
| `path` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--me ME` | kendi adın (WhatsApp/Telegram: mesajların from_addr='me' olur) |
| `--days DAYS` | tarayıcı geçmişi: kaç gün geriye (varsayılan 365) |
| `--dry-run` | yazmadan say: kayıt sayısı, tarih aralığı, 3 örnek başlık |
| `--discover` | browser: bu bilgisayardaki tarayıcı profillerini listele |

**Örnek:** `sb import whatsapp sohbet.zip --me "Ayşe" --dry-run`

### sb history-import

**Ne yapar:** ChatGPT / Claude.ai / Gemini geçmişini içe aktar (önce --apply olmadan dene).

```
sb history-import [--since SINCE] [--until UNTIL] [--exclude EXCLUDE] [--private] [--apply] src
```

| Değer | Anlamı |
|---|---|
| `src` | dışa aktarım zip'i, klasörü ya da conversations.json |

| Seçenek | Anlamı |
|---|---|
| `--since SINCE` | (açıklama yok) |
| `--until UNTIL` | (açıklama yok) |
| `--exclude EXCLUDE` | virgülle ayrılmış kelimeler: geçen sohbet alınmaz |
| `--private` | notları gizli yap (otomatik bağlama girmez) |
| `--apply` | (açıklama yok) |

**Örnek:** `sb history-import conversations.json`

### sb takeout

**Ne yapar:** Google Takeout zip'lerinden Gemini, Keep, Chrome, YouTube, etkinlik geçmişi, Play.

```
sb takeout [--account ACCOUNT] [--dry-run] paths [paths ...]
```

| Değer | Anlamı |
|---|---|
| `paths` | zip dosyaları ya da içinde takeout-*.zip olan klasör |

| Seçenek | Anlamı |
|---|---|
| `--account ACCOUNT` | hangi hesap (ör. main, side) — Keep notlarının kimliği için |
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb takeout`

### sb linkedin-import

**Ne yapar:** 00-Inbox/_imports altındaki LinkedIn arşivini kasaya aktar.

```
sb linkedin-import [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb linkedin-import`

## Arama ve beyin

### sb search

**Ne yapar:** Belgeler, mailler, SMS ve Drive içinde ara.

```
sb search [--limit LIMIT] query [query ...]
```

| Değer | Anlamı |
|---|---|
| `query` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--limit LIMIT` | (açıklama yok) |

**Örnek:** `sb search "fatura nisan"`

### sb find

**Ne yapar:** karma arama (kelime + anlam) bütün kaynaklarda.

```
sb find [-k K] [--kind KIND] [--since SINCE] [--until UNTIL] query
```

| Değer | Anlamı |
|---|---|
| `query` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `-k K` | (açıklama yok) |
| `--kind KIND` | note \| mail \| chat \| file \| item |
| `--since SINCE` | (açıklama yok) |
| `--until UNTIL` | (açıklama yok) |

**Örnek:** `sb find "sözleşme"`

### sb answer

**Ne yapar:** beyin dizininden kaynak numaralı cevap.

```
sb answer [--kind KIND] question
```

| Değer | Anlamı |
|---|---|
| `question` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--kind KIND` | (açıklama yok) |

**Örnek:** `sb answer "geçen ay en çok kimle yazıştım?"`

### sb similar

**Ne yapar:** bir belgeye benzeyen belgeler (doc_id: note:<yol> | mail:<hesap>:<id> ..).

```
sb similar doc_id
```

| Değer | Anlamı |
|---|---|
| `doc_id` | (zorunlu değer) |

**Örnek:** `sb similar`

### sb search2

**Ne yapar:** gelişmiş arama: doğal dil süzgeçleri, kayıtlı aramalar, araştırma, hatırlama, ek/görsel, SSS.

```
sb search2 [--save] [--recall RECALL] [--research RESEARCH] [--web] [--attachments ATTACHMENTS] [--images IMAGES] [--index] [--saved] [--faq] [--eval EVAL] [query]
```

| Değer | Anlamı |
|---|---|
| `query` | doğal dil sorgu ('geçen ay hocadan gelen mailler') |

| Seçenek | Anlamı |
|---|---|
| `--save` | sonuçları 40-Kaynaklar/Aramalar'a not olarak kaydet |
| `--recall RECALL` | yarım hatırlanan şeyi bul |
| `--research RESEARCH` | çok adımlı araştırma → 40-Kaynaklar/Araştırmalar |
| `--web` | --research: alt soruları DuckDuckGo'da da ara (kasa içeriği gitmez) |
| `--attachments ATTACHMENTS` | mail ekleri + belge içeriği içinde ara |
| `--images IMAGES` | görsellerin OCR metninde ara |
| `--index` | görsel OCR dizinini güncelle |
| `--saved` | kayıtlı aramaları kontrol et (yeni eşleşmeler) |
| `--faq` | soru günlüğünden 40-Kaynaklar/SSS.md üret |
| `--eval EVAL` | arama kalite testi YAML'ı (hit@5, MRR) |

**Örnek:** `sb search2`

### sb index

**Ne yapar:** beyin dizinini güncelle (notlar, mailler/mesajlar, belgeler, diğer kaynaklar + gömme).

```
sb index [--sources SOURCES] [--days DAYS] [--no-embed] [--stats]
```

| Seçenek | Anlamı |
|---|---|
| `--sources SOURCES` | (açıklama yok) |
| `--days DAYS` | mesajlar için geriye kaç gün |
| `--no-embed` | (açıklama yok) |
| `--stats` | (açıklama yok) |

**Örnek:** `sb index`

### sb mentions

**Ne yapar:** kişi notlarına 'Bahsedildiği yerler' bölümü (beyin dizininden).

```
sb mentions
```

**Örnek:** `sb mentions`

### sb chat-links

**Ne yapar:** WhatsApp/Telegram sohbetlerini kişi ve proje notlarına bağla.

```
sb chat-links
```

**Örnek:** `sb chat-links`

### sb clusters

**Ne yapar:** notları konu kümelerine ayır (40-Kaynaklar/Kümeler; --docs: belge/mail/sohbet kümeleri → Analiz).

```
sb clusters [-k K] [--docs]
```

| Seçenek | Anlamı |
|---|---|
| `-k K` | (açıklama yok) |
| `--docs` | (açıklama yok) |

**Örnek:** `sb clusters`

### sb suggest-links

**Ne yapar:** anlamca yakın ama bağlı olmayan notlar (--apply: [x] işaretlilere bağlantı; --auto: kurala göre karar ver ve bağla).

```
sb suggest-links [--apply] [--auto] [--threshold THRESHOLD]
```

| Seçenek | Anlamı |
|---|---|
| `--apply` | (açıklama yok) |
| `--auto` | (açıklama yok) |
| `--threshold THRESHOLD` | (açıklama yok) |

**Örnek:** `sb suggest-links`

### sb analyze

**Ne yapar:** beyin analizleri (40-Kaynaklar/Analiz): zaman çizelgesi, proje haritası, sınıflar, tekrarlar..

```
sb analyze [--dry-run] [{all,timeline,projects,classify,duplicates,aging,freshness,conflicts,skills,glossary,tags,quality,trust,map,pipeline}] [topic]
```

| Değer | Anlamı |
|---|---|
| `topic` | timeline için konu |

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | kasaya yazma, özet bas |

**Örnek:** `sb analyze`

### sb merge-people

**Ne yapar:** tekrar kişi notları: öneri yaz (--apply: [x] işaretlileri birleştir; --auto: kurala göre karar ver ve birleştir).

```
sb merge-people [--apply] [--auto]
```

| Seçenek | Anlamı |
|---|---|
| `--apply` | (açıklama yok) |
| `--auto` | (açıklama yok) |

**Örnek:** `sb merge-people`

### sb graph-style

**Ne yapar:** Obsidian grafiği renkleri (küme başına, kategori); görünürlüğe dokunmaz. --hide: teknik/etiket/ek/bağlantısız düğümleri gizle.

```
sb graph-style [--hide]
```

| Seçenek | Anlamı |
|---|---|
| `--hide` | (açıklama yok) |

**Örnek:** `sb graph-style`

### sb topic-map

**Ne yapar:** kasadaki projelerden konu haritası notlarını üretir (argümansız).

```
sb topic-map
```

**Örnek:** `sb topic-map`

### sb links

**Ne yapar:** Teknoloji/konu bağlantı notları (derlenmiş projelerden).

```
sb links [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb links`

### sb deep-relink

**Ne yapar:** derlenmiş proje/ders dosyalarının bağlantılarını yeniden kurar (argümansız).

```
sb deep-relink
```

**Örnek:** `sb deep-relink`

### sb ask

**Ne yapar:** tek soru: verilen (ya da tasks.chat) modele sor, ör. --model openai:gpt-5-mini.

```
sb ask [--model MODEL] [--stream] question
```

| Değer | Anlamı |
|---|---|
| `question` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--model MODEL` | <sağlayıcı>:<model>; boşsa tasks.chat |
| `--stream` | cevabı parça parça yazdır |

**Örnek:** `sb ask`

## Okul, plan ve görevler

### sb obs-import

**Ne yapar:** _system/data/obs.yaml (ÖBS, elle) → Akademik Durum + ders not geçmişi.

```
sb obs-import [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb obs-import`

### sb course-files

**Ne yapar:** Bilgisayardaki ders dosyalarını ders notlarına link olarak bağla.

```
sb course-files [--dry-run]
```

| Seçenek | Anlamı |
|---|---|
| `--dry-run` | (açıklama yok) |

**Örnek:** `sb course-files`

### sb course-deep

**Ne yapar:** ders dosyalarının metninden Claude ile 'Ders dosyası' derler; ders kodu ya da --all verilir.

```
sb course-deep [--all] [--force] [--show-prompt] [code]
```

| Değer | Anlamı |
|---|---|
| `code` | ders kodu, ör. YPZ204 |

| Seçenek | Anlamı |
|---|---|
| `--all` | (açıklama yok) |
| `--force` | (açıklama yok) |
| `--show-prompt` | (açıklama yok) |

**Örnek:** `sb course-deep`

### sb courses

**Ne yapar:** ders panosu: yaklaşan sınav/teslim, dosya sayısı.

```
sb courses
```

**Örnek:** `sb courses`

### sb gpa

**Ne yapar:** GANO; --what-if KOD=HARF ile senaryo.

```
sb gpa [--what-if [WHAT_IF ...]]
```

| Seçenek | Anlamı |
|---|---|
| `--what-if [WHAT_IF ...]` | (açıklama yok) |

**Örnek:** `sb gpa --what-if BIL101=AA`

### sb plan

**Ne yapar:** bugünün planı: en önemli 3 iş, takvim boşluklarına bloklar, uyarılar.

```
sb plan
```

**Örnek:** `sb plan`

### sb tasks-board

**Ne yapar:** görev panosu (yapılacak / yapılıyor / bitti).

```
sb tasks-board
```

**Örnek:** `sb tasks-board`

### sb task

**Ne yapar:** görevler (25-Görevler): add | update | list.

```
sb task [--text TEXT] [--owner OWNER] [--project PROJECT] [--due DUE] [--criterion CRITERION] [--status STATUS] [--evidence EVIDENCE] [--note NOTE] [--expected-revision EXPECTED_REVISION] {add,update,list} [title]
```

| Değer | Anlamı |
|---|---|
| `title` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--text TEXT` | (açıklama yok) |
| `--owner OWNER` | (açıklama yok) |
| `--project PROJECT` | (açıklama yok) |
| `--due DUE` | (açıklama yok) |
| `--criterion CRITERION` | gözlenebilir bitiş ölçütü (verilirse bitirmek için kanıt gerekir) |
| `--status STATUS` | (açıklama yok) |
| `--evidence EVIDENCE` | kanıt dosyası (kasa içi yol) |
| `--note NOTE` | (açıklama yok) |
| `--expected-revision EXPECTED_REVISION` | (açıklama yok) |

**Örnek:** `sb task add "Rapor taslağı"`

### sb automation-tick

**Ne yapar:** otomasyon kurallarını bir kez değerlendir (dış etkili eylemler onaya düşer).

```
sb automation-tick
```

**Örnek:** `sb automation-tick`

## Hafıza ve Claude Code

### sb receipt

**Ne yapar:** iş sonucu makbuzu (kaynak bağlantılı tek satır; günlük nota da düşer).

```
sb receipt --summary SUMMARY [--ref REF] [--link LINK] [--learned LEARNED] [--project PROJECT] [--session SESSION] [--event-id EVENT_ID]
```

| Seçenek | Anlamı |
|---|---|
| `--summary SUMMARY` | (açıklama yok) |
| `--ref REF` | kasa içi göreli yol (tekrarlanabilir) |
| `--link LINK` | https bağlantı (PR, sayfa) |
| `--learned LEARNED` | kalıcı öğrenim (tek cümle); yoksa boş |
| `--project PROJECT` | (açıklama yok) |
| `--session SESSION` | (açıklama yok) |
| `--event-id EVENT_ID` | (açıklama yok) |

**Örnek:** `sb receipt`

### sb recap

**Ne yapar:** son günlerde ne yapıldı (makbuzlardan).

```
sb recap [--days DAYS] [--project PROJECT]
```

| Seçenek | Anlamı |
|---|---|
| `--days DAYS` | (açıklama yok) |
| `--project PROJECT` | (açıklama yok) |

**Örnek:** `sb recap`

### sb learn

**Ne yapar:** öğrenim adayı defteri.

```
sb learn [--source SOURCE] [--scope SCOPE] [--list] [candidate]
```

| Değer | Anlamı |
|---|---|
| `candidate` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--source SOURCE` | (açıklama yok) |
| `--scope SCOPE` | (açıklama yok) |
| `--list` | (açıklama yok) |

**Örnek:** `sb learn`

### sb concept

**Ne yapar:** kavram notu oluştur/güncelle (40-Kaynaklar/Kavramlar).

```
sb concept --text TEXT [--point POINT] [--limits LIMITS] [--source SOURCE] title
```

| Değer | Anlamı |
|---|---|
| `title` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--text TEXT` | (açıklama yok) |
| `--point POINT` | (açıklama yok) |
| `--limits LIMITS` | (açıklama yok) |
| `--source SOURCE` | (açıklama yok) |

**Örnek:** `sb concept`

### sb connect

**Ne yapar:** iki not arasında gerekçeli bağlantı notu.

```
sb connect --why WHY a b
```

| Değer | Anlamı |
|---|---|
| `a` | (zorunlu değer) |
| `b` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--why WHY` | (açıklama yok) |

**Örnek:** `sb connect`

### sb trace

**Ne yapar:** dosya değişmeyen anlamlı sohbetin ≤450 karakterlik izi.

```
sb trace [--session SESSION] [--project PROJECT] text
```

| Değer | Anlamı |
|---|---|
| `text` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--session SESSION` | (açıklama yok) |
| `--project PROJECT` | (açıklama yok) |

**Örnek:** `sb trace`

### sb error-log

**Ne yapar:** hata kataloğu; aynı hata ikinci kez gelince çözüm kural olur.

```
sb error-log [--fix FIX] error
```

| Değer | Anlamı |
|---|---|
| `error` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--fix FIX` | (açıklama yok) |

**Örnek:** `sb error-log`

### sb knowledge-index

**Ne yapar:** Kavramlar/_Dizin.md'yi yenile.

```
sb knowledge-index
```

**Örnek:** `sb knowledge-index`

### sb hook-flush

**Ne yapar:** (kanca içi) oturum dökümünü yerel modelle özetleyip günlük nota yaz.

```
sb hook-flush --transcript TRANSCRIPT --session SESSION [--project PROJECT] [--reason {end,precompact}]
```

| Seçenek | Anlamı |
|---|---|
| `--transcript TRANSCRIPT` | (açıklama yok) |
| `--session SESSION` | (açıklama yok) |
| `--project PROJECT` | (açıklama yok) |
| `--reason {end,precompact}` | (açıklama yok) |

**Örnek:** `sb hook-flush`

### sb person

**Ne yapar:** kişi notuna beyan / çıkarım / takma ad (60-Kişiler).

```
sb person [--inference] [--reject] [--alias ALIAS] name [fact]
```

| Değer | Anlamı |
|---|---|
| `name` | (zorunlu değer) |
| `fact` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--inference` | modelin tahmini: onay bekleyen çıkarım |
| `--reject` | bu metni içeren çıkarımı reddet |
| `--alias ALIAS` | (açıklama yok) |

**Örnek:** `sb person`

### sb rule

**Ne yapar:** kalıcı kural ekle (--scope proje: yalnız o projede yüklenir).

```
sb rule [--scope SCOPE] text
```

| Değer | Anlamı |
|---|---|
| `text` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--scope SCOPE` | (açıklama yok) |

**Örnek:** `sb rule`

### sb hygiene

**Ne yapar:** hafıza hijyeni raporu (tekrar, kopuk bağlantı, bayat, büyüyen dosya).

```
sb hygiene
```

**Örnek:** `sb hygiene`

### sb mode

**Ne yapar:** Claude Code hafıza modu: normal | ekonomik | manuel (config/hafiza.yaml).

```
sb mode [{normal,ekonomik,manuel}]
```

**Örnek:** `sb mode ekonomik`

### sb persona

**Ne yapar:** asistan kimliği ve hafıza işleri: --reflect (günlük yansıma), --weekly (beni tanı), --prefs (tercih adayları).

```
sb persona [--reflect] [--weekly] [--prefs]
```

| Seçenek | Anlamı |
|---|---|
| `--reflect` | (açıklama yok) |
| `--weekly` | (açıklama yok) |
| `--prefs` | (açıklama yok) |

**Örnek:** `sb persona`

### sb qwen

**Ne yapar:** yerel Qwen'e iş ver (büyük metin/log/belge özeti; Claude limiti harcanmaz).

```
sb qwen [--file FILE] [--text TEXT] instruction
```

| Değer | Anlamı |
|---|---|
| `instruction` | (zorunlu değer) |

| Seçenek | Anlamı |
|---|---|
| `--file FILE` | (açıklama yok) |
| `--text TEXT` | (açıklama yok) |

**Örnek:** `sb qwen "bu log dosyasını özetle"`

### sb night

**Ne yapar:** gece koşusu: 00-Inbox/Gece işleri.md maddelerini claude -p ile sırayla çalıştır.

```
sb night [--plan] [--run] [--start] [--add ADD] [--where WHERE]
```

| Seçenek | Anlamı |
|---|---|
| `--plan` | yalnız ne çalışacağını göster |
| `--run` | şimdi çalıştır (bu pencerede, sırayla) |
| `--start` | arka planda başlat (bitince bildirim) |
| `--add ADD` | listeye iş ekle |
| `--where WHERE` | --add için çalışma klasörü |

**Örnek:** `sb night`

### sb arsenal

**Ne yapar:** kasada 'Araçlar ve erişimler' notunu güncelle.

```
sb arsenal
```

**Örnek:** `sb arsenal`

### sb capture

**Ne yapar:** Beyne at: panodaki bağlantı/metni kasaya kaydet (Ctrl+Alt+B).

```
sb capture [--file FILE] [text]
```

| Değer | Anlamı |
|---|---|
| `text` | pano yerine bu metni/bağlantıyı kaydet |

| Seçenek | Anlamı |
|---|---|
| `--file FILE` | dosyayı kaydet (Sağ tık › Gönder › Beyne At bunu kullanır) |

**Örnek:** `sb capture`

### sb asistan-undo

**Ne yapar:** asistanın son kasa değişikliğini geri al.

```
sb asistan-undo
```

**Örnek:** `sb asistan-undo`

## Telegram

### sb telegram

**Ne yapar:** (İsteğe bağlı) Telegram: bağla / bota yazılanları 00-Inbox'a çek / deneme.

```
sb telegram {setup,pull,send}
```

**Örnek:** `sb telegram`

## Ses

### sb voice

**Ne yapar:** ses: --setup (faster-whisper kurulum durumu), --transcribe <dosya> (yazıya çevir).

```
sb voice [--setup] [--transcribe TRANSCRIBE] [--lang LANG]
```

| Seçenek | Anlamı |
|---|---|
| `--setup` | (açıklama yok) |
| `--transcribe TRANSCRIBE` | (açıklama yok) |
| `--lang LANG` | (açıklama yok) |

**Örnek:** `sb voice --setup`
