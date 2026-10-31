---
name: form-doldur
description: Tarayıcıdaki bir formu (başvuru, tedarikçi kaydı, resmi form) ikinci beyindeki bilgilerle doldur. "formu doldur", "başvuru formunu kasadaki bilgilerle doldur", "şu sayfadaki alanları doldur" dendiğinde kullan.
---

# Kasadaki bilgilerle form doldurma

Kural: **uydurma yok, gönderme yok.** Bilgisi kasada olmayan alan boş kalır; formu kullanıcı kendisi gönderir.

1. Formu tarayıcıda aç (yerleşik tarayıcı ya da kullanıcı isterse Claude in Chrome). Önce tüm alanları listele.
2. Her alan için kasada kaynak ara: `brain_search`, `brain_note`, özellikle `40-Kaynaklar/Belgeler/Kurumsal bilgiler.md`,
   `30-Kariyer/LinkedIn profili`, proje ve kişi notları. Her doldurulan alanın kaynağını (not yolu) not et.
3. Doldurma:
   - Kaynağı net olan alanları doldur.
   - Emin olmadığını ya da kasada olmayanı BOŞ bırak ve listele (iki benzer değer varsa kullanıcıya sor).
   - Şifre, kart numarası, TC kimlik, IBAN, pasaport gibi alanlara asla yazma — kasada da tutulmaz; kullanıcı kendisi girer.
4. Gönder/Onayla/Başvur düğmesine BASMA. Kullanıcıya tablo ver: alan · değer · kaynak; boş bırakılanlar ve neden.
5. Bittiğinde `sb receipt --summary "X formu dolduruldu (N/M alan), boşlar: ..." --ref <kullanılan not>`.

Resmi belgelerde (devlet, vergi, banka) her alanı kullanıcı gözden geçirmeden gönderilmemeli; yanlış bilgi ciddi sonuç doğurur.
