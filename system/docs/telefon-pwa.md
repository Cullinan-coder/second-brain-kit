# Telefon: PWA, paylaş, bildirim, çevrimdışı kuyruk, tünel (Faz 5 · Paket M)

## 1. Kurulum (PWA)
Telefonda arayüzü aç (Tailscale adresi) -> tarayıcı menüsü -> "Ana ekrana ekle". `manifest.webmanifest` + `sw.js` kabuğu önbelleğe alır;
API yanıtları önbelleğe ALINMAZ (özel veri). Android'de "Paylaş" menüsünde "İkinci Beyin" görünür (share_target -> `/share` -> `POST /api/v2/share`).

## 2. HTTPS (Tailscale) — push ve ana ekran için şart
```
tailscale serve --https=443 http://127.0.0.1:<sb-portu>
```
Tailscale yönetim panelinde MagicDNS + HTTPS Certificates açık olmalı. Adres `https://<makine>.<tailnet>.ts.net`. Servis worker ve push yalnız HTTPS'te çalışır.

## 3. Bildirimler (Web Push)
- Sunucuda `pip install pywebpush` (isteğe bağlı; yoksa `/api/v2/push/status` -> `available:false`, uygulama içi bildirim merkezi geçerli).
- VAPID özel anahtarı ilk kullanımda üretilir ve yalnız keyring'e (`second-brain` / `push-vapid-private`) yazılır. Abonelikler `~/.secondbrain/push_subs.json` (kasaya yazılmaz).
- Telefonda ayar: `SB.mobile.enablePush()` (izin ister, abone olur). Her `convstore.notify` bildirimi abonelere gider (gövde `redact`'lı).
- iOS: yalnız ana ekrana eklenmiş PWA'da (16.4+) çalışır.

## 4. iOS Kestirme ("Beyne at")
Kestirmeler uygulamasında yeni kestirme: **Paylaşım sayfasında göster** açık -> "URL'yi kodla" (Metin = Kestirme Girdisi) ->
"URL'leri aç": `https://<adres>/share?text=<kodlanmış metin>`. Açılan sayfa metni önizler; "Beyne at" düğmesi `POST /api/v2/share` yapar.
(Eşlenmiş cihaz çerezi gerekir.)

## 5. Çevrimdışı kuyruk
Bağlantı yokken gönderilen mesaj ve başarısız paylaşımlar IndexedDB'ye (`sb-mobile/queue`) yazılır; ekranda "Kuyrukta N". Bağlantı gelince
sırayla gönderilir (biri takılırsa durur, sıra bozulmaz).

## 6. Dış erişim tüneli (Cloudflare Tunnel + Access)
Tünel kendiliğinden BAŞLAMAZ; `mobile.tunnel_status()` / `tunnel_plan()` yalnız durum ve komut üretir.
1. `cloudflared` kur; `cloudflared tunnel login`, `cloudflared tunnel create second-brain`, `cloudflared tunnel route dns second-brain <alt.alan>`.
2. Cloudflare Zero Trust -> Access -> Applications: self-hosted, alan adın; politika: yalnız kendi e-postan (One-time PIN). **Politika olmadan tünel açılmaz.**
3. `~/.secondbrain/tunnel.json`: `{"hostname": "<alt.alan>", "tunnel": "second-brain", "port": 8765, "access_policy": true}` (politikayı kurduktan sonra elle).
4. `ready:true` olunca plan çalıştırma komutunu verir: `cloudflared tunnel run --url http://127.0.0.1:<port> second-brain`.
Cihaz eşlemesi (kod + çerez) tünelde de geçerlidir; Access ikinci kapıdır.

## 7. Yakında (kod yok)
Widget (79), konum (81), saat (84), ekran görüntüsü (85).
