# 04 · API anahtarları (bulut yapay zekâ modelleri)

Bu bölüm sihirbazın **6. adımını** (Ayarlar → **Anahtarlar** sekmesi) anlatır: bulut yapay zekâ sağlayıcılarının anahtarlarını nereden alacağını, nasıl gireceğini, ne kadar paraya mal olabileceğini ve «tam yerel» seçeneğinin ne demek olduğunu.

> **Anahtarlar tümüyle isteğe bağlıdır.** Hiç bulut anahtarı girmeden de Second Brain yerel modelle çalışır ([Modeller ve ses](05-modeller-ses.md)).

## API anahtarı nedir?

Bir bulut yapay zekâ hizmetini (ör. ChatGPT'nin modelleri) kendi programından kullanmak için o şirketten aldığın **gizli bir parola** gibi uzun bir yazıdır. Anahtar **senin hesabına bağlıdır ve kullandıkça hesabına ücret yazar.** Bu yüzden:

- Anahtarı **kimseyle paylaşma**, e-postaya/sohbete/depoya yapıştırma.
- Her şirket **kullanıma göre ücretlendirir** (genelde girdi ve çıktı «token» sayısına göre). Çoğu sağlayıcı önce **bakiye yüklemeni** ya da ödeme yöntemi eklemeni ister.
- Sağlayıcılar fiyatları ve ücretsiz kotaları sık değiştirir. Güncel fiyat için her sağlayıcının kendi fiyat sayfasına bak (aşağıdaki adresler).

## Tam yerel ne demek?

**Tam yerel** gizlilik seçimi (sihirbaz 2. adım, Gizlilik ekseni):

- Hiçbir istek bulut modeline gitmez; asistan, özetler, arama gömmeleri yalnız bilgisayardaki **yerel modelle** çalışır.
- İzin profili otomatik **sıkı** olur (aşağıda), bulut gönderimi `never`, maskeleme açık.
- 6. adım «Tam yerel seçtin: hiçbir şey buluta gitmez, bu yüzden bulut API anahtarları gerekmez.» der; anahtar alanları «isteğe bağlı» görünür. Anahtar girsen bile kullanılmaz.
- Görsel üretme gibi bulut gerektiren özellikler kapanır.
- Bedeli: yerel model, büyük bulut modellerinden daha küçüktür; bilgisayarın zayıfsa kalite ve hız düşer (sihirbaz «Tam yerel gizlilik + zayıf donanım: küçük yerel model kullanılır, kalite düşebilir» uyarısı verir).

**Karma** (varsayılan): özel notlar yerelde kalır, genel işler buluta gidebilir, maskeleme açıktır. **Bulut öncelikli:** bulut modeller önce denenir; `gizli` etiketli notlar yine yerelde kalır.

## Anahtar nasıl girilir?

### Sihirbazda / Ayarlar'da

1. 6. adımda (ya da **Ayarlar → Anahtarlar**) sağlayıcının satırını bul.
2. Gizli alana anahtarı yapıştır (yazdığın görünmez).
3. **Kaydet ve test et**'e bas. Anahtar şifre kasasına yazılır ve sağlayıcıya küçük bir «modelleri listele» isteği gönderilir. Sonuç satırında **Kaydedildi.** ya da hata mesajı çıkar.
4. Durum rozeti **kayıtlı** olur. Önceden kayıtlı olan alanda yer tutucu «kayıtlı (değiştirmek için yaz)» der; yeni değer yazarsan üzerine yazılır.



### Komutla

`sb set-secret api-<sağlayıcı>` (ör. `sb set-secret api-openai`) → anahtarı sorunca yapıştır (ekranda görünmez) → şifre kasasına yazılır. Ortam değişkeni de kabul edilir (aşağıdaki tablo); ortam değişkeni varsa önce o kullanılır.

### Test edilen adresler

Test, her sağlayıcıda yalnız **modelleri listeleyen** salt okunur bir istektir (ücret yazmaz ya da çok küçüktür):

| Sağlayıcı | Test adresi |
|---|---|
| OpenAI | `https://api.openai.com/v1/models` |
| Anthropic | `https://api.anthropic.com/v1/models` |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/models` |
| OpenRouter | `https://openrouter.ai/api/v1/models` |
| Groq | `https://api.groq.com/openai/v1/models` |
| DeepSeek | `https://api.deepseek.com/v1/models` |
| Mistral | `https://api.mistral.ai/v1/models` |

## Sağlayıcılar: anahtar nereden alınır?

> Aşağıdaki adresler ve menü adları yazıldığı andaki hâlidir; sağlayıcılar arayüzünü ve fiyatlarını değiştirir. Bulamazsan sağlayıcının yardım sayfasında «API key» ara. Anahtarlar genellikle **bir kere gösterilir**: kopyalamayı unutma.

Her sağlayıcı için şifre kasası adı `api-<sağlayıcı>`, ortam değişkeni parantez içindedir.

<a id="anahtar-openai"></a>
### OpenAI (`OPENAI_API_KEY`)

1. https://platform.openai.com adresinde giriş yap / hesap aç.
2. Sol menü ya da profil → **API keys** (anahtarlar) → **Create new secret key**.
3. Ad ver (`second-brain`) → oluştur → anahtarı kopyala (`sk-` ile başlar).
4. **Billing** (faturalandırma) bölümünden bakiye yükle; bakiyesiz hesapta istek hata verir.
5. Fiyat: https://openai.com/api/pricing — Kullanım paneli: platform.openai.com → **Usage**.

Görsel üretme özelliği (`image_gen`) OpenAI ya da Gemini anahtarı ister.

<a id="anahtar-anthropic"></a>
### Anthropic (`ANTHROPIC_API_KEY`)

1. https://console.anthropic.com adresinde giriş yap / hesap aç.
2. **API Keys** → **Create Key** → adını ver → kopyala (`sk-ant-` ile başlar).
3. **Plans & Billing**'den ödeme/kredi ekle.
4. **Not:** Claude **sohbet aboneliği** (Pro/Max) ile **API kullanımı ayrı faturalanır**. Claude Code'u abonelikle kullanıyorsan buna anahtar gerekmez; bu anahtar yalnız Second Brain'in kendi asistanının bulut modeli olarak Claude kullanması içindir.
5. Fiyat: https://www.anthropic.com/pricing

<a id="anahtar-gemini"></a>
### Gemini (`GEMINI_API_KEY`)

1. https://aistudio.google.com adresinde Google hesabınla giriş yap.
2. **Get API key** → **Create API key** (bir Google Cloud projesi seçmeni isteyebilir).
3. Anahtarı kopyala.
4. Ücretsiz bir kullanım katmanı olabilir ama kotalar sık değişir ve sınırlıdır; ücretli katmana geçişi aynı sayfada görürsün. Fiyat: https://ai.google.dev/pricing

<a id="anahtar-openrouter"></a>
### OpenRouter (`OPENROUTER_API_KEY`)

OpenRouter, onlarca şirketin modeline **tek anahtarla** ulaştıran bir aracıdır.

1. https://openrouter.ai → giriş → **Keys** (profil menüsü) → **Create Key**.
2. Anahtarı kopyala; **Credits** bölümünden kredi yükle.
3. İstersen anahtara **harcama limiti** koy (oluştururken ya da düzenlerken) — önerilir.

<a id="anahtar-groq"></a>
### Groq (`GROQ_API_KEY`)

Çok hızlı çıkarım yapan bir sağlayıcı.

1. https://console.groq.com → giriş → **API Keys** → **Create API Key**.
2. Anahtarı kopyala. Ücretsiz katman ve kota sınırları sağlayıcının sayfasında yazar; değişebilir.

<a id="anahtar-deepseek"></a>
### DeepSeek (`DEEPSEEK_API_KEY`)

1. https://platform.deepseek.com → giriş → **API keys** → oluştur → kopyala.
2. Kullanmadan önce bakiye yüklemen gerekebilir (**Top up**). Sunucular yurt dışındadır; gizlilik politikasını kendin oku.

<a id="anahtar-mistral"></a>
### Mistral (`MISTRAL_API_KEY`)

1. https://console.mistral.ai → giriş → **API Keys** → **Create new key** → kopyala.
2. Ücretli kullanım için **Billing**'i etkinleştirmen gerekir.

## Anahtarı girdim, hangi iş buluta gider?

Yalnız hangi göreve hangi modeli verdiysen. `config/llm.yaml` içindeki `tasks:` bölümü her göreve `sağlayıcı:model` biçiminde model atar (ör. `openai:gpt-5-mini`). Donanım seçimin «Zayıf laptop / bulut» ise sohbet için buluta bir model önerilir; yerel model yalnız küçük özetler için kalır. Tek soru için: `sb ask --model openai:gpt-5-mini "..."`.

Model profili ve donanım eşleşmesi: [Modeller ve ses](05-modeller-ses.md).

<a id="maliyeti-kontrol-altinda-tut"></a>

## Maliyeti kontrol altında tut

- **Bütçe sınırı:** `config/llm.yaml` içindeki `budget:` bölümü günlük ve aylık dolar sınırı koyar (`daily_usd`, `monthly_usd`; `warn_at` = uyarı oranı, varsayılan %80). Sınır dolunca bulut çağrısı **yapılmaz**; `fallback_to_local` açıksa iş yerel modele düşer. Sınırı kaldırmak için 0 yaz. Yerel modeller bütçeye takılmaz.
- **Kullanım ve maliyet:** `sb usage` günlük/aylık özeti ve bütçeyi gösterir. Gizlilik ekranındaki **Buluta giden** kartı son 30 günde kaç bulut çağrısı yapıldığını ve hangi bulut sağlayıcılarının açık olduğunu gösterir.
- **Sağlayıcı tarafında da limit koy:** OpenAI/Anthropic/OpenRouter panellerinde aylık harcama sınırı ve uyarı e-postası ayarlanabilir; mutlaka koy.
- Anahtarın sızdığını düşünürsen sağlayıcının panelinden **hemen sil/yenile**, sonra `sb set-secret api-<sağlayıcı>` ile yenisini gir.

## Buluta giden veri nasıl süzülür?

Bulut modele giden metinden **API anahtarı, şifre ataması, doğrulama kodu (OTP), kart numarası, IBAN, TCKN** otomatik maskelenir; **Kişi bilgisi maskeleme** açıksa e-posta, telefon ve adres de gizlenir. `gizli` (private) işaretli notlar hiç gönderilmez. Ayrıntı: [Güvenlik ve gizlilik](10-guvenlik-gizlilik.md).

## Sorun giderme

| Belirti | Ne yap |
|---|---|
| «Önce anahtarı yaz.» | Alan boş; anahtarı yapıştır |
| Test **Başarısız** / 401 | Anahtar yanlış ya da iptal edilmiş; yeniden üret |
| 429 / «quota» / «insufficient» | Bakiye bitti ya da kota doldu; sağlayıcı panelinde bakiyeyi kontrol et |
| «API anahtarı yok: … ortam değişkeni ya da `sb set-secret api-…`» | Anahtar kaydedilmemiş; yukarıdaki adımları izle |
| «günlük bütçe doldu: …» | `budget` sınırına ulaştın; `config/llm.yaml`'da sınırı artır ya da yarını bekle |
| «şifre kasası (keyring) yok» | İşletim sistemi şifre kasası kullanılamıyor ([Sorun giderme](11-sorun-giderme.md)) |
