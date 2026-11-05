"""Asistan sohbet modu (bulut ↔ yerel): mod dosyası, güvenlik katmanları, yerele düşme bildirimi, API ve CLI. Ağ/model yok."""
import json

import pytest

from sb import chat, chat_mode, config, llm, providers, usage, webroutes
from sb.webroutes import Ctx

CLOUD = "gemini:gemini-2.5-pro"
CFG = {"tasks": {"chat": CLOUD}, "fallback_to_local": True,
       "ollama": {"host": "http://x", "model": "qwen3:14b", "num_ctx": 1000}, "budget": {"daily_usd": 2, "monthly_usd": 10}}
LOCAL_CFG = {**CFG, "tasks": {"chat": "ollama"}}
MSGS = [{"role": "system", "content": "Sistem"}, {"role": "user", "content": "Merhaba, nasılsın?"}]


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setattr(llm, "config", lambda: CFG)
    monkeypatch.setattr(llm, "ensure_ollama", lambda c: None)
    monkeypatch.setattr(llm, "_http", lambda host, path, payload, timeout: {"message": {"role": "assistant", "content": "yerel cevap"}})
    monkeypatch.setattr(providers, "has_key", lambda p: True)
    monkeypatch.setattr(chat, "_perm", lambda a: False)
    chat_mode.reset_turn()


def cloud_ok(calls):
    def fake(spec, messages, **kw):
        calls.append(spec)
        return {"content": "bulut cevap", "tool_calls": []}
    return fake


# ---- mod dosyası
def test_varsayilan_bulut_ayarliysa_bulut():
    assert chat_mode.get_mode(CFG) == "cloud"
    assert chat_mode.get_mode(LOCAL_CFG) == "local"
    assert not (config.DATA / "chat_mode.json").exists()


def test_yaz_oku_ve_atomik_dosya():
    assert chat_mode.set_mode("local", CFG) == "local"
    d = json.loads((config.DATA / "chat_mode.json").read_text(encoding="utf-8"))
    assert d["mode"] == "local" and d["ts"]
    assert chat_mode.get_mode(CFG) == "local"
    chat_mode.set_mode("cloud", CFG)
    assert chat_mode.get_mode(CFG) == "cloud"


def test_bulut_ayarli_degilse_cloud_istenemez_ve_yazilmaz():
    with pytest.raises(ValueError, match="ayarlı değil"):
        chat_mode.set_mode("cloud", LOCAL_CFG)
    assert not (config.DATA / "chat_mode.json").exists()
    with pytest.raises(ValueError):
        chat_mode.set_mode("karisik", CFG)


def test_bozuk_dosya_varsayilana_doner():
    config.DATA.mkdir(parents=True, exist_ok=True)
    (config.DATA / "chat_mode.json").write_text("{bozuk", encoding="utf-8")
    assert chat_mode.get_mode(CFG) == "cloud"


def test_etiket():
    assert chat_mode.label(CLOUD) == "Gemini 2.5 Pro"


# ---- ollama_tools_chat
def test_yerel_modda_bulut_hic_cagrilmaz(monkeypatch):
    chat_mode.set_mode("local", CFG)
    monkeypatch.setattr(providers, "chat", lambda *a, **k: pytest.fail("yerel modda bulut çağrıldı"))
    assert chat.ollama_tools_chat(MSGS, CFG)["content"] == "yerel cevap"
    assert chat_mode.last_turn() == {"model": "ollama:qwen3:14b"}


def test_bulut_modunda_bulut_cevaplar(monkeypatch):
    calls = []
    monkeypatch.setattr(providers, "chat", cloud_ok(calls))
    monkeypatch.setattr(llm, "_http", lambda *a: pytest.fail("yerel çağrılmamalı"))
    assert chat.ollama_tools_chat(MSGS, CFG)["content"] == "bulut cevap" and calls == [CLOUD]
    assert chat_mode.last_turn() == {"model": CLOUD}


def test_hassas_icerik_yerele(monkeypatch):
    monkeypatch.setattr(providers, "chat", lambda *a, **k: pytest.fail("hassas içerik buluta gitti"))
    msgs = MSGS[:1] + [{"role": "user", "content": "IBAN numaram TR33 0006 1005 1978 6457 8413 26"}]
    assert chat.ollama_tools_chat(msgs, CFG)["content"] == "yerel cevap"
    assert chat_mode.last_turn() == {"model": "ollama:qwen3:14b", "reason": "hassas içerik"}


def test_siki_profil_yerele(monkeypatch):
    monkeypatch.setattr(chat, "_perm", lambda a: a == "bulut")
    monkeypatch.setattr(providers, "chat", lambda *a, **k: pytest.fail("sıkı profilde bulut"))
    chat.ollama_tools_chat(MSGS, CFG)
    assert chat_mode.last_turn()["reason"] == "izin profili (sıkı)"


@pytest.mark.parametrize("err,kisa", [
    (providers.ProviderError("gemini", 429, "quota"), "kota"),
    (providers.ProviderError("gemini", 503, "x"), "sunucu"),
    (providers.ProviderError("gemini", 0, "API anahtarı yok: GEMINI_API_KEY"), "anahtar"),
    (providers.ProviderError("gemini", 0, "yanıt okunamadı"), "ağ"),
    (usage.BudgetExceeded("günlük bütçe doldu: $2.00 / $2.00"), "bütçe"),
])
def test_bulut_hatasinda_yerele_duser_ve_bildirir(monkeypatch, err, kisa):
    def boom(*a, **k):
        raise err
    monkeypatch.setattr(providers, "chat", boom)
    assert chat.ollama_tools_chat(MSGS, CFG)["content"] == "yerel cevap"
    info = chat_mode.last_turn()
    assert info["fallback"] is True and kisa in info["reason"] and info["model"] == "ollama:qwen3:14b"


def test_fallback_kapaliysa_hata_yukselir(monkeypatch):
    def boom(*a, **k):
        raise providers.ProviderError("gemini", 429, "quota")
    monkeypatch.setattr(providers, "chat", boom)
    with pytest.raises(providers.ProviderError):
        chat.ollama_tools_chat(MSGS, {**CFG, "fallback_to_local": False})


def test_butce_asimi_gercek_kontrol(monkeypatch):
    monkeypatch.setattr(providers, "api_key", lambda *a, **k: "k")
    monkeypatch.setattr(usage, "spent_today", lambda: 5.0)
    monkeypatch.setattr(providers, "_open", lambda *a, **k: pytest.fail("bütçe aşıldı, istek atılmamalı"))
    assert chat.ollama_tools_chat(MSGS, CFG)["content"] == "yerel cevap"
    assert "bütçe" in chat_mode.last_turn()["reason"]


# ---- respond: bildirim ve model meta
def test_respond_bildirim_ve_model(monkeypatch):
    def boom(*a, **k):
        raise providers.ProviderError("gemini", 429, "quota")
    monkeypatch.setattr(providers, "chat", boom)
    monkeypatch.setattr(chat, "retrieve", lambda t, budget=14000: ("", ""))
    out = chat.respond(chat.Session(), "selam", chat.ollama_tools_chat)
    assert out["reply"].startswith("Bulut modeli yanıt vermedi, bu tur yerel modelle cevaplandı: kota")
    assert out["model"]["fallback"] and out["model"]["model"] == "ollama:qwen3:14b"


def test_respond_bulut_model_meta(monkeypatch):
    monkeypatch.setattr(providers, "chat", cloud_ok([]))
    monkeypatch.setattr(chat, "retrieve", lambda t, budget=14000: ("", ""))
    out = chat.respond(chat.Session(), "selam", chat.ollama_tools_chat)
    assert out["reply"] == "bulut cevap" and out["model"] == {"model": CLOUD}


# ---- API
def call(method, path, data=None, remote=False, respond=None):
    r = webroutes.find(method, path)
    assert r is not None, path
    if r.local_only and remote:                      # sunucu (chat.py _v2_inner) telefonu burada reddeder
        return 403, {"error": "yalniz bilgisayardan"}
    ctx = Ctx(method, path, data or {}, {}, b"", "", "x", remote, chat.Session(), respond)
    code, body, _, _ = webroutes.call(r, ctx)
    return code, json.loads(body)


def test_api_durum_ve_degistirme():
    code, st = call("GET", "/api/v2/chat/mode")
    assert code == 200 and st["mode"] == "cloud" and st["cloud_model"] == CLOUD and st["local_model"] == "qwen3:14b"
    assert st["cloud_available"] is True and set(st["budget"]) == {"today_usd", "limit_usd"} and st["budget"]["limit_usd"] == 2
    code, st = call("POST", "/api/v2/chat/mode", {"mode": "local"})
    assert code == 200 and st["mode"] == "local" and st["why_local"]
    assert call("GET", "/api/v2/chat/mode")[1]["mode"] == "local"
    assert call("POST", "/api/v2/chat/mode", {"mode": "x"})[0] == 400


def test_api_telefon_da_degistirebilir():
    assert webroutes.find("POST", "/api/v2/chat/mode").local_only is False
    code, st = call("POST", "/api/v2/chat/mode", {"mode": "local"}, remote=True)
    assert code == 200 and st["mode"] == "local" and chat_mode.get_mode(CFG) == "local"
    assert call("GET", "/api/v2/chat/mode", remote=True)[0] == 200


def test_sunucu_telefon_kapisi(tmp_path):
    """Gerçek telefon kapısı: eşlenmemiş istek reddedilir; eşlenmiş cihaz (çerez + X-SB + Origin) modu değiştirir."""
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer
    a = chat.RemoteAuth(tmp_path / "t.json")
    a.ip = "127.0.0.1"
    srv = ThreadingHTTPServer(("127.0.0.1", 0), chat.make_handler(chat_fn=lambda m, c: {"content": "ok"}, auth=a, is_remote=True))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"

    def req(path, body=None, headers=None):
        h = {"Content-Type": "application/json", "X-SB": "1", "Origin": base, **(headers or {})}
        r = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, resp.read(), resp.headers
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers
    try:
        assert req("/api/v2/chat/mode", {"mode": "local"})[0] == 401                       # eşlenmemiş: reddedilir
        assert chat_mode.get_mode(CFG) == "cloud"
        code, _, hdr = req("/api/pair", {"pin": a.pin})
        cookie = hdr["Set-Cookie"].split(";")[0]
        assert code == 200 and cookie.startswith("sbs=")
        assert req("/api/v2/chat/mode", {"mode": "local"}, {"Origin": "http://evil.example", "Cookie": cookie})[0] == 403     # yabancı Origin
        assert req("/api/v2/chat/mode", {"mode": "local"}, {"X-SB": "", "Cookie": cookie})[0] == 403                          # X-SB yok
        code, body, _ = req("/api/v2/chat/mode", {"mode": "local"}, {"Cookie": cookie})                                       # eşlenmiş cihaz
        assert code == 200 and json.loads(body)["mode"] == "local" and chat_mode.get_mode(CFG) == "local"
    finally:
        srv.shutdown()


def test_api_bulut_ayarli_degil(monkeypatch):
    monkeypatch.setattr(llm, "config", lambda: LOCAL_CFG)
    code, st = call("GET", "/api/v2/chat/mode")
    assert st["mode"] == "local" and st["why_local"] == "bulut modeli ayarlı değil" and st["cloud_model"] == ""
    code, out = call("POST", "/api/v2/chat/mode", {"mode": "cloud"})
    assert code == 400 and "ayarlı değil" in out["error"]


def test_sohbet_kaydina_model_yazilir():
    def respond(text):
        return {"reply": "merhaba", "trace": [], "proposals": [], "model": {"model": CLOUD}}
    code, out = call("POST", "/api/v2/chat", {"sid": "abcdef12", "text": "selam"}, respond=respond)
    assert code == 200 and out["reply"]["model"] == {"model": CLOUD}


# ---- CLI
def test_cli(capsys):
    from sb.__main__ import main
    assert main(["chat-mode", "local"]) == 0
    assert "qwen3:14b · yerel" in capsys.readouterr().out
    assert main(["chat-mode", "cloud"]) == 0
    assert "Gemini 2.5 Pro · bulut" in capsys.readouterr().out
    assert main(["chat-mode"]) == 0
    assert "Bugünkü harcama" in capsys.readouterr().out


def test_cli_bulut_ayarli_degil(monkeypatch, capsys):
    from sb.__main__ import main
    monkeypatch.setattr(llm, "config", lambda: LOCAL_CFG)
    assert main(["chat-mode", "cloud"]) == 1
    assert "ayarlı değil" in capsys.readouterr().err
