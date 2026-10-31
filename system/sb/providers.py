"""Model sağlayıcıları: OpenAI uyumlular, Anthropic, Gemini ve yerel Ollama için tek arayüz.

`chat("openai:gpt-5-mini", mesajlar, tools=...)` her sağlayıcıda aynı (Ollama) biçimde döner:
{"content", "tool_calls": [{"function": {"name", "arguments": dict}}], "usage": {"input", "output"}, "provider", "model"}.
Mesajlar ve araçlar Ollama/OpenAI biçiminde verilir; sağlayıcıya çevrilir. Yalnız standart kütüphane.
API anahtarı ASLA hata mesajına, loga ya da çıktıya yazılmaz.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Iterator

THINK_RE = re.compile(r"<think>.*?</think>", re.S)

# kind: openai (OpenAI uyumlu /chat/completions) | anthropic | gemini | ollama
PROVIDERS: dict[str, dict] = {
    "openai": {"kind": "openai", "base_url": "https://api.openai.com/v1", "env": "OPENAI_API_KEY"},
    "openrouter": {"kind": "openai", "base_url": "https://openrouter.ai/api/v1", "env": "OPENROUTER_API_KEY"},
    "groq": {"kind": "openai", "base_url": "https://api.groq.com/openai/v1", "env": "GROQ_API_KEY"},
    "deepseek": {"kind": "openai", "base_url": "https://api.deepseek.com/v1", "env": "DEEPSEEK_API_KEY"},
    "mistral": {"kind": "openai", "base_url": "https://api.mistral.ai/v1", "env": "MISTRAL_API_KEY"},
    "lmstudio": {"kind": "openai", "base_url": "http://localhost:1234/v1", "env": None},
    "llamacpp": {"kind": "openai", "base_url": "http://localhost:8080/v1", "env": None},
    "vllm": {"kind": "openai", "base_url": "http://localhost:8000/v1", "env": None},
    "anthropic": {"kind": "anthropic", "base_url": "https://api.anthropic.com/v1", "env": "ANTHROPIC_API_KEY"},
    "gemini": {"kind": "gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta", "env": "GEMINI_API_KEY"},
    "ollama": {"kind": "ollama", "base_url": "http://localhost:11434", "env": None},
}


class ProviderError(Exception):
    """Sağlayıcı hatası: (sağlayıcı, http kodu — ağ hatasında 0, kısa mesaj). Anahtar içermez."""

    def __init__(self, provider: str, code: int, msg: str):
        self.provider, self.code, self.msg = provider, code, msg
        super().__init__(f"{provider} HTTP {code}: {msg}" if code else f"{provider}: {msg}")


def _cfg() -> dict:
    try:
        from . import llm
        return llm.config() or {}
    except Exception:
        return {}


def table() -> dict[str, dict]:
    """Varsayılan tablo + config/llm.yaml `providers:` ezmeleri (base_url, api_key_env; yeni ad için kind)."""
    cfg = _cfg()
    t = {k: dict(v) for k, v in PROVIDERS.items()}
    if isinstance(cfg.get("ollama"), dict) and cfg["ollama"].get("host"):
        t["ollama"]["base_url"] = cfg["ollama"]["host"]
    for name, over in (cfg.get("providers") or {}).items():
        if not isinstance(over, dict):
            continue
        cur = t.setdefault(name, {"kind": over.get("kind", "openai"), "base_url": "", "env": None})
        if over.get("base_url"):
            cur["base_url"] = str(over["base_url"])
        if "api_key_env" in over:
            cur["env"] = over["api_key_env"] or None
        if over.get("kind"):
            cur["kind"] = over["kind"]
    return t


def split_spec(spec: str) -> tuple[str, str]:
    """"openai:gpt-5-mini" → ("openai", "gpt-5-mini"); model adındaki iki nokta korunur ("ollama:qwen3:14b")."""
    prov, _, model = (spec or "").partition(":")
    if not prov or not model:
        raise ProviderError(prov or "?", 0, f"geçersiz model biçimi '{spec}' (beklenen <sağlayıcı>:<model>)")
    return prov.strip().lower(), model.strip()


def _keyring_get(name: str) -> str | None:
    try:
        import keyring
        from .config import KEYRING_SERVICE
        return keyring.get_password(KEYRING_SERVICE, name)
    except Exception:
        return None


def api_key(provider: str, spec: dict | None = None) -> str | None:
    """Önce ortam değişkeni, sonra keyring (`api-<sağlayıcı>`)."""
    spec = spec or table().get(provider) or {}
    env = spec.get("env")
    return (os.environ.get(env) if env else None) or _keyring_get(f"api-{provider}") or None


def keyless(provider: str, spec: dict) -> bool:
    """Anahtar gerekmeyen sağlayıcı: ollama, lmstudio ve yerel adrese giden her şey."""
    return spec.get("kind") == "ollama" or provider == "lmstudio" or bool(re.match(r"https?://(localhost|127\.0\.0\.1|\[::1\])", spec.get("base_url", "")))


def has_key(provider: str) -> bool:
    spec = table().get(provider)
    return bool(spec) and (keyless(provider, spec) or bool(api_key(provider, spec)))


def _need_key(provider: str, spec: dict) -> str | None:
    key = api_key(provider, spec)
    if not key and not keyless(provider, spec):
        env = spec.get("env") or f"{provider.upper()}_API_KEY"
        raise ProviderError(provider, 0, f"API anahtarı yok: {env} ortam değişkeni ya da `sb set-secret api-{provider}`")
    return key


# ---------------------------------------------------------------- mesaj / araç çevirileri

def _args(a) -> dict:
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except json.JSONDecodeError:
            return {}
    return a if isinstance(a, dict) else {}


class _Ids:
    """Araç çağrılarına sıralı kimlik üretir; `role: tool` mesajlarını ada göre (yoksa sıraya göre) eşler."""

    def __init__(self):
        self.n, self.pending = 0, []

    def issue(self, name: str) -> str:
        self.n += 1
        cid = f"call_{self.n}"
        self.pending.append((cid, name))
        return cid

    def take(self, name: str | None) -> str:
        for i, (cid, nm) in enumerate(self.pending):
            if not name or nm == name:
                return self.pending.pop(i)[0]
        if self.pending:
            return self.pending.pop(0)[0]
        self.n += 1
        return f"call_{self.n}"


def _calls(m: dict) -> list[tuple[str, dict]]:
    return [((c.get("function") or {}).get("name", "?"), _args((c.get("function") or {}).get("arguments")))
            for c in (m.get("tool_calls") or [])]


def _to_openai(messages: list[dict]) -> list[dict]:
    out, ids = [], _Ids()
    for m in messages:
        role, content = m.get("role"), m.get("content") or ""
        if role == "assistant" and m.get("tool_calls"):
            calls = [{"id": ids.issue(n), "type": "function", "function": {"name": n, "arguments": json.dumps(a, ensure_ascii=False)}}
                     for n, a in _calls(m)]
            out.append({"role": "assistant", "content": content or None, "tool_calls": calls})
        elif role == "tool":
            out.append({"role": "tool", "tool_call_id": ids.take(m.get("tool_name")), "content": content})
        else:
            out.append({"role": role, "content": content})
    return out


def _to_anthropic(messages: list[dict]) -> tuple[str, list[dict]]:
    system, out, ids = [], [], _Ids()
    for m in messages:
        role, content = m.get("role"), m.get("content") or ""
        if role == "system":
            system.append(content)
        elif role == "assistant":
            blocks = ([{"type": "text", "text": content}] if content else [])
            blocks += [{"type": "tool_use", "id": ids.issue(n), "name": n, "input": a} for n, a in _calls(m)]
            out.append({"role": "assistant", "content": blocks or content or " "})
        elif role == "tool":
            block = {"type": "tool_result", "tool_use_id": ids.take(m.get("tool_name")), "content": content}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list) and out[-1]["content"][-1]["type"] == "tool_result":
                out[-1]["content"].append(block)           # ardışık araç sonuçları tek kullanıcı mesajında
            else:
                out.append({"role": "user", "content": [block]})
        else:
            out.append({"role": "user", "content": content})
    return "\n\n".join(system), out


def _to_gemini(messages: list[dict]) -> tuple[str, list[dict]]:
    system, out = [], []
    for m in messages:
        role, content = m.get("role"), m.get("content") or ""
        if role == "system":
            system.append(content)
        elif role == "assistant":
            parts = ([{"text": content}] if content else []) + [{"functionCall": {"name": n, "args": a}} for n, a in _calls(m)]
            out.append({"role": "model", "parts": parts or [{"text": " "}]})
        elif role == "tool":
            part = {"functionResponse": {"name": m.get("tool_name") or "tool", "response": {"result": content}}}
            if out and out[-1]["role"] == "user" and out[-1]["parts"] and "functionResponse" in out[-1]["parts"][-1]:
                out[-1]["parts"].append(part)
            else:
                out.append({"role": "user", "parts": [part]})
        else:
            out.append({"role": "user", "parts": [{"text": content}]})
    return "\n\n".join(system), out


_GEMINI_DROP = {"additionalProperties", "$schema", "$id", "$defs", "definitions", "strict", "default"}


def _gemini_schema(s):
    """Gemini'nin desteklemediği JSON-şema alanlarını ayıklar."""
    if isinstance(s, dict):
        return {k: _gemini_schema(v) for k, v in s.items() if k not in _GEMINI_DROP}
    if isinstance(s, list):
        return [_gemini_schema(v) for v in s]
    return s


def _tool_defs(tools: list[dict]) -> list[dict]:
    return [t.get("function", t) for t in tools]


# ---------------------------------------------------------------- istek kurma

def _build(provider: str, spec: dict, model: str, messages: list[dict], tools, schema, think: bool, stream: bool, key) -> tuple[str, dict, dict]:
    """(url, başlıklar, gövde) — sağlayıcının biçiminde."""
    kind, base = spec["kind"], spec["base_url"].rstrip("/")
    headers = {"Content-Type": "application/json"}
    if kind == "openai":
        body = {"model": model, "messages": _to_openai(messages)}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        if tools:
            body["tools"] = [{"type": "function", "function": f} for f in _tool_defs(tools)]
        if schema:
            body["response_format"] = {"type": "json_schema", "json_schema": {"name": "out", "schema": schema, "strict": False}}
        if think:
            body["reasoning_effort"] = "medium"
        if stream:
            body["stream"] = True
        return f"{base}/chat/completions", headers, body
    if kind == "anthropic":
        system, msgs = _to_anthropic(messages)
        if schema:
            system = (system + "\n\n" if system else "") + ("Yalnız geçerli JSON döndür, başka metin ya da kod bloğu yazma. "
                                                           "JSON şu şemaya uymalı:\n" + json.dumps(schema, ensure_ascii=False))
        headers.update({"x-api-key": key or "", "anthropic-version": "2023-06-01"})
        body = {"model": model, "messages": msgs, "max_tokens": 8192 if think else 4096}
        if system:
            body["system"] = system
        if tools:
            body["tools"] = [{"name": f["name"], "description": f.get("description", ""),
                              "input_schema": f.get("parameters") or {"type": "object", "properties": {}}} for f in _tool_defs(tools)]
        if think:
            body["thinking"] = {"type": "enabled", "budget_tokens": 4000}
        if stream:
            body["stream"] = True
        return f"{base}/messages", headers, body
    if kind == "gemini":
        system, contents = _to_gemini(messages)
        body = {"contents": contents}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if tools:
            decl = []
            for f in _tool_defs(tools):
                d = {"name": f["name"], "description": f.get("description", "")}
                params = _gemini_schema(f.get("parameters") or {})
                if params.get("properties"):                 # boş özellikli şemayı Gemini reddeder
                    d["parameters"] = params
                decl.append(d)
            body["tools"] = [{"functionDeclarations": decl}]
        if schema:
            body["generationConfig"] = {"responseMimeType": "application/json", "responseSchema": _gemini_schema(schema)}
        if key:                                              # anahtar başlıkta: URL'ye (loglara, vekil sunuculara) düşmesin
            headers["x-goog-api-key"] = key
        method = "streamGenerateContent?alt=sse" if stream else "generateContent"
        return f"{base}/models/{model}:{method}", headers, body
    # ollama
    body = {"model": model, "messages": [_ollama_msg(m) for m in messages], "stream": stream, "think": bool(think)}
    if tools:
        body["tools"] = tools
    if schema:
        body["format"] = schema
    opts = {}
    try:
        n = (_cfg().get("ollama") or {}).get("num_ctx")
        if n:
            opts["num_ctx"] = n
    except Exception:
        pass
    if opts:
        body["options"] = opts
    return f"{base}/api/chat", headers, body


def _ollama_msg(m: dict) -> dict:
    out = {"role": m.get("role"), "content": m.get("content") or ""}
    if m.get("tool_calls"):
        out["tool_calls"] = [{"function": {"name": n, "arguments": a}} for n, a in _calls(m)]
    if m.get("tool_name"):
        out["tool_name"] = m["tool_name"]
    return out


# ---------------------------------------------------------------- HTTP

def _redact(text: str, key) -> str:
    text = str(text)
    if key:
        text = text.replace(key, "***")
    return re.sub(r"([?&]key=)[^&\s'\"]+", r"\1***", text)


def _open(provider: str, url: str, headers: dict, body: dict, timeout: int, key):
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        msg = ""
        try:
            raw = e.read().decode("utf-8", "replace")
            try:
                j = json.loads(raw)
                err = j.get("error", j) if isinstance(j, dict) else j
                msg = err.get("message", "") if isinstance(err, dict) else str(err)
            except ValueError:
                msg = raw
        except Exception:
            pass
        raise ProviderError(provider, e.code, _redact((msg or e.reason or "hata").strip(), key)[:200]) from None
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise ProviderError(provider, 0, _redact(getattr(e, "reason", None) or e, key)[:200]) from None


# ---------------------------------------------------------------- yanıt normalizasyonu

def _out(provider: str, model: str, content: str, calls: list, i: int, o: int) -> dict:
    return {"content": THINK_RE.sub("", content or "").strip(), "tool_calls": calls,
            "usage": {"input": int(i or 0), "output": int(o or 0)}, "provider": provider, "model": model}


def _norm(kind: str, provider: str, model: str, d: dict) -> dict:
    if kind == "openai":
        msg = ((d.get("choices") or [{}])[0].get("message")) or {}
        calls = [{"function": {"name": (c.get("function") or {}).get("name", ""), "arguments": _args((c.get("function") or {}).get("arguments"))}}
                 for c in (msg.get("tool_calls") or [])]
        u = d.get("usage") or {}
        return _out(provider, model, msg.get("content") or "", calls, u.get("prompt_tokens"), u.get("completion_tokens"))
    if kind == "anthropic":
        text, calls = [], []
        for b in d.get("content") or []:
            if b.get("type") == "text":
                text.append(b.get("text", ""))
            elif b.get("type") == "tool_use":
                calls.append({"function": {"name": b.get("name", ""), "arguments": b.get("input") or {}}})
        u = d.get("usage") or {}
        return _out(provider, model, "".join(text), calls, u.get("input_tokens"), u.get("output_tokens"))
    if kind == "gemini":
        parts = (((d.get("candidates") or [{}])[0].get("content")) or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if "text" in p and not p.get("thought"))
        calls = [{"function": {"name": p["functionCall"].get("name", ""), "arguments": p["functionCall"].get("args") or {}}}
                 for p in parts if "functionCall" in p]
        u = d.get("usageMetadata") or {}
        return _out(provider, model, text, calls, u.get("promptTokenCount"), u.get("candidatesTokenCount"))
    msg = d.get("message") or {}
    calls = [{"function": {"name": (c.get("function") or {}).get("name", ""), "arguments": _args((c.get("function") or {}).get("arguments"))}}
             for c in (msg.get("tool_calls") or [])]
    return _out(provider, model, msg.get("content") or "", calls, d.get("prompt_eval_count"), d.get("eval_count"))


def chat(spec: str, messages: list[dict], tools: list[dict] | None = None, schema: dict | None = None,
         think: bool = False, timeout: int = 600, stream: bool = False, task: str = "") -> dict:
    """Tek tur sohbet. `stream=True`: yanıt akışla toplanıp aynı biçimde döner (araç çağrısı döndürmez).

    Bulutta çağrıdan önce bütçe denetlenir (`usage.BudgetExceeded`); başarılı dönüşte kullanım kaydedilir."""
    provider, model = split_spec(spec)
    ps = table().get(provider)
    if not ps:
        raise ProviderError(provider, 0, f"bilinmeyen sağlayıcı (tanımlılar: {', '.join(sorted(table()))})")
    if stream:
        text = "".join(stream_text(spec, messages, timeout, schema=schema, think=think, task=task))
        return _out(provider, model, text, [], 0, 0)
    key = _need_key(provider, ps)
    _budget(provider)
    url, headers, body = _build(provider, ps, model, messages, tools, schema, think, False, key)
    try:
        with _open(provider, url, headers, body, timeout, key) as r:
            data = json.loads(r.read())
    except ProviderError:
        raise
    except (OSError, ValueError) as e:
        raise ProviderError(provider, 0, _redact(f"yanıt okunamadı: {e}", key)[:200]) from None
    out = _norm(ps["kind"], provider, model, data)
    _record(provider, model, out["usage"]["input"], out["usage"]["output"], task)
    return out


# ---------------------------------------------------------------- akış

def _delta(kind: str, line: str) -> str:
    """Akıştaki tek satırdan metin parçası ('' = parça yok)."""
    if kind == "ollama":
        try:
            return (json.loads(line).get("message") or {}).get("content") or ""
        except ValueError:
            return ""
    if not line.startswith("data:"):
        return ""
    payload = line[5:].strip()
    if not payload or payload == "[DONE]":
        return ""
    try:
        d = json.loads(payload)
    except ValueError:
        return ""
    if kind == "openai":
        ch = d.get("choices") or []
        return ((ch[0].get("delta") or {}).get("content") or "") if ch else ""
    if kind == "anthropic":
        if d.get("type") == "content_block_delta" and (d.get("delta") or {}).get("type") == "text_delta":
            return d["delta"].get("text", "")
        return ""
    parts = (((d.get("candidates") or [{}])[0].get("content")) or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


def stream_text(spec: str, messages: list[dict], timeout: int = 600, schema: dict | None = None, think: bool = False,
                task: str = "") -> Iterator[str]:
    """Metni parça parça verir (OpenAI/Anthropic/Gemini SSE, Ollama satır başı JSON)."""
    provider, model = split_spec(spec)
    ps = table().get(provider)
    if not ps:
        raise ProviderError(provider, 0, "bilinmeyen sağlayıcı")
    key = _need_key(provider, ps)
    _budget(provider)
    url, headers, body = _build(provider, ps, model, messages, None, schema, think, True, key)
    if ps["kind"] != "ollama":
        headers["Accept"] = "text/event-stream"
    with _open(provider, url, headers, body, timeout, key) as r:
        n_out = 0
        try:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if line and (piece := _delta(ps["kind"], line)):
                    n_out += len(piece)
                    yield piece
        except ProviderError:
            raise
        except (OSError, ValueError) as e:
            raise ProviderError(provider, 0, _redact(f"akış kesildi: {e}", key)[:200]) from None
        else:                                                # akış sağlayıcıdan sayaç gelmez: karakter/4 tahmini
            _record(provider, model, sum(len(m.get("content") or "") for m in messages) // 4, n_out // 4, task)


# ---------------------------------------------------------------- maliyet kancaları

def _budget(provider: str) -> None:
    from . import usage
    usage.check(provider)


def _record(provider: str, model: str, i: int, o: int, task: str = "") -> None:
    try:
        from . import usage
        usage.record(provider, model, i, o, task)
    except Exception:
        pass


# ---------------------------------------------------------------- gömme (embedding)

def _embed_build(provider: str, ps: dict, model: str, texts: list[str], key) -> tuple[str, dict, dict]:
    kind, base = ps["kind"], ps["base_url"].rstrip("/")
    headers = {"Content-Type": "application/json"}
    if kind == "ollama":
        return f"{base}/api/embed", headers, {"model": model, "input": texts}
    if kind == "openai":
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return f"{base}/embeddings", headers, {"model": model, "input": texts}
    if kind == "gemini":
        if key:
            headers["x-goog-api-key"] = key                  # URL'de değil
        reqs = [{"model": f"models/{model}", "content": {"parts": [{"text": t}]}} for t in texts]
        return f"{base}/models/{model}:batchEmbedContents", headers, {"requests": reqs}
    raise ProviderError(provider, 0, "bu sağlayıcı gömme (embedding) sunmuyor; ollama:, openai: ya da gemini: bir model seç")


def embed(spec: str, texts: list[str], timeout: int = 120, task: str = "embed") -> list[list[float]]:
    """Metinleri gömer: `ollama:<m>` (/api/embed), `openai:<m>` ve uyumlular (/embeddings), `gemini:<m>` (batchEmbedContents)."""
    provider, model = split_spec(spec)
    ps = table().get(provider)
    if not ps:
        raise ProviderError(provider, 0, f"bilinmeyen sağlayıcı (tanımlılar: {', '.join(sorted(table()))})")
    if not texts:
        return []
    if ps["kind"] == "anthropic":
        _embed_build(provider, ps, model, texts, None)       # anlaşılır hatayı fırlatır
    key = _need_key(provider, ps)
    _budget(provider)
    url, headers, body = _embed_build(provider, ps, model, texts, key)
    try:
        with _open(provider, url, headers, body, timeout, key) as r:
            d = json.loads(r.read())
    except ProviderError:
        raise
    except (OSError, ValueError) as e:
        raise ProviderError(provider, 0, _redact(f"yanıt okunamadı: {e}", key)[:200]) from None
    kind = ps["kind"]
    if kind == "ollama":
        vecs, used = d.get("embeddings"), d.get("prompt_eval_count")
    elif kind == "openai":
        vecs = [x.get("embedding") for x in sorted(d.get("data") or [], key=lambda x: x.get("index", 0))]
        used = (d.get("usage") or {}).get("prompt_tokens")
    else:
        vecs, used = [x.get("values") for x in d.get("embeddings") or []], None
    if not isinstance(vecs, list) or len(vecs) != len(texts) or not all(isinstance(v, list) and v for v in vecs):
        raise ProviderError(provider, 0, f"gömme yanıtı beklenen biçimde değil (model '{model}' gömme destekliyor mu / indirildi mi?)")
    _record(provider, model, used if used else sum(len(t) for t in texts) // 4, 0, task)
    return vecs
