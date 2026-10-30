# Güvenlik ve gizlilik

| Konu | Nasıl korunur |
|---|---|
| Şifre ve token'lar | İşletim sisteminin şifre kasası (keyring, servis `second-brain`). Repoda, kasada, kayıtlarda yok. `tools/secrets_status.py` var/yok gösterir, değer yazdırmaz |
| Google | Gmail `readonly`; takvim yazma yalnız onaylı; OAuth istemcisi senin projen, `~/.secondbrain/secrets` (git dışı) |
| Mail gönderme | Kodda yok; tek istisna sabah özeti, yalnız `accounts.yaml notify.to` listesine (kod da doğrular) |
| Kasaya hassas veri | Kart numarası, TC kimlik, IBAN, OTP maskelenir (`redact.py`); `tools/lint.py` kasayı tarar; hafıza/not kutusu reddeder |
| Yerel arşiv | `~/.secondbrain` git'e ve telefona gitmez. Yedeklemek istersen kendi şifreli yedeğini kur |
| Asistan eylemleri | Serbest / onaylı / yasak sınıfları; kirli içerik kuralı; WhatsApp yalnız onaydan sonra ve WhatsApp öndeyse |
| Terminal | Salt-okunur izinli komutlar hemen; diğerleri tam metniyle onaya; yıkıcı kalıplar hiç; kullanıcı yetkisiyle, zaman sınırlı |
| Asistan sunucusu | Yalnız 127.0.0.1 + (varsa) Tailscale adresi; Host/Origin denetimi, POST'ta özel başlık, CSP |
| Telefon | Tailscale özel ağı, 6 haneli kod (5 yanlış → 15 dk kilit), 180 günlük HttpOnly çerez (diskte SHA-256), tek tuşla iptal |
| Claude Code kancaları | Model çağırmaz, ağa çıkmaz, hata verirse sessizce çıkar; `sb`'nin kendi `claude -p` çağrılarında susar |
| Kasa değişiklikleri | Her biri ayrı git commit'i + `asistan_log.jsonl`; "geri al" ile `git revert` |

Kasa reposunu GitHub'a koyacaksan **özel (private)** repo kullan: kasada kişisel notların var.
