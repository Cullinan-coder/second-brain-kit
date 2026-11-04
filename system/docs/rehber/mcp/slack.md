# Slack (MCP)

> Slack kanallarını okur ve mesaj yazar. NOT: bu paket arşivlendi (modelcontextprotocol/servers-archived); Slack'in güncel resmi MCP'si için docs_url'ye bak.

| | |
|---|---|
| MCP kimliği | `slack` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://docs.slack.dev/ai/mcp-server |
| Ne ister | hesap: [Slack](../mcp/slack.md); gizli değer: Slack bot belirteci (xoxb-…) (`slack_bot_token`); alan: Slack takım kimliği (T…) (`slack_team_id`); program: Node.js |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Slack kanallarını okur ve mesaj yazar. NOT: bu paket arşivlendi (modelcontextprotocol/servers-archived); Slack'in güncel resmi MCP'si için docs_url'ye bak. Genel anlatım: [MCP](../06-mcp.md).

> **Dikkat:** açıklamada belirtildiği gibi bu paket arşivlenmiş olabilir. Güncel sürüm için resmi belge adresine bak; sihirbaz yine de kurmayı dener.

## Gerekenler

**Hesaplar:** [Slack](../mcp/slack.md)

**Bilgisayarda kurulu olması gereken programlar:** Node.js


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| Slack bot belirteci (xoxb-…) (`slack_bot_token`) | gizli değer (yalnız şifre kasasına yazılır) | evet | api.slack.com/apps'ta uygulama oluştur, gereken izinleri ver, çalışma alanına kur. |
| Slack takım kimliği (T…) (`slack_team_id`) | metin | evet | — |

Gizli değerler (`slack_bot_token`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **Slack** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **Slack bot belirteci (xoxb-…)** alanını doldur (gizli değer (yalnız şifre kasasına yazılır), zorunlu). api.slack.com/apps'ta uygulama oluştur, gereken izinleri ver, çalışma alanına kur.
3. **Slack takım kimliği (T…)** alanını doldur (metin, zorunlu). 
4. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`npm view @modelcontextprotocol/server-slack version`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
5. Başarılıysa kartta `Slack kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add slack --scope user -e SLACK_BOT_TOKEN=<slack_bot_token> -e SLACK_TEAM_ID=<slack_team_id> -- npx -y @modelcontextprotocol/server-slack
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **Node.js** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| `gerekli alan eksik: slack_bot_token` | **Slack bot belirteci (xoxb-…)** alanını doldur |
| `gerekli alan eksik: slack_team_id` | **Slack takım kimliği (T…)** alanını doldur |
| `şifre kasası (keyring) yok` | İşletim sisteminin şifre kasası kullanılamıyor; Windows'ta Kimlik Bilgisi Yöneticisi'nin açık olduğundan emin ol |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
