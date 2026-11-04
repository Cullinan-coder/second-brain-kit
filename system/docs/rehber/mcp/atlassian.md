# Jira / Atlassian (MCP)

> Jira ve Confluence (Atlassian'ın uzak MCP sunucusu).

| | |
|---|---|
| MCP kimliği | `atlassian` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | uzak sunucu (elle bağlanır) |
| Resmi belge | https://www.atlassian.com/platform/remote-mcp-server |
| Ne ister | hesap: [Atlassian (Jira)](../mcp/atlassian.md) |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Jira ve Confluence (Atlassian'ın uzak MCP sunucusu). Genel anlatım: [MCP](../06-mcp.md).

## Gerekenler

**Hesaplar:** [Atlassian (Jira)](../mcp/atlassian.md)


## Sihirbazda kurulum (8. adım: MCP)

Bu MCP sihirbaz tarafından kurulmaz; kartında yalnız **Belge** bağlantısı görünür ve `Elle kurulum: belgeye bak.` yazar.
1. Resmi belgeyi aç: https://www.atlassian.com/platform/remote-mcp-server
2. Belgedeki bağlama adımlarını izle (menü adları sürüme göre değişebilir).
3. Claude Code'da `claude mcp list` ile bağlandığını doğrula.



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
