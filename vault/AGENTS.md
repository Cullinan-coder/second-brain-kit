# AGENTS.md — bu klasör bir "ikinci beyin" (Obsidian kasası)

Her yapay zeka ajanı (Claude Code, Codex, Gemini/Antigravity, OpenCode...) bu dosyayı okur. Ayrıntılı kurallar `CLAUDE.md`'de;
ajan hangisi olursa olsun önce onu, sonra `Asistan kuralları.md`, `Asistan hafızası.md`, `Son oturum.md` (en üstteki kartlar)
ve `Açık konular.md` (## Aktif) dosyalarını oku.

## Ne var
- Notlar düz Markdown + YAML frontmatter (şema `_system/tools/lint.py`). Klasörler: 00-Inbox, 10-Dersler, 20-Projeler, 25-Görevler,
  30-Kariyer, 40-Kaynaklar (Kavramlar, Bağlantılar, Videolar, Web, Belgeler, Sohbet geçmişi), 50-Günlük (+ Makbuzlar), 60-Kişiler, 90-Arşiv.
- `sb:auto` işaretli bölümler araçlarla üretilir; elle düzenleme (bir sonraki çalışmada ezilir).
- Komut satırı: `sb <komut>` (ya da `uv run --directory _system python -m sb <komut>`); `sb --help`.

## Hafıza protokolü (her ajan)
- Anlamlı iş bitince: `sb receipt --summary "..." --ref <kasa-yolu> --learned "..." --project <p>` + `Son oturum.md` en üstüne kart.
- Kalıcı öğrenim: `sb concept`; olgunlaşmamış: `sb learn`; gerçek ilişki: `sb connect`; dosyasız anlamlı sohbet: `sb trace`.
- "Son günlerde ne yaptık": `sb recap --days 7`. Bilmediğini uydurma; kaynağı ve tarihi söyle.
- Kullanıcı düzeltirse: `sb rule "..."` (tek projeye aitse `--scope <proje>`). Aynı hata ikinci kez: `sb error-log`.

## Sınırlar
- Mail salt okunur: gönderme, silme, cevaplama yok. Takvim, mesaj ve dışarıya giden her şey kullanıcı onayıyla.
- Şifre, kart, TC kimlik, IBAN kasaya yazılmaz. `visibility: private` notlar otomatik okunmaz.
- Kullanıcı notlarını silme ya da toplu yeniden yazma; arşive taşı. `git reset --hard`/`checkout --`/`stash` ile başkasının işine dokunma.
- Kod işleri kasada değil, projenin kendi klasöründe yapılır; kasaya yalnız o projenin notları ve kararları yazılır.
