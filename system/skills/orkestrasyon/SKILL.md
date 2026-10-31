---
name: orkestrasyon
description: Büyük, çok parçalı işlerde ajan ekibi yönetimi — alt ajanlara dağıtma, sahiplik/worktree, yerel Qwen'e ucuz iş verme, çapraz doğrulama, gece koşusu, Codex'i alt ajan olarak kullanma. Çok dosyalı/çok yönlü işler, "ekip kur", "paralel çalış", "gece çalışsın", "alt ajan", "codex'e ver" dendiğinde kullan.
---

# Orkestrasyon (şef + alt ajanlar)

Ana oturum **şeftir**: plan, mimari, karar, sentez, birleştirme. İşçilik alt ajanlarda; yukarıya yalnız kısa rapor gelir
(şefin bağlamı dolmaz, daha uzun ve tutarlı çalışır). Her iş paralel değildir: sıralı bağımlılık varsa tek ajanla, commit commit git.

## Dağıtım
- Bağlam toplama / tarama / inceleme → alt ajan (Explore ya da genel amaçlı). Görev tarifi **gevşek** ve amaç odaklı olsun;
  fazla ayrıntı zeki modeli kısıtlar. Amacı, çekinceleri ve "şu olursa sorun" listesini yaz.
- Net şartnameli uygulama (migration, refactor, test yazma) → ayrıntılı şartname ver; Codex kuruluysa `codex exec` (aşağıda).
- Büyük metin/log/mail yığını (çok token, düşük zekâ ihtiyacı) → **yerel Qwen** (ücretsiz): MCP `local_work` aracı ya da
  `sb qwen "talimat" --file <yol> [--file ...]`. Qwen'in çıktısı özet/çıkarımdır; kritik sonucu kaynaktan doğrula.
- Karar, sentez, çakışma çözümü ve son kontrol → şefin kendisi.

## Sınırlar (iş kaybolmasın, birbirini bozmasın)
- **Sahiplik**: aynı dosyaya iki ajan dokunmaz. Ortak dosyalar tek sahipli; brief'te "şunlara dokunma" yaz.
- Büyük/çakışabilir işlerde her ajan ayrı **git worktree**'de (Agent aracında `isolation: worktree`); bitince şef birleştirir.
- Alt ajanlar anlamlı ilerlemede **commit** atar; `git reset --hard`, `checkout --`, `stash` ile başkasının (ya da başka oturumun)
  işine dokunmaz. Paralel oturum uyarısı geldiyse önce `git status`.
- Ortak **rapor dosyası**: her ajan kendi bölümüne bulgu yazar (ör. `rapor/<ajan>.md`), şef derler. Aynı alanı iki kez taramazlar.

## Kalite
- Kritik işte **çapraz doğrulama**: bir ajan bulur/yazar, ikinci bağımsız ajan doğrular (kendi kodundaki hatayı farklı bakışla bulur).
  Hata bulunursa önce onu yakalayan test, sonra düzeltme.
- Sahte test olmasın: test gerçekten hatayı yakalıyor mu, düzeltmeyi geri alınca kırmızı oluyor mu?
- Tekrarlayan sorun → `sb error-log "hata" --fix "çözüm"` (ikinci tekrarda kural olur) ya da skill/CLAUDE.md kuralı.

## Gece koşusu (uzun, gözetimsiz iş)
- Plan + kurallar baştan net olmalı. Kullanıcı `00-Inbox/Gece işleri.md`'ye `- [ ] ` satırları yazar (çalışma klasörü: `@<yol>`).
- `sb night --plan` ne çalışacağını gösterir; gece görevi (`sb night --run`) her maddeyi `claude -p` ile sırayla çalıştırır,
  sonucu nota ve makbuza yazar, kesintide kaldığı maddeden devam eder. Yalnız kullanıcının yazdığı maddeler çalışır.

## Codex'i alt ajan yapmak (kuruluysa)
- Kurulum (kullanıcı onayıyla): `npm i -g @openai/codex` sonra `codex login` (abonelikle; API anahtarı gerekmez).
- Kullanım: `codex exec --skip-git-repo-check -C <klasör> "ayrıntılı şartname"`; paralel işler için ayrı worktree'ler.
  Codex ayrıntılı şartnamede iyidir, yaratıcı karar vermez. Sonucu şef inceler.
- `sb doctor` Codex'in kurulu/girişli olup olmadığını gösterir.

## Limit
Limitin azsa agresif paralelliği azalt; ucuz işi Qwen'e ya da daha ucuz modele ver. Durum çubuğunda 5 saatlik / 7 günlük kullanım görünür.
