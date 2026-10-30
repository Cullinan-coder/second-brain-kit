# LinkedIn arşivi

1. LinkedIn → **Settings → Data privacy → Get a copy of your data** → *Download larger data archive* (ya da hızlı arşiv) → iste.
2. Mail ile gelen zip'i kasada `00-Inbox/_imports/` klasörüne koy (bu klasör git'e girmez).
3. `uv run --directory <kasa>/_system python -X utf8 -m sb linkedin-import` (önce `--dry-run` ile bak).

Kasaya giren: `30-Kariyer/LinkedIn profili.md` (profil, deneyim, eğitim, beceriler, yayınlar → ilgili proje notu bağlantısı,
takip edilen şirketler, iş tercihleri), bağlantıların (rehberde varsa kişi notuna "LinkedIn" bölümü, yoksa yeni kişi notu),
mesajlar (yalnız yerel arşivde, aranabilir).
**Alınmayan:** doğum tarihi, adres, telefon, reklam hedefleme, faturalar, kimlik doğrulama, kayıt IP'si.
Yayın başlığı → proje eşlemesi `sb/linkedin.py` içindeki `PROJECT_HINTS`'te.
