# Spotify'da doğrudan çalma (Premium)

Spotify uygulaması dışarıdan yalnız "ara" komutunu kabul eder; "çal" için resmi Web API gerekir ve bu **Premium** ister.
Premium değilsen asistan Spotify aramasını açar, ▶'ye sen basarsın (ya da "YouTube'da aç" de).

1. https://developer.spotify.com/dashboard → kendi Spotify hesabınla giriş → **Create app**
   - App name `Second Brain`, description `Kişisel asistan`
   - Redirect URI: `http://127.0.0.1:8765/spotify/callback` → **Add**
   - **Web API** işaretli → kutucuğu onayla → **Save**
2. **Settings → Client ID**'yi kopyala → `_system/config/spotify.yaml` içine `client_id: "..."` (gizli değildir).
   **Client Secret kullanılmaz** (PKCE akışı).
3. **Bilgisayarda** tarayıcıda `http://127.0.0.1:8765/spotify/login` aç → **Agree** → "Spotify bağlandı".
4. Asistana: "Spotify'da Tarkan Kuzu Kuzu çal".

Teşhis: `uv run python -X utf8 tools/spotify_check.py ["şarkı"]` (hesap, cihazlar, arama; şarkı verirsen çalar).

Notlar: Şarkı her zaman **bu bilgisayarda** çalar (Spotify kapalıysa açılır). İzinler yalnız çalma durumu/kontrolü.
Yenileme anahtarı işletim sisteminin şifre kasasında (`spotify-refresh`).
