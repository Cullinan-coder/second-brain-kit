# Web getir (Fetch) (MCP)

> Web sayfalarını çekip modele okunur metin olarak verir.

| | |
|---|---|
| MCP kimliği | `fetch` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/modelcontextprotocol/servers/tree/main/src/fetch |
| Ne ister | program: uv |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Web sayfalarını çekip modele okunur metin olarak verir. Genel anlatım: [MCP](../06-mcp.md).

## Gerekenler

**Bilgisayarda kurulu olması gereken programlar:** uv


## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **Web getir (Fetch)** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`uvx mcp-server-fetch --help`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
3. Başarılıysa kartta `Web getir (Fetch) kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add fetch --scope user -- uvx mcp-server-fetch
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **uv** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
