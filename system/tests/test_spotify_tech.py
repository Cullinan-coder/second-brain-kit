"""Spotify teknik günlük paketi içe aktarıcısı: yalnız müzik bilgisi, yazım adımı ayıklama, ağsız ad çözümleme."""
import json
import zipfile
from pathlib import Path

from sb import maildb
from sb.connectors import spotify_tech as st

P = "Spotify Technical Log Information/"


def _pack(tmp_path: Path) -> Path:
    z = tmp_path / "my_spotify_data.zip"
    dev = {"context_device_model": "TEST-MODEL", "context_conn_country": "TR", "context_ip": "10.0.0.1"}
    data = {
        "SearchViewResponse": [
            {**dev, "context_time": 1_000_000, "message_query": "Kib"},
            {**dev, "context_time": 1_001_000, "message_query": "Kibri"},
            {**dev, "context_time": 1_002_000, "message_query": "Kibrit"},
            {**dev, "context_time": 9_000_000, "message_query": "Dağlar bizimdir"},
            {**dev, "context_time": 9_500_000, "message_query": "B"},
        ],
        "AddedToCollection": [{"context_time": 2_000_000, "message_item_uri": "spotify:track:AAA"},
                              {"context_time": 2_000_001, "message_item_uri": "spotify:track:AAA"}],
        "OnRepeatContents": [{"context_time": 3_000_000, "message_contents": ["spotify:track:AAA", "spotify:track:BBB"]},
                             {"context_time": 4_000_000, "message_contents": ["spotify:track:AAA"]}],
        "DaylistGenerated": [{"context_time": 5_000_000, "message_playlist_title": "gece slow pop",
                              "message_playlist_description": "<a href='x'>slow pop</a> ve daha fazlası"}],
        "MinimumLyricsCharactersSeen": [{**dev, "message_track_uri": "spotify:track:BBB"}],
        "AndroidDeviceReport": [{"context_device_model": "TEST-MODEL", "serial": "S3CR3T"}],
    }
    with zipfile.ZipFile(z, "w") as f:
        for name, rows in data.items():
            f.writestr(P + name + ".json", json.dumps(rows, ensure_ascii=False))
        f.writestr(P + "ReadMeFirst_TechnicalLogInformation.pdf", b"%PDF")
    return z


def test_detects_pack(tmp_path):
    assert st.is_tech_pack(_pack(tmp_path))
    other = tmp_path / "x.zip"
    with zipfile.ZipFile(other, "w") as f:
        f.writestr("StreamingHistory0.json", "[]")
    assert not st.is_tech_pack(other)


def test_typing_steps_collapsed():
    ev = [{"context_time": t, "message_query": q} for t, q in
          [(0, "Kib"), (1000, "Kibri"), (2000, "Kibrit"), (500_000, "Manolya"), (600_000, "B")]]
    assert [q for q, _ in st.final_searches(ev)] == ["Kibrit", "Manolya"]


def test_parse_keeps_only_music_fields(tmp_path):
    rows, stats = st.parse(_pack(tmp_path))
    kinds = sorted({r["kind"] for r in rows})
    assert kinds == ["daylist", "lyrics", "repeat", "save", "search"]
    assert [r["meta"]["query"] for r in rows if r["kind"] == "search"] == ["Kibrit", "Dağlar bizimdir"]
    assert sum(r["kind"] == "save" for r in rows) == 1                      # aynı şarkı iki kez eklenmez
    assert stats["repeat"]["AAA"] == 2
    blob = json.dumps(rows, ensure_ascii=False)
    for leak in ("TEST-MODEL", "10.0.0.1", "S3CR3T"):                         # cihaz/ağ alanı kayda girmez
        assert leak not in blob
    assert "<a" not in next(r["body"] for r in rows if r["kind"] == "daylist")


def test_run_offline_names_and_note(tmp_path, monkeypatch):
    monkeypatch.setattr(st, "_cache_path", lambda: tmp_path / "names.json")
    con = maildb.connect(tmp_path / "mail.db")
    maildb.insert_item(con, {"source": "spotify", "id": "p1", "date_ms": 1, "kind": "play", "title": "Kibrit",
                             "url": "https://open.spotify.com/track/AAA", "body": "", "meta": {"artist": "Test Sanatçı"}})
    con.commit()
    import sb.spotify_api as api
    monkeypatch.setattr(api, "ready", lambda: False)                          # ağ yok
    vault = tmp_path / "vault"
    res = st.run(_pack(tmp_path), con, vault=vault)
    note = (vault / "40-Kaynaklar" / "Spotify" / "Müzik zevki.md").read_text(encoding="utf-8")
    assert "Kibrit — Test Sanatçı" in note and "spotify:track:BBB" in note
    assert res["yeni"] == 7 and res["adlandirilan"] == 1          # 2 arama + 1 beğeni + 2 tekrar + 1 günlük liste + 1 söz
    again = st.run(_pack(tmp_path), con, vault=vault)
    assert again["yeni"] == 0                                                 # ikinci içe aktarma tekrar yazmaz
