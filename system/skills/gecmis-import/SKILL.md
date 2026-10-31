---
name: gecmis-import
description: Eski yapay zeka sohbet geçmişini (ChatGPT, Claude.ai, Gemini Takeout) ikinci beyne aktar ve bilgiye damıt. "geçmiş import", "geçmişimi aktar", "chatgpt geçmişi", "takeout", "eski sohbetlerimi beyne yükle" dendiğinde kullan.
---

# Geçmiş içe aktarımı

Onay kapısı ZORUNLU — kullanıcının açık izni olmadan dışa aktarım dosyasını ayrıştırma ya da kasaya yazma.

1. Veri akışını anlat: dosya yerelde okunur; seçilen sohbetler `40-Kaynaklar/Sohbet geçmişi/<Kaynak> YYYY-AA.md` notlarına
   kısaltılarak yazılır; başka hiçbir yere gönderilmez. Sonradan damıtma yaparken notları okuyan model (Claude) bu metni görür.
2. Özel/hassas sohbetlerin varsayılan olarak DAHİL olacağını söyle; tarih sınırı (`--since/--until`) ve hariç tutma kelimeleri
   (`--exclude "sağlık,ilişki,..."`) öner. Gizli tutmak isterse `--private` (otomatik bağlama girmez).
3. Dışa aktarımı nasıl alacağını gerekiyorsa anlat:
   - ChatGPT: Ayarlar › Veri kontrolleri › Verileri dışa aktar (mailde zip; içinde conversations.json).
   - Claude.ai: Ayarlar › Gizlilik › Verileri dışa aktar (zip; conversations.json).
   - Gemini: takeout.google.com › yalnız "Etkinliğim › Gemini Uygulamaları", JSON biçimi.
4. Deneme: `sb history-import <zip|klasör> [--since ..] [--exclude ..]` — yazmadan ay/sohbet sayısını gösterir. Kullanıcıya göster.
5. Onay gelince aynı komut `--apply`.
6. Damıtma (isteğe bağlı, kullanıcı isterse): ayları tek tek oku; tekrar kullanılabilir bilgi için `sb concept`, kararlar için ilgili
   proje notu, kişiler için `sb person`. Ham sohbeti kopyalama; kaynak olarak ilgili ay notunu ver. Bitince `sb receipt`.
