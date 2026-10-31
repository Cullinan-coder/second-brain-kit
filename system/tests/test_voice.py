"""Paket C: ses uçları. Whisper, PowerShell, ollama ve ağ taklit edilir."""
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from sb import config, llm, tasks, vault_ops, voice, webroutes
from sb.webroutes import Ctx


class FakeModel:
    def __init__(self, text="merhaba dünya", lang="tr"):
        self.text, self.lang, self.calls = text, lang, []

    def transcribe(self, path, **kw):
        self.calls.append((path, kw))
        seg = SimpleNamespace(start=0.0, end=2.5, text=" " + self.text)
        return iter([seg]), SimpleNamespace(language=self.lang, duration=2.5)


@pytest.fixture
def fake(monkeypatch):
    m = FakeModel()
    monkeypatch.setattr(voice, "WhisperModel", object())
    monkeypatch.setattr(voice, "_get_model", lambda name, force_cpu=False: (m, threading.Lock()))
    return m


@pytest.fixture
def vault(monkeypatch, tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "abc123")
    return v


def call(method, path, **kw):
    r = webroutes.find(method, path)
    assert r, path
    code, body, ctype, _ = webroutes.call(r, Ctx(method=method, path=path, **kw))
    return code, (json.loads(body) if "json" in ctype else body)


def test_routes_registered():
    for m, p in [("POST", "/api/v2/stt"), ("GET", "/api/v2/tts/voices"), ("POST", "/api/v2/tts"), ("POST", "/api/v2/wake"),
                 ("POST", "/api/v2/voice-note"), ("POST", "/api/v2/meeting"), ("POST", "/api/v2/transcribe-url"),
                 ("POST", "/api/v2/pronounce")]:
        assert webroutes.find(m, p)
    assert webroutes.find("POST", "/api/v2/wake").model is False


def test_stt_unavailable(monkeypatch):
    monkeypatch.setattr(voice, "WhisperModel", None)
    code, out = call("POST", "/api/v2/stt", raw=b"x", ctype="audio/webm")
    assert code == 200 and out["available"] is False and "faster-whisper" in out["hint"]


def test_stt_ok_auto_language(fake):
    code, out = call("POST", "/api/v2/stt", raw=b"RIFFxxxx", ctype="audio/webm;codecs=opus", query={"lang": ""})
    assert code == 200 and out["text"] == "merhaba dünya" and out["language"] == "tr"
    assert out["segments"][0] == {"start": 0.0, "end": 2.5, "text": "merhaba dünya"} and out["duration"] == 2.5
    path, kw = fake.calls[0]
    assert path.endswith(".webm") and kw["language"] is None
    call("POST", "/api/v2/stt", raw=b"x", ctype="audio/wav", query={"lang": "en"})
    assert fake.calls[1][1]["language"] == "en"


def test_stt_empty_body(fake):
    assert call("POST", "/api/v2/stt", raw=b"", ctype="audio/wav")[0] == 400


def test_detect_language_text():
    assert voice.detect_language("bu bir deneme ve çok güzel") == "tr"
    assert voice.detect_language("this is the test and you are fine") == "en"


def test_detect_language_audio(fake):
    assert voice.detect_language(b"abc", "audio/wav") == "tr"


def test_status_no_load(monkeypatch):
    monkeypatch.setattr(voice, "WhisperModel", None)
    s = voice.status()
    assert s["faster_whisper"] is False and s["model_loaded"] is False and s["device"] == "cpu" and "faster-whisper" in s["hint"]
    assert {"yt_dlp", "stt_model", "sapi"} <= set(s)


def test_tts_voices_parse(monkeypatch):
    monkeypatch.setattr(voice.sys, "platform", "win32")
    out = json.dumps({"name": "Microsoft Tolga", "lang": "tr-TR", "gender": "Male"}).encode()
    monkeypatch.setattr(voice, "_ps", lambda *a, **k: SimpleNamespace(stdout=out, returncode=0, stderr=b""))
    r = voice.tts_voices()
    assert r["available"] and r["voices"][0]["lang"] == "tr-TR"
    monkeypatch.setattr(voice.sys, "platform", "linux")
    assert voice.tts_voices()["available"] is False


def test_tts_text_via_env_not_cmdline(monkeypatch):
    monkeypatch.setattr(voice.sys, "platform", "win32")
    seen = {}

    def fake_ps(script, env=None, timeout=60):
        seen.update(script=script, env=env)
        Path(env["SB_TTS_OUT"]).write_bytes(b"RIFFwav")
        return SimpleNamespace(returncode=0, stderr=b"", stdout=b"")

    monkeypatch.setattr(voice, "_ps", fake_ps)
    evil = "merhaba'; Remove-Item C:\\ -Recurse; '"
    code, body = call("POST", "/api/v2/tts", data={"text": evil, "voice": "Microsoft Tolga", "rate": 99})
    assert code == 200 and body == b"RIFFwav"
    assert evil not in seen["script"] and seen["env"]["SB_TTS_TEXT"] == evil and seen["env"]["SB_TTS_RATE"] == "10"


def test_tts_non_windows(monkeypatch):
    monkeypatch.setattr(voice.sys, "platform", "linux")
    assert call("POST", "/api/v2/tts", data={"text": "x"})[0] == 501


def test_wake(fake, monkeypatch):
    monkeypatch.setattr(voice, "_assistant_name", lambda: "Beyin")
    fake.text = "Hey Beyin, saat kaç"
    assert call("POST", "/api/v2/wake", raw=b"a", ctype="audio/webm")[1]["wake"] is True
    fake.text = "bugün hava güzel"
    assert call("POST", "/api/v2/wake", raw=b"a", ctype="audio/webm")[1]["wake"] is False
    fake.text = "hey asistan nasılsın"
    assert call("POST", "/api/v2/wake", raw=b"a", ctype="audio/webm", query={"phrase": "hey asistan"})[1]["wake"] is True


def test_voice_note(fake, vault):
    code, out = call("POST", "/api/v2/voice-note", raw=b"audio", ctype="audio/webm", query={"title": "Fikir"})
    assert code == 200 and out["text"] == "merhaba dünya"
    p = vault / out["path"]
    assert out["path"].startswith("00-Inbox/Sesli notlar/") and "Fikir" in out["path"] and p.exists()
    body = p.read_text(encoding="utf-8")
    assert "merhaba dünya" in body and "Süre: 0:02" in body
    assert len(list((config.DATA / "audio").glob("*.webm"))) == 1


def test_voice_note_redacts(fake, vault):
    fake.text = "iban TR33 0006 1005 1978 6457 8413 26 dir"
    out = call("POST", "/api/v2/voice-note", raw=b"a", ctype="audio/wav")[1]
    assert "6457" not in (vault / out["path"]).read_text(encoding="utf-8")


def test_meeting(fake, vault, monkeypatch):
    seen = {}

    def fake_complete(task, prompt, **kw):
        seen["private"] = kw.get("private")
        return json.dumps({"summary": "Plan konuşuldu.", "decisions": ["Cuma teslim"], "tasks": ["Raporu hazırla"],
                           "questions": ["Bütçe?"]}), "yerel qwen3:14b"

    monkeypatch.setattr(llm, "complete", fake_complete)
    added = []
    monkeypatch.setattr(tasks, "add", lambda title, text="", **kw: added.append((title, kw)) or "Görev oluşturuldu: x")
    fake.text = "Cuma teslim edeceğiz"
    code, out = call("POST", "/api/v2/meeting", raw=b"a", ctype="audio/webm", query={"title": "Haftalık"})
    assert code == 200 and out["summary"] == "Plan konuşuldu." and out["decisions"] == ["Cuma teslim"] and out["tasks"] == ["Raporu hazırla"]
    assert seen["private"] is True and added and added[0][1]["owner"]
    assert out["path"].startswith("40-Kaynaklar/Toplantılar/")
    txt = (vault / out["path"]).read_text(encoding="utf-8")
    assert "## Kararlar" in txt and "Cuma teslim" in txt and "## Döküm" in txt


def test_meeting_course_folder(fake, vault, monkeypatch):
    (vault / "10-Dersler" / "BIL101 Algoritma").mkdir(parents=True)
    monkeypatch.setattr(llm, "complete", lambda *a, **k: (json.dumps({"summary": "s", "decisions": [], "tasks": [], "questions": []}), "yerel"))
    out = call("POST", "/api/v2/meeting", raw=b"a", ctype="audio/webm", query={"course": "bil101"})[1]
    assert out["path"].startswith("10-Dersler/BIL101 Algoritma/")


def test_transcribe_url_captions(vault, monkeypatch):
    from sb import capture
    monkeypatch.setattr(capture, "youtube", lambda vid: ("Başlık", "Kanal", "altyazı metni"))
    monkeypatch.setattr(capture, "summarize", lambda kind, title, text: {"summary": "özet", "points": ["a"], "tags": ["t"]})
    code, out = call("POST", "/api/v2/transcribe-url", data={"url": "https://youtu.be/abcdefghijk"})
    assert code == 200 and out["method"] == "altyazı" and out["path"].startswith("40-Kaynaklar/Videolar/")
    assert "altyazı metni" in (vault / out["path"]).read_text(encoding="utf-8")


def test_transcribe_url_no_ytdlp(vault, monkeypatch):
    import sys
    from sb import capture
    monkeypatch.setattr(capture, "youtube", lambda vid: ("B", "", ""))
    monkeypatch.setattr(voice, "WhisperModel", object())
    monkeypatch.setitem(sys.modules, "yt_dlp", None)
    out = call("POST", "/api/v2/transcribe-url", data={"url": "https://youtu.be/abcdefghijk"})[1]
    assert out["available"] is False and "yt-dlp" in out["hint"]


def test_transcribe_url_bad():
    assert call("POST", "/api/v2/transcribe-url", data={"url": "file:///etc/passwd"})[0] == 400


def test_pronounce(fake):
    q = {"target": "I like to eat a banana", "lang": "en"}
    fake.text = "I like to eat a banana"
    out = call("POST", "/api/v2/pronounce", raw=b"a", ctype="audio/webm", query=q)[1]
    assert out["score"] == 100 and all(w["ok"] for w in out["words"])
    fake.text = "I like to eat a bandana"
    out = call("POST", "/api/v2/pronounce", raw=b"a", ctype="audio/webm", query=q)[1]
    bad = [w for w in out["words"] if not w["ok"]]
    assert 0 < out["score"] < 100 and bad[0]["word"] == "banana" and bad[0]["heard"] == "bandana" and out["tips"]
    assert fake.calls[-1][1]["language"] == "en"


def test_pronounce_needs_target(fake):
    assert call("POST", "/api/v2/pronounce", raw=b"a", ctype="audio/wav")[0] == 400
