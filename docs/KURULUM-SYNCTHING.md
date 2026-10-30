# Kasayı Redmi'ye eşitleme (Syncthing, ücretsiz) — ~15 dk

Kasa telefonda Obsidian ile açılır: oku, düzenle, ara. Eşitleme **bilgisayar açıkken** olur (bulut yok, doğrudan cihazlar arası).
`.stignore` dosyası `.git`, Python ortamı (209 MB) ve cihaza özel ayarları dışarıda tutar.

## 1. Bilgisayar (bir kez)
1. Syncthing bilgisayarda kurulu: `C:\Users\kullanici\syncthing-windows-amd64-v2.0.15\syncthing.exe`. `schedule.ps1` onu her oturum açılışında
   arka planda başlatan görevi de kaydeder. Şimdi elle başlatmak için exe'ye çift tıkla, panel tarayıcıda açılır: http://127.0.0.1:8384.
2. Panelde **Actions → Show ID** ile bilgisayarın cihaz kimliğini (uzun kod) görürsün. QR kodu da var.

## 2. Telefon (Redmi 13 Pro)
1. **Syncthing-Fork** uygulamasını kur (Play Store ya da F-Droid; geliştirici: Catfriend1).
2. Açılışta depolama iznini ver. Xiaomi'de: Ayarlar → Uygulamalar → Syncthing-Fork → **Pil: Kısıtlama yok**, **Otomatik başlatma: Açık**.
3. **Cihazlar → +** → bilgisayarın QR kodunu okut (ya da kimliği yapıştır).
4. Bilgisayarda panelde "Yeni cihaz eklensin mi?" çıkar → **Add Device** → Sharing sekmesinde `Default Folder` yerine aşağıdaki klasörü paylaş.

## 3. Klasörü paylaş
1. Bilgisayar panelinde **Add Folder**: Folder Label `SecondBrain`, Folder Path `C:\Users\kullanici\SecondBrain`,
   **Sharing** sekmesinde telefonu işaretle → Save.
2. Telefonda bildirim gelir: klasörü kabul et, yol olarak `Documents/SecondBrain` seç.
3. Telefonda klasörün **Ignore Patterns** bölümüne `.stignore`'daki satırları gir (`.git`, `_system/.venv`, `.obsidian/plugins/obsidian-git`,
   `.obsidian/workspace.json`, `.obsidian/workspace-mobile.json`, `**/__pycache__`).
4. İlk eşitleme birkaç dakika sürer.

## 4. Obsidian (telefon)
Obsidian'ı aç → **Kasayı klasör olarak aç** → `Documents/SecondBrain`. Çekirdek eklentiler (Bases, Şablonlar) telefonda da çalışır.
Topluluk eklentisi (Obsidian Git) telefona gelmez; gerek yok: değişiklikleri bilgisayardaki Obsidian Git commit/push eder.

## Notlar
- Telefon ve bilgisayar aynı anda aynı notu düzenlerse Syncthing `*.sync-conflict-*` dosyası üretir; ikisini birleştirip birini sil.
- Bilgisayar kapalıyken telefondaki düzenlemeler bekler, açılınca eşitlenir.
- Daha kesintisiz istersen Obsidian Sync (aylık $4) planı hâlâ ayakta; bu kuruluma dokunmadan geçilebilir.
