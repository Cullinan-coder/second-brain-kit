# Model katmanı

> Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.

| | |
|---|---|
| Modül kimliği | `models` |
| Kategori | Kurulum ve model |
| Varsayılan | açık |
| Madde sayısı | 15 |
| Ne ister | hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`) |

## Ne işe yarar

Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.

Bu modül özellik kataloğundan **15 maddeyi** kapsar (aşağıda tek tek). Her madde için ayrı bir sihirbaz kutusu vardır.

<a id="nasil-acilir"></a>

## Nasıl açılır

1. **Kurulum sihirbazında:** 3. adım **Bütün özellikler** → arama kutusuna modül adını yaz (`Model katmanı`) → modül kutusunu işaretle. Kapattığında altındaki maddeler de kapanır; istersen maddeleri tek tek açıp kapatırsın.
2. **Kurulduktan sonra:** Second Brain uygulamasında **Uygulama ayarları → Ayarları aç** → **Özellikler** sekmesi (sihirbazın aynısı).
3. Bu modül bir **yol haritası grubudur**; ayrı bir komut anahtarı yoktur, yalnız Özellikler ekranından seçilir.

## Hangi hesap, veri ya da anahtar ister

**Hesaplar:** [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral)


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| OpenAI API anahtarı (`openai_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | platform.openai.com > API keys. |
| Anthropic API anahtarı (`anthropic_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | console.anthropic.com > API keys. |
| Gemini API anahtarı (`gemini_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | aistudio.google.com > Get API key. |
| OpenRouter API anahtarı (`openrouter_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | openrouter.ai > Keys. |
| Groq API anahtarı (`groq_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | console.groq.com > API Keys. |
| DeepSeek API anahtarı (`deepseek_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | platform.deepseek.com > API keys. |
| Mistral API anahtarı (`mistral_key`) | gizli değer (yalnız şifre kasasına yazılır) | hayır | console.mistral.ai > API keys. |

Gizli değerler (`openai_key`, `anthropic_key`, `gemini_key`, `openrouter_key`, `groq_key`, `deepseek_key`, `mistral_key`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Hazır seçimlerde

- **Yoğunluk:** Minimal, Günlük hayat, Güç kullanıcısı seçildiğinde açıktır.

Hazır seçimlerin ne olduğu: [Hazır seçimler](../15-hazir-secimler.md). Sihirbazın 2. adımı bu seçimleri birleştirir.

## Nasıl kullanılır

- **Ekranlar / kullanım yeri:** **Uygulama ayarları → Modeller sekmesi** (Görünümler menüsü ve ayarlar; tanıtım: [Uygulama turu](../08-uygulama-turu.md)).
- **Komutlar:** [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask) (tümü: [Komut referansı](../14-komut-referansi.md)).
- **Asistan:** sohbet kutusuna doğal dille isteyebilirsin; ayrıntılı kullanım ve örnekler: [Asistan kullanımı](../09-asistan-kullanimi.md).

## Sağlık testi

Çalışıp çalışmadığını `sb doctor` ile denetle (ayrıntı: [`sb doctor`](../14-komut-referansi.md#sb-doctor)). Uygulamada **Çalışmaya başla** düğmesi aynı sağlık kontrolünü çalıştırır.

## Maddeler

| No | Madde | Durum | Sürüm |
|---|---|---|---|
| [23](#madde-23) | API sağlayıcıları (OpenAI, Anthropic, Gemini, OpenRouter, Groq, Mistral, DeepSeek) | hazır | 0.4.0 |
| [24](#madde-24) | Model yönlendirici (yerel/bulut, kural/maliyet) | hazır | 0.4.0 |
| [25](#madde-25) | Görev başına model seçimi | hazır | 0.4.0 |
| [26](#madde-26) | Maliyet takibi ve bütçe sınırı | hazır | 0.4.0 |
| [27](#madde-27) | Yedek zinciri (bulut↔yerel) | hazır | 0.4.0 |
| [28](#madde-28) | Yerel model yöneticisi | hazır | 0.4.0 |
| [29](#madde-29) | LM Studio, llama.cpp, vLLM desteği | hazır | 0.4.0 |
| [30](#madde-30) | Küçük ekran kartı modu | hazır | 0.4.0 |
| [31](#madde-31) | Kullanıcı verisiyle model sınavı ve öneri | hazır | 0.4.0 |
| [32](#madde-32) | Gizlilik etiketine göre yönlendirme | hazır | 0.4.0 |
| [33](#madde-33) | Cevap önbelleği | hazır | 0.4.0 |
| [34](#madde-34) | Akış (streaming) cevap | yapım aşamasında (kısmen) | 0.4.0 |
| [35](#madde-35) | Düşünme modu düğmesi | hazır | 0.4.0 |
| [36](#madde-36) | Uzun bağlam modu (parça parça okuma) | hazır | 0.4.0 |
| [37](#madde-37) | Gömme (embedding) modeli seçimi | hazır | 0.4.0 |

<a id="madde-23"></a>

### 23. API sağlayıcıları (OpenAI, Anthropic, Gemini, OpenRouter, Groq, Mistral, DeepSeek)

- **Ne işe yarar:** «API sağlayıcıları (OpenAI, Anthropic, Gemini, OpenRouter, Groq, Mistral, DeepSeek)» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-24"></a>

### 24. Model yönlendirici (yerel/bulut, kural/maliyet)

- **Ne işe yarar:** «Model yönlendirici (yerel/bulut, kural/maliyet)» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-25"></a>

### 25. Görev başına model seçimi

- **Ne işe yarar:** «Görev başına model seçimi» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-26"></a>

### 26. Maliyet takibi ve bütçe sınırı

- **Ne işe yarar:** «Maliyet takibi ve bütçe sınırı» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-27"></a>

### 27. Yedek zinciri (bulut↔yerel)

- **Ne işe yarar:** «Yedek zinciri (bulut↔yerel)» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-28"></a>

### 28. Yerel model yöneticisi

- **Ne işe yarar:** «Yerel model yöneticisi» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-29"></a>

### 29. LM Studio, llama.cpp, vLLM desteği

- **Ne işe yarar:** «LM Studio, llama.cpp, vLLM desteği» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-30"></a>

### 30. Küçük ekran kartı modu

- **Ne işe yarar:** «Küçük ekran kartı modu» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-31"></a>

### 31. Kullanıcı verisiyle model sınavı ve öneri

- **Ne işe yarar:** «Kullanıcı verisiyle model sınavı ve öneri» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-32"></a>

### 32. Gizlilik etiketine göre yönlendirme

- **Ne işe yarar:** «Gizlilik etiketine göre yönlendirme» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-33"></a>

### 33. Cevap önbelleği

- **Ne işe yarar:** «Cevap önbelleği» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-34"></a>

### 34. Akış (streaming) cevap

- **Ne işe yarar:** «Akış (streaming) cevap» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** yapım aşamasında (kısmen); yol haritasında Faz 0 / sürüm 0.4.0 için yer alır. Şu an tam çalışmasını bekleme.
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** henüz kullanılamaz; hazır olunca bu sayfa ve sürüm notları ([Değişiklikler](../00-baslangic.md#surum-ve-guncelleme)) duyurur.
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-35"></a>

### 35. Düşünme modu düğmesi

- **Ne işe yarar:** «Düşünme modu düğmesi» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-36"></a>

### 36. Uzun bağlam modu (parça parça okuma)

- **Ne işe yarar:** «Uzun bağlam modu (parça parça okuma)» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).

<a id="madde-37"></a>

### 37. Gömme (embedding) modeli seçimi

- **Ne işe yarar:** «Gömme (embedding) modeli seçimi» (Model katmanı kategorisi), «Model katmanı» modülünün parçasıdır. Modülün amacı: Sağlayıcılar, yönlendirici, görev başına model, maliyet takibi, yerel model yöneticisi.
- **Durum:** hazır (sürüm 0.4.0).
- **Nasıl açılır:** «Model katmanı» modülü açıkken gelir; sihirbazın 3. adımında bu maddenin kendi kutusu vardır (modül sayfasının [Nasıl açılır](#nasil-acilir) bölümü).
- **Ne ister:** hesap: [OpenAI](../04-api-anahtarlari.md#anahtar-openai), [Anthropic](../04-api-anahtarlari.md#anahtar-anthropic), [Gemini](../04-api-anahtarlari.md#anahtar-gemini), [OpenRouter](../04-api-anahtarlari.md#anahtar-openrouter), [Groq](../04-api-anahtarlari.md#anahtar-groq), [DeepSeek](../04-api-anahtarlari.md#anahtar-deepseek), [Mistral](../04-api-anahtarlari.md#anahtar-mistral); gizli değer: OpenAI API anahtarı (`openai_key`), Anthropic API anahtarı (`anthropic_key`), Gemini API anahtarı (`gemini_key`), OpenRouter API anahtarı (`openrouter_key`), Groq API anahtarı (`groq_key`), DeepSeek API anahtarı (`deepseek_key`), Mistral API anahtarı (`mistral_key`).
- **Nasıl kullanılır:** modül açık ve gereksinimler tamamsa şuralardan kullanılır: ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask). Asistana doğal dille de isteyebilirsin ([Asistan kullanımı](../09-asistan-kullanimi.md)).
- **İlgili ekran/komut:** ekran: **Uygulama ayarları → Modeller sekmesi**; komut: [`sb models`](../14-komut-referansi.md#sb-models), [`sb usage`](../14-komut-referansi.md#sb-usage), [`sb embed-test`](../14-komut-referansi.md#sb-embed-test), [`sb qwen`](../14-komut-referansi.md#sb-qwen), [`sb ask`](../14-komut-referansi.md#sb-ask).
