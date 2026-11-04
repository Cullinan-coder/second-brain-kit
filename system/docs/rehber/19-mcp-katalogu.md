# MCP kataloğu

Sihirbazın 8. adımında **18 hazır MCP** vardır. Her birinin sayfasında ne işe yaradığı, ne istediği, sihirbazda kurulum ve sorun giderme yazar. Genel anlatım: [MCP](06-mcp.md).

| MCP | Ne yapar | Tür | Ne ister |
|---|---|---|---|
| [Jira / Atlassian](mcp/atlassian.md) | Jira ve Confluence (Atlassian'ın uzak MCP sunucusu). | uzak/elle | hesap: [Atlassian (Jira)](mcp/atlassian.md) |
| [Brave Arama](mcp/brave-search.md) | Brave Search API ile web arama. NOT: eski paket arşivlendi; Brave'in güncel sunucusu için docs_url. | yerel | hesap: [Brave Search](mcp/brave-search.md); gizli değer: Brave Search API anahtarı (`brave_key`); program: Node.js |
| [Web getir (Fetch)](mcp/fetch.md) | Web sayfalarını çekip modele okunur metin olarak verir. | yerel | program: uv |
| [Figma](mcp/figma.md) | Figma tasarımlarını koda/okumaya açar (Figma'nın MCP sunucusu). | uzak/elle | hesap: [Figma](mcp/figma.md) |
| [Dosya sistemi](mcp/filesystem.md) | İzin verilen klasörlerde dosya okuma/yazma/arama. | yerel | alan: İzin verilen klasör (`allowed_dir`); program: Node.js |
| [Google Drive](mcp/gdrive.md) | Drive dosyalarını arar ve okur. NOT: paket arşivlendi; OAuth kurulumu gerekir (docs_url). | yerel | hesap: [Google](03-hesaplar.md#hesap-google); alan: Kaydedilmiş OAuth kimlik dosyası yolu (`gdrive_credentials`); program: Node.js |
| [GitHub](mcp/github.md) | Depo, issue, PR ve kod araması (GitHub'ın resmi MCP sunucusu). | yerel | hesap: [GitHub](03-hesaplar.md#hesap-github); gizli değer: GitHub kişisel erişim belirteci (PAT) (`github_pat`); program: Docker |
| [Linear](mcp/linear.md) | Linear sorunlarını ve projelerini okur/yazar (Linear'ın uzak MCP sunucusu). | uzak/elle | hesap: [Linear](mcp/linear.md) |
| [Bellek (bilgi grafı)](mcp/memory.md) | Yerel bilgi grafı ile konuşmalar arası basit bellek. | yerel | program: Node.js |
| [Notion](mcp/notion.md) | Notion sayfa ve veritabanlarını okuyup yazar (Notion'un resmi MCP sunucusu). | yerel | hesap: [Notion](mcp/notion.md); gizli değer: Notion entegrasyon belirteci (`notion_token`); program: Node.js |
| [Playwright](mcp/playwright.md) | Tarayıcı otomasyonu ve sayfa testi (Microsoft'un resmi MCP sunucusu). | yerel | program: Node.js |
| [PostgreSQL](mcp/postgres.md) | PostgreSQL veritabanını salt okunur sorgular. NOT: paket arşivlendi. | yerel | gizli değer: Bağlantı adresi (postgresql://…) (`postgres_url`); program: Node.js |
| [Puppeteer](mcp/puppeteer.md) | Tarayıcıyı komutla gezdirir, ekran görüntüsü alır. NOT: paket arşivlendi; yenisi için Playwright. | yerel | program: Node.js |
| [Second Brain (kendi MCP'miz)](mcp/second-brain.md) | Kasada ve arşivde arama, proje/ders/kişi dosyaları, bugün ve özet araçlarını Claude Code/Desktop'a verir. | yerel | ek hesap, anahtar ya da program gerekmez |
| [Sentry](mcp/sentry.md) | Hata kayıtları ve sorunlar (Sentry'nin uzak MCP sunucusu). | uzak/elle | hesap: [Sentry](mcp/sentry.md) |
| [Sıralı düşünme](mcp/sequential-thinking.md) | Karmaşık sorunları adım adım düşünmeye yarayan araç. | yerel | program: Node.js |
| [Slack](mcp/slack.md) | Slack kanallarını okur ve mesaj yazar. NOT: bu paket arşivlendi (modelcontextprotocol/servers-archived); Slack'in güncel resmi MCP'si için docs_url'ye bak. | yerel | hesap: [Slack](mcp/slack.md); gizli değer: Slack bot belirteci (xoxb-…) (`slack_bot_token`); alan: Slack takım kimliği (T…) (`slack_team_id`); program: Node.js |
| [SQLite](mcp/sqlite.md) | Bir SQLite dosyasını sorgular. NOT: paket arşivlendi. | yerel | alan: SQLite dosya yolu (`sqlite_path`); program: uv |
