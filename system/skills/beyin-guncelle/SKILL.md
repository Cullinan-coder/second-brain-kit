---
name: beyin-guncelle
description: Second Brain'i güncelle ya da güncellemeyi geri al. "beynimi güncelle", "yeni sürüm var mı", "güncellemeyi geri al", "sürüm" dendiğinde kullan.
---

# Beyin güncelleme

- Sürüm: `sb version`. Yeni sürüm var mı: `sb update --check`.
- Güncelle: `sb update` — önce kodu `~/.secondbrain/backups/` altına yedekler, kit klasöründe `git pull`, sonra yalnız kodu yeniler.
  Notlar, `config/*.yaml` ayarları ve şifreler değişmez. Ne değiştiğini CHANGELOG'dan gösterir.
- Yarım kaldıysa: `sb update --recover`. Geri dön: `sb update --rollback` (son yedek; kişisel ayarlar korunur).
- Güncellemeden sonra asistanı yeniden başlat (ya da bilgisayarı yeniden başlat) ve `sb doctor` çalıştır.
- Kaynak kasa (kiti üreten bilgisayar) için `sb update` çalışmaz: kodu düzenle, testleri geç, `_system/VERSION` ve
  `_system/kit/CHANGELOG.md`'yi güncelle, `uv run python -X utf8 tools/build_kit.py` (kişisel veri taraması) → kit reposunda commit + etiket + push.
  GitHub Actions Windows ve macOS'ta sıfırdan kurulumu dener; kırmızıysa düzelt.

Kendi `git pull`/kopyalama zincirinle kurulu bir kasayı güncelleme; resmi yolu kullan.
