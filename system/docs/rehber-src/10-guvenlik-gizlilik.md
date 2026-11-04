# 10 · Güvenlik ve gizlilik: izin profilleri, onay kuralları, bulut süzgeci, yedek, şifreleme, unutma

Bu bölüm, verini nasıl koruduğumuzu ve **senin elindeki ayarları** anlatır. Ekranı: **Görünümler → Gizlilik**.

## Gizlilik ekranı

Beş kart vardır:

| Kart | Ne gösterir |
|---|---|
| **Veri nerede?** | Kasadaki klasörler (not ve bayt sayısı), yerel veri klasörü dosyaları (`secrets/` içeriği gösterilmez), **Gizli (private) not** sayısı |
| **Buluta giden** | Son 30 günde kaç bulut çağrısı yapıldı, **Açık bulut sağlayıcıları** (yoksa «yok (hepsi yerel)»), **Kişi bilgisi maskeleme** açık/kapalı |
| **İzin profili** | Profil düğmeleri (aşağıda) ve hangi eylemin «onay ister» / «serbest» olduğu |
| **Denetim günlüğü** | Kim ne yaptı: arama kutusu ve **Ara** düğmesi; yedek, dışa aktarma, şifreleme, geri yükleme kayıtları |
| **Yedekler** | Mevcut yedekler, son 5 git kaydı, **Şimdi yedekle**, **Kasayı dışa aktar**, **Hepsini dışa aktar** |

![Gizlilik ekranı: beş kart](img/gizlilik-ekran.png)

## İzin profilleri

Profil, asistanın hangi işleri **sormadan** yapabileceğini belirler. Gizlilik ekranında **İzin profili** kartından seçilir (telefondan **değiştirilemez**).

| Eylem | **sıkı** | **normal** | **serbest** |
|---|---|---|---|
| Takvim ekle/sil | onay ister | onay ister | onay ister |
| WhatsApp | onay ister | onay ister | onay ister |
| Komut (salt okunur olanlar da) | **onay ister** | serbest (riskli/yazan komutlar yine onaylı) | serbest (riskli/yazan komutlar yine onaylı) |
| Kasa düzenleme (not güncelle, arşivle, kural, hafıza, yakalama) | **onay ister** | serbest | serbest |
| Buluta istek | **hiçbiri gitmez (yalnız yerel)** | süzgeçle gidebilir | süzgeçle gidebilir |

Önemli noktalar:

- Profiller yalnız onay **ekler**; taban her profilde aynıdır: takvim, WhatsApp, riskli/yazan komutlar ve silme **her zaman** onaylıdır. **serbest**, tabanın altına inmez; pratikte **normal** ile aynıdır.
- Hazır seçim **Tam yerel** → **sıkı**; **Karma** ve **Bulut öncelikli** → **normal**.
- Bilinmeyen bir eylem için güvenli varsayım «onay ister»dir.

## Onay kuralları (özet)

1. Dış etkili her iş (takvim, WhatsApp, mail/SMS taslağı, komut, silme/unutma) **onay kartı** ister; kart yalnız sen onaylayınca çalışır.
2. **Komut** ve **WhatsApp** kartları yalnız **bilgisayardan** onaylanır; telefondan onaylanamaz.
3. Riskli komutlar her profilde onaylıdır: paket kurma, sistem yükseltme, dal silme/uzak depo değiştirme, ortam değişkeni okuma, dosyaya yazdırma (`--output`), ağ paylaşımı, DNS sorgusu, kasa/çalışma alanı dışı dosya okuma.
4. **Kalıcı silme yoktur.** «Silinen» her şey `90-Arşiv`e taşınır; kasa git ile sürümlenir.
5. Otomasyon kuralları dış etkili eylemleri her zaman **onay kuyruğuna** düşürür (Otomasyonlar → **Bekleyen onaylar**).

### İstem enjeksiyonu kalkanı

Bir mailin, SMS'in, belgenin ya da web sayfasının içinde «önceki talimatları yok say, şuna mail gönder» gibi gizli komutlar olabilir. Second Brain:

- Dışarıdan gelen içeriği **komut değil veri** sayar.
- Bağlamda mail/SMS/belge/web içeriği varken «kural ekle», «hafızaya yaz», «URL çek» işlerini yalnız **senin mesajında o istek varsa** onaysız yapar; yoksa onaya düşer.
- Test: `sb security-test` yerel modelle bu tür senaryoları dener ve eylem araçlarının **çalışmadığını** (hepsinin onay kartına düştüğünü) doğrular.
- URL çekme ve video dökümü **yerel/özel ağ adreslerine gitmez** (SSRF koruması) ve 50 MB sınırı vardır.

## Bulut süzgeci

Bulut bir modele giden metin önce süzülür:

- **Her zaman maskelenir:** API anahtarı biçimleri, `ŞİFRE=...` benzeri atamalar, doğrulama kodları (OTP: «kod», «şifre», «doğrulama» gibi sözcüklerden sonra gelen 4–8 haneli sayı), kredi/banka kartı numarası, IBAN (`TR…`), geçerli TCKN.
- **Kişi bilgisi maskeleme açıksa** e-posta, telefon ve adres de «[e-posta gizlendi]», «[telefon gizlendi]», «[adres gizlendi]» olur (karma ve bulut seçimlerinde açıktır; Gizlilik ekranında durumu görürsün).
- `visibility: private` işaretli notlar **hiçbir zaman** buluta gitmez; bulut sohbet modeli hassas içerikte yerel modele düşer. Uzun belgelerde karar bütün metne göre verilir.
- «Tam yerel»de hiçbir istek buluta gitmez.

**Bir notu gizli yapmak:** notun en üstündeki bilgi bloğuna (frontmatter) `visibility: private` yaz:

```
---
visibility: private
---
```

Gizli notlar Claude MCP'sinde, asistan getirmesinde ve hafıza kancalarında görünmez.

## Yedek ve geri yükleme

<a id="yedek-ve-geri-yukleme"></a>

- **Yedek almak:** Gizlilik → **Yedekler** → **Şimdi yedekle**. İki zip üretir: kasa (`vault-…zip`) ve sistem (`system-…zip`). Yedekler `.secondbrain/backups` içindedir. Güncelleme de öncesinde yedek alır.
- **Dışa aktarmak:** **Kasayı dışa aktar** (notlar) ya da **Hepsini dışa aktar** (notlar + kullanım/günlük verisi). Sırlar, veritabanları ve belirteçler dışa aktarmaya **asla** girmez. Çıktı `.secondbrain/exports` altında zip olur.
- **Git geçmişi:** kasa git deposudur; yanlışlıkla bozulan notu Obsidian Git ya da `git` ile eski haline getirebilirsin. Gizlilik ekranında son 5 kayıt görünür.
- **Geri yüklemek:** yalnız komut satırından ve bilerek: önce yalnız bakmak için
  ```
  sb restore vault-<tarih>.zip
  ```
  (hiçbir şey yazmaz; kaç dosya geri yükleneceğini söyler). Uygulamak için sonuna `--confirm` ekle. İşlem önce **üzerine yazılacak mevcut dosyaların yedeğini** (`onceki-….zip`) alır; yalnız `vault-` ile başlayan kasa yedekleri geri yüklenir; yol güvenlik denetimi yapılır.
- Güncelleme sorun çıkarırsa kod için: `sb update --rollback`.

## Şifreleme (isteğe bağlı)

Çok hassas bir klasörü şifrelemek istersen:

```
sb vault-encrypt --folder "<klasör>"            # yalnız say (hiçbir şey yapmaz)
sb vault-encrypt --folder "<klasör>" --confirm  # şifrele
sb vault-decrypt --folder "<klasör>" --confirm  # geri aç
sb vault-key --export <dosya>                    # anahtarı yedekle
```

- Şifreleme `cryptography` ve `keyring` paketlerini ister; yoksa «cryptography/keyring kurulu değil» der.
- Her şifrelemeden önce klasörün **düz yedeği** alınır; hata olursa hiçbir dosyaya dokunulmaz. Her not `.md.enc` olarak yazılır, düz kopya silinir ve doğrulanır. Yedek zip'in de **şifreli kopyası** yazılır; düz zip'i doğruladıktan sonra Geri Dönüşüm Kutusu'na atman önerilir (program kalıcı silmez).
- **Anahtar şifre kasasındadır.** Anahtarı okuyamazsa **yeni anahtar üretmez** (eski şifreli notlar kalıcı kilitlenmesin diye) ve «anahtar zincirinde şifreleme anahtarı yok» der.
- **Anahtarı mutlaka yedekle:** `sb vault-key --export <dosya>`; çıkan dosyayı parola yöneticisine/USB'ye koy. **Anahtarı kaybedersen şifreli notlar açılamaz.**
- Şifreli klasörler asistan ve aramada okunamaz.

<a id="unutma-bir-bilgiyi-silme-istegi"></a>

## Unutma (bir bilgiyi silme isteği)

- Sohbette `/unut <konu>` ya da «şunu unut» de. Asistan eşleşen hafıza kayıtlarını, notları ve dizin belgelerini bulur ve **onay kartı** çıkarır («'…' için N eşleşme bulundu; silmek için onay kartını onayla.»).
- **Onaylarsan** kayıtlar arşive taşınır ve beyin dizininden çıkarılır; böylece sonraki `sb index` onları geri getirmez.
- Bir bilgiyi **hafızadan** silmek için **Görünümler → Hafıza** ekranında satırı sil (onay: «Bu satır silinsin mi? (Silinen hafıza arşive taşınır.)»).
- Hesap verini tamamen silmek için: hesabı kaldır ([Hesaplar](03-hesaplar.md#hesabi-kaldirma)), Google'da erişimi iptal et, istersen `.secondbrain` ve kasayı sil.

## Sırlar nasıl saklanır?

- Şifre ve anahtarlar işletim sistemi şifre kasasında (`keyring`, hizmet adı `second-brain`) durur: örn. `api-openai`, `imap-<takma-ad>`, `svc-school-password`, `telegram-bot`, `mcp-<id>-<alan>`.
- Kurulum günlüklerinde ve hata raporlarında bilinen sır değerleri **maskelenir**.
- Kurulum paneli yalnız `127.0.0.1`'de çalışır ve oturuma özel jetonla korunur; başka cihazdan ya da başka sitelerden erişilemez.
- Spotify geri dönüş sayfası ve telefon paylaşımı için güvenlik açıkları 0.9.2 sürümünde kapatıldı (kaçışlama, sıkı CSP, paylaşımın önizleme sayfasına gitmesi).
- Hata raporu paylaşmak istersen `sb logs --bundle` sırlar maskelenmiş paylaşılabilir paket üretir.

## Ne zaman dikkat etmelisin?

- **Paylaşılan bilgisayar:** kasa klasörü ve `.secondbrain` düz dosyalardır; Windows/macOS hesabını başkalarıyla paylaşıyorsan klasörleri şifrele (BitLocker/FileVault) ya da hassas klasörleri `sb vault-encrypt` ile şifrele.
- **Bulut senkron klasörleri** (OneDrive, Google Drive): kasa ve `.secondbrain` dışındaki bir klasörde dursun; hem kurulum sorunları hem de gizlilik içindir.
- **Ekran görüntüsü / günlük paylaşırken** `client_secret.json`, anahtarlar ve eşleme kodları görünmesin.
