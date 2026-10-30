# Asistanı telefondan kullanma (Tailscale)

Asistan sunucusu bilgisayarında `127.0.0.1:8765`'te çalışır. Telefona açmak için **internete açık tünel kullanılmaz**:
[Tailscale](https://tailscale.com) yalnız senin cihazlarından oluşan şifreli bir özel ağ kurar (ücretsiz kişisel plan).

1. **Bilgisayar:** Tailscale'i kur, hesabınla giriş yap, *Connected* olsun.
2. **Telefon:** Play Store / App Store'dan Tailscale, **aynı hesapla** giriş, *Connected*.
3. ~1 dk içinde asistan sunucusu Tailscale adresini fark eder. Obsidian'da `Asistan.md`'nin üstünde şu satır görünür:
   `📱 Telefon: http://100.x.y.z:8765 · eşleme kodu 123456`
4. Telefonda tarayıcıda o adresi aç (https değil **http**), 6 haneli kodu gir → **Eşle**.
5. Tarayıcı menüsü → **Ana ekrana ekle / Add to Home screen**. Tanınma 180 gün sürer ve her açılışta yenilenir.

**Güvenlik:** Dinleyici yalnız Tailscale adresine (100.64.0.0/10) bağlanır; ev ağından ya da internetten erişilemez.
5 yanlış kodda eşleme 15 dk kilitlenir. Telefondan istenen her bilgisayar eylemi (uygulama, müzik, komut, not düzenleme)
**onay kartına** düşer. Bilgisayardaki sayfada "telefon bağlantılarını kapat" tüm eşlemeleri iptal eder.
