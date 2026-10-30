# macOS notları

Kod macOS için yazıldı (`sb/platform_mac.py`, `tools/schedule_macos.py`) ama **gerçek bir Mac'te uçtan uca denenmedi**; kurulum ve testler her push'ta GitHub Actions macOS'ta otomatik çalışır.
Sorun görürsen `sb doctor` çıktısıyla birlikte bildir.

| Özellik | macOS karşılığı | İzin |
|---|---|---|
| Zamanlayıcı | launchd (`~/Library/LaunchAgents/com.secondbrain.{daily,weekly,chat}.plist`) | — |
| Uygulama açma | `/Applications` + `open -a` | — |
| Medya | AppleScript: ses `set volume`, Spotify/Music `playpause/next` | Otomasyon |
| WhatsApp onaylı gönderme | `whatsapp://` + WhatsApp'ı öne getir + Return | **Erişilebilirlik** (Terminal/Python) |
| Ekran okuma | `mss` ekran görüntüsü + Apple Vision OCR (pyobjc) + görsel model | **Ekran Kaydı** |
| Kamera | OpenCV | **Kamera** |
| Bildirim | `osascript display notification` | Bildirimler |
| Terminal | `/bin/zsh -lc` (yasak kalıplar: sudo, diskutil erase, csrutil, launchctl, defaults write, rm -rf /…) | — |
| Tailscale | `/Applications/Tailscale.app/Contents/MacOS/Tailscale` | — |
| YouTube | tarayıcıda (Edge YouTube uygulaması yalnız Windows'ta) | — |
| Şifreler | Anahtar Zinciri (keyring) | ilk erişimde "İzin ver" |
| Beyne at (pano) | `pbpaste`; kısayol elle: Kestirmeler (Shortcuts) → yeni kestirme → "Kabuk Betiği Çalıştır": `cd ~/SecondBrain/_system && ~/.local/bin/uv run python -m sb capture` → Ayrıntılar → Klavye Kestirmesi ⌃⌥B | — |

Asistanı yeniden başlatmak: `python3 _system/tools/schedule_macos.py --restart-chat`.
Görsel model ve Qwen Apple Silicon'da Ollama ile çalışır; 16 GB birleşik bellekte `qwen3:14b` sınırda, `qwen3:8b` önerilir
(`config/llm.yaml` → `ollama.model`).
