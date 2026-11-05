# Değişiklikler

Kurulu sürümünü `sb version` gösterir. Güncellemek için `sb update` yaz; notlarına ve ayarlarına dokunmaz.

## 0.13.1 — 2026-11-05

- Kök `SHA256SUMS` temiz klonda diske düşen içerikten hesaplanır: `eol=crlf` kuralıyla CRLF dağıtılan `.ps1` betikleri dahil (ilk denemede 15 dosya tutmuyordu).

İş ortağı incelemesi (v0.12.0) düzeltmeleri. Güvenlik denetimi özeti: `docs/GUVENLIK-DENETIM-OZET.md`.

### Güvenlik (B-01)
- **`git diff` ile kasa dışı dosya okuma kapandı:** komut ev klasöründe (genelde git deposu değil) çalıştığı için `git diff A B` iki dosyayı karşılaştırma kipinde onaysız gösterebiliyordu.
  Artık git komutlarında dosya yoluna benzeyen her bağımsız değişken (`/ \ . :` içeren, `NUL`, `/dev/null`, `--` sonrası hepsi, `rev:yol` biçiminde yol kısmı) kasa/Workspace kuralıyla denetlenir
  (`_system/config` hariç) ve `git diff` iki ya da daha fazla konumsal argüman alırsa onay ister. Seçenek kısaltmaları (`--outp=`), `-O`, `--orderfile`, `--help`, `-c`/`--git-dir`/`--work-tree`/`GIT_DIR=` önekleri,
  `git grep --no-index`, `hash-object`, `cat-file` onaylı. `git status`, `git log`, argümansız `git diff` serbest kalır.
  **Etkisi:** `git diff HEAD~1 HEAD` ve `git log -- dosya.py` gibi komutlar (ev klasöründe, kasa/Workspace dışı yolla) artık kart ister.

### Kit bütünlüğü
- **Kök `SHA256SUMS` temiz checkout'ta tutuyor:** özetler Windows CRLF çalışma kopyasından değil, git'in depoda SAKLAYACAĞI içerikten hesaplanır (`text=auto` sezgisi: CRLF→LF, NUL/yalın CR içeren ikili dosya olduğu gibi; iç içe `.gitattributes` kuralları dahil).
- **`sb verify` (yeni):** kurulu `_system` klasörünü kitin `SHA256SUMS` dosyasıyla karşılaştırır; yerel değişmiş / eksik / kitte olmayan fazla dosyaları ayrı listeler. `config/`, `.venv`, `data/`, `__pycache__`, `*.pyc` gibi
  kurulumdan sonra değişmesi normal olanlar atlanır (çıktıda yazar). Kurucular (`install.py`, `setup/engine.py`) `SHA256SUMS` dosyasını `_system/SHA256SUMS` olarak da kopyalar; eski kurulumda dosya yoksa `sb update` sonrası oluşur.
  `python setup/engine.py --verify <zip> <sha256>` (zip özeti) aynen kalır.
- **Belge:** CHANGELOG'daki depoda olmayan rapor atfı kaldırıldı; yerine saldırı adımı içermeyen `docs/GUVENLIK-DENETIM-OZET.md` (30 bulgu + B-01 durum tablosu, D-07 / D-17 / D-30 ayrıntısı).

### Hazır uygulamalar güven zinciri (ClipBoardLine, Nashi)
- **Bilinen iyi sürüm + dosya SHA-256 katalogda sabit** (her platform): ClipBoardLine windows-1.7.8-build71 `ClipBoardLine-Setup-1.7.8-x64.exe` `69a2e770…7387`, macOS `ClipboardLine-1.7.8-build78.zip` `6bcd8be6…9aed`;
  Nashi v0.7.14-45 `Nashi-Windows-x64.zip` `9b822f18…d3fb` (gerçek dosyayla çapraz doğrulandı), macOS `Nashi-macOS-arm64.zip` `28d3cfd3…2f51d`. `install` yalnız bu sürümü kurar, indirileni SABİT özetle karşılaştırır
  (uyuşmazsa siler ve durur); sürümdeki SHA256SUMS ikinci denetimdir (sabitle çelişirse indirmeden durur). Yayıncı hesabı ele geçirilse bile sabit özet değişmez.
- **`sb apps update <id>` artık yalnız bildirir:** yeni sürüm, değişiklik notu bağlantısı ve yeni dosya özeti gösterilir; kurmak için açık onay: `sb apps update <id> --accept <sürüm>` (sürüm+özet `~/.secondbrain/apps_pins.json` içinde sabitlenir, sonra kurulur).
  Arayüzde (Çalışmaya başla → Uygulamalar) «Yeni sürüm var mı?» ve onay kartı «Bu sürümü kabul et» (yalnız sabitler; kurulum `sb apps install <id> --force`). Kullanıcı sabiti kataloğdan eskiyse yok sayılır.
- **Manifest doğrulaması:** `app.<platform>.sha256` zorunlu. **Sektör paketi `tekstil`:** `disabled: [clipboardline, nashi]`, ClipBoardLine varsayılan kapalı.

## 0.13.0 — 2026-11-05

### Kasa şeması
- **Kasa şema sürümü + göç sistemi:** kasa biçimi (ön bilgi alanı, klasör/dosya adı, config anahtarı) artık sürümlü: `_system/config/kasa.yaml` → `schema_version: N` (dosya/anahtar yoksa 1 = mevcut kasalar; yeni kurulan kasaya güncel sürüm yazılır).
  Göçler `sb/migrations/m000N_*.py` sıralı modülleridir. Her adım: kasa git'i temiz mi (kirliyse durur) → **şifreli yedek** (alınamazsa durur) → göç → tek commit «şema göçü N→M»;
  hata olursa yalnız göçün kendi değişiklikleri geri alınır, başka hiçbir şeye dokunulmaz.
- **`sb migrate --check`** (salt okunur: kaç göç bekliyor, hangi notlar değişecek; bekleyen varsa çıkış 3) · **`--dry-run`** · **`--yes`** (uygular). `sb update` güncelleme sonrası bekleyen göçü listeler ve onay ister (`--yes` ile otomatik).
  `sb doctor` kasa şeması koddan gerideyse ✗ (`sb migrate`), kasa koddan yeniyse ✗ (eski kod + yeni kasa; yazma komutları önce uyarır).
- **İlk göç (m0002):** `type` taşıyan ama `source` / `source_id` alanı olmayan notlara (Asistan.md, Açık konular.md, Makbuzlar, Inbox önerileri ... 17 not) `source: manual`, `source_id: ""` eklenir. Başka hiçbir değer değişmez; okuyan kod eksik alanı zaten «manual» sayar.
  **Etkisi:** `sb update` sonrası ilk seferde `sb doctor` bir kez ✗ gösterir; `sb migrate --yes` ile kapanır.

### Mimari (denetim D-30, D-06a)
- **Tek sohbet yığını:** klasik arayüz (`/classic`, `PAGE`) ve onun ayrı sohbet yolu kaldırıldı; `/classic` ana sayfaya yönlenir. Eski uçlar (`POST /api/chat`, `/api/decide`, `/api/reset`)
  v2'nin tek giriş noktasına giden ince uyumluluk katmanıdır (yanıt biçimi aynı). Model geçmişi her turda sohbet kaydından kurulur (araç çıktıları turdan tura taşınmaz) ve **kirlilik bayrağı**
  (bağlamda mail/belge/ekran içeriği var) artık sohbet kaydında kalıcıdır: sunucu yeniden başlasa ya da eski sohbet açılsa da dış içerik görmüş sohbette komut/kalıcı yazma onaya düşer; yeni sohbette sıfırlanır.
- **Tek onay deposu** (`sb/approvals.py`, `~/.secondbrain/approvals.jsonl`; süreçler arası kilit + atomik yazım): sohbet kartları, otomasyon onayları ve mail/SMS tarih adayları aynı yerde; her kayıtta
  tür, kaynak (bilgisayar/telefon), sohbet ve **süre aşımı** (komut/WhatsApp 12 saat, takvim 7 gün, tarih adayı 60 gün). Kartlar **yeniden başlatmada kaybolmaz**; komut, WhatsApp, takvim,
  takvim silme, kasa eylemi, gece işi ve otomasyon kartları yeniden açılıştan sonra da onaylanır (bellek içi kartlar «süresi doldu» olur). Çift yürütme yok (önce işaretle, sonra yürüt).
  Eski `pending_approvals.jsonl` ilk okumada taşınır (`.tasindi` olarak kalır). `00-Inbox/onay-bekleyenler.md` artık depodan **üretilen görünüm**: Obsidian'da `[x]` = onay, satırı silmek = iptal; eski satırlar depoya alınır.
- **Onaylar görünümü:** asistanın üst çubuğunda ✓ düğmesi + bekleyen sayısı; **Görünümler → Onaylar** hepsini tek listede gösterir (Onayla/İptal). Tek karar ucu `POST /api/v2/approvals/decide`.
  Telefon kuralları korunur ve sıkılaşır: telefon yalnız **kendi** takvim/eylem kartını onaylar; komut, WhatsApp, gece koşusu, silme, otomasyon ve tarih kartları yalnız bilgisayardan; bilgisayardaki kartların metni telefona gösterilmez.
- **Hassasiyet kalıpları tek kaynakta** (`sb/sensitive.py`): kasa süzgeci (`vault_ops.SENSITIVE_RE`), bulut süzgeci (`router`), `redact`, makbuz/hafıza/kural/öğrenim filtreleri ve gizli not (`visibility: private`) denetimi aynı kalıpları kullanır.
  Kalıplar **kelime anlamına** göre: «şifreli / şifreleme / şifrelenmiş» parola sayılmaz; değer taşıyan biçimler («şifre: X», «şifrem 1234», «parola=…», «pin kodu 1234», kart, IBAN, TCKN, API anahtarı) hassastır.
  **Etkisi:** `sb receipt --summary "… şifreli yedek …"` artık reddedilmez; «pin kodu değişti», «şifremi değiştirdim» gibi değersiz cümleler ve 0 ile başlayan telefon numaraları kasaya yazılabilir.
  Bulut süzgeci daha sıkı kalır: sır konusu («şifrem şu», «IBAN'ım») buluta gitmez.
- **WhatsApp ürün dili:** araç `whatsapp_draft` → **`whatsapp_send`** (onaylı gönderim; eski ad bu sürümde takma ad). Arayüz, rehber ve modül açıklaması artık açıkça söylüyor: kartı onaylayınca mesaj **gönderilir**.
- **Belge:** rehberde «Ayarlar nerede durur» tablosu (`config/*.yaml`, `~/.secondbrain`, keyring, `~/.claude.json`: ne var, git'e/yedeğe girer mi) ve «Kasaya hangi metin yazılmaz» tablosu (10 · Güvenlik ve gizlilik).

### Yedek ve CI
- **Yedek kapsamı düzeltildi:** kasa yedeği eskiden yalnız `.md/.enc/.yaml/.png/.jpg/.pdf` alıyordu; **Word, PowerPoint, Excel ekleri, `.jpeg/.webp`, Obsidian ayarları ve canvas'lar yedeğe girmiyordu.**
  Artık `_system` ve `.git` dışındaki her dosya alınır (Office kilit dosyaları `~$…`, yarım indirmeler ve 500 MB üstü dosyalar hariç). 0.12.0 ile alınmış yedekleri yenile: `sb backup`.
- **CI:** her push'ta yalnız Windows testi; macOS testi yalnız sürüm etiketinde (`v*`) ve elle çalıştırmada (gizli depoda macOS dakikası 10 kat sayılıyordu, işler kuyrukta iptal oluyordu).

## 0.12.0 — 2026-11-04

### Güvenlik (denetim 2026-11, ikinci tur: D-10, D-13, D-18, D-20, D-22, D-23, D-25, D-27, D-28, D-29)
- **Yedekler artık gerçekten şifreli (D-10):** kasa yedekleri kasa anahtarıyla (`vault-key`) `~/.secondbrain/backups/vault-*.zip.enc` olarak yazılır; düz metin zip diske hiç düşmez
  (şifreleme öncesi yedeği, geri yükleme öncesi `onceki-*` yedeği dahil). `sb restore` hem `.zip.enc` hem eski `.zip` yedekleri okur. Şifreleme (cryptography/keyring) yoksa ya da anahtar okunamıyorsa
  **düz yedek ALINMAZ**, nedeni söylenir. **Etkisi:** yedeği açmak anahtarı ister; `sb vault-key --export <dosya>` ile anahtarı ayrıca sakla (önceki sürümün «yedekler şifreli» notu o zaman eksikti, şimdi doğru).
  Kod yedeği `system-*.zip` not içermez, düz kalır (`sb update --rollback` okur). **Eski düz zip'ler** (`vault-*.zip`, 0.11 ve öncesi) diskte durur: kontrol edip Geri Dönüşüm Kutusu'na at.
- **Şifreleme git geçmişini uyarır (D-10):** `sb vault-encrypt` / `sb encrypt` sonunda klasörün düz metin notları git geçmişinde duruyorsa kaç not ve hangi commit aralığı olduğunu açıkça yazar.
  Geçmişi temizlemek ayrı ve onaylı: `sb encrypt --purge-history <klasör>` (yalnız anlatır) / `... --confirm` (çalıştırır). Önce kasanın **tam şifreli yedeğini** (zip + git paketi) alır,
  `git filter-repo` yoksa çalışmaz ve nasıl kurulacağını söyler; düz not kaldıysa ya da commit edilmemiş değişiklik varsa reddeder. Geçmişi yeniden yazar: sonrasında uzak depoya **zorla push** gerekir,
  diğer cihazlarda kasa yeniden klonlanmalıdır. Hiçbir zaman otomatik çalışmaz.
- **Haftalık şifreli yedek + `sb backup` + doktor:** haftalık görev (Pazar 15:00, `sb weekly`) şifreli tam kasa yedeği alır, son **8**'ini tutar (`config/gizlilik.yaml` → `backup_keep`);
  yalnız `vault-tum-*.zip.enc` budanır. `sb backup` elle alır (budamaz). `sb doctor` «Kasa yedeği: N gün önce» gösterir; **14 günden eskiyse ya da hiç yoksa ✗**.
- **Yayın zinciri (D-13):** `release.yml` kilit dosyasından kurar (`uv export --frozen --group build` + `pip --require-hashes`; `pyproject.toml`a `build` bağımlılık grubu, `uv.lock` yalnız eklemeyle güncellendi),
  GitHub Actions adımları tam commit SHA'sına sabit (yorumda sürüm etiketi), yazma izni yalnız etiketle çalışan ayrı `publish` işinde; sürüme Setup.exe ve macOS zip için **`SHA256SUMS`** eklenir.
  `ci.yml` `uv run --frozen`. **`install.ps1` / `install.sh` indirdiği Setup dosyasını `SHA256SUMS` ile doğrular; uyuşmazsa ya da özet dosyası yoksa dosyayı siler ve durur** (özetsiz eski sürümler artık otomatik kurulmaz).
- **SSRF / DNS rebinding (D-18):** `sb capture` ve «beyne at» bağlantı indirirken adresi bir kez çözüp doğrular ve bağlantıyı doğrulanan IP'ye yapar (Host/SNI alan adı kalır); her yönlendirme adımı yeniden doğrulanır, ortam proxy'si kullanılmaz.
- **Süreçler arası kilit + atomik yazma (D-20):** yeni `sb/filelock.py`. Onay kaydı (`pending_approvals.jsonl`), otomasyon kuralları/durumu, telefon eşleme jetonları, push abonelikleri, asistan kural/hafıza notları,
  `note_update` eklemeleri ve bellek notu ekleme kilit altında okunup yazılır; dosyalar geçici dosya + fsync + `os.replace` ile yazılır (yarım yazma dosyayı bozmaz). `sb daily` ile arayüz aynı anda onay kaydına dokunsa kayıt kaybolmaz.
- **Ollama kurulumu (D-22):** macOS'ta ortak `/tmp` yerine `mktemp -d`, `codesign --verify` geçmeden kurmaz; Windows'ta kurucu özel dizine iner ve Authenticode imzası geçerli + imzalayan «Ollama» değilse **çalıştırılmaz, silinir**.
- **Telefon eşleme (D-23):** yanlış deneme kilidi **istemci IP'si başına** (tailnet'teki bir cihaz gerçek eşlemeyi kilitleyemez), kod **10 dakika** geçerli (süresi dolunca yenilenir; ekranda görünen kod da), sayaçlar kilitli; tüm istemcilerden toplam 30 yanlışta kod yenilenir.
- **`schedule.ps1` (D-25):** Syncthing yalnız bilinen kurulum yollarından/PATH'ten alınır (ev klasöründe «ilk bulunan» artık çalıştırılmaz: **elle başka yere kurduysan** görev kaydedilmez, `syncthing`i PATH'e ekle); yoldaki tek tırnak (`O'Brien`) doğru kaçırılır.
- **Push aboneliği (D-27):** uç nokta alan adı yalnız bilinen push hizmetleri (FCM, Mozilla, Apple, Windows); abonelik eşlenmiş cihaza bağlı, cihaz başına en çok 3, toplam 20; tavan dolunca başkasının kaydı atılmaz.
- **Yükleme ve zip bombası (D-28):** aynı anda en çok 2 yükleme (fazlası 429); `guard_zip`: toplam açılmış boyut 200 MB, tek üye 100 MB, sıkıştırma oranı 200x (büyük üyelerde), 5000 dosya; ChatGPT/Takeout geçmiş zip'i ve LinkedIn zip'i de denetlenir.
- **Atlatma testleri (D-29):** `sb security-test` artık modelden bağımsız kural katmanını da sınar: 48 komut sınıflandırıcı atlatması (D-01/D-09) + mail bağlamında modelin uyduğu 7 senaryo (komut, kural, hafıza, not, arşiv, kutu) — hepsi onay kartına düşmeli.
  `tests/test_audit_2026_11_b.py` (75 test) bu turdaki bulguların saldırı yollarını yeniden üretir.

## 0.11.1 — 2026-11-04

- Nashi kurulumu Başlat menüsüne kısayol ekliyor (taşınabilir zip'te kısayol yoktu, uygulama aramada bulunamıyordu).
- `sb/apps.py` macOS'ta `%LOCALAPPDATA%\...` biçimli katalog yollarını doğru çözüyor; macOS testleri yeşil.

## 0.11.0 — 2026-11-04 (ClipBoardLine ve Nashi: hazır uygulamalar)
- **Hazır uygulamalar:** iki açık kaynak (MIT) uygulama OLDUĞU GİBİ kurulup beyne bağlanır; yeniden yazılmadı. **ClipBoardLine** (kopya geçmişi, Windows
  Electron, ~520 MB; macOS zip) ve **Nashi** (dosya dönüştürücü, Windows taşınabilir zip ~91 MB; macOS zip). Resmî GitHub sürümü indirilir, sürümdeki
  `SHA256SUMS` ile **SHA-256 doğrulanır** (uyuşmazsa dosya silinir, kurulum durur); yalnız `github.com/orkunisitmak/...` ve GitHub'ın dosya CDN'i; boyut sınırı;
  zip güvenli açılır (zip-slip / sembolik bağ / zip bombası denetimi). ClipBoardLine NSIS sessiz kurulumla (`/S`; olmazsa normal kurulum penceresi açılır),
  Nashi `%LOCALAPPDATA%\Programs\Nashi` altına. Kaynak kodlarının değiştirilmemiş kopyası kitte `apps/clipboardline/` ve `apps/nashi/` (`UPSTREAM.md`: depo, commit, tarih, lisans).
- **Komut:** `sb apps list | status [id] | install <id> | start <id> | autostart <id> login|startup|off | update <id> | sync <id|all>`.
- **Başlangıç kurulumda sorulur** (varsayılan: bilgisayar açılınca): `login` = kaldırılabilir `HKCU\...\Run` kaydı (uygulamanın kendi ayarına dokunulmaz;
  macOS LaunchAgent), `startup` = Second Brain «Çalışmaya başla» ile, `off`. Sihirbaz **Başlangıç** adımı ve Ayarlar → Başlangıç sekmesinde **Hazır uygulamalar** kartları
  (açıklama, boyut, durum, Kur + ilerleme, başlangıç seçimi); deneme kipinde indirme/kurulum/Run kaydı «[deneme] atlandı». TR/EN.
- **Bağlayıcılar (salt okunur):** `ClipBoardLine` → metin, bağlantı (başlık), görsel OCR metni, ad, etiket, klasör, not (mail arşivi `items`, `sb search` ve beyin dizini görür);
  parola/API anahtarı/kart/IBAN/TCKN/OTP içeren kayıt **atlanır** (sayısı raporlanır), çöpe atılan alınmaz. `Nashi` → son 50 dışa aktarımın yolu/türü/zamanı +
  desteklenen türlerde (pdf, docx, pptx, xlsx, txt/md/csv, görsel OCR) içerik. Uygulamanın `library.json` dosyası kopyalanıp okunur, kilitliyse sonra denenir; tekrar önleme: kimlik + içerik karması.
- **Otomatik:** günlük çalışma (`apps sync all`), «Çalışmaya başla» yeni **Uygulamalar** adımı (başlangıç kipi `startup` olanları açar + senkron), asistan açıkken 5 dakikada bir hafif senkron;
  asistanın «Çalışmaya başla» görünümünde **Uygulamalar** kartı (durum, Aç, son senkron, kayıt sayısı, atlanan sır).
- **Kaldırıldı:** 0.10.1'deki yerleşik «Kopya geçmişi (Pano)» modülü (`sb pano`, `/api/v2/pano/*`, Kopya geçmişi görünümü) — yerini ClipBoardLine aldı.
- **Katalog** 258 madde (251-258 yeniden tanımlandı), modül 52 (`clipboardline`, `nashi`), veri kaynağı 41. **Rehber** 135 sayfa: «Uygulamalar: ClipBoardLine ve Nashi» + `sb apps` komutu.
- Sınır: macOS kurulum/başlangıç komutları yazıldı ama denenmedi; bağlayıcılar yalnız Windows veri biçimini okur. ClipBoardLine'da metin toplama varsayılan kapalıdır (uygulamanın kendi ayarı).

### Güvenlik (denetim 2026-11; özet: `docs/GUVENLIK-DENETIM-OZET.md`)
- **Komut sınıflandırıcı yeniden yazıldı (D-01, D-09):** `run_command` artık metin regex'iyle değil, "ayrıştır ve doğrula" ile sınıflanır. Komut tek bir basit çağrı + düz bağımsız
  değişkenler (+ `Sort-Object`/`Select-Object`/`Format-Table` gibi biçimleyici borular) değilse en az onay kartı çıkar: alt ifade `( )`, `$( )`, `@( )`, `{ }` betik bloğu, değişken,
  ters tırnak, `;` `&` `<` `>`, virgüllü dizi, yeni satır, `%ortam%`, ASCII dışı (benzer) karakter, `python -c/-m/-v`, `node -e`. `python`/`node`/`uv` yalnız sürüm sorgusu.
  `Select-String`/`findstr` boruları ve `git diff --no-index` onaylı; `cat` yalnız tek yol (kasa/Workspace içi). **Etkisi:** eskiden anında çalışan bazı komutlar (ör. `python -v`) artık kart ister.
- **Dış içerik varken komut ve kalıcı yazma hep onaylı (D-02, D-06):** mail/SMS/belge/web/ek/ekran bağlamdayken `run_command` her zaman, `rule_add`/`memory_add`/`note_update`/`note_archive`/`inbox_add`
  (ve `geceye ekle`) onay kartıyla çalışır; "kural/hatırla" gibi anahtar sözcükler artık onay yerine geçmez. Kirlilik bayrakları **yapışkandır**: bir kez girdiyse sohbet boyunca (yeni sohbete kadar) sürer.
  `brain_note/project/course/today` ve `calendar_list` çıktıları da bağlamı kirli sayar. Ek (PDF/DOCX) metni kullanıcı sözü sayılmaz. Kod, kirli bağlamda `run_command`'ı kendisi önermez.
  **Etkisi:** mail konuşulan bir sohbetin devamında "bundan sonra ..." gibi kural eklemek onay kartı çıkarır.
- **Tarayıcı eklentisi (D-03):** sağ tık "Beyne at" artık sohbet modeline değil araçsız `/api/v2/share` ucuna gider. Eklenti kökeni yalnız `/api/v2/share` ve `/api/v2/chat`e erişir;
  eklenti oturumu (`eklenti`) güvenilmez sayılır (komut/yazma hep onaylı) ve kullanıcının sohbet oturumuna yazamaz.
- **Yerel kimlik (D-04, D-19):** 127.0.0.1:8765'e her durum değiştiren istek `X-SB-Token` ister (rastgele, kalıcı jeton `~/.secondbrain/chat.token`, yalnız kullanıcıya açık). Arayüz jetonu sayfa yüklenirken gömülü alır
  (`sbtoken.js` bütün aynı-köken isteklere ekler); masaüstü uygulaması, tepsi, Obsidian eklentisi ve `tools/e2e.py` dosyadan okur. Kurulum jetonu veren `GET /api/v2/startup/settings-url`, model çağıran ve
  keyring'e yazan GET uçları (`thread-summary`, `screen/summary`, `push/status`) jeton + aynı köken ister: başka bir sitedeki `<img>` ile tetiklenemez. Telefon yolu eşleme çerezini kullanmaya devam eder.
  Not: aynı kullanıcı hesabıyla çalışan zararlı bir yerel süreç sayfayı yükleyip jetonu okuyabilir; bu önlem tarayıcı tabanlı saldırıları ve başka kullanıcı hesaplarını kapatır.
- **Telefondan gece koşusu kapandı (D-05):** gece işi ekleme ve onaylama yalnız bilgisayardan; telefondan yalnız `takvim` ve `eylem` onayları. `/api/v2/agents/code` yalnız yerel. Gece işi yalnız izinli klasörlerde
  çalışır (`config/hafiza.yaml` → `night_allowed_dirs`; yoksa kasa ve `~/Workspace`).
- **Not ekleme (D-08):** `note_update` eklemesi tek satıra indirilir (satır sonuyla gece işi/başlık enjekte edilemez); gece işi `@klasör` değeri tek satır.
- **Gizli not tespiti (D-11):** tek işlev (`notes.is_private_text`): ön bilgi YAML okunur; `"private"`, `Private`, BOM, satır sonu yorumu ve uzun ön bilgi yakalanır.
- **Bulut süzgeci (D-12):** `providers` içinde (sohbet, akış, gömme) bulut hedefe giden her mesaja `redact` her zaman, "kişi bilgilerini maskele" açıksa e-posta/telefon/adres maskesi uygulanır.
- **Çift sunucu (D-14):** Windows'ta `SO_EXCLUSIVEADDRUSE`; ikinci süreç 8765'e bağlanamaz (net hata mesajı).
- **Arka plan döngüleri (D-15):** hatırlatma/uygulama senkronu iş parçacıkları `SystemExit` dahil her hatayı `~/.secondbrain/logs/loops.log`'a yazar ve sürer; `run_tool` ve API uçları da `SystemExit`i yakalar.
- **MCP kataloğu (D-16):** `@latest`/sürümsüz `npx -y` ve `uvx` paketleri tam sürüme (`paket@x.y.z`, `==`), GitHub MCP görüntüsü `:v2.1.0`'a sabitlendi. Sırlar `claude mcp add -e KEY=değer` ile
  `~/.claude.json`'a düz metin yazılmaz; `python -m sb.mcp_env` sarmalayıcısı çalışma anında şifre kasasından okur (kendi MCP'm ekranındaki değerler de). Arşivlenmiş paketler (brave-search, gdrive, puppeteer, postgres, slack) hâlâ katalogda, açıklamada "arşivlendi" notu var.
- **`undo_last` (D-21):** geri alınacak commit asistan günlüğündeki son girdiden belirlenir; son değişiklik commit edilemediyse (ör. `index.lock`) eski bir değişikliği geri almak yerine nedenini söyler. Commit hataları günlüğe yazılır.
- **`restore` (D-24):** `_system/`, `.git/` ve `.venv/` yollarına yazmaz; hedef kasa dışına çözümlenirse ya da yolda sembolik bağ varsa üye atlanır.
- **İzin profili (D-26):** `izinler.yaml` varsa ama okunamıyorsa **sıkı** profil uygulanır ve arayüzde uyarı gösterilir (eskiden sessizce "normal"); `_perm`/`_strict_local` istisnada onay ister / bulutu kapatır.

## 0.10.1 — 2026-11-04 (Kopya geçmişi / Pano + sihirbaz düzeltmesi)
- **Kopya geçmişi (Pano)**, varsayılan KAPALI yeni modül (`pano`; ClipBoardLine'dan esinli): kopyaladığın metin, bağlantı ve görseller üç rafta yerelde saklanır;
  sabitleme, klasör, etiket, arama ve görsellerde OCR, tutma süresi (1-30 gün) ve geri alınabilir çöp kutusu. Parola, anahtar, IBAN, kart numarası gibi görünen
  metin ve parola yöneticisi uygulamaları hiç kaydedilmez; veri buluta/modele gitmez. Görünüm: **Kopya geçmişi**; komut: `sb pano`.
  Açmak için: `sb features --on pano` ya da sihirbaz/Özellikler ekranı; modül kapalıyken izleyici ve `/api/v2/pano/*` uçları çalışmaz. Katalog 250 → 258 madde (251-258), modül sayısı 51.
- **Sihirbaz Adım 9 (Veri):** ekranda görünen "null" yazısı düzeldi.
- **Rehber:** ekran görüntüleri yenilendi; Kopya geçmişi modül sayfası eklendi (131 sayfa).

## 0.10.0 — 2026-11-04 (tasarım cilası + ayrıntılı kullanıcı rehberi)
- **Rehber** (`docs/rehber/`, 130 sayfa): kurulum, sihirbazın her adımı ve alanı, hesap bağlama (Google Cloud, Gmail/Outlook/iCloud/Yandex uygulama şifresi,
  okul, Tailscale, Spotify, Telegram, GitHub), API anahtarları, modeller ve ses, MCP, veri yükleme, uygulama turu, asistan kullanımı, güvenlik ve gizlilik,
  30+ sorun giderme maddesi, SSS, sözlük, 97 komutun referansı. Katalogdaki **250 özelliğin her biri** kendi modül sayfasında; 39 veri kaynağı ve 18 MCP için ayrı sayfa.
  Üçüncü taraf menüleri için resmi yardım adresi verilir. Üretici: `python tools/build_guide.py` (`--check` eksik madde/bağlantı/sır denetler).
- **Tasarım:** asistanın bütün ekranları ve kurulum sihirbazı tek bileşen katmanında (`components.css`) ve tek belirteç kümesinde; sabit renkler kalktı,
  koyu temada okunmayan metinler düzeldi, odak halkası ve dar ekran desteği.
- **Kit:** rehber ve üreticisi kitle birlikte gelir.

## 0.9.9 — 2026-11-04
- Aynı anda oluşan iki çökme raporu (Windows saat çözünürlüğü) birbirinin üstüne yazılıyordu; artık ayrı dosya olur (`sb logs`, hata panosu).

## 0.9.8 — 2026-11-04
- Kurulum motoru yol ayırıcısından bağımsız: `C:\...\uv.exe` ve OneDrive yolu macOS'ta da tanınır. macOS CI testleri kendi otomatik başlatma klasörünü bekler.

## 0.9.7 — 2026-11-04
- **macOS:** zamanlayıcı kurulumu paketli Setup.app içinde çalışmıyordu (betik, uygulamanın kendi çalıştırılabilir dosyasıyla çalıştırılıyordu); artık hedef kasanın Python'uyla.
- **Kurulum paneli sunucusu:** reddedilen isteklerde (yanlış jeton, çok büyük ya da geçersiz yükleme) Windows'ta zaman zaman "bağlantı koptu" görünüyordu;
  gövde boşaltılıp yanıt iletilir. Testler 5 ardışık koşuda kararlı.
- Testler kurulmuş kopyada (CI, arkadaşların makinesi) kendi dosya yerleşimine ve saat dilimine bağlı değil.

## 0.9.6 — 2026-11-04 (kurulum sihirbazı canlı denemeden çıkan düzeltmeler)
- **Deneme kipi:** `SB_SETUP_SANDBOX=<klasör>` ya da `--sandbox` — şifreler, zamanlanmış görevler, kısayollar, otomatik başlatma, MCP, Ollama ve Google
  girişi gerçek sisteme dokunmadan ayrı klasöre yazılır; sihirbaz baştan sona gerçek kurulumla denenebilir.
- **Kişisel bilgiler:** boş kasa klasörü varsayılana gider, saat dilimi listeden seçilir ("Gmt+3", "Türkiye" de anlaşılır), uzun/OneDrive yolu uyarısı.
- **Hesaplar:** Google için e-posta ve `client_secret.json` yükleme; okul hesabı formu; hesaplar ve API anahtarları ayrı, okunur adlarla.
- **Kurulum:** kurulum kasanın kendi koduyla çalışır (çalışan kuruluma dokunmaz), kişisel ayar dosyaları kopyalanmaz, `.venv` doğru klasörde;
  hatada ne yapılacağı ve "Yeniden dene". Ayrıntılı özet ekranı, IMAP hataları Türkçe, MCP/model/içe aktarma geri bildirimleri.
- **Testler:** kullanıcının özellik ayarına ve izin profiline bağlı değil (kurulu kopyada "Öğrenci" seçimi testleri kırıyordu); ayarlar testte geçici klasöre yönlenir.

## 0.9.5 — 2026-11-04
- Paketleme testleri kurulmuş kasada (derleme dosyaları yokken) atlanır. Setup.exe ve .app 0.9.4'te ilk kez derlendi ve açıldı.

## 0.9.4 — 2026-11-04
- Soru-cevap kurucusu (`install.py --cli`) uygulama ve eklenti tanımı klasörlerini de kopyalar; Windows derlemesi Türkçe çıktıda düşmez (0.9.3 CI'da bulundu).

## 0.9.3 — 2026-11-04 (kurulum sihirbazı + masaüstü uygulaması)
- **`Second Brain Setup.exe` / `.app`:** tek satırlık komut kurulum dosyasını masaüstüne indirir (depo gizli: `gh auth login` ya da `SB_GH_TOKEN`).
  12 adımlı sihirbaz: hoş geldin → hazır seçim (meslek / donanım / gizlilik / yoğunluk) → **bütün özellikler** (50 modül, 250 madde, arama,
  gereksinim rozetleri) → kişisel bilgiler → hesaplar (Google adım adım, birden çok IMAP) → API anahtarları → yerel modeller (Ollama, ses, GPU) →
  MCP (Claude Code bağlantısı, 18 hazır MCP, kendi MCP'n) → veri yükleme (39 kaynak; her birinde "nasıl alınır", sürükle-bırak, önizleme) →
  telefon → başlangıç (otomatik açılsın mı) → özet ve kurulum. Türkçe/İngilizce, yarıda kalanı sürdürme.
- **`Second Brain.exe` / `.app`:** tek pencere, tepsi simgesi, masaüstü ve Başlat menüsü kısayolu; **"Çalışmaya başla"** — güncelleme, sağlık,
  günlük işler, modelleri ısıtma, hazır. Ayarlar kipi: sihirbazın bütün sayfaları sekme olarak.
- **Eklenti tanımları** (`plugins/`): her özellik, kaynak, MCP ve sektör bir tanım dosyası; tekstil sektör paketi örneği.

## 0.9.2 — 2026-11-03 (güvenlik incelemesi)
- **Kritik:** Spotify geri dönüş sayfasında yansıyan XSS kapatıldı (adres çubuğundaki metin kaçışlanır, sıkı CSP).
- **Telefon paylaşımı:** siteler arası formla kasaya veri yazdırma kapatıldı — paylaşım önizleme sayfasına gider, "Beyne at"a basmadan kaydedilmez.
- **İstem enjeksiyonu:** bağlamda mail/SMS/belge/web içeriği varken "kural ekle", "hafızaya yaz", "URL çek" yalnız senin mesajında o istek varsa onaysız.
- **Komutlar:** paket kurma, sistem yükseltme, dal silme/uzak depo değiştirme, ortam değişkeni okuma, dosyaya yazdırma (`--output`), ağ paylaşımı,
  DNS sorgusu ve kasa/Workspace dışı dosya okuma artık onaylı.
- **İzin profilleri gerçekten uygulanır** (Gizlilik ekranı): normal = önceki davranış; sıkı = salt okunur komutlar ve kasa düzenlemeleri de onaylı,
  hiçbir istek buluta gitmez. Profiller onay yalnız EKLER; takvim ve WhatsApp her profilde onaylı. Profil telefondan değiştirilemez;
  komut ve WhatsApp kartları yalnız bilgisayardan onaylanır.
- **Bulut süzgeci:** API anahtarı, şifre ataması, OTP içeren metin buluta gitmez; uzun belgelerde karar bütün metne göre; bulut sohbet modeli
  hassas içerikte yerele düşer.
- **SSRF:** URL çekme ve video dökümü yerel/özel ağ adreslerine gitmez, 50 MB sınırı.
- **Şifreleme:** anahtar okunamazsa yenisi üretilmez (eski notlar kilitlenmesin), `sb vault-key --export`, yedekler de şifreli (düzeltme 0.12.0: o sürümde yalnız şifreleme öncesi yedeğin ek bir şifreli kopyası yazılıyor, düz zip de kalıyordu; `create_backup` düz zip üretiyordu — 0.12.0'da tüm kasa yedekleri `.zip.enc`).
- **Diğer:** zip bombası sınırı, geri yüklemede yol denetimi, kaldırmada sırların listelenmesi, ajan kum havuzunda sembolik bağ, `brain_note` gizli notlar,
  derin analizde ek sır dosyası desenleri, güncellemede önce özet + onay (`sb update --yes`, `--tags-only`), negatif istek uzunluğu, oturum sınırı.
- **Testler gerçek sisteme dokunamaz:** kurulum motoru komutları ve şifre kasası testte kilitli.

## 0.9.1 — 2026-11-03
- Kurulum testleri kurulmuş kit düzeninde (betikler kökte) ve macOS'ta (Apple Silicon) da doğru çalışır (0.9.0 CI'da bulundu).

## 0.9.0 — 2026-11-03 (Faz 5: kurulum paneli + telefon)
- **Kurulum paneli (masaüstü pencere):** tek satırla başlar (Windows `irm .../install.ps1 | iex`, macOS/Linux `curl ... | sh`; argümanla eski soru-cevap kurucusu).
  Sekmeler: Kur (hazır seçimler Tam / Bulut / Minimal / Öğrenci / Ajans + kategorili özellik kutuları), Hesaplar (bilgiler; şifreler yalnız
  işletim sistemi kasasına, "Test et" düğmeleri), Model (donanım taraması ve öneri), Sihirbazlar (Google Cloud, Spotify, Telegram, Tailscale),
  Güncelle, Sağlık, Kaldır (önce plan + onay; notlara asla dokunmaz), Günlük (canlı ilerleme). Türkçe/İngilizce, kurulum sonrası 5 adımlık tur,
  yarıda kalan kurulumu sürdürme, profil dışa/içe aktarma. Panel yalnız 127.0.0.1'de, oturum jetonuyla.
- **Sessiz/kurumsal kurulum:** `python setup/engine.py --preset ogrenci --profile profil.json --yes` (sırlar `SB_SECRET_<ALAN>`).
- **Doğrulama:** her sürümde `SHA256SUMS`; `python setup/engine.py --verify <dosya> <sha256>`.
- **Telefon:** uygulama gibi kurulur (PWA, çevrimdışı kabuk), herhangi bir uygulamadan "Paylaş → Beyne at", iOS Kestirme hedefi (`/share`),
  çevrimdışı kuyruk (bağlantı gelince gönderir), anlık bildirim (Tailscale HTTPS + isteğe bağlı `pywebpush`), dış erişim tüneli planı
  (Cloudflare Tunnel; e-posta doğrulamalı erişim politikası olmadan açılmaz). Rehber: `docs/telefon-pwa.md`.
- **Düzeltme:** `sb models` / `sb doctor` ekran kartını hiç algılamıyordu (eksik içe aktarma) — artık doğru profil önerir.

## 0.8.1 — 2026-11-01
- Kurulum ve güncelleme `integrations` klasörünü (Obsidian/tarayıcı/tepsi eklentileri) de kopyalar (0.8.0'da eksikti).
- Takvime erişilemeyince (giriş yok) günlük plan çökmek yerine takvimsiz çıkar; testler hiçbir zaman gerçek Google Takvim'e gitmez.

## 0.8.0 — 2026-11-01 (Faz 4: ajanlar, kişisel, güvenlik, yeni kaynaklar, eklentiler)
- **Otomasyon:** `config/otomasyon.yaml` kuralları (yeni mail, teslim yaklaştı, zaman, not değişti, webhook → görev, bildirim, not, özet,
  takvim önerisi, WhatsApp taslağı); dış etkili eylemler her zaman onay kuyruğuna düşer (görünüm `automations`); `sb automation-tick` günlük çalışmada.
- **Ajanlar:** 5 hazır ajan (ders asistanı, proje raporu, mail özetleyici, araştırmacı, haftalık planlayıcı), izin kum havuzu, çok ajanlı akış,
  izleme paneli, gece raporu; kod ajanı yalnız gece listesine ekler.
- **Güvenlik ve gizlilik:** gizlilik paneli, bulut maskeleme süzgeci, denetim günlüğü, izin profilleri, yedekler, dışa aktarma, istem enjeksiyonu
  testleri (`sb security-test`); isteğe bağlı kasa şifreleme `sb vault-encrypt --folder <klasör> --confirm` (önce yedek).
- **Kişisel:** harcama ve bütçe, abonelikler, garanti, ilaç hatırlatma (onaylı), okuma/izleme listesi, yemek planı, bakım, hediye fikirleri,
  ruh hali, seyahat planı (görünüm `life`).
- **21 yeni içe aktarıcı:** `sb import <kaynak> <dosya>` — discord, slack, notion, keep, apple-notlar, onenote, evernote, instagram, x, todoist,
  ticktick, mstodo, trello, jira, linear, pocket, raindrop, gphotos, gmaps, bank (hesap/kart numarası saklanmaz), coursera, udemy, screentime.
- **Eklentiler** (`_system/integrations/`, elle kurulum): Obsidian yan paneli, tarayıcı "Beyne at" (yalnız `config/eklentiler.yaml`'daki kimliğe izin),
  tepsi simgesi, mini sohbet balonu (`/bubble`).
- **Beyin grafiği:** notlardan konu kümeleri (küme başına renk), belge/mail kümeleri analizde, bağlantı önerileri otomatik; `sb graph-style` yalnız renk.

## 0.7.0 — 2026-11-01 (Faz 3: verimlilik, iletişim, okul, iş)
- **Verimlilik:** görev panosu, akıllı günlük plan ve "bugün en önemli 3 iş" (`sb plan`), zaman bloklama (onaylı), pomodoro, alışkanlık, hedefler,
  haftalık gözden geçirme, teslim riski ve takvim çakışması uyarısı, tekrarlayan/bağımlı görevler.
- **Okul:** ders panosu (`sb courses`), GANO ve senaryo (`sb gpa --what-if KOD=HARF`), sınav çalışma planı, başvuru takibi, okul belgeleri.
- **İletişim (mail salt okunur):** taslaklar yalnız kasada, zincir özeti, cevap bekleyenler, takip, kişiye özel ton, önemli tarihler, ilişki sağlığı,
  bülten temizliği önerisi, toplantı hazırlık/sonrası, mail → görev, çeviri.
- **Kariyer:** CRM (`musteri: true`), teklif, saat takibi ve rapor, başvuru panosu, CV/ön yazı, mülakat, portfolyo, LinkedIn taslağı, sözleşmeler,
  gelir/gider ve vergi tarihleri; ödev yardımcısı (öğretici kip), kaynakça, yazım asistanı.
- **Ses:** NVIDIA ekran kartında Whisper (`voice-gpu` isteğe bağlı bağımlılık), NotebookLM Takeout içe aktarımı.

## 0.6.0 — 2026-11-01 (Faz 2: asistan, ses, arayüz)
- **Yeni asistan arayüzü** (`http://127.0.0.1:8765/`; eskisi `/classic`): açık/koyu tema, vurgu rengi, yazı boyutu; sohbet geçmişi
  (arama, sabitleme, yeniden adlandırma, arşiv); tıklanabilir kaynak kartları; yeniden tasarlanmış onay kartları; Ctrl+K komut paleti;
  `/` komutları (`/ara /not /gorev /ozet /hatirla /unut /bugun /kisi /proje /kart /foto /tara /toplanti /dokum /telaffuz`);
  mesajı düzenle / yeniden üret / nota çevir; sürükle-bırak ve yapıştırarak dosya ekleme; bildirim merkezi; hızlı tepki düğmeleri;
  klavyeyle tam kullanım. Telefonda (Tailscale) aynı arayüz, kenar çubuğu çekmece.
- **Görünümler:** pano, bilgi grafiği (yakınlaştır/kaydır/sürükle), zaman çizelgesi, kişi sayfası, proje sayfası.
- **Ses:** yerel Whisper ile konuşma → yazı (dil otomatik), basılı tut-konuş (`Ctrl+Space`), sesli cevap, konuşma kesme,
  uyandırma sözcüğü (varsayılan kapalı), telefonda sesli not, toplantı/ders kaydı → döküm + özet + karar + görev, video/podcast dökümü,
  telaffuz koçu. Kurulum: `uv pip install "faster-whisper>=1.1" "av>=15,<18"`; durum `sb voice --setup`.
- **Görüntü:** fotoğrafla soru, el yazısı/tahta → metin, PDF'e sayfa atıflı soru, izinli ekran izleme (varsayılan kapalı, görüntü saklanmaz),
  görsel üretme (varsayılan kapalı, bulut anahtarı gerekir).
- **Hafıza ve kişilik:** asistan kimliği (`Asistan kimliği.md`), kişilik ayarı (ton, uzunluk, sen/siz), ortak günlük, onaylı tercih öğrenme,
  hafıza düzenleyici, her yerden unutma isteği (onaylı; unutulan bir daha dizinlenmez), proje/kişiye bağlı hafıza, günlük yansıma,
  haftalık "beni tanı", bilgi kartları + aralıklı tekrar, öğrenme yolu, hata panosu. `sb persona --reflect|--weekly|--prefs`.
- **Güvenlik:** kasaya giden metinde API anahtarı ve `*_PASSWORD/SECRET/TOKEN` atamaları da maskelenir.

## 0.5.0 — 2026-10-31 (Faz 1: derin beyin)
- **Beyin dizini:** notlar, mailler, dosyalar, Drive, sohbetler tek dizinde; kelime + anlam (yerel `nomic-embed-text`) karma arama.
  `sb index`, `sb find "..."`, `sb answer "..."` (kaynaklı cevap), `sb similar <not>`; MCP `brain_find` / `brain_answer`.
- **Akıllı arama:** doğal dil süzgeçleri ("geçen ay hocadan gelen pdf"), kayıtlı aramalar + uyarı, yarım hatırlananı bulma,
  ek dosya ve görsel içinde arama, çok adımlı araştırma (kasa + istersen internet), SSS, arama kalite testi (`sb search2`).
- **Yeni kaynaklar:** WhatsApp dışa aktarımları (sohbet + gün bazında), Google Takeout (Gemini, Keep, Chrome, YouTube),
  tarayıcı geçmişi/yer imleri (giriş/jeton adresleri süzülür), GitHub derin (issue/PR/commit/release), RSS, arXiv/Scholar/Zotero,
  Kindle, Spotify, Telegram; Outlook/iCloud IMAP ve CalDAV hazır ayarları; fatura ve kargo çıkarımı (`sb derive`).
- **Kişiler:** tekrar kişi notları otomatik birleşir (`sb merge-people --auto`, günlük çalışmada); rehberde ad değişince not da
  yeniden adlandırılır ve bağlantılar güncellenir (büyük/küçük harf değişikliği dahil); sohbetler ve geçen adlar kişi/proje notlarına bağlanır.
- **Kümeleme ve analiz:** konu kümeleri + küme haritası, bağlantı önerileri (onayla/reddet), konu zaman çizelgesi, proje haritası,
  belge sınıflandırma, tekrar belge, yaşlanan/tazelik/çelişki, yetenek profili, sözlük, etiket düzeni, not kalitesi,
  kaynak güveni, veri hattı panosu (`sb analyze all`).

## 0.4.1 — 2026-10-31
- Özellik kataloğu (`features.yaml`) pakete, kurulum güncellemesine ve güncelleme yedeğine eklendi (0.4.0'da eksikti; `sb roadmap` boş görünüyordu).

## 0.4.0 — 2026-10-31 (Faz 0: temel altyapı · yol haritası `ROADMAP.md`)
- **Yol haritası:** 250 özellik, 6 faz (`features.yaml`); ilerleme `sb roadmap`.
- **Özellik anahtarları:** `sb features --on/--off <modül>` — kapalı modülün günlük adımı çalışmaz, asistan aracı modele gösterilmez.
- **Bulut modeller:** OpenAI, Anthropic, Gemini, OpenRouter, Groq, DeepSeek, Mistral + yerel LM Studio / llama.cpp / vLLM.
  Görev başına model (`llm.yaml` → `tasks: <görev>: "<sağlayıcı>:<model>"`; asistan için `tasks.chat`). Anahtar: `sb set-secret api-<ad>`.
  Tek soru: `sb ask "..." --model openai:gpt-5-mini [--stream]`.
- **Yönlendirici:** kurallar (`routing`), yedek zinciri (`fallback`), önbellek (`cache`). Şifre/kart/TC/IBAN içeren ya da gizli
  işaretli içerik hiçbir koşulda buluta gitmez (yalnız yerel model). Uzun belgeler parça parça okunup birleştirilir.
- **Maliyet:** her çağrı kaydedilir, `sb usage`; aylık/günlük bütçe (`budget`), aşılırsa bulut yerine yerel model, %80'de bildirim.
- **Gömme modeli** seçimi (`embedding`), `sb embed-test`.
- **Yerel model yöneticisi:** `sb models` (donanım: RAM, ekran kartı, VRAM → önerilen profil full/medium/small/cloud),
  `--apply <profil>`, `--bench` (kendi notlarınla hız ve biçim testi), `--pull/--rm` (onaylı).
- **Kalite:** `sb e2e [--live]` uçtan uca test, `sb logs [--crash|--bundle]` çökme raporu (kişisel veri maskeli, hiçbir yere gönderilmez),
  `sb perf` performans, `sb whatsnew` yenilikler.

## 0.3.1 — 2026-10-31
- **Gece koşusu yalnız sen istediğinde:** otomatik saat yok. Asistana (Obsidian ya da telefon) `geceye ekle: iş @klasör`,
  `gece işleri neler`, `gece koşusunu başlat` (onay kartı) yaz; arka planda sırayla yapılır, bitince bildirim gelir.
  Komut satırı: `sb night --add "..." --where <klasör>`, `--plan`, `--start`.

## 0.3.0 — 2026-10-31 (hafıza kendi kendine birikir)
- **Makbuz + son günler:** iş bitince `sb receipt` kaynak bağlantılı tek satır yazar (`50-Günlük/Makbuzlar`, günlük notta özet);
  `sb recap --days 7` / asistana "son günlerde ne yaptık" / MCP `brain_recap`.
- **Kavram ve bağlantı notları:** `sb concept` (`40-Kaynaklar/Kavramlar` + `_Dizin.md`), `sb connect` (gerekçeli bağlantı),
  öğrenim adayları `sb learn`, sohbet izi `sb trace`, hata kataloğu `sb error-log` (ikinci tekrarda kural olur).
- **Kancalar:** konuşma sıkıştırılmadan önce ve kart yazılmadan kapanan oturumda yerel model özeti günlük nota düşer (arka planda);
  aynı anda açık başka oturum uyarısı; projeye kapsamlı kurallar (`[kapsam: proje]`, proje notunda `## Kurallar`);
  `sb mode normal|ekonomik|manuel`.
- **Görevler** (`25-Görevler`, `sb task`): sorumlu zorunlu, bitiş ölçütü varsa kanıt dosyası olmadan bitmez.
- **Kişi notları:** Beyan / Çıkarım (onay bekliyor) ayrımı, takma ad, reddedilen çıkarım bağlama girmez (`sb person`).
- **Gizli notlar:** `visibility: private` Claude'a, asistan aramasına ve kancaya gitmez.
- **Hijyen:** `sb hygiene` (tekrar not, kopuk bağlantı, bayat not, büyüyen dosya); haftalık özete eklenir.
- **Güvenli güncelleme:** `sb update` önce kodu yedekler; `--rollback`, `--recover`.
- **Beyne at:** Sağ tık › Gönder › Beyne At (dosya), panodaki ekran görüntüsü (OCR), birden çok bağlantı, Web Clipper şablonu.
- **Sohbet geçmişi:** `sb history-import` (ChatGPT, Claude.ai, Gemini Takeout; önce deneme, kelimeyle eleme, gizli seçeneği).
- **Skill'ler:** beyin, beyin-doktor, beyin-guncelle, gecmis-import, form-doldur, orkestrasyon (`~/.claude/skills`); `AGENTS.md`
  (Codex/Gemini aynı kasayı kullanır); Claude Code durum çubuğu (model · proje · dal · bağlam · limit).
- **Orkestrasyon:** yerel Qwen işçisi (`sb qwen`, MCP `local_work`), gece koşusu (`00-Inbox/Gece işleri.md` → `sb night --run`),
  Codex alt ajan kontrolü (`sb doctor`). Mail konusundaki köşeli parantezin sahte bağlantı üretmesi düzeltildi.

## 0.2.3 — 2026-10-31
- Asistan: "Burak kim" gibi yalnız adla sorulan kişiyi bulur; aynı adlı herkesi şirket/rol/kaynakla listeler ve hangisi olduğunu sorar.
- Asistan: "bundan sonra hep ..." dendiğinde kalıcı kural olarak kaydeder.
- Not kutusu: ders kodu ya da proje adı geçen not o dersin/projenin ana notuna eklenir.
- Canlı sınav: 32 özellik (takvim, hatırlatma, not, beyne at, hafıza, kural, durum, geri al, kişi, ekran, kamera, uygulama, ses, YouTube, Spotify, arama, WhatsApp taslağı, komut, yasak komut, silme önerisi) 32/32.

## 0.2.2 — 2026-10-31
- Asistana **beyne at**: "şu videoyu beyne at <bağlantı>" ya da yalnız bir bağlantı yapıştırmak yeterli (telefondan da). Ekran/kamera okunduğu turda bağlantı indirilmeden önce onay ister.
- Takvim: söylenen "yarın/bugün/öbür gün" modelin yazdığı tarihe üstün (gece yarısından sonra iki gün sonraya kayıyordu). Model sınavı 24/24.

## 0.2.1 — 2026-10-31
- macOS: Spotify kapalıyken açma düzeltildi (Windows'a özgü çağrı kullanılıyordu).
- Kurucu: Türkçe karakterleri gösteremeyen eski konsollarda çökmüyor.

## 0.2.0 — 2026-10-31
- **Beyne at (Ctrl+Alt+B):** Bir bağlantıyı ya da metni kopyala, kısayola bas. YouTube videosunun altyazısı, web sayfasının
  metni yerel modelle özetlenip `40-Kaynaklar/Videolar` ya da `40-Kaynaklar/Web` altına not olur. Düz metin not kutusuna düşer.
  Aynı bağlantı iki kez kaydedilmez. Komut satırından: `sb capture "metin ya da bağlantı"`.
- **Araçlar ve erişimler notu:** Kasa kökünde, sistemin neye bağlı olduğunu (Google, IMAP, model, zamanlayıcı, telefon...) ve
  hangi kaynaktan kaç not geldiğini gösterir. Her gün yenilenir; şifre ya da anahtar içermez. Elle: `sb arsenal`.
- **Sürüm ve güncelleme:** `sb version`, `sb update` (`--check` yalnız bakar). `sb doctor` sürümü de gösterir.
- **Otomatik test:** Her güncellemede GitHub, Windows ve macOS'ta sıfırdan kurulum yapıp testleri çalıştırır.

## 0.1.0 — 2026-10-30
- İlk sürüm: Obsidian kasası, mail/takvim/rehber/Drive/SMS/ÖBS/LinkedIn aktarımı, günlük ve haftalık çalışma, sabah özeti,
  yerel asistan (Qwen) ve telefon erişimi, Claude Code hafızası (MCP + kancalar), tek komut kurulum.
