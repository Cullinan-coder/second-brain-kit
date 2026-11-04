# 06 · MCP: Claude'a araçlar vermek

Bu bölüm sihirbazın **8. adımını** (Ayarlar → **MCP** sekmesi) ve Second Brain'in kendi MCP sunucusunu anlatır. Her hazır MCP'nin kendi sayfası da var: [MCP kataloğu](19-mcp-katalogu.md).

## MCP nedir?

**MCP (Model Context Protocol)**, bir yapay zekâ asistanına (Claude Code, Claude Desktop) **ek araçlar ve bilgi kaynakları** bağlamanın standart yoludur. Her MCP küçük bir «sunucu» programdır: örneğin GitHub MCP'si Claude'a depolarını okuma yeteneği, dosya sistemi MCP'si izin verilen klasörlerde dosya okuma yeteneği verir.

Second Brain iki yönde MCP kullanır:

1. **Kendi MCP'miz (`second-brain`)**: Claude Code/Desktop'a **senin kasanı ve arşivini** okuma araçları verir. Böylece Claude Code her oturumda seni ve projelerini tanır.
2. **Hazır MCP kataloğu**: GitHub, Notion, Slack, dosya sistemi, tarayıcı… gibi 18 hazır sunucuyu seç → kur → bağla.

> MCP bağlamak için **Claude Code** kurulu olmalı (kurulumu: https://claude.com/code). Claude Code yoksa 8. adım «claude komutu bulunamadı (Claude Code kurulu değil)» der; bu adımı sonra yapabilirsin.

## Second Brain MCP'si

### Ne verir?

Aşağıdaki araçlar Claude'a açılır (hepsi **salt okunur** ya da yerel; sırlar araçlara verilmez):

| Araç | Ne yapar |
|---|---|
| `brain_overview` | Kasanın genel görünümü: projeler, aktif dersler, akademik durum |
| `brain_project` | Bir projenin tam notu (proje dosyası, oturum günlüğü, son çalışmalar) |
| `brain_course` | Bir dersin notu (kod ya da ad parçasıyla) |
| `brain_person` | Bir kişinin notu (telefon, şirket, son mesajlar) |
| `brain_note` | Kasadaki herhangi bir notu yoluyla okur (`gizli` notlar korunur) |
| `brain_search` | Belge içeriği, mail, SMS ve Drive adlarında tam metin arama |
| `brain_find` | Doğal dille anlam + kelime araması (`geçen ay`, `hocadan gelen mailler` gibi süzgeçler) |
| `brain_answer` | Soruyu yerel modelle, **yalnız bulunan kaynaklara dayanarak** cevaplar |
| `brain_today` | Yaklaşan teslim/sınav/başvuru tarihleri ve onay bekleyen takvim adayları |
| `brain_recap` | Son günlerde ne yapıldı (iş makbuzlarından) |
| `local_work` | Büyük metin/log/belge yığınını ücretsiz yerel modele özetletir (Claude limitini korur) |

### Sihirbazdan bağlama

1. 8. adımda **Second Brain (kendi MCP'miz)** kartı (**önerilen** rozetiyle).
2. **Kur ve bağla**'ya bas. Sihirbaz `claude mcp add` ile kullanıcı düzeyinde ekler; kasadaki Python ortamını kullanır.
3. Başarılıysa «**Second Brain (kendi MCP'miz) kuruldu ✓**» ve **kurulu** rozeti.
4. Claude Code'u kapatıp aç. Yeni oturumda araçlar görünür.

### Elle bağlama (Claude Code kuruluysa)

Kasadaki `_system` klasöründe:

```
claude mcp add --scope user second-brain -- uv run --directory <kasa>/_system python -m sb.mcp_server
```

`<kasa>` yerine kasanın yolunu yaz. Kaldırmak: `claude mcp remove second-brain -s user`. Listelemek: `claude mcp list`.

### Güvenlik

- Sunucu **yalnız senin bilgisayarında** çalışır; veri dışarı gönderilmez.
- Mail ve arşiv **salt okunurdur**; şifre/API anahtarı araçlara verilmez.
- `gizli` işaretli notlar `brain_note` ile okunamaz.
- Claude Code'un hafıza kancaları (oturum başı bağlam, son oturum kartları) da bu kasadan beslenir; kapatmak için **Claude Code hafızası** modülünü kapat veya `sb mode manuel`.

## Hazır MCP kataloğu (18 sunucu)

8. adımda katalog kartları görünür. Seçimin için gerekenler önce ve **önerilen** rozetiyle gelir; diğerleri aşağıdadır.

![MCP katalog kartları](img/mcp-katalog.png)

| MCP | Ne yapar | Tür |
|---|---|---|
| [Second Brain (kendi MCP'miz)](mcp/second-brain.md) | Kasa ve arşiv araçları | yerel |
| [GitHub](mcp/github.md) | Depo, issue, PR, kod arama | yerel (Docker) |
| [Notion](mcp/notion.md) | Notion sayfa/veritabanları | yerel (Node.js) |
| [Slack](mcp/slack.md) | Slack kanalları | yerel (Node.js; paket arşivlenmiş) |
| [Dosya sistemi](mcp/filesystem.md) | İzinli klasörlerde dosya işleri | yerel (Node.js) |
| [Playwright](mcp/playwright.md) | Tarayıcı otomasyonu | yerel (Node.js) |
| [Puppeteer](mcp/puppeteer.md) | Tarayıcı komutla gezdirme (arşivlenmiş) | yerel (Node.js) |
| [Web getir (Fetch)](mcp/fetch.md) | Web sayfasını metne çevirir | yerel (uv) |
| [Brave Arama](mcp/brave-search.md) | Brave ile web arama | yerel (Node.js) |
| [Bellek (bilgi grafı)](mcp/memory.md) | Konuşmalar arası basit bellek | yerel (Node.js) |
| [Sıralı düşünme](mcp/sequential-thinking.md) | Adım adım düşünme aracı | yerel (Node.js) |
| [PostgreSQL](mcp/postgres.md) | Veritabanı sorgulama (arşivlenmiş) | yerel (Node.js) |
| [SQLite](mcp/sqlite.md) | SQLite dosyası sorgulama (arşivlenmiş) | yerel (uv) |
| [Google Drive](mcp/gdrive.md) | Drive dosyaları (arşivlenmiş) | yerel (Node.js) |
| [Jira / Atlassian](mcp/atlassian.md) | Jira ve Confluence | uzak, elle |
| [Linear](mcp/linear.md) | Linear sorunları | uzak, elle |
| [Sentry](mcp/sentry.md) | Hata kayıtları | uzak, elle |
| [Figma](mcp/figma.md) | Figma tasarımları | uzak, elle |

«Arşivlenmiş» paketler resmî depoda arşive alınmıştır; çalışabilirler ama güncel değildir. Güncel sürüm için kartın **Belge** bağlantısına bak.

### Bir MCP'yi kurmak (genel adımlar)

1. 8. adımda kartı bul. Gerekli alanları doldur:
   - Gizli alanlar (belirteç, anahtar) **parola kutusu**dur; değer şifre kasasına `mcp-<id>-<alan>` adıyla yazılır, günlükte maskelenir.
   - Yol alanları (ör. dosya sistemi için **izinli klasör**) normal metin kutusudur.
2. **Kur ve bağla**'ya bas.
3. Sihirbaz önce **ön koşulu** dener: Node.js tabanlı sunucular için `npm view <paket> version`, uv tabanlıları için `uvx <sunucu> --help`, GitHub için `docker pull ...`. Bu başarısız olursa «**Ön koşul başarısız: … kurulu mu?**» der.
4. Sonra `claude mcp add <id> --scope user -e ANAHTAR=değer -- <komut> <argümanlar>` çalıştırır. Windows'ta `npx/uvx` komutları `cmd /c` ile sarılır.
5. Başarılıysa «**… kuruldu ✓**». Aynı MCP daha önce kuruluysa önce kaldırılıp yenisi eklenir (günceller).
6. Claude Code/Desktop'u yeniden başlat.

Uzak sunucularda (Atlassian, Linear, Sentry, Figma) kartta yalnız **Belge** bağlantısı vardır: «**Elle kurulum: belgeye bak.**» Resmî adımları izle; bu sunucular genelde tarayıcıda oturum açtırır.

### Ön koşul programları

| Gerekli program | Nerede lazım | Kurulum |
|---|---|---|
| **Node.js** (`npx`) | Notion, Slack, dosya sistemi, Playwright, Brave, Bellek, Sıralı düşünme, Puppeteer, PostgreSQL, Google Drive | https://nodejs.org (LTS) |
| **uv** (`uvx`) | Fetch, SQLite | https://docs.astral.sh/uv/ |
| **Docker** | GitHub MCP'si | https://www.docker.com/products/docker-desktop (kurduktan sonra Docker açık olmalı) |
| **Claude Code** (`claude`) | Hepsi | https://claude.com/code |

## Kendi MCP'ni eklemek

Elinde bir **komutla çalışan (stdio) MCP sunucusu** varsa (kendi yazdığın ya da internetten bulduğun):

1. 8. adımda en alta in: **Kendi MCP'ni ekle**.
2. **Ad:** harf/rakam/`-`/`_`, en çok 40 karakter, harf ya da rakamla başlar.
3. **Komut:** çalıştırılacak program (`npx`, `uvx`, `python`, …). Tek satır olmalı.
4. **Bağımsız değişkenler (boşlukla):** komutun argümanları (ör. `-y @org/server-adi`).
5. **Ortam değişkenleri:** her satıra `ANAHTAR=değer`. **Değerlerin hepsi gizli sayılır** (maskelenir, günlüğe yazılmaz). Ad geçerli bir ortam değişkeni adı olmalı.
6. **Ekle.** Başarılıysa «**MCP eklendi.**» Eksikse «Ad ve komut gerekli.»

Bilmediğin kaynaktan gelen bir MCP'yi eklemeden önce kodunu/güvenilirliğini kontrol et: MCP sunucusu bilgisayarında program çalıştırır.

## Kurulu MCP'leri görmek ve kaldırmak

- 8. adımın (ya da Ayarlar'ın) üstünde **kurulu** olanlar Claude Code (`claude mcp list`) ve Claude Desktop yapılandırmasından okunur; ortam değişkeni **değerleri** gösterilmez.
- Kart üzerinde **Kaldır** → «… MCP bağlantısı kaldırılsın mı?» onayı → «MCP kaldırıldı.»
- Claude Desktop yapılandırma dosyası: Windows `%APPDATA%\Claude\claude_desktop_config.json`, macOS `~/Library/Application Support/Claude/claude_desktop_config.json`.

## Sorun giderme

| Belirti | Neden / çözüm |
|---|---|
| «claude komutu bulunamadı (Claude Code kurulu değil)» | Claude Code'u kur; terminali yeniden aç |
| «Ön koşul başarısız: npm kurulu mu?» | Node.js'i kur; terminal/uygulamayı yeniden başlat |
| «Ön koşul başarısız: docker …» | Docker Desktop'ı kur **ve aç** |
| «gerekli alan eksik: …» | Karttaki zorunlu alanı doldur |
| «şifre kasası (keyring) yok» | İşletim sistemi şifre kasası kullanılamıyor ([Sorun giderme](11-sorun-giderme.md)) |
| «claude mcp add başarısız» | Günlüğe bak (**Günlük** sekmesi); aynı adla çakışma varsa kaldırıp yeniden kur |
| MCP kurulu ama Claude'da araç görünmüyor | Claude Code/Desktop'u tamamen kapatıp aç; `claude mcp list` ile durumu kontrol et |
| `sb doctor`: «MCP: second-brain» ! | 8. adımda **Kur ve bağla** |
