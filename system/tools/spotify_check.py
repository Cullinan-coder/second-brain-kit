"""Spotify bağlantı teşhisi: hesap türü, cihazlar, arama. Kullanım: uv run python -X utf8 tools/spotify_check.py"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import urllib.error

from sb import spotify_api as s

for method, path, q in [("GET", "/me", None), ("GET", "/me/player/devices", None),
                        ("GET", "/search", {"q": "ben fero demet akalin", "type": "track", "limit": 1})]:
    try:
        r = s._api(method, path, query=q)
        if path == "/me":
            print(path, "OK product=", r.get("product"), "country=", r.get("country"))
        elif path == "/me/player/devices":
            print(path, "OK", [(d["name"], d["type"], d["is_active"]) for d in r.get("devices", [])])
        else:
            print(path, "OK", [t["name"] for t in r.get("tracks", {}).get("items", [])])
    except urllib.error.HTTPError as e:
        print(path, e.code, e.read().decode("utf-8", "replace")[:300])

if len(sys.argv) > 1:                                    # örn: tools/spotify_check.py "tarkan kuzu kuzu" → çalar
    print(s.play(sys.argv[1]))
