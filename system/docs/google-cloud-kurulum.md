# Google Cloud kurulumu (bir kez, ~10 dk)

Amaç: Second Brain scriptlerinin Gmail'i **salt okunur** okuyabilmesi ve takvime etkinlik ekleyebilmesi için bir OAuth istemcisi.
Hepsi **ornek@gmail.com** ile yapılır. Şifre ya da kod paylaşman gerekmiyor.

## 1. Proje
1. https://console.cloud.google.com → sağ üstte kocaayse16 hesabı seçili olsun.
2. Üstteki proje seçici → **New project** → ad: `second-brain` → **Create** → oluşan projeyi seç.

## 2. API'leri aç
**APIs & Services → Library** içinde tek tek ara ve **Enable** de:
- Gmail API
- Google Calendar API
- People API (rehber, Faz 3b)
- Google Drive API (Faz 4)

## 3. İzin ekranı (Google Auth Platform)
1. Sol menü **Google Auth Platform** (veya APIs & Services → OAuth consent screen) → **Get started**.
2. App name: `Second Brain`, User support email: ornek@gmail.com → Next.
3. Audience: **External** → Next. Contact email: ornek@gmail.com → Next → kabul et → **Create**.
4. **Audience** sekmesi → **Test users → Add users**: `ornek@gmail.com`, `ornek2@gmail.com` → Save.
5. Aynı sekmede **Publish app** → onayla. (Testing'de kalırsa giriş her 7 günde düşer.
   Doğrulanmamış uygulama uyarısı çıkacak; kendi uygulaman olduğu için sorun değil.)
6. **Data Access → Add or remove scopes** → şunları işaretle → Update → Save:
   - `.../auth/gmail.readonly`
   - `.../auth/calendar.events`
   - `.../auth/contacts.readonly`
   - `.../auth/drive.readonly`

## 4. İstemci (client) oluştur
1. **Clients → Create client** → Application type: **Desktop app** → Name: `sb-desktop` → **Create**.
2. Açılan pencerede **Download JSON**.
3. İnen dosyayı şu ada ve konuma taşı:
   `C:\Users\kullanici\.secondbrain\secrets\client_secret.json`
   (Bu klasör kasanın dışında, GitHub'a gitmez.)

Bitince Claude'a "tamam" yaz. İlk çalıştırmada tarayıcı açılır, kocaayse16 ile giriş yapıp izin verirsin.
"Google hasn't verified this app" çıkarsa: **Advanced → Go to Second Brain (unsafe)**.
