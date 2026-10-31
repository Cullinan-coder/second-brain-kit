<!-- second-brain-kit -->
## Second brain (kişisel bilgi sistemi)
{{NAME}}'in bilgileri `{{VAULT}}` Obsidian kasasında ve yerel arşivde (`~/.secondbrain`). `second-brain` MCP sunucusu bağlı.

- **Yeni bir işe başlarken önce beyne bak:** proje → `brain_project("ad")`, ders → `brain_course("kod")`, genel → `brain_overview()`.
- Belge/mail/SMS/Drive araması: `brain_search("sorgu")`. Yaklaşan tarihler: `brain_today()`.
- Oturum başında kanca kuralları, hafızayı, açık konuları ve son oturum kartlarını ekler. Anlamlı bir iş bitince kasadaki
  `Son oturum.md` en üstüne kart yaz (`## YYYY-AA-GG SS:DD · <proje> · <oturum-id>`: Ne yapıldı / Kararlar / Nerede kaldık / Sıradaki),
  yarım kalanları `Açık konular.md` "## Aktif" altında güncelle. Öğretilen kural → `Asistan kuralları.md`, kalıcı kişisel bilgi → `Asistan hafızası.md`.
- Kasaya yazarken kasadaki `CLAUDE.md` kurallarına uy (frontmatter şeması, takvim kuralları, mail salt okunur).
- **Hafıza komutları (`beyin` skill'i):** iş bitince `sb receipt` (makbuz), kalıcı öğrenim `sb concept`, olgunlaşmamış `sb learn`,
  "son günlerde ne yaptık" `sb recap`/`brain_recap`, görev `sb task`, kişi bilgisi `sb person` (beyan/çıkarım ayrı),
  tekrarlayan hata `sb error-log`. Bir işi ikinci kez yapıyorsan skill'e çevir (`~/.claude/skills/`).

## Orkestrasyon (büyük işlerde; ayrıntı `orkestrasyon` skill'i)
- Ana oturum şeftir: plan, karar, sentez. Tarama/inceleme alt ajanlarda; yukarıya kısa rapor. Görev tarifi gevşek, amaç odaklı.
- Büyük metin/log/belge yığınını önce yerel Qwen'e ver (`local_work` MCP aracı ya da `sb qwen`; ücretsiz).
- Aynı dosyaya iki ajan dokunmaz; çakışabilecek işlerde worktree. Anlamlı ilerlemede commit; başkasının işine `git reset/checkout/stash` yok.
- Kritik işte çapraz doğrulama: biri yazar/bulur, bağımsız ikinci ajan doğrular. Her iş paralel değildir.
