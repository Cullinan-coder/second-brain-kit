# GitHub (MCP)

> Depo, issue, PR ve kod araması (GitHub'ın resmi MCP sunucusu).

| | |
|---|---|
| MCP kimliği | `github` |
| Varsayılan | kapalı (isteğe bağlı) |
| Tür | yerel komut (sihirbaz kurar) |
| Resmi belge | https://github.com/github/github-mcp-server |
| Ne ister | hesap: [GitHub](../03-hesaplar.md#hesap-github); gizli değer: GitHub kişisel erişim belirteci (PAT) (`github_pat`); program: Docker |

## MCP nedir, bu ne işe yarar

MCP (Model Context Protocol), Claude'a ek araçlar vermenin standart yoludur. Bu MCP bağlanınca Claude Code ve Claude Desktop şunu yapabilir: Depo, issue, PR ve kod araması (GitHub'ın resmi MCP sunucusu). Genel anlatım: [MCP](../06-mcp.md).

## Gerekenler

**Hesaplar:** [GitHub](../03-hesaplar.md#hesap-github)

**Bilgisayarda kurulu olması gereken programlar:** Docker


| Alan | Ne girilir | Zorunlu mu | Açıklama |
|---|---|---|---|
| GitHub kişisel erişim belirteci (PAT) (`github_pat`) | gizli değer (yalnız şifre kasasına yazılır) | evet | GitHub > Settings > Developer settings > Personal access tokens; yalnız gereken izinleri ver. |

Gizli değerler (`github_pat`) **yalnız işletim sisteminin şifre kasasına** yazılır; ayar dosyalarında, günlükte ya da bu rehberde görünmez.

## Sihirbazda kurulum (8. adım: MCP)

1. 8. adımda **GitHub** kartını bul (seçimin için gerekenler başta, öbürleri aşağıda).
2. **GitHub kişisel erişim belirteci (PAT)** alanını doldur (gizli değer (yalnız şifre kasasına yazılır), zorunlu). GitHub > Settings > Developer settings > Personal access tokens; yalnız gereken izinleri ver.
3. **Kur ve bağla**'ya bas. Sihirbaz önce ön koşulu dener (`docker pull ghcr.io/github/github-mcp-server:v2.1.0`); başarısızsa `Ön koşul başarısız: … kurulu mu?` der.
4. Başarılıysa kartta `GitHub kuruldu ✓` ve **kurulu** rozeti çıkar. Kaldırmak için kartta **Kaldır**.

Arka planda çalışan komut (gizli değerler `<alan>` yer tutucusuyla, gerçek değer şifre kasasından alınır):

```
claude mcp add github --scope user -e GITHUB_PERSONAL_ACCESS_TOKEN=<github_pat> -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server:v2.1.0
```



## Sorun giderme

| Belirti | Ne yap |
|---|---|
| `claude komutu bulunamadı (Claude Code kurulu değil)` | Claude Code'u kur, terminali yeniden aç, sihirbazda **Kur ve bağla**'yı tekrar dene |
| `Ön koşul başarısız: … kurulu mu?` | **Docker** kurulu ve komut satırından çalışır olmalı; kurup yeniden dene |
| `gerekli alan eksik: github_pat` | **GitHub kişisel erişim belirteci (PAT)** alanını doldur |
| `şifre kasası (keyring) yok` | İşletim sisteminin şifre kasası kullanılamıyor; Windows'ta Kimlik Bilgisi Yöneticisi'nin açık olduğundan emin ol |
| MCP kurulu görünüyor ama araçlar gelmiyor | Claude Code/Desktop'u kapatıp aç; `claude mcp list` ile durumu gör |

Ortak sorunlar: [Sorun giderme](../11-sorun-giderme.md).
