"""Maliyet kaydı, bütçe sınırı, özet ve gömme istek şekli. Ağ yok; gerçek ~/.secondbrain'e yazılmaz."""
import io
import json
import urllib.request

import pytest

from sb import providers, usage

KEY = "sk-gizli-123"


class Resp:
    def __init__(self, data: dict):
        self.data = json.dumps(data).encode()

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(usage, "FILE", tmp_path / "usage.jsonl")
    monkeypatch.setattr(usage, "WARN_FILE", tmp_path / "usage_warn.json")
    cfg = {"budget": {"monthly_usd": 10, "daily_usd": 2, "warn_at": 0.8}}
    monkeypatch.setattr(usage, "_cfg", lambda: cfg)
    monkeypatch.setattr(providers, "_cfg", lambda: cfg)
    toasts = []
    monkeypatch.setattr("sb.actions.toast", lambda t, b: toasts.append(b))
    for k in ("OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(k, KEY)
    monkeypatch.setattr(providers, "_keyring_get", lambda n: None)
    env.cfg, env.toasts = cfg, toasts
    return env


@pytest.fixture
def net(monkeypatch):
    class N:
        reply, reqs = {}, []
    N.reqs = []

    def fake(req, timeout=0):
        N.reqs.append(req)
        return Resp(N.reply)
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return N


def test_kayit_ve_maliyet(env):
    r = usage.record("openai", "gpt-5-mini", 1_000_000, 500_000, task="inbox")
    assert r["cost_usd"] == pytest.approx(0.25 + 1.0)
    row = json.loads(usage.FILE.read_text(encoding="utf-8").splitlines()[0])
    assert set(row) == {"ts", "provider", "model", "in", "out", "cost_usd", "task"} and row["task"] == "inbox"
    assert usage.cost("anthropic", "claude-sonnet-5-5-20260101", 1000, 1000) == pytest.approx(0.018)  # önek eşleşmesi


def test_yerel_sifir_ama_kayitli(env):
    r = usage.record("ollama", "qwen3:14b", 100, 50)
    assert r["cost_usd"] == 0.0 and len(usage.rows()) == 1


def test_bilinmeyen_model_none(env):
    assert usage.record("openai", "gizemli-model", 10, 10)["cost_usd"] is None
    assert "fiyat bilinmiyor" in usage.summary()


def test_config_fiyati_ezer(env):
    env.cfg["prices"] = {"gizemli-model": [1.0, 2.0]}
    assert usage.cost("openai", "gizemli-model", 1_000_000, 1_000_000) == pytest.approx(3.0)


def test_gunluk_butce_asimi(env):
    usage.record("openai", "gpt-5", 0, 200_000)          # $2.00
    with pytest.raises(usage.BudgetExceeded):
        usage.check("openai")
    usage.check("ollama")                                 # yerelde asla


def test_aylik_butce_asimi(env):
    env.cfg["budget"]["daily_usd"] = 0
    usage.record("openai", "gpt-5", 0, 1_000_000)        # $10
    with pytest.raises(usage.BudgetExceeded, match="aylık"):
        usage.check("openai")
    usage.check("lmstudio")


def test_uyari_gunde_bir_kez(env):
    usage.record("openai", "gpt-5", 0, 170_000)          # $1.70 = günlük %85
    usage.check("openai")
    usage.check("openai")
    assert len(env.toasts) == 1
    usage.WARN_FILE.write_text(json.dumps({"day": "2000-01-01"}), encoding="utf-8")
    usage.check("openai")
    assert len(env.toasts) == 2


def test_summary_bicimi(env):
    usage.record("openai", "gpt-5-mini", 1000, 2000, task="inbox")
    usage.record("ollama", "qwen3:14b", 500, 100, task="flush")
    s = usage.summary(30)
    assert "openai:gpt-5-mini" in s and "inbox" in s and "ollama:qwen3:14b" in s
    assert "Toplam: $" in s and "Bugün:" in s and "/ $2.00" in s and "Bu ay:" in s and "/ $10.00" in s


def test_chat_kayit_ve_butce(env, net):
    net.reply = {"choices": [{"message": {"content": "tamam"}}], "usage": {"prompt_tokens": 100, "completion_tokens": 20}}
    providers.chat("openai:gpt-5-mini", [{"role": "user", "content": "x"}], task="deneme")
    row = usage.rows()[0]
    assert (row["in"], row["out"], row["task"]) == (100, 20, "deneme")
    usage.record("openai", "gpt-5", 0, 200_000)
    n = len(net.reqs)
    with pytest.raises(usage.BudgetExceeded):
        providers.chat("openai:gpt-5-mini", [{"role": "user", "content": "x"}])
    assert len(net.reqs) == n                             # çağrı hiç yapılmadı


def _hdr(req, name):
    return {k.lower(): v for k, v in req.header_items()}.get(name.lower())


def test_embed_ollama(env, net):
    net.reply = {"embeddings": [[0.1, 0.2], [0.3, 0.4]], "prompt_eval_count": 7}
    assert providers.embed("ollama:nomic-embed-text", ["a", "b"]) == [[0.1, 0.2], [0.3, 0.4]]
    req = net.reqs[0]
    assert req.full_url.endswith("/api/embed")
    assert json.loads(req.data) == {"model": "nomic-embed-text", "input": ["a", "b"]}
    assert usage.rows()[0]["in"] == 7 and usage.rows()[0]["cost_usd"] == 0.0


def test_embed_openai(env, net):
    net.reply = {"data": [{"index": 1, "embedding": [2.0]}, {"index": 0, "embedding": [1.0]}], "usage": {"prompt_tokens": 5}}
    assert providers.embed("openai:text-embedding-3-small", ["a", "b"]) == [[1.0], [2.0]]
    req = net.reqs[0]
    assert req.full_url == "https://api.openai.com/v1/embeddings"
    assert json.loads(req.data) == {"model": "text-embedding-3-small", "input": ["a", "b"]}
    assert _hdr(req, "Authorization") == f"Bearer {KEY}"
    assert usage.rows()[0]["in"] == 5 and usage.rows()[0]["cost_usd"] is not None


def test_embed_gemini_anahtar_basliktadir(env, net):
    net.reply = {"embeddings": [{"values": [0.5, 0.6]}]}
    assert providers.embed("gemini:text-embedding-004", ["merhaba"]) == [[0.5, 0.6]]
    req = net.reqs[0]
    assert req.full_url.endswith("/models/text-embedding-004:batchEmbedContents")
    assert KEY not in req.full_url and "key=" not in req.full_url
    assert _hdr(req, "x-goog-api-key") == KEY
    body = json.loads(req.data)["requests"][0]
    assert body["model"] == "models/text-embedding-004" and body["content"]["parts"][0]["text"] == "merhaba"
    assert usage.rows()[0]["in"] == len("merhaba") // 4     # sağlayıcı sayaç dönmedi: tahmin


def test_embed_anthropic_hata(env, net):
    with pytest.raises(providers.ProviderError, match="gömme"):
        providers.embed("anthropic:claude-sonnet-5-5", ["x"])
    assert not net.reqs


def test_embed_bozuk_yanit(env, net):
    net.reply = {"embeddings": []}
    with pytest.raises(providers.ProviderError, match="beklenen biçimde değil"):
        providers.embed("ollama:yok", ["x"])
