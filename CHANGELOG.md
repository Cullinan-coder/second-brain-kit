# Değişiklikler

Kurulu sürümünü `sb version` gösterir. Güncellemek için `sb update` yaz; notlarına ve ayarlarına dokunmaz.

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
