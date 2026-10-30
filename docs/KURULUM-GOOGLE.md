# Google bağlantısı (bir kez, ~10 dk)

Gmail'i **salt-okunur** okumak, takvime (onaylı) etkinlik eklemek, rehberi ve Drive'ı okumak için kendi Google Cloud
OAuth istemcin gerekir. Ücretsizdir; kimseyle şifre paylaşmazsın. Hepsini **kendi Gmail hesabınla** yap.

## 1. Proje
1. https://console.cloud.google.com → sağ üstte kendi hesabın seçili olsun.
2. Proje seçici → **New project** → ad: `second-brain` → **Create** → projeyi seç.
   (“Proje sınırı doldu” derse var olan bir projeyi kullanabilirsin.)

## 2. API'leri aç
**APIs & Services → Library** → tek tek ara → **Enable**: Gmail API · Google Calendar API · People API · Google Drive API

## 3. İzin ekranı
1. **Google Auth Platform** (ya da OAuth consent screen) → **Get started**.
2. App name `Second Brain`, destek maili kendi adresin → **External** → iletişim maili → kabul → **Create**.
3. **Audience → Test users → Add users**: kullanacağın Gmail adres(ler)in.
4. **Publish app** (Testing'de kalırsa giriş 7 günde bir düşer). "Doğrulanmamış uygulama" uyarısı normaldir: uygulama senin.
5. **Data Access → Add or remove scopes**: `gmail.readonly`, `calendar.events`, `contacts.readonly`, `drive.readonly` → Save.

## 4. İstemci
1. **Clients → Create client** → **Desktop app** → ad `sb-desktop` → **Create** → **Download JSON**.
2. Kurucu sorduğunda bu dosyanın yolunu ver; ya da elle şuraya koy (kasanın dışında, git'e girmez):
   - Windows: `C:\Users\<kullanıcı>\.secondbrain\secrets\client_secret.json`
   - macOS: `~/.secondbrain/secrets/client_secret.json`

## 5. Giriş
```bash
uv run --directory <kasa>/_system python -m sb login main
```
Tarayıcı açılır, hesabınla izin verirsin. "Google hasn't verified this app" → **Advanced → Go to Second Brain**.
Yenileme anahtarı işletim sisteminin şifre kasasına yazılır. İkinci Gmail için `config/accounts.yaml`'a `side:` ekleyip `sb login side`.

**Neden bu izinler?** Mail yalnız okunur (gönderme/silme izni hiç istenmez). Takvim yazma izni yalnız senin onayladığın
etkinlikler içindir. Sabah özeti Gmail'den değil, (varsa) kendi SMTP hesabından gider.
