<!-- second-brain-kit -->
## Second brain (kişisel bilgi sistemi)
{{NAME}}'in bilgileri `{{VAULT}}` Obsidian kasasında ve yerel arşivde (`~/.secondbrain`). `second-brain` MCP sunucusu bağlı.

- **Yeni bir işe başlarken önce beyne bak:** proje → `brain_project("ad")`, ders → `brain_course("kod")`, genel → `brain_overview()`.
- Belge/mail/SMS/Drive araması: `brain_search("sorgu")`. Yaklaşan tarihler: `brain_today()`.
- Oturum başında kanca kuralları, hafızayı, açık konuları ve son oturum kartlarını ekler. Anlamlı bir iş bitince kasadaki
  `Son oturum.md` en üstüne kart yaz (`## YYYY-AA-GG SS:DD · <proje> · <oturum-id>`: Ne yapıldı / Kararlar / Nerede kaldık / Sıradaki),
  yarım kalanları `Açık konular.md` "## Aktif" altında güncelle. Öğretilen kural → `Asistan kuralları.md`, kalıcı kişisel bilgi → `Asistan hafızası.md`.
- Kasaya yazarken kasadaki `CLAUDE.md` kurallarına uy (frontmatter şeması, takvim kuralları, mail salt okunur).
