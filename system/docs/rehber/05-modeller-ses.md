# 05 · Yerel modeller, Ollama, Whisper (ses) ve GPU kütüphaneleri

Bu bölüm sihirbazın **7. adımını** (Ayarlar → **Modeller** sekmesi) anlatır: yerel yapay zekâ modelini bilgisayarına kurmak, donanımına uygun modeli seçmek, sesi yazıya çeviren Whisper'ı ve NVIDIA ekran kartı kütüphanelerini kurmak.

## Neden yerel model?

Yerel model **internete çıkmadan, ücretsiz** çalışır; verin bilgisayarından ayrılmaz. Asistanın cevapları, mail/belge özetleri, tarih çıkarma ve gelen kutusu dağıtımı yerel model ile yapılır. Karşılığında **disk alanı** (birkaç GB) ve **bellek/ekran kartı** gerekir. Bilgisayarın zayıfsa bulut modeli kullanabilirsin ([API anahtarları](04-api-anahtarlari.md)).

## Ollama nedir?

**Ollama**, yerel modelleri indirip çalıştıran ücretsiz bir programdır (https://ollama.com). Second Brain modellerle Ollama üzerinden konuşur (`http://localhost:11434`). Sihirbaz Ollama'yı senin yerine kurabilir.

### Ollama'yı sihirbazdan kurma

1. 7. adımda **Ollama (yerel model çalıştırıcı)** kartına bak.
2. «**Ollama kurulu.**» ✓ yazıyorsa bu adımı geç.
3. «**Ollama kurulu değil.**» yazıyorsa **Ollama'yı kur**'a bas. Altında «Resmi kurucu indirilip çalıştırılır; ilerleme aşağıda görünür.» yazar. Kurulum başlar («Kurulum başladı…»); bitince ✓ olur.
4. Windows'ta bir kurulum penceresi/UAC onayı çıkabilir; onayla. macOS'ta uygulamayı **Uygulamalar** klasörüne sürüklemen gerekebilir.
5. Elle kurmak istersen https://ollama.com/download adresinden kur, sonra **Yeniden tara**.



Ollama kurulu ama çalışmıyorsa: Windows'ta görev çubuğundaki gizli simgelerde Ollama simgesini kontrol et; yoksa Başlat menüsünden **Ollama**'yı aç. Doğrulama: `sb doctor` → «Ollama (yerel model)» ✓.

## Donanımına göre model seçimi

7. adımda **Donanım kartı** şunları gösterir: **Bellek** (RAM), **İşlemci** (çekirdek sayısı), **Ekran kartı** (ad ve VRAM), **Disk**. «Önerilen model profili» VRAM'e göre seçilir (`sb models` aynı taramayı yapar):

| VRAM (ekran kartı belleği) | Profil | Yazı modeli | Görüntü modeli | Bağlam (`num_ctx`) | İndirme boyutu | Not |
|---|---|---|---|---|---|---|
| ≥ 14 GB | **full** (güçlü) | `qwen3:14b` | `qwen3-vl:8b` | 24576 | ≈ 15,4 GB | 16 GB sınıfı kartta ikisi birlikte rahat sığar |
| 8–14 GB | **medium** (orta) | `qwen3:8b` | `qwen3-vl:4b` | 16384 | ≈ 8,5 GB | Bağlam penceresi daraltılmış |
| 4–8 GB | **small** (küçük) | `qwen3:4b` | yok | 8192 | ≈ 2,6 GB | Ekran görüntüsünde yalnız OCR yazısı okunur |
| < 4 GB / kart yok | **cloud** (bulut) | `qwen3:1.7b` (yalnız özetler için) | yok | 8192 | ≈ 1,4 GB | Sohbet için bulut API önerilir |

- **Mac (Apple Silicon):** ekran kartı belleği yerine **birleşik bellek** kullanılır. Hazır seçim «Mac» 16 GB altında **orta** profili, 32 GB ve üstünde **güçlü** profili seçer; uyandırma sözcüğü ve ekran izleme kapalı başlar.
- **VRAM bilinmiyorsa** (ör. `nvidia-smi` yok) profil **cloud** önerilir; Windows'ta 4 GB üstü bazen eksik görünür. Bu durumda donanımını kendin biliyorsan sihirbazın 2. adımında doğru **Donanım** kartını seç.
- VRAM taraması öncelikle **NVIDIA** kartlar (`nvidia-smi`) üzerinden yapılır; başka kartlarda bellek bilgisi bulunamayabilir. Modeller işlemcide de çalışır (daha yavaş).
- Profili sonradan komutla uygula: `sb models` (donanımı ve öneriyi göster) → `sb models --apply medium` (farkı gösterir) → `sb models --apply medium --yes` (`config/llm.yaml`'a yazar; yorumları korur).
- Model indirme/silme: `sb models --pull qwen3:8b --yes`, `sb models --rm <model> --yes`.
- Kendi notlarınla hız/biçim sınavı: `sb models --bench ollama:qwen3:14b,ollama:qwen3:4b` (yalnız **hız ve biçim uyumunu** ölçer, cevap kalitesini değil; `gizli` notlar ve bulut modeller dışarıda tutulur).

### Model indirme (sihirbaz)

1. **Kurulu modeller:** liste ya da «Henüz model indirilmemiş.»
2. **Önerilen:** satırında profilin modelleri yazar.
3. Önerileni indirmek için adını kopyalayıp **model adı** kutusuna yaz (örn. `qwen3:8b`) → **Modeli indir**. «`qwen3:8b` indiriliyor…» ve ilerleme çubuğu çıkar.
4. İndirme **birkaç GB**'dır; bağlantını ve diskini kontrol et. Yarıda kalırsa aynı komutu tekrar çalıştır, Ollama kaldığı yerden sürdürür.
5. Bitince model listede görünür. `sb doctor` «Model … » satırları ✓ olur.



### Hangi model hangi iş için?

Yazı modeli sohbet, özet ve tarih çıkarmada; **görüntü modeli** (vision) ekran/kamera ve resim okumada kullanılır; **gömme (embedding) modeli** arama ve beyin dizini içindir (`sb embed-test` yapılandırılmış gömme modeliyle denenir). Hangi görevin hangi modelle yapıldığı `config/llm.yaml` içindeki `ollama:` ve `tasks:` bölümlerinden okunur.

## Ses: Whisper (konuşmayı yazıya çevirme)

**Ne işe yarar:** mikrofonla konuşup asistana yazdırmak (sohbet kutusundaki mikrofon düğmesi), sesli not, toplantı/ders kaydı dökümü, video/ses dosyası dökümü. Yerel **faster-whisper** kullanılır: ses dosyası bilgisayardan çıkmaz; notlara yalnız döküm girer.

### Sihirbazdan kurma

1. 7. adımda **Ses (Whisper)** kartı: «Konuşmayı yazıya çeviren yerel faster-whisper kurulur.»
2. NVIDIA ekran kartın varsa **NVIDIA GPU kütüphanelerini de kur** kutusunu işaretle (aşağıya bak). Yoksa boş bırak.
3. **Sesi kur**'a bas → «Ses kurulumu başladı…». Python ortamına `voice` (ve işaretlediysen `voice-gpu`) paketleri eklenir, sonra durum denetlenir.
4. Süre: paketler ve ilk model indirmesi nedeniyle birkaç dakika sürebilir.

Komutla: `sb voice --setup` (kurulum durumu), `sb voice --transcribe <dosya>` (dosyayı yazıya çevir).

### Whisper modeli

Varsayılan Whisper modeli **`small`**'dır (Türkçe için iyi bir denge). Daha küçük/büyük model için `config/asistan.yaml` içindeki `voice:` altında `stt_model:` değerini değiştirirsin (`tiny`, `base`, `small`, `medium`, `large-v3` gibi faster-whisper model adları). Uyandırma sözcüğü ayrıca `tiny` modeli kullanır. Model ilk kullanımda indirilir ve bellekte kalır. **Büyük model = daha doğru ama daha yavaş ve daha çok bellek.**

### GPU kütüphaneleri (NVIDIA)

- Whisper **GPU'da** (CUDA) çok daha hızlıdır. Bunun için **NVIDIA** ekran kartı ve `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` kütüphaneleri gerekir. **NVIDIA GPU kütüphanelerini de kur** kutusu bunları kurar (yaklaşık birkaç GB).
- Second Brain Windows'ta bu kütüphanelerin DLL klasörlerini otomatik tanır.
- **GPU yoksa ya da kütüphane eksikse** hata vermez: otomatik olarak **işlemciye (CPU)** düşer ve çalışmaya devam eder (daha yavaş).
- Sorun: ilk çalıştırmada «cuda / cudnn / cublas / .dll» hataları görürsen kütüphaneleri kurmadığındandır; **Sesi kur**'u kutuyu işaretleyerek tekrar çalıştır ya da kutusuz bırakıp CPU ile devam et.
- AMD/Intel kartlarda ve Mac'te bu kütüphaneler kullanılmaz; ses işlemcide çalışır.

### Sesli cevap (okuma)

Asistanın cevaplarını sesli okuma tarayıcının/işletim sisteminin konuşma sentezini kullanır: **Ayarlar** (sohbet ekranında **Görünüm ve cihazlar**/**Ayarlar** görünümü) → **Cevapları sesli oku** kutusu ve **Ses** listesi (**Otomatik (dile göre)** ya da bir ses); **Dene** düğmesi örnek cümle okur. **Uyandırma sözcüğü** kutusu isteğe bağlıdır ve yalnız sekme açıkken çalışır.

## Kendi modelini kullanmak (ileri düzey)

LM Studio, llama.cpp ve vLLM gibi **yerel OpenAI uyumlu sunucular** da tanınır (`http://localhost:1234/v1`, `:8080/v1`, `:8000/v1`); `config/llm.yaml`'da ilgili `sağlayıcı:model` adını göreve yazman yeterlidir. Bu sunucular yerel sayılır, bütçeye takılmaz.

## Sorun giderme (kısa)

| Belirti | Çözüm |
|---|---|
| «Ollama'ya ulaşılamadı (ollama.com'dan kur)» | Ollama'yı kur ve başlat |
| «Yerel model indirilemedi. Ollama çalışıyor mu ve internet var mı bak» | Ollama'yı aç, interneti kontrol et; model indirmeyi sonra **Modeller** sekmesinden tekrar dene |
| İndirme çok yavaş/yarım | Aynı indirmeyi tekrar çalıştır; kaldığı yerden sürer |
| Asistan çok yavaş | Bir alt profile geç (`sb models --apply small --yes`) ya da bulut kullan |
| Bellek yetmiyor / çöküyor | Daha küçük model; diğer büyük programları kapat |
| Ses çalışmıyor, «faster-whisper» yok | **Sesi kur** ya da `sb voice --setup` |
| CUDA/DLL hataları | [Sorun giderme → Whisper GPU](11-sorun-giderme.md#whisper-gpu) |

Daha fazlası: [Sorun giderme](11-sorun-giderme.md).
