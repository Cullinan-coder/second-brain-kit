# Second Brain (kendi MCP'miz) (MCP)

> Kasada ve arşivde arama, proje/ders/kişi dosyaları, bugün ve özet araçlarını Claude Code/Desktop'a verir.

| | |
|---|---|
| MCP kimliği | `second-brain` |
| Varsayılan | açık |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | docs/mcp-second-brain.md |
| Ne ister | ek hesap, anahtar ya da program gerekmez |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Kasada ve arşivde arama, proje/ders/kişi dosyaları, bugün ve özet araçlarını Claude Code/Desktop'a verir. Genel anlatım: [MCP](../06-mcp.md).

## Gerekenler

Bu kayıt için ek hesap, anahtar ya da program gerekmez.

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **Second Brain (kendi MCP'miz)** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`claude mcp add --scope user second-brain -- <python> -m sb.mcp_server`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
3. Başarılıysa kartta `Second Brain (kendi MCP'miz) kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add second-brain --scope user -- python -m sb.mcp_server
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
