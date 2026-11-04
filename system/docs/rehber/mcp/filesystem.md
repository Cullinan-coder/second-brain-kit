# Dosya sistemi (MCP)

> İzin verilen klasörlerde dosya okuma/yazma/arama.

| | |
|---|---|
| MCP kimliği | `filesystem` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem |
| Ne ister | alan: İzin verilen klasör (`allowed_dir`); program: Node.js |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: İzin verilen klasörlerde dosya okuma/yazma/arama. Genel anlatım: [MCP](../06-mcp.md).

## Gerekenler

**Bilgisayarda kurulu olması gereken programlar:** Node.js


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| İzin verilen klasör (`allowed_dir`) | dosya ya da klasör yolu | evet | Yalnız bu klasörün içine erişilir. |

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **Dosya sistemi** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **İzin verilen klasör** alanını doldur (dosya ya da klasör yolu, zorunlu). Yalnız bu klasörün içine erişilir.
3. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`npm view @modelcontextprotocol/server-filesystem version`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
4. Başarılıysa kartta `Dosya sistemi kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add filesystem --scope user -- npx -y @modelcontextprotocol/server-filesystem@2.1.0 {allowed_dir}
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **Node.js** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| `gerekli alan eksik: allowed_dir` | **İzin verilen klasör** alanını doldur |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
