# CLAUDE.md — Second Brain kasası

Bu dosya kasanın kalıcı kurallarıdır. Claude Code bu klasörde açıldığında okur. Kendi tercihlerini ve kararlarını en alta ekle.

## İletişim
- Türkçe konuş, kısa ve net ol. Seçenek listesi yerine net öneri + tek sonraki adım.
- Geri alınamaz işlemden önce (silme, toplu değişiklik, dışarıya gönderme) onay al.

## Konumlar
- Kasa: bu klasör (git ile sürümlü; yedek için ÖZEL GitHub reposu).
- Yerel veri (git'e ve telefona girmez): `~/.secondbrain/` → `mail.db`, kayıtlar, `secrets/`.
- Gizli bilgiler: işletim sisteminin şifre kasası (keyring, servis `second-brain`). Repoda token/şifre YOK.
- Kod: `_system/` (`uv run --directory _system python -m sb <komut>`; `sb doctor` kurulumu kontrol eder).

## Klasörler
| Klasör | Anlamı |
|---|---|
| `00-Inbox` | İşlenmemiş: `onay-bekleyenler.md` (emin olunamayan tarihler), `Dump/` (hızlı notlar), `_imports/` (zip'ler, git dışı) |
| `10-Dersler` | Her ders bir klasör + içinde `teslim` notları |
| `20-Projeler` | Projeler (otomatik derlenen "proje dosyası" + elle notlar) |
| `30-Kariyer` | `Başvurular/`, `Görüşmeler/`, LinkedIn profili |
| `40-Kaynaklar` | `Konular/`, `Teknolojiler/`, `Mail/`, `Drive/`, `Bilgisayar/`, `Notlar/` |
| `50-Günlük` | Günlük notlar + sabah özetleri |
| `60-Kişiler` | Kişi başına bir not |
| `90-Arşiv` | Biten/iptal (silme yok, buraya taşı) |
| `_templates`, `_attachments`, `_system` | Şablonlar, ekler, kod |

## Frontmatter şeması
Ortak alanlar: `type, status, tags, source, source_id, created, updated, due` (tarih `YYYY-MM-DD`, saat ayrı `due_time: "HH:MM"`).
Tekilleştirme anahtarı `source + source_id`; aynı anahtarla ikinci not açılmaz. Status değerleri ASCII küçük harf.

| type | status |
|---|---|
| `ders` | aktif, tamamlandi, tekrar |
| `teslim` | acik, tamamlandi, iptal |
| `proje` | fikir, aktif, beklemede, tamamlandi, arsiv |
| `kisi` | aktif, pasif |
| `basvuru` | planlandi, hazirlaniyor, gonderildi, sonuc-bekleniyor, kabul, red, vazgecildi |
| `gorusme` | planlandi, yapildi, iptal |
| `gunluk` | acik · `akademik`/`kaynak`: aktif, arsiv |

Otomatik bölümler `<!-- sb:auto:<ad>:start/end -->` arasındadır; araçlar yalnız bu aralığı yeniden yazar.

## Takvim kuralları (ana Google takvimi)
| Başlık | Renk | Hatırlatma |
|---|---|---|
| `[SINAV]`, `[SUNUM]` | 11 kırmızı | 7g, 3g, 1g (+2s) |
| `[ÖDEV] … (23:59)` | 6 turuncu | 3g, 1g, 3s; 23:59'da 1 dk |
| `[BAŞVURU]` | 3 mor | 14g, 7g, 2g |
| `[GÖRÜŞME]` | 10 yeşil | 1g, 2s, 30dk |
| `[YOLCULUK]` | 9 koyu mavi | 1g, 3s |
| `[RANDEVU]` | 4 pembe | 1g, 2s |
| `[HATIRLATMA]` | 5 sarı | istenen dakikalar |
| `[AKADEMİK]`, `[TATİL]` | 8 gri | yok, tüm gün |
Eklemeden önce aynı başlık + tarih var mı bak. Emin olunmayan tarih → `00-Inbox/onay-bekleyenler.md`.

## Güvenlik
- Mail salt okunur; gönderme/silme/cevaplama/etiketleme kodu yazma.
- Kasaya şifre, kart, kimlik numarası, IBAN, OTP yazma.

## Süreklilik
- Anlamlı bir iş bitince `Son oturum.md` en üstüne kart: `## YYYY-AA-GG SS:DD · <proje> · <oturum-id>` + Ne yapıldı / Kararlar / Nerede kaldık / Sıradaki.
- Yarım kalanlar `Açık konular.md` "## Aktif" altında; bitince "## Kapanan"a.
- Öğretilen kural → `Asistan kuralları.md`; kalıcı kişisel bilgi → `Asistan hafızası.md` (yerel asistanla ortak).

## Kendi notların
<!-- Buraya kendi tercihlerini, kararlarını, sistem hakkındaki notlarını ekle. -->
