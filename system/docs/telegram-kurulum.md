# Telegram botu kurulumu (~3 dk)

Sabah özeti ve hata uyarıları telefonuna Telegram'dan gelecek; bota yazdığın her şey `00-Inbox`'a not olarak düşecek.

1. Telegram'da **@BotFather**'ı aç (mavi tikli resmi hesap) → `/newbot`
   - Ad: `Second Brain` (istediğin ad olabilir)
   - Kullanıcı adı: `ayse_secondbrain_bot` gibi, **bot** ile bitmeli. Alınmışsa başka bir şey dene.
2. BotFather sana bir **token** verecek (`123456789:AA...` biçiminde uzun bir yazı). **Kimseyle paylaşma, bana da gönderme.** Kopyala.
3. Bilgisayarında bir terminal aç ve şunu çalıştır, token'ı sorunca yapıştır (ekranda görünmez):
```
uv run --directory C:\Users\kullanici\SecondBrain\_system python -m sb set-secret telegram-bot
```
4. Telegram'da yeni botunu bul (BotFather'ın verdiği linke tıkla) → **Start**'a bas, sonra ona `merhaba` yaz.
5. Aynı terminalde botu sana bağla:
```
uv run --directory C:\Users\kullanici\SecondBrain\_system python -m sb telegram-setup
```
   "bağlandı" yazısını görünce bana "tamam" yaz; deneme mesajı telefonuna gelecek.

Güvenlik: Bot sadece **senin** sohbet kimliğinden gelen mesajları işler; başkası yazarsa yok sayılır.
