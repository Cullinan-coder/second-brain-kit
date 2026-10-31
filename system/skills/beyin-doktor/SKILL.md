---
name: beyin-doktor
description: Second Brain'in gerçekten çalışıp çalışmadığını denetle — kurulum, kancalar, zamanlanmış görevler, yerel model, hafıza hijyeni, yarım güncelleme. "beyin çalışıyor mu", "hafıza bozuk", "kanca çalışmıyor", "doktor", "sağlık kontrolü", "hijyen" dendiğinde kullan.
---

# Beyin doktoru

1. `sb doctor` — her ✗/! satırı ne yapılacağını söyler. Exit 0 "her şey doğrulandı" demek değildir.
2. `sb hygiene` — tekrar başlıklı notlar, kopuk [[bağlantı]], bayat aktif notlar, büyüyen hafıza dosyaları, bekleyen kutu notları.
   Tekrar kişi notlarını birleştirmeden önce kullanıcıya sor; hiçbir notu silme (arşive taşı: asistan "arşivle" ya da 90-Arşiv).
3. Şema: `uv run --directory <kasa>/_system python tools/lint.py` (frontmatter, tekrar source_id, hassas veri).
4. Kancalar: `~/.claude/settings.json` içinde SessionStart / UserPromptSubmit / PreCompact / SessionEnd → `cc_hook.py`.
   Durum dosyaları `~/.secondbrain/hooks/` (active.*, count.*, needs_card.*, flush.*.log). Yerel özet hatası `flush.*.log`'da.
   Gerçek kanıt: yeni bir oturumda bağlamın (kurallar, son oturum kartı) geldiğini görmek.
5. Günlük/haftalık çalışma: `~/.secondbrain/logs/` ve Görev Zamanlayıcı (SecondBrain-Daily/Weekly/Chat) ya da macOS launchd.
6. Yarım güncelleme (`~/.secondbrain/update.pending` var): `sb update --recover`; sorun sürerse `sb update --rollback`.
7. Asistan sunucusu düştüyse: Windows `powershell -File <kasa>/_system/tools/restart_chat.ps1`, macOS `python3 tools/schedule_macos.py --restart-chat`.

Sağlık göstergesini yeşile çevirmek için veritabanı, not ya da log silme. Arızayı ve en küçük düzeltmeyi açıkla; özel notları sohbete dökme.
