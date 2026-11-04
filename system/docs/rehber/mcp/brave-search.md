# Brave Arama (MCP)

> Brave Search API ile web arama. NOT: eski paket arşivlendi; Brave'in güncel sunucusu için docs_url.

| | |
|---|---|
| MCP kimliği | `brave-search` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/brave/brave-search-mcp-server |
| Ne ister | hesap: [Brave Search](../mcp/brave-search.md); gizli değer: Brave Search API anahtarı (`brave_key`); program: Node.js |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Brave Search API ile web arama. NOT: eski paket arşivlendi; Brave'in güncel sunucusu için docs_url. Genel anlatım: [MCP](../06-mcp.md).

> **Dikkat:** açıklamada belirtildiği gibi bu paket arşivlenmiş olabilir. Güncel sürüm için resmi belge adresine bak; sihirbaz yine de kurmayı dener.

## Gerekenler

**Hesaplar:** [Brave Search](../mcp/brave-search.md)

**Bilgisayarda kurulu olması gereken programlar:** Node.js


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Brave Search API anahtarı (`brave_key`) | gizli değer (yalnız şifre kasasına yazılır) | evet | brave.com/search/api adresinden alınır. |

Gizli değerler (`brave_key`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **Brave Arama** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **Brave Search API anahtarı** alanını doldur (gizli değer (yalnız şifre kasasına yazılır), zorunlu). brave.com/search/api adresinden alınır.
3. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`npm view @modelcontextprotocol/server-brave-search version`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
4. Başarılıysa kartta `Brave Arama kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add brave-search --scope user -e BRAVE_API_KEY=<brave_key> -- npx -y @modelcontextprotocol/server-brave-search@0.6.2
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **Node.js** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| `gerekli alan eksik: brave_key` | **Brave Search API anahtarı** alanını doldur |
| `şifre kasası (keyring) yok` | İşletim sisteminin şifre kasası kullanılamıyor; Windows'ta Kimlik Bilgisi Yöneticisi'nin açık olduğundan emin ol |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
