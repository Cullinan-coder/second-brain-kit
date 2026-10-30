# Değişiklikler

Kurulu sürümünü `sb version` gösterir. Güncellemek için `sb update` yaz; notlarına ve ayarlarına dokunmaz.

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
