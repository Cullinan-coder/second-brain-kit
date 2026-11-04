# Sentry (MCP)

> Hata kayıtları ve sorunlar (Sentry'nin uzak MCP sunucusu).

| | |
|---|---|
| MCP kimliği | `sentry` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | uzak sunucu (elle bağlanır) |
| Resmi belge | https://docs.sentry.io/product/sentry-mcp/ |
| Ne ister | hesap: [Sentry](../mcp/sentry.md) |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Hata kayıtları ve sorunlar (Sentry'nin uzak MCP sunucusu). Genel anlatım: [MCP](../06-mcp.md).

## Gerekenler

**Hesaplar:** [Sentry](../mcp/sentry.md)


## Sihirbazda kurulum (8. adım: MCP)

Bu MCP sihirbaz tarafından kurulmaz; kartında yalnız **Belge** bağlantısı görünür ve `Elle kurulum: belgeye bak.` yazar.
1. Resmi belgeyi aç: https://docs.sentry.io/product/sentry-mcp/
2. Belgedeki bağlama adımlarını izle (menü adları sürüme göre değişebilir).
3. Claude Code'da `claude mcp list` ile bağlandığını doğrula.



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
