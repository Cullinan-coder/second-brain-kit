"""Sağlayıcı katmanı: istek şekli, yanıt normalizasyonu, akış, hata ve anahtar güvenliği. Ağ çağrısı yok."""
import io
import json
import urllib.error
import urllib.request

import pytest

from sb import chat, llm, providers

KEY = "sk-gizli-123"
TOOLS = [{"type": "function", "function": {"name": "brain_search", "description": "ara",
          "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
         {"type": "function", "function": {"name": "brain_overview", "description": "genel",
          "parameters": {"type": "object", "properties": {}}}}]
MSGS = [{"role": "system", "content": "Sistem"}, {"role": "user", "content": "Merhaba"}]
SCHEMA = {"type": "object", "properties": {"a": {"type": "string"}}, "additionalProperties": False}


class Resp:
    def __init__(self, data: bytes):
        self.data = data

    def read(self):
        return self.data

    def __iter__(self):
        return iter(io.BytesIO(self.data).readlines())

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def net(monkeypatch):
    """urlopen taklidi: net.reply = bayt/sözlük; net.reqs = yakalanan istekler."""
    class N:
        reqs: list = []
        reply = b"{}"
        error = None

        def body(self, i=-1):
            return json.loads(self.reqs[i].data)
    n = N()
    n.reqs = []

    def fake(req, timeout=None):
        n.reqs.append(req)
        if n.error:
            raise n.error
        return Resp(n.reply if isinstance(n.reply, bytes) else json.dumps(n.reply).encode())
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    monkeypatch.setattr(providers, "_cfg", lambda: {})
    for env in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY",
                "DEEPSEEK_API_KEY", "MISTRAL_API_KEY"):
        monkeypatch.delenv(env, raising=False)
    monkeypatch.setattr(providers, "_keyring_get", lambda name: None)
    return n


OPENAI_CALL = {"choices": [{"message": {"content": "", "tool_calls": [
    {"id": "c1", "type": "function", "function": {"name": "brain_search", "arguments": "{\"query\": \"x\"}"}}]}}],
    "usage": {"prompt_tokens": 11, "completion_tokens": 5}}


@pytest.mark.parametrize("prov,url", [
    ("openai", "https://api.openai.com/v1/chat/completions"),
    ("openrouter", "https://openrouter.ai/api/v1/chat/completions"),
    ("groq", "https://api.groq.com/openai/v1/chat/completions"),
    ("deepseek", "https://api.deepseek.com/v1/chat/completions"),
    ("mistral", "https://api.mistral.ai/v1/chat/completions"),
])
def test_openai_uyumlular(net, monkeypatch, prov, url):
    monkeypatch.setenv(providers.PROVIDERS[prov]["env"], KEY)
    net.reply = OPENAI_CALL
    out = providers.chat(f"{prov}:m-1", MSGS, tools=TOOLS)
    req = net.reqs[0]
    assert req.full_url == url and req.get_header("Authorization") == f"Bearer {KEY}"
    b = net.body()
    assert b["model"] == "m-1" and b["messages"][0] == {"role": "system", "content": "Sistem"}
    assert b["tools"][0] == {"type": "function", "function": TOOLS[0]["function"]}
    assert out == {"content": "", "tool_calls": [{"function": {"name": "brain_search", "arguments": {"query": "x"}}}],
                   "usage": {"input": 11, "output": 5}, "provider": prov, "model": "m-1"}


def test_lmstudio_anahtarsiz(net):
    net.reply = {"choices": [{"message": {"content": "selam"}}]}
    out = providers.chat("lmstudio:yerel-model", MSGS)
    assert net.reqs[0].full_url == "http://localhost:1234/v1/chat/completions"
    assert net.reqs[0].get_header("Authorization") is None
    assert out["content"] == "selam" and out["tool_calls"] == [] and out["usage"] == {"input": 0, "output": 0}


def test_openai_sema_think_ve_arac_sonucu(net, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    net.reply = {"choices": [{"message": {"content": "{}"}}]}
    msgs = MSGS + [{"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "brain_search", "arguments": {"query": "x"}}}]},
                   {"role": "tool", "tool_name": "brain_search", "content": "sonuç"}]
    providers.chat("openai:gpt-5-mini", msgs, schema=SCHEMA, think=True)
    b = net.body()
    assert b["response_format"] == {"type": "json_schema", "json_schema": {"name": "out", "schema": SCHEMA, "strict": False}}
    assert b["reasoning_effort"] == "medium"
    asst, tool = b["messages"][2], b["messages"][3]
    assert asst["tool_calls"][0]["function"]["arguments"] == "{\"query\": \"x\"}"          # OpenAI: arguments metin
    assert tool == {"role": "tool", "tool_call_id": asst["tool_calls"][0]["id"], "content": "sonuç"}


def test_anthropic(net, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", KEY)
    net.reply = {"content": [{"type": "text", "text": "önce"}, {"type": "tool_use", "id": "t1", "name": "brain_search", "input": {"query": "q"}}],
                 "usage": {"input_tokens": 7, "output_tokens": 3}}
    msgs = MSGS + [{"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "brain_search", "arguments": {"query": "x"}}},
                                                                      {"function": {"name": "brain_overview", "arguments": {}}}]},
                   {"role": "tool", "tool_name": "brain_search", "content": "r1"}, {"role": "tool", "tool_name": "brain_overview", "content": "r2"}]
    out = providers.chat("anthropic:claude-x", msgs, tools=TOOLS, schema=SCHEMA, think=True)
    req, b = net.reqs[0], net.body()
    assert req.full_url == "https://api.anthropic.com/v1/messages"
    assert req.get_header("X-api-key") == KEY and req.get_header("Anthropic-version") == "2023-06-01"
    assert b["system"].startswith("Sistem") and "JSON" in b["system"] and "properties" in b["system"]
    assert b["thinking"] == {"type": "enabled", "budget_tokens": 4000} and b["max_tokens"] > 4000
    assert b["tools"][0] == {"name": "brain_search", "description": "ara", "input_schema": TOOLS[0]["function"]["parameters"]}
    assert b["messages"][1]["content"][0]["type"] == "tool_use"
    results = b["messages"][2]["content"]                                                 # iki sonuç tek kullanıcı mesajında
    assert [r["type"] for r in results] == ["tool_result", "tool_result"]
    assert [r["tool_use_id"] for r in results] == [c["id"] for c in b["messages"][1]["content"]]
    assert out["content"] == "önce" and out["tool_calls"] == [{"function": {"name": "brain_search", "arguments": {"query": "q"}}}]
    assert out["usage"] == {"input": 7, "output": 3}


def test_gemini(net, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    net.reply = {"candidates": [{"content": {"parts": [{"text": "cevap"}, {"functionCall": {"name": "brain_search", "args": {"query": "q"}}}]}}],
                 "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 4}}
    msgs = MSGS + [{"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "brain_search", "arguments": {"query": "x"}}}]},
                   {"role": "tool", "tool_name": "brain_search", "content": "r1"}]
    out = providers.chat("gemini:gemini-2.5-flash", msgs, tools=TOOLS, schema=SCHEMA)
    req, b = net.reqs[0], net.body()
    assert req.full_url == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    assert req.get_header("X-goog-api-key") == KEY and KEY not in req.full_url
    assert b["systemInstruction"] == {"parts": [{"text": "Sistem"}]}
    decl = b["tools"][0]["functionDeclarations"]
    assert decl[0]["name"] == "brain_search" and "parameters" in decl[0] and "parameters" not in decl[1]   # boş şema atlanır
    assert b["generationConfig"]["responseMimeType"] == "application/json"
    assert "additionalProperties" not in b["generationConfig"]["responseSchema"]
    assert b["contents"][1] == {"role": "model", "parts": [{"functionCall": {"name": "brain_search", "args": {"query": "x"}}}]}
    assert b["contents"][2] == {"role": "user", "parts": [{"functionResponse": {"name": "brain_search", "response": {"result": "r1"}}}]}
    assert out["content"] == "cevap" and out["tool_calls"][0]["function"]["arguments"] == {"query": "q"}
    assert out["usage"] == {"input": 9, "output": 4}


def test_ollama_yolu(net):
    net.reply = {"message": {"role": "assistant", "content": "<think>iç</think>Selam", "tool_calls": [
        {"function": {"name": "brain_overview", "arguments": {}}}]}, "prompt_eval_count": 5, "eval_count": 2}
    out = providers.chat("ollama:qwen3:14b", MSGS, tools=TOOLS, schema=SCHEMA, think=True)
    b = net.body()
    assert net.reqs[0].full_url == "http://localhost:11434/api/chat" and net.reqs[0].get_header("Authorization") is None
    assert b["model"] == "qwen3:14b" and b["think"] is True and b["stream"] is False and b["format"] == SCHEMA
    assert out["content"] == "Selam" and out["usage"] == {"input": 5, "output": 2}
    assert out["tool_calls"] == [{"function": {"name": "brain_overview", "arguments": {}}}]


def test_config_ile_base_url_ezme(net, monkeypatch):
    monkeypatch.setattr(providers, "_cfg", lambda: {"providers": {"openai": {"base_url": "http://vekil/v1/"}, "lmstudio": {"base_url": "http://pc:1234/v1"}}})
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    net.reply = {"choices": [{"message": {"content": "a"}}]}
    providers.chat("openai:x", MSGS)
    providers.chat("lmstudio:y", MSGS)
    assert [r.full_url for r in net.reqs] == ["http://vekil/v1/chat/completions", "http://pc:1234/v1/chat/completions"]


def test_anahtar_sirasi_ve_keyring(net, monkeypatch):
    monkeypatch.setattr(providers, "_keyring_get", lambda name: "kr-anahtar" if name == "api-groq" else None)
    net.reply = {"choices": [{"message": {"content": "a"}}]}
    providers.chat("groq:m", MSGS)
    assert net.reqs[0].get_header("Authorization") == "Bearer kr-anahtar"
    monkeypatch.setenv("GROQ_API_KEY", "env-anahtar")                                       # ortam değişkeni önce gelir
    providers.chat("groq:m", MSGS)
    assert net.reqs[1].get_header("Authorization") == "Bearer env-anahtar"


def test_anahtar_yok_hatasi(net):
    with pytest.raises(providers.ProviderError) as e:
        providers.chat("anthropic:x", MSGS)
    assert e.value.provider == "anthropic" and "sb set-secret api-anthropic" in str(e.value) and not net.reqs
    with pytest.raises(providers.ProviderError):
        providers.chat("yok:x", MSGS)
    with pytest.raises(providers.ProviderError):
        providers.chat("modelsiz", MSGS)


def test_anahtar_hata_mesajina_gecmez(net, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    net.error = urllib.error.HTTPError("u", 401, "Unauthorized", {}, io.BytesIO(json.dumps({"error": {"message": f"Incorrect API key {KEY}"}}).encode()))
    with pytest.raises(providers.ProviderError) as e:
        providers.chat("openai:x", MSGS)
    assert e.value.code == 401 and KEY not in str(e.value) and KEY not in repr(e.value) and "***" in str(e.value)
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    net.error = urllib.error.URLError(f"bağlanılamadı https://x/y?key={KEY}&a=1")
    with pytest.raises(providers.ProviderError) as e:
        providers.chat("gemini:x", MSGS)
    assert e.value.code == 0 and KEY not in str(e.value)


def test_akis_ayrıstirma(net, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    net.reply = (b'data: {"choices":[{"delta":{"role":"assistant"}}]}\n\ndata: {"choices":[{"delta":{"content":"Mer"}}]}\n\n'
                 b'data: {"choices":[{"delta":{"content":"haba"}}]}\n\ndata: [DONE]\n\n')
    assert list(providers.stream_text("openai:x", MSGS)) == ["Mer", "haba"]
    assert net.body()["stream"] is True

    monkeypatch.setenv("ANTHROPIC_API_KEY", KEY)
    net.reply = (b'event: message_start\ndata: {"type":"message_start"}\n\nevent: content_block_delta\n'
                 b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"A"}}\n\n'
                 b'data: {"type":"content_block_delta","delta":{"type":"input_json_delta","partial_json":"{"}}\n\n'
                 b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"B"}}\n\n')
    assert "".join(providers.stream_text("anthropic:x", MSGS)) == "AB"

    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    net.reply = (b'data: {"candidates":[{"content":{"parts":[{"text":"G"}]}}]}\n\ndata: {"candidates":[{"content":{"parts":[{"text":"M"}]}}]}\n\n')
    assert list(providers.stream_text("gemini:g", MSGS)) == ["G", "M"]
    assert net.reqs[-1].full_url.endswith(":streamGenerateContent?alt=sse") and KEY not in net.reqs[-1].full_url

    net.reply = (b'{"message":{"content":"O"},"done":false}\n{"message":{"content":"l"},"done":false}\n{"message":{"content":""},"done":true}\n')
    assert list(providers.stream_text("ollama:q", MSGS)) == ["O", "l"]
    assert net.body()["stream"] is True


def test_chat_stream_true_toplar(net, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    net.reply = b'data: {"choices":[{"delta":{"content":"a"}}]}\n\ndata: {"choices":[{"delta":{"content":"b"}}]}\n\n'
    out = providers.chat("openai:x", MSGS, stream=True)
    assert out["content"] == "ab" and out["tool_calls"] == [] and out["provider"] == "openai"


# --- llm.complete yönlendirmesi ve asistan

CFG = {"tasks": {"api_gorev": "openai:gpt-x", "sessions": "ollama"}, "fallback_to_local": True,
       "ollama": {"host": "http://x", "model": "qwen3:14b", "num_ctx": 1000, "max_chars": 100}}


def test_complete_saglayici_yonlendirmesi(monkeypatch):
    monkeypatch.setattr(llm, "config", lambda: CFG)
    seen = {}

    def fake_chat(spec, messages, **kw):
        seen.update(spec=spec, messages=messages, **kw)
        return {"content": "api-cevap"}
    monkeypatch.setattr(providers, "chat", fake_chat)
    text, lbl = llm.complete("api_gorev", "soru", schema=SCHEMA, timeout=5)
    assert (text, lbl) == ("api-cevap", "api openai:gpt-x") and not llm.is_local(lbl)
    assert seen["spec"] == "openai:gpt-x" and seen["messages"] == [{"role": "user", "content": "soru"}] and seen["schema"] == SCHEMA


def test_complete_api_hatasinda_yerel_yedek(monkeypatch):
    monkeypatch.setattr(llm, "config", lambda: CFG)
    monkeypatch.setattr(llm, "ollama_chat", lambda prompt, cfg, schema=None, timeout=0: "yerel-cevap")

    def boom(*a, **k):
        raise providers.ProviderError("openai", 429, "rate limit")
    monkeypatch.setattr(providers, "chat", boom)
    text, lbl = llm.complete("api_gorev", "p")
    assert text == "yerel-cevap" and lbl.startswith("yerel qwen3:14b (API yedeği: openai HTTP 429")
    monkeypatch.setattr(llm, "config", lambda: {**CFG, "fallback_to_local": False})
    with pytest.raises(providers.ProviderError):
        llm.complete("api_gorev", "p")


def test_ollama_tools_chat_sağlayıcıya_gider(monkeypatch):
    cfg = {**CFG, "tasks": {**CFG["tasks"], "chat": "anthropic:claude-x"}}
    seen = {}

    def fake_chat(spec, messages, tools=None, think=False, timeout=0, **kw):
        seen.update(spec=spec, tools=tools, think=think)
        return {"content": "x", "tool_calls": [{"function": {"name": "brain_overview", "arguments": {}}}]}
    monkeypatch.setattr(providers, "chat", fake_chat)
    monkeypatch.setattr(llm, "ensure_ollama", lambda c: pytest.fail("Ollama açılmamalı"))
    msg = chat.ollama_tools_chat(MSGS, cfg)
    assert seen["spec"] == "anthropic:claude-x" and seen["tools"] and all(t["function"]["name"] for t in seen["tools"])
    assert msg == {"role": "assistant", "content": "x", "tool_calls": [{"function": {"name": "brain_overview", "arguments": {}}}]}


def test_ollama_tools_chat_varsayilan_ollama(monkeypatch):
    called = {}
    monkeypatch.setattr(llm, "ensure_ollama", lambda c: called.setdefault("up", True))
    monkeypatch.setattr(llm, "_http", lambda host, path, payload, timeout: {"message": {"role": "assistant", "content": "yerel"}})
    monkeypatch.setattr(providers, "chat", lambda *a, **k: pytest.fail("sağlayıcıya gitmemeli"))
    assert chat.ollama_tools_chat(MSGS, CFG)["content"] == "yerel" and called["up"]
