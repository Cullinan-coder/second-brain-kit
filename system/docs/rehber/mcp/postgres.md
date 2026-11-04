# PostgreSQL (MCP)

> PostgreSQL veritabanını salt okunur sorgular. NOT: paket arşivlendi.

| | |
|---|---|
| MCP kimliği | `postgres` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/modelcontextprotocol/servers-archived/tree/main/src/postgres |
| Ne ister | gizli değer: Bağlantı adresi (postgresql://…) (`postgres_url`); program: Node.js |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: PostgreSQL veritabanını salt okunur sorgular. NOT: paket arşivlendi. Genel anlatım: [MCP](../06-mcp.md).

> **Dikkat:** açıklamada belirtildiği gibi bu paket arşivlenmiş olabilir. Güncel sürüm için resmi belge adresine bak; sihirbaz yine de kurmayı dener.

## Gerekenler

**Bilgisayarda kurulu olması gereken programlar:** Node.js


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Bağlantı adresi (postgresql://…) (`postgres_url`) | gizli değer (yalnız şifre kasasına yazılır) | evet | Parola içerir; yalnız şifre kasasında tutulur. |

Gizli değerler (`postgres_url`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **PostgreSQL** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **Bağlantı adresi (postgresql://…)** alanını doldur (gizli değer (yalnız şifre kasasına yazılır), zorunlu). Parola içerir; yalnız şifre kasasında tutulur.
3. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`npm view @modelcontextprotocol/server-postgres version`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
4. Başarılıysa kartta `PostgreSQL kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add postgres --scope user -- npx -y @modelcontextprotocol/server-postgres {postgres_url}
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **Node.js** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| `gerekli alan eksik: postgres_url` | **Bağlantı adresi (postgresql://…)** alanını doldur |
| `şifre kasası (keyring) yok` | İşletim sisteminin şifre kasası kullanılamıyor; Windows'ta Kimlik Bilgisi Yöneticisi'nin açık olduğundan emin ol |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
