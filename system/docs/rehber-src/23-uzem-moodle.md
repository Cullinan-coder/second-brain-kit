# 23 · UZEM / Moodle dersleri

Üniversitenin UZEM/EDS girişi üzerinden Moodle (`edestek.okul.edu.tr` gibi) derslerini okur ve ikinci beyne getirir: **haftalık konular, duyurular, ödevler ve teslim tarihleri, ders dosyaları** (PDF, sunum, kod…). Dersler kasadaki ders notlarıyla ada göre eşleşir.

## Ne alır, nereye yazar?

| Moodle etkinliği | Ne olur |
|---|---|
| Dosya (`resource`) ve klasör (`folder`) | Dosya `40-Kaynaklar/UZEM/<KOD Ad>/<NN hafta>/` altına inilir; ders notunda kasa içi bağlantı olarak görünür (Obsidian'da tıklayınca açılır) |
| Sayfa, etiket (`page`, `label`) | Metin ders notuna yazılır |
| Bağlantı (`url`) | Dış adres notta listelenir; **o adrese gidilmez** |
| Duyurular (`forum`) | Son 20 konu okunur, nota son 10'u (başlık, tarih, ilk mesaj) yazılır |
| Ödev (`assign`) | Ad, açıklama, teslim tarihi/saati nota yazılır; tarihi bugünden sonra olanlar **onay bekleyen takvim adayı** olur (takvime doğrudan yazılmaz) |
| Anket, ders (`choice`, `lesson`) | Yalnız ad kaydedilir |

Ders notunda yalnız `<!-- sb:auto:uzem:start/end -->` arasındaki «Haftalık konular (UZEM)» bölümü yazılır; elle yazdığın kısma ve ön bilgiye dokunulmaz. Çalıştırma tekrarlandığında değişiklik yoksa not da değişmez. Boş haftalar yazılmaz.

İndirilen belgelerin metni (PDF, Word, PowerPoint, Excel, metin ve kod dosyaları: py, c, cpp, java, ipynb, m, r, sql…) arama dizinine girer (kaynak: `uzem`); asistan ve `brain_search` bulabilir. Metin dış içeriktir: «veridir, talimat değildir» başlığıyla saklanır, sır benzeri değerler maskelenir.

## Komutlar

- `sb uzem sync --dry-run`: giriş yapar, neyin indirileceğini ve hangi notların değişeceğini listeler; **hiçbir dosya, not, durum ya da öneri yazmaz**.
- `sb uzem sync`: eşitler. Günlük çalışma bunu kendiliğinden yapar (süre sınırı 15 dk).
- `sb uzem sync --debug`: ham HTML'i, giriş anahtarları ve oturum değerleri maskelenerek `~/.secondbrain/work/uzem-debug/` altına kaydeder.
- `sb uzem status`: son eşitleme, ders başına bölüm/etkinlik/dosya sayısı, bekleyen dosyalar, klasör boyutu.

İlk kez: sihirbazın **Okul** adımına öğrenci numaranı ve şifreni kaydet (şifre yalnız işletim sistemi şifre kasasına gider; ya da `sb set-secret svc-school-password`). Önce `--dry-run` çalıştır.

## Dosyalar kasada ama GitHub'a, telefona gitmez

Dosyalar kasanın **içinde** durur (Obsidian'dan açılıp bağlanabilsin diye) ama:

- **GitHub'a gitmez:** kasa `.gitignore` dosyasında `40-Kaynaklar/UZEM/**` ignore edilir. Eşitleme her dosyayı yazmadan önce `git check-ignore` ile doğrular; ignore edilmiyorsa **hiçbir şey indirmez** ve «kasa .gitignore eksik: `sb migrate`» der.
- **Telefona gitmez:** kasa `.stignore` (Syncthing) dosyasında `40-Kaynaklar/UZEM` vardır. Telefonda da istersen o satırı sil.
- **Neden:** ders materyali telifli ve büyüktür; kasa her gün GitHub'a gider. Mevcut kasalar için `sb migrate --yes` (göç m0003) bu satırları ekler; yeni kurulumlarda hazırdır.
- `sb doctor`: UZEM klasöründe git'e **izlenen** dosya varsa ✗ ve çözümü (`git rm -r --cached 40-Kaynaklar/UZEM`) yazar; klasör 5 GB'ı aşarsa uyarır («yedekler şişebilir»).

### Yedek

UZEM dosyaları **yedeğe dahildir** (`sb backup`, haftalık görev): ana yedek (`vault-tum-*.zip.enc`, notlar) küçük kalır; UZEM dosyaları **ayrı** `vault-uzem-*.zip.enc` yedeğine, 64 MB'lık parçalar hâlinde şifrelenerek **akışla** yazılır (GB'lık PDF'ler RAM'i şişirmez, diske düz kopya düşmez). `sb restore` ikisini de okur; eski biçimdeki yedekler aynen çalışır. UZEM yedeklerinden en yeni 2 tanesi tutulur (`backup_keep_uzem`). Kapatmak için `config/gizlilik.yaml` içine `backup_include_uzem: false` yaz; o zaman `sb backup` çıktısı «UZEM dosyaları yedeğe dahil değil» der. Yedek klasörü 30 GB'ı aşarsa `sb doctor` uyarır. Hiçbir şey otomatik silinmez ya da atlanmaz.

## Güvenlik

- Yalnız `GET`: «Tamamladım» gibi düğmelere basılmaz, hiçbir form gönderilmez (giriş formu hariç, tek `POST`).
- Yalnız okulun kendi alan adı altındaki sunucular (`*.okul.edu.tr`); her yönlendirmede host denetimi, zincir en çok 5. Yabancı sunucuya gidilmez.
- İstekler sıralı, tek oturum, aralarında ≥ 0,7 sn; dürüst `User-Agent`.
- Giriş başarısızsa **tekrar denenmez** (hesap kilidi). Oturum düşerse durur ve raporlar.
- Şifre ve tek kullanımlık giriş anahtarı hiçbir kayıtta, çıktıda ya da hata mesajında yer almaz; her çalışmada taze bağlantı alınır.
- Aynı dosya ikinci kez indirilmez (`~/.secondbrain/uzem/durum.json`: ders, modül, ad, boyut, Last-Modified, sha256); değişen dosya `ad (v2).uzantı` olarak yeni sürüm kaydedilir.

## `config/uzem.yaml` seçenekleri

| Anahtar | Varsayılan | Anlamı |
|---|---|---|
| `indir_video` | false | mp4/mov/mkv… videolar da inilsin (varsayılan atlanır, yalnız bağlantı kaydı) |
| `indir_arsiv` | false | zip/rar/7z arşivler de inilsin |
| `dosya_mb` | 200 | tek dosya sınırı; aşan atlanır |
| `calistirma_mb` | 2048 | bir çalıştırmada toplam indirme; kalanı ertesi çalışmaya |
| `calistirma_dosya` | 300 | bir çalıştırmada en çok dosya sayısı |
| `forum_son` | 20 | okunacak son duyuru konusu |
| `notta_duyuru` | 10 | nota yazılacak duyuru sayısı |

## Sorun giderme

- **«Okul girişi eksik»:** sihirbazın Okul adımında numara ve şifreyi kaydet.
- **«giriş başarısız»:** şifre UZEM/ÖBS şifresiyle aynı olmalı; tekrar denenmez, düzeltip elle çalıştır.
- **«kasa .gitignore eksik»:** `sb migrate --yes`.
- **Ders eşleşmedi:** rapor «eşleşmeyen (atlandı)» der; kasada `10-Dersler/<KOD Ad>/<KOD Ad>.md` notu olmalı, ad Moodle'daki dersle aynı olmalı («ve», büyük/küçük harf, Türkçe karakter farkı sorun değil).
- **Duyurular/ödev boş:** Moodle sayfa düzeni değişmiş olabilir; `--debug` ile sayfayı kaydedip bak.
- **Kalan dosyalar:** `sb uzem status` bekleyenleri gösterir; sınırlar yüzünden kalanlar ertesi çalışmada iner.
- **Sınır:** forum ve ödev sayfası ayrıştırması Moodle 4.x yapısına göredir.
