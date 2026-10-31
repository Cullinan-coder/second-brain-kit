# Değişiklikler

Kurulu sürümünü `sb version` gösterir. Güncellemek için `sb update` yaz; notlarına ve ayarlarına dokunmaz.

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
