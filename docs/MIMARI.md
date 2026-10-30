# Mimari

Üç katman: **ham veri** (`~/.secondbrain`, git dışı) → **kasa** (Obsidian, git'te) → **asistanlar** (Claude Code + yerel Qwen).
Kod `_system/sb/` paketinde; her şey `sb <komut>` ile çalışır (`uv run --directory _system python -m sb ...`).

## Veri akışı (`sb daily`, her gün 13:00 + oturum açılınca; `sb/runner.py`)

| Adım | Modül | Ne yapar |
|---|---|---|
| mail <hesap> | `gmail.py`, `imap.py`, `maildb.py` | Gmail API (readonly) / IMAP EXAMINE → `mail.db` (SQLite + FTS5). Artımlı: son görülen kimlikten |
| sms/arama | `sms.py` | Telefondaki *SMS Backup & Restore* XML'i Drive'dan → `mail.db` (account=sms), `calls` |
| mail kategori | `categorize` (`config/mail_rules.yaml`) | Kurallarla kategori (okul, kariyer, finans…); ilk eşleşen kazanır |
| tarih çıkarma | `extract.py` + `llm.py` | Son 14 gün maillerinden tarih/teslim/başvuru/randevu (yerel model, JSON şema). Güven <0.8 → `00-Inbox/onay-bekleyenler.md` |
| onayladıkların → takvim | `approve` | Onay listesinde `[x]` işaretlenenleri kurallarla takvime ekler (`gcal_api.py`: renk, hatırlatma, tekilleştirme) |
| takvim → kasa | `gcal.py` | Ders programı, teslim/sınav, başvuru/görüşme, akademik takvim notları |
| arşivleme | `vault_ops.housekeep` | Süresi geçen/biten teslim·görüşme·başvuru → `90-Arşiv`; eski oturum kartları → aylık arşiv |
| not kutusu | `inbox.py` | `00-Inbox/Dump` notlarını yerel modelle ilgili nota ekler ya da bilgi notu açar |
| rehber | `contacts.py` | Google People → `60-Kişiler` (+ son mail/SMS/arama) |
| drive / drive notları | `drive.py` | Drive (paylaşılanlar dahil, 8 paralel) → indeks + `40-Kaynaklar/Drive` |
| bilgisayar dosyaları / belge içerikleri | `local_files.py`, `content.py` | `config/local_files.yaml` kökleri → klasör indeks notları; PDF/DOCX/PPTX/XLSX/kod metni → FTS |
| projeler / proje derleme | `projects.py`, `deep.py` | `workspace` klasörü + GitHub → `20-Projeler`; değişen projeler Claude ile "proje dosyası"na derlenir (yerel yedek) |
| ders dosyaları / ders derleme | `course_files.py`, `course_deep.py` | Ders ↔ dosya eşlemesi, LMS bildirimleri; ders dosyası derlemesi |
| oturum günlükleri | `sessions.py` | Claude Code oturum kayıtları → yerel modelle özet → ilgili proje notuna |
| obs / bağlantılar / mail notları | `obs.py`, `links.py`, `mail_index.py` | ÖBS not dökümü, Konular/Teknolojiler bağlantı notları, mail kategori indeksleri |
| özet | `digest.py`, `mailer.py` | Sabah özeti → kasa + mail (yalnız `notify.to` listesine); git commit + push |

`sb weekly`: denetim (lint, bozuk bağlantılar, büyüyen notlar) + haftalık özet.

## Kasa kuralları
- Her not frontmatter'lı (`type, status, tags, source, source_id, created, updated, due`); şema `tools/lint.py`'de.
- Tekilleştirme anahtarı `source + source_id` (`notes.Vault.upsert`): aynı kaynaktan ikinci not açılmaz, güncellenir.
- Otomatik bölümler `<!-- sb:auto:<ad>:start/end -->` arasında; dışındaki elle yazılanlara dokunulmaz.
- Kasaya yazan tek kapı `vault_ops.py`: izinli klasörler, şemaya uygun durum, her değişiklik ayrı git commit'i + `asistan_log.jsonl`.

## Asistanlar
**Claude Code** — `sb/mcp_server.py` (FastMCP, salt-okunur): `brain_overview/project/course/person/note/search/today`.
`tools/cc_hook.py` kancaları: SessionStart'ta kurallar + hafıza + açık konular + son oturum kartları + cwd projesi; 15 mesajda
kart hatırlatması; kartsız kapanışta sonraki oturuma uyarı. `sb` kendi `claude -p` çağrılarında kancayı susturur (`SB_NO_HOOK`).

**Yerel asistan** — `sb/chat.py` (HTTP sunucusu, Obsidian'a iframe ile gömülü; `Asistan.md`):
1. *Niyet tanıma (kod)*: `action_hint` regex'leri eylem isteklerini tanır; müzik/ekran/sistem/durum bildirimi gibi işleri **kod**
   çalıştırır (küçük modeller aracı çağırmadan uydurabiliyor).
2. *Otomatik getirme*: proje/ders/kişi adı + FTS araması + niyete göre (son mailler, genel bakış, yaklaşan tarihler) bağlam.
3. *Araç döngüsü* (Ollama tool-calling, en fazla 6 adım): `brain_*`, takvim, kasa düzenleme, bilgisayar eylemleri.
4. *Onay kartları*: takvim, WhatsApp, izinli liste dışı komut, takvimden silme; telefondan/ekran okunduktan sonra her eylem.
- `actions.py` + `platform_mac.py`: uygulama, medya, YouTube/Spotify, sistem bilgisi, komut sınıflandırma, OCR, kamera, bildirim.
- `spotify_api.py` (PKCE), `RemoteAuth` (telefon eşlemesi), `reminder_loop` (15 dk kala bildirim), `remote_loop` (Tailscale dinleyicisi).

**Model katmanı** — `sb/llm.py` + `config/llm.yaml`: iş başına sağlayıcı (oturum özeti, tarih çıkarma, not kutusu → yerel;
proje/ders derleme, konu haritası → Claude). Claude kota/hata verirse yerel yedeğe düşer; yerel çıktı **her zaman etiketlenir**.

## Yerel veri (`~/.secondbrain`, git ve telefon dışı)
`mail.db` (mesajlar, aramalar, Drive ve dosya indeksleri, belge metinleri, oturum özetleri, tarih çıkarımları), `secrets/client_secret.json`,
`asistan_log.jsonl`, `notified.json`, `remote_tokens.json` (yalnız SHA-256), `hooks/` (oturum sayaçları), `logs/`, `imports/`.
Şifre ve token'lar: işletim sisteminin şifre kasası, servis adı `second-brain`.
