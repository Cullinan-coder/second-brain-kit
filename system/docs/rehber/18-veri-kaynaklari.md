# Veri kaynakları

Sihirbazın 9. adımı **39 kaynaktan** veri alır. Her kaynağın sayfasında dışa aktarma adımları, sihirbazda yükleme, komut ve sorun giderme vardır. Genel anlatım: [Veri yükleme](07-veri-yukleme.md).

| Kaynak | Biçim | Bağlı modül | Hesap |
|---|---|---|---|
| [Apple Notlar](kaynaklar/apple-notlar.md) | klasör, .html, .txt | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [arXiv sorguları](kaynaklar/arxiv.md) | config/rss.yaml | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [Banka ekstresi (CSV)](kaynaklar/bank.md) | .csv | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [BibTeX dosyası](kaynaklar/bibtex.md) | .bib | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [ChatGPT / Claude / Gemini sohbet geçmişi](kaynaklar/history-import.md) | .zip, .json, klasör | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [Coursera ilerlemesi](kaynaklar/coursera.md) | .csv, .json | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [Discord veri paketi](kaynaklar/discord.md) | .zip, klasör | [Mesaj içe aktarmaları](moduller/imports_comm.md) | — |
| [Ekran süresi / uygulama kullanımı](kaynaklar/screentime.md) | .csv | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [Evernote](kaynaklar/evernote.md) | .enex | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [Google Fotoğraflar meta verisi](kaynaklar/gphotos.md) | klasör, .json | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | [Google](03-hesaplar.md#hesap-google) |
| [Google Haritalar zaman çizelgesi](kaynaklar/gmaps.md) | .json, klasör | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | [Google](03-hesaplar.md#hesap-google) |
| [Google Keep notları](kaynaklar/keep.md) | .zip, klasör | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | [Google](03-hesaplar.md#hesap-google) |
| [Google Takeout](kaynaklar/takeout.md) | .zip | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | [Google](03-hesaplar.md#hesap-google) |
| [iCloud mail, takvim, kişiler](kaynaklar/icloud.md) | hesap | [Mesaj içe aktarmaları](moduller/imports_comm.md) | [iCloud](03-hesaplar.md#hesap-icloud), [E-posta (IMAP)](03-hesaplar.md#hesap-imap) |
| [Instagram verileri](kaynaklar/instagram.md) | .zip, klasör | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [Jira](kaynaklar/jira.md) | .csv, .json | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [Kindle vurguları](kaynaklar/kindle.md) | .txt | [Medya ve okuma içe aktarmaları](moduller/imports_media.md) | — |
| [Linear](kaynaklar/linear.md) | .csv, .json | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [LinkedIn veri arşivi](kaynaklar/linkedin.md) | .zip | [LinkedIn arşivi](moduller/linkedin.md) | — |
| [Microsoft To Do](kaynaklar/mstodo.md) | .csv, .json | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [Notion dışa aktarımı](kaynaklar/notion.md) | .zip, klasör | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [OneNote](kaynaklar/onenote.md) | klasör, .docx, .html | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [Outlook / Microsoft 365 mail](kaynaklar/outlook.md) | hesap | [Mesaj içe aktarmaları](moduller/imports_comm.md) | [Outlook](03-hesaplar.md#hesap-outlook), [E-posta (IMAP)](03-hesaplar.md#hesap-imap) |
| [Pocket](kaynaklar/pocket.md) | .html, .csv | [Medya ve okuma içe aktarmaları](moduller/imports_media.md) | — |
| [Raindrop.io yer imleri](kaynaklar/raindrop.md) | .csv | [Medya ve okuma içe aktarmaları](moduller/imports_media.md) | — |
| [RSS ve haber bültenleri](kaynaklar/rss.md) | config/rss.yaml | [Medya ve okuma içe aktarmaları](moduller/imports_media.md) | — |
| [Slack dışa aktarımı](kaynaklar/slack.md) | .zip, klasör | [Mesaj içe aktarmaları](moduller/imports_comm.md) | — |
| [SMS ve aramalar](kaynaklar/sms.md) | .xml | [SMS ve aramalar](moduller/sms.md) | [Google](03-hesaplar.md#hesap-google) |
| [Spotify dinleme geçmişi](kaynaklar/spotify.md) | .json, klasör | [Medya ve okuma içe aktarmaları](moduller/imports_media.md) | [Spotify](03-hesaplar.md#hesap-spotify) |
| [Tarayıcı geçmişi ve yer imleri](kaynaklar/browser.md) | History, Bookmarks, places.sqlite | [Tarayıcı geçmişi](moduller/browser.md) | — |
| [Telegram arşivi](kaynaklar/telegram.md) | .json | [Mesaj içe aktarmaları](moduller/imports_comm.md) | — |
| [TickTick](kaynaklar/ticktick.md) | .csv, .json | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [Todoist](kaynaklar/todoist.md) | .csv, .json | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [Trello](kaynaklar/trello.md) | .csv, .json | [Not ve görev içe aktarmaları](moduller/imports_notes.md) | — |
| [Udemy ilerlemesi](kaynaklar/udemy.md) | .csv, .json | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [WhatsApp sohbetleri](kaynaklar/whatsapp.md) | .txt, .zip | [WhatsApp](moduller/whatsapp.md) | — |
| [X (Twitter) arşivi](kaynaklar/x.md) | .zip, klasör | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
| [YouTube izleme geçmişi](kaynaklar/youtube.md) | .json, .html, .csv | [Medya ve okuma içe aktarmaları](moduller/imports_media.md) | [Google](03-hesaplar.md#hesap-google) |
| [Zotero kütüphanesi](kaynaklar/zotero.md) | .sqlite | [Yaşam ve akademik içe aktarmalar](moduller/imports_life.md) | — |
