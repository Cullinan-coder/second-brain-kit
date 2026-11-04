# Notion (MCP)

> Notion sayfa ve veritabanlarını okuyup yazar (Notion'un resmi MCP sunucusu).

| | |
|---|---|
| MCP kimliği | `notion` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/makenotion/notion-mcp-server |
| Ne ister | hesap: [Notion](../mcp/notion.md); gizli değer: Notion entegrasyon belirteci (`notion_token`); program: Node.js |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Notion sayfa ve veritabanlarını okuyup yazar (Notion'un resmi MCP sunucusu). Genel anlatım: [MCP](../06-mcp.md).

## Gerekenler

**Hesaplar:** [Notion](../mcp/notion.md)

**Bilgisayarda kurulu olması gereken programlar:** Node.js


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Notion entegrasyon belirteci (`notion_token`) | gizli değer (yalnız şifre kasasına yazılır) | evet | notion.so/profile/integrations'da iç entegrasyon oluştur ve sayfaları ona paylaş. |

Gizli değerler (`notion_token`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **Notion** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **Notion entegrasyon belirteci** alanını doldur (gizli değer (yalnız şifre kasasına yazılır), zorunlu). notion.so/profile/integrations'da iç entegrasyon oluştur ve sayfaları ona paylaş.
3. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`npm view @notionhq/notion-mcp-server version`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
4. Başarılıysa kartta `Notion kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add notion --scope user -e NOTION_TOKEN=<notion_token> -- npx -y @notionhq/notion-mcp-server
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **Node.js** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| `gerekli alan eksik: notion_token` | **Notion entegrasyon belirteci** alanını doldur |
| `şifre kasası (keyring) yok` | İşletim sisteminin şifre kasası kullanılamıyor; Windows'ta Kimlik Bilgisi Yöneticisi'nin açık olduğundan emin ol |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
