# Mini sohbet balonu

Tek dosya (`bubble.html`), küçük pencerede açılır. Yalnız `127.0.0.1:8765` ile konuşur.
Dosyadan (`file://`) açılınca tarayıcı çapraz-köken kuralları nedeniyle sunucu `X-SB` başlıklı isteklere CORS izni vermiyorsa istekler düşer;
o durumda balonu sunucu üzerinden servis et.

## Açma (masaüstü kısayolu)
Kısayol hedefi:

    msedge --app="file:///C:/Users/kullanici/SecondBrain/_system/integrations/bubble/bubble.html" --window-size=380,560

Kısayolu masaüstüne ya da görev çubuğuna sen oluştur (otomatik kurulum yok).

## Özellikler
- Soru yaz, Enter ile gönder (`/api/v2/chat`); kaynaklar listelenir.
- Mik düğmesi: MediaRecorder ile kayıt, `/api/v2/stt`'ye gönderilir, döküm kutuya yazılır.

## Önerilen açılış
Dosyayı doğrudan açma (`file://` kaynağını sunucu güvenlik için reddeder). Asistan balonu kendisi sunar:

```
msedge --app=http://127.0.0.1:8765/bubble --window-size=420,640
```
