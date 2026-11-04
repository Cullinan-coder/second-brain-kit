# Sıralı düşünme (MCP)

> Karmaşık sorunları adım adım düşünmeye yarayan araç.

| | |
|---|---|
| MCP kimliği | `sequential-thinking` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking |
| Ne ister | program: Node.js |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Karmaşık sorunları adım adım düşünmeye yarayan araç. Genel anlatım: [MCP](../06-mcp.md).

## Gerekenler

**Bilgisayarda kurulu olması gereken programlar:** Node.js


## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **Sıralı düşünme** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`npm view @modelcontextprotocol/server-sequential-thinking version`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
3. Başarılıysa kartta `Sıralı düşünme kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add sequential-thinking --scope user -- npx -y @modelcontextprotocol/server-sequential-thinking
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **Node.js** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
