# Second Brain tarayıcı eklentisi (Chrome/Edge, MV3)

Yükleme: `chrome://extensions` -> Geliştirici modu -> "Paketlenmemiş öğe yükle" -> bu klasör.

Sağ tık "Beyne at": seçili metin yoksa sayfa adresi (brain_capture), varsa "Not al:" ile inbox'a.
Adres `login|signin|checkout|bank` içeriyorsa devre dışı. Yalnız `http://127.0.0.1:8765` ile konuşur;
asistan sunucusu (SecondBrain-Chat) açık olmalı.

Not: sunucu `chrome-extension://` Origin'ini reddedebilir (403); o durumda sunucu tarafında izin gerekir.

## İzin (zorunlu)
Asistan sunucusu güvenlik için bilinmeyen eklentileri reddeder. Eklentiyi yükledikten sonra `chrome://extensions` sayfasındaki
**Kimlik** (32 harf) değerini `_system/config/eklentiler.yaml` dosyasına yaz ve asistanı yeniden başlat:

```yaml
chrome: [buraya-32-harflik-kimlik]
```
