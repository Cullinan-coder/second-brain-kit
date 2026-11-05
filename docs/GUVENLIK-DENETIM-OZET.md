# Güvenlik denetimi özeti (2026-11)

Kasanın kodu 2026-11'de iki turda denetlendi (v0.11.0 ve v0.12.0 ile düzeltildi), sonra iş ortağı incelemesinde bir bulgu daha çıktı (B-01, v0.13.1).
Tam denetim raporu **bilerek bu depoya konmadı**: rapor her bulgunun saldırı yolunu adım adım anlatır, açık bir depoda yol haritası olurdu.
Bu belge yalnız **ne bulundu, ne durumda, ne kaldı** sorularını yanıtlar. Saldırı komutu, yeniden üretme adımı ya da kaynak satırı içermez.
Her düzeltmenin bir regresyon testi vardır (`system/tests/test_audit_2026_11*.py`, `test_d30_architecture.py`); testler düzeltmeden önceki kodda başarısız olarak görüldü.

Sayılar: 1 kritik, 6 yüksek, 10 orta, 11 düşük, 2 bilgi (toplam 30) + 1 inceleme bulgusu.
Durum: **28 düzeltildi (bazılarında aşağıda yazılı bilinen kalan sınır var), 2 kullanıcı kararı bekliyor (D-07, D-17)**; B-01 0.13.1'de düzeltildi.

## Bulgu tablosu

| Kimlik | Ciddiyet | Başlık | Durum |
|---|---|---|---|
| D-01 | Kritik | Komut sınıflandırıcısı onaysız çalışacak komutları yeterince katı ayıramıyordu | Düzeltildi (0.11.0) |
| D-02 | Yüksek | Dış içerik (mail, belge) varken komutlar onaya düşmüyordu | Düzeltildi (0.11.0) |
| D-03 | Yüksek | Tarayıcı eklentisinden gelen web seçimi kullanıcı sözü gibi işleniyordu | Düzeltildi (0.11.0) |
| D-04 | Yüksek | Yerel arayüz ucunda kimlik doğrulaması yoktu; kurulum jetonu fazla kolay veriliyordu | Düzeltildi (0.11.0); kalan risk: aynı kullanıcı hesabındaki kötü niyetli yerel süreç |
| D-05 | Yüksek | Telefondan gece işi eklemek ve onaylamak mümkündü | Düzeltildi (0.11.0) |
| D-06 | Yüksek | Dış içerik izleme (kirlilik bayrağı) boşluklu; kalıcı kural/hafıza yazımı Claude Code'a taşınabiliyordu | Düzeltildi (0.11.0, 0.13.0 ile kalıcı hale geldi); kalan: kanca eylemci işareti |
| D-07 | Yüksek | Kasanın tamamı uzak depoya itiliyor; uzak depodan kod değişikliği çekilebiliyor | **Kullanıcı kararı bekliyor** (aşağıda) |
| D-08 | Orta | Not eklemede satır sonu kontrolü yoktu | Düzeltildi (0.11.0); kalan: gece işi imzası ertelendi |
| D-09 | Orta | Salt okunur sayılan komutlarla kasa dışı dosya okunabiliyordu | Düzeltildi (0.11.0); ek kaçış yolu B-01 olarak 0.13.1'de kapandı |
| D-10 | Orta | Kasa şifreleme ve yedekler düz metni geçmişte bırakıyordu | Düzeltildi (0.12.0); kalan: eski düz yedekleri kullanıcı silmeli |
| D-11 | Orta | Gizli not (`visibility: private`) tespiti kırılgandı | Düzeltildi (0.11.0) |
| D-12 | Orta | «Kişi bilgilerini maskele» ayarı bulut çağrılarında uygulanmıyordu | Düzeltildi (0.11.0) |
| D-13 | Orta | Güncelleme ve kurulum zinciri doğrulamasızdı; yayın derlemesi kilit dosyasını kullanmıyordu | Düzeltildi (0.12.0); kalan: kod imzası |
| D-14 | Orta | Windows'ta ikinci bir süreç aynı yerel porta bağlanabiliyordu | Düzeltildi (0.11.0) |
| D-15 | Orta | Bazı kütüphane çıkışları arka plan döngülerini sessizce durduruyordu | Düzeltildi (0.11.0) |
| D-16 | Orta | MCP kataloğunda sürümü sabitlenmemiş paketler ve düz metin sırlar | Düzeltildi (0.11.0) |
| D-17 | Orta | Cloudflare tünel planı, yerel (kimliksiz) işleyiciyle birleştirilebilir | **Kullanıcı kararı bekliyor** (aşağıda) |
| D-18 | Düşük | Dış adres denetiminde ad çözümleme ile bağlantı arasında zaman farkı | Düzeltildi (0.12.0); kalan: yt-dlp kendi bağlantıları |
| D-19 | Düşük | Yan etkili ya da model çağıran GET uçları başka sitelerden tetiklenebiliyordu | Düzeltildi (0.11.0, D-04 kapsamında) |
| D-20 | Düşük | Süreçler arası kilitsiz oku-değiştir-yaz | Düzeltildi (0.12.0); kalan: bazı not ekleme yardımcıları kilitsiz |
| D-21 | Düşük | `undo_last` yanlış değişikliği geri alabiliyordu | Düzeltildi (0.11.0) |
| D-22 | Düşük | Ollama kurulumunda ortak geçici klasör, imza denetimi yok | Düzeltildi (0.12.0); macOS yolu denenmedi |
| D-23 | Düşük | Telefon eşleme kilidi küresel, kod süresizdi | Düzeltildi (0.12.0); kalan: kodu ekranda varsayılan gizleme yok |
| D-24 | Düşük | `restore` kod ve git klasörlerine yazabiliyordu | Düzeltildi (0.11.0) |
| D-25 | Düşük | Zamanlanmış görev betiğinde Syncthing yolu ve tırnak işleme | Düzeltildi (0.12.0); kalan: Syncthing imza denetimi yok |
| D-26 | Düşük | İzin profili okunamazsa sessizce gevşek profile düşülüyordu | Düzeltildi (0.11.0) |
| D-27 | Düşük | Push aboneliği uç noktası ve sahipliği | Düzeltildi (0.12.0); kalan: abonelik listesi/silme arayüzü yok |
| D-28 | Düşük | Yükleme ve zip açma boyut sınırları | Düzeltildi (0.12.0); kalan: gövde hâlâ belleğe okunuyor |
| D-29 | Bilgi | Testler gerçek atlatma yollarını yeterince kapsamıyordu | Düzeltildi (0.12.0): `sb security-test` kural katmanını da sınar |
| D-30 | Bilgi | İki sohbet yığını, üç onay sistemi, iki gizli-not ve iki hassasiyet kalıbı | Düzeltildi (0.13.0) |
| B-01 | Orta-düşük | `git diff`, ev klasörü bir depo değilken depo dışındaki dosyaları onaysız gösterebiliyordu (İş ortağı incelemesi, v0.12.0) | Düzeltildi (0.13.1) |

Sütundaki «kalan» ifadeleri yalnız bilinen sınırlardır; ayrıntı için ilgili sürümün `CHANGELOG.md` notuna bak.

## Ayrıntılı durum: D-07 (kasa uzak depo politikası)

**Ne risk:** Günlük görev kasanın değişikliklerini commit edip uzak depoya iter. Uzak depo hesabı ya da erişim jetonu ele geçirilirse kasadaki tüm notlar
ve geçmişi okunabilir. Ayrıca kasa deposu `_system` kodunu da içeriyorsa, uzaktan gelen kod değişikliği bir sonraki eşitlemede yerel çalışan koda karışabilir.

**Durum:** Bu bir güvenlik hatası değil, **kullanıcı politikası**. Kasanın nereye yedekleneceği kişiye bağlıdır, bu yüzden kitte varsayılan davranış değiştirilmedi.

**Bugün ne var:** Kasa bir git deposudur; uzak depo bağlıysa günlük görev oraya iter. Şifreli yedekler (D-10) uzak depodan bağımsızdır.
Gizli not işareti (`visibility: private`) ve `.md.enc` dosyaları kasa içinde ayrıca korunur ama git'e girmelerini engelleyen bir kural yoktur.

**Kullanıcı kararı gerekenler** (ikisi de sen uzak depo bağladıysan geçerli):
1. Uzak depoyu **gizli** tut, erişim jetonunu yalnız o depo ve en az yetkiyle ver, iki adımlı doğrulama aç.
2. Kod (`_system/`) ile kişisel notları aynı uzak depoda tutmamayı düşün; kitin kendi güncellemesi zaten `sb update` ile ayrı depodan gelir.
3. Çok hassas klasörleri (`_attachments/`, `60-Kişiler/`, gizli notlar) kasa `.gitignore` dosyasına eklemek senin seçimin.

**Kalan risk:** Uzak depo bağlıysa ve hesap ele geçirilirse tüm kasa içeriği riske girer. İstenirse ileride «uzak itme kapalı» ayarı ve itmeden önce gizli not engeli eklenebilir.

## Ayrıntılı durum: D-17 (Cloudflare tüneli)

**Ne risk:** Asistan ayrıca telefon için isteğe bağlı bir Cloudflare tüneli planı sunar (kendiliğinden başlamaz). Yerel arayüz ve internetten gelen telefon isteği
aynı işleyiciye yönlendirilirse, internetten gelen bir istek yanlışlıkla «yerel» sayılabilir. Bu durumda yerel-yalnız uçlar internete açılır.

**Durum:** Kullanıcı kararı bekliyor. Tünel hiçbir zaman kendiliğinden kurulmaz; planı elle uygulamadıkça risk yoktur.

**Bugün ne var:** Telefon yolu eşleme çerezi ister; yerel işleyici ayrı kimlik jetonu ister (D-04). Tünel için `access_policy` bayrağı yalnız senin elle yazdığın bir işarettir ve doğrulanmaz.

**Tünel kullanacaksan:**
1. Cloudflare Access'te e-posta politikasını kur ve **bayrağı ancak politikayı kurduktan sonra** `true` yap.
2. Tüneli yerel arayüz portuna değil, telefon yoluna yönlendir; «Host başlığını yerel yap» türü ayarlar ekleme.
3. Kullanmayacaksan hiçbir şey yapma; tünel kapalı kalır.

**Kalan risk:** Tünel + yanlış yapılandırma = yerel uçların dışarı açılması. Kalıcı çözüm (tüneli ayrı, her zaman uzak sayılan bir işleyiciye bağlamak) önerildi, uygulanmadı.

## Ayrıntılı durum: D-30 (mimari tutarsızlıklar), 0.13.0'da düzeltildi

**Ne risk:** İki ayrı sohbet yığını, üç ayrı onay deposu, birbirinden farklı iki gizli-not ve iki hassasiyet kalıbı vardı. Aynı eylem hangi yoldan geldiğine göre
farklı güvenlik davranışı gösterebiliyordu ve kullanıcı hangi onayın nerede beklediğini göremiyordu. Ürün dilinde WhatsApp için «taslak» denirken mesaj aslında gönderiliyordu.

**Düzeltme (0.13.0):**
- Tek sohbet yığını: klasik arayüz kaldırıldı; eski uçlar yeni yığına giden ince uyumluluk katmanı. Dış içerik (kirlilik) bayrağı sohbet kaydında kalıcı: sunucu yeniden başlasa da sürer.
- Tek onay deposu (`sb/approvals.py`): sohbet kartları, otomasyon ve tarih adayları aynı yerde; her kayıtta tür, kaynak, süre aşımı. Yeniden başlatmada kartlar kaybolmaz. Arayüzde **Görünümler → Onaylar**.
- Tek hassasiyet kaynağı (`sb/sensitive.py`): kasa süzgeci, bulut süzgeci, maskeleme ve gizli not denetimi aynı kalıpları kullanır.
- Araç adı `whatsapp_send`: kullanıcıya verilen söz davranışla uyuşuyor (onaylayınca mesaj gönderilir).
- Kasa şeması sürümlü hale geldi (`sb migrate`); ayar dosyalarının nerede durduğu rehberde tablolandı.

**Kalan risk:** Yok bilinen. Test: `tests/test_d30_architecture.py`.

## Ayrıntılı durum: B-01 (`git diff` depo dışı okuma), 0.13.1'de düzeltildi

İş ortağı incelemesinde (v0.12.0) bulundu. Komut sınıflandırıcısı `git diff` komutunu «salt okunur» sayıyordu; komut ev klasöründe (genelde git deposu değil) çalıştığı için
git, iki yol verildiğinde depo dışı dosyaları karşılaştırma kipine geçebiliyordu ve kasa dışı bir dosyanın içeriği onay kartı çıkmadan okunabiliyordu.
Etki orta-düşük: dış içerik varken her komut zaten onaya düşer (D-02).

**Düzeltme:** git komutlarında dosya yoluna benzeyen her bağımsız değişken kasa/Workspace kuralıyla denetlenir (kasanın `_system/config` klasörü hariç); `git diff` ikiden çok konumsal argüman alırsa
onay ister; git seçeneklerinin kısaltmaları da dahil, dosyaya yazan ya da harici program çalıştıran seçenekler onay ister. `git status`, `git log`, argümansız `git diff` serbest kalır.
Test: `tests/test_audit_2026_11_c.py`.
