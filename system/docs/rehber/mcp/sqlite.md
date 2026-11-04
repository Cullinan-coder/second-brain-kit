# SQLite (MCP)

> Bir SQLite dosyasını sorgular. NOT: paket arşivlendi.

| | |
|---|---|
| MCP kimliği | `sqlite` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite |
| Ne ister | alan: SQLite dosya yolu (`sqlite_path`); program: uv |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Bir SQLite dosyasını sorgular. NOT: paket arşivlendi. Genel anlatım: [MCP](../06-mcp.md).

> **Dikkat:** açıklamada belirtildiği gibi bu paket arşivlenmiş olabilir. Güncel sürüm için resmi belge adresine bak; sihirbaz yine de kurmayı dener.

## Gerekenler

**Bilgisayarda kurulu olması gereken programlar:** uv


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| SQLite dosya yolu (`sqlite_path`) | dosya ya da klasör yolu | evet | — |

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **SQLite** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **SQLite dosya yolu** alanını doldur (dosya ya da klasör yolu, zorunlu). 
3. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`uvx mcp-server-sqlite --help`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
4. Başarılıysa kartta `SQLite kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add sqlite --scope user -- uvx mcp-server-sqlite==2025.4.25 --db-path {sqlite_path}
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **uv** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| `gerekli alan eksik: sqlite_path` | **SQLite dosya yolu** alanını doldur |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
