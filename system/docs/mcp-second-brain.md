# Second Brain MCP sunucusu

Second Brain'in kendi MCP sunucusu, Claude Code ve Claude Desktop'a kasanda ve arşivinde arama yapma, proje/ders/kişi dosyalarını okuma,
"bugün" ve "özet" araçlarını verir. Kurulum sihirbazının MCP adımında **Kur ve bağla** düğmesiyle eklenir.

## Elle kurmak istersen

Claude Code kuruluysa, kasadaki `_system` klasöründe:

```
claude mcp add --scope user second-brain -- uv run --directory <kasa>/_system python -m sb.mcp_server
```

`<kasa>` yerine Second Brain kasanın yolunu yaz. Kaldırmak için:

```
claude mcp remove second-brain -s user
```

## Güvenlik

- Sunucu yalnız senin bilgisayarında çalışır; veri dışarı gönderilmez.
- Mail ve arşiv salt okunurdur; sırlar (şifre, API anahtarı) araçlara verilmez.
