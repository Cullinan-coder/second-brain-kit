# Google Drive (MCP)

> Drive dosyalarını arar ve okur. NOT: paket arşivlendi; OAuth kurulumu gerekir (docs_url).

| | |
|---|---|
| MCP kimliği | `gdrive` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/modelcontextprotocol/servers-archived/tree/main/src/gdrive |
| Ne ister | hesap: [Google](../03-hesaplar.md#hesap-google); alan: Kaydedilmiş OAuth kimlik dosyası yolu (`gdrive_credentials`); program: Node.js |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Drive dosyalarını arar ve okur. NOT: paket arşivlendi; OAuth kurulumu gerekir (docs_url). Genel anlatım: [MCP](../06-mcp.md).

> **Dikkat:** açıklamada belirtildiği gibi bu paket arşivlenmiş olabilir. Güncel sürüm için resmi belge adresine bak; sihirbaz yine de kurmayı dener.

## Gerekenler

**Hesaplar:** [Google](../03-hesaplar.md#hesap-google)

**Bilgisayarda kurulu olması gereken programlar:** Node.js


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Kaydedilmiş OAuth kimlik dosyası yolu (`gdrive_credentials`) | dosya ya da klasör yolu | evet | docs_url'deki adımlarla üretilir. |

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **Google Drive** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **Kaydedilmiş OAuth kimlik dosyası yolu** alanını doldur (dosya ya da klasör yolu, zorunlu). docs_url'deki adımlarla üretilir.
3. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`npm view @modelcontextprotocol/server-gdrive version`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
4. Başarılıysa kartta `Google Drive kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add gdrive --scope user -e GDRIVE_CREDENTIALS_PATH=<gdrive_credentials> -- npx -y @modelcontextprotocol/server-gdrive
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **Node.js** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| `gerekli alan eksik: gdrive_credentials` | **Kaydedilmiş OAuth kimlik dosyası yolu** alanını doldur |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
