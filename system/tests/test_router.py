"""Faz 0.3: yönlendirici, gizlilik yönlendirmesi, yedek zinciri, önbellek, uzun metin."""
import pytest

from sb import llm, router

CFG = {"tasks": {"ozet": "openai:gpt-5-mini", "derin": "claude", "yerel": "ollama"}, "fallback_to_local": True,
       "ollama": {"model": "qwen3:14b", "max_chars": 9000}}


def test_chain_rules_fallback_and_privacy():
    assert router.chain(CFG, "ozet", "merhaba") == ["openai:gpt-5-mini", "ollama"]
    assert router.chain(CFG, "yerel", "x") == ["ollama"]
    assert router.chain(CFG, "bilinmeyen", "x") == ["claude", "ollama"]
    cfg = dict(CFG, routing=[{"when": {"min_chars": 100}, "use": "gemini:gemini-2.5-flash"},
                             {"when": {"task": ["derin"]}, "use": "anthropic:claude-sonnet-5-5"}],
               fallback={"*": ["groq:llama", "ollama"], "derin": ["lmstudio:qwen"]})
    assert router.chain(cfg, "ozet", "a" * 200) == ["gemini:gemini-2.5-flash", "groq:llama", "ollama"]
    assert router.chain(cfg, "derin", "kısa") == ["anthropic:claude-sonnet-5-5", "lmstudio:qwen"]
    # gizli ya da hassas içerik: bulut hedefleri atılır, yalnız yerel kalır
    assert router.chain(cfg, "derin", "kısa", private=True) == ["lmstudio:qwen"]
    assert router.chain(cfg, "ozet", "IBAN TR12 0006 1005 1978 6457 8413 26 gönder") == ["ollama"]
    assert router.chain(CFG, "derin", "şifrem şu") == ["ollama"]
    assert router.chain(dict(CFG, fallback_to_local=False), "derin", "tc kimlik 12345678901") == ["ollama"]
    assert not router.sensitive("2026-11-02 23:59 teslim, 2 adet ödev") and router.is_local("vllm:x")


def test_complete_uses_chain_labels_and_privacy(monkeypatch):
    calls = []

    def run(cfg, target, prompt, schema, model, timeout, task):
        calls.append(target)
        if target.startswith("openai"):
            raise RuntimeError("openai HTTP 429: kota")
        return f"{target}-cevap", ("yerel qwen3:14b" if target == "ollama" else f"api {target}")
    monkeypatch.setattr(llm, "config", lambda: CFG)
    monkeypatch.setattr(llm, "_run", run)
    text, lbl = llm.complete("ozet", "soru")
    assert text == "ollama-cevap" and lbl.startswith("yerel qwen3:14b (API yedeği: openai HTTP 429") and calls == ["openai:gpt-5-mini", "ollama"]
    calls.clear()
    assert llm.complete("derin", "x", private=True)[0] == "ollama-cevap" and calls == ["ollama"]
    monkeypatch.setattr(llm, "config", lambda: dict(CFG, fallback_to_local=False))
    with pytest.raises(RuntimeError, match="429"):
        llm.complete("ozet", "soru")


def test_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(router, "CACHE_DIR", tmp_path / "c")
    cfg = dict(CFG, cache={"enabled": True, "ttl_days": 1})
    n = []
    monkeypatch.setattr(llm, "config", lambda: cfg)
    monkeypatch.setattr(llm, "_run", lambda c, t, p, s, m, to, task: (n.append(1) or f"cevap{len(n)}", "yerel qwen3:14b"))
    assert llm.complete("yerel", "aynı soru") == ("cevap1", "yerel qwen3:14b")
    assert llm.complete("yerel", "aynı soru") == ("cevap1", "yerel qwen3:14b (önbellek)") and len(n) == 1
    assert llm.complete("yerel", "başka soru")[0] == "cevap2"
    assert not router.cacheable(cfg, "chat") and not router.cacheable(CFG, "yerel")
    assert router.cache_clear() == 2


def test_chunks_and_long_complete(monkeypatch):
    text = "\n\n".join(f"Paragraf {i}: " + "x" * 900 for i in range(30))
    parts = router.chunks(text, 5000, overlap=100)
    assert len(parts) > 1 and all(len(p) <= 5000 for p in parts) and parts[0].startswith("Paragraf 0")
    assert "Paragraf 29" in parts[-1] and router.chunks("kısa", 100) == ["kısa"]
    seen = []
    monkeypatch.setattr(llm, "config", lambda: CFG)
    monkeypatch.setattr(llm, "complete", lambda task, prompt, **k: (seen.append(prompt) or f"özet{len(seen)}", "yerel qwen3:14b"))
    out, lbl = llm.long_complete("worker", "Özetle", text, chunk_chars=5000)
    assert out == f"özet{len(seen)}" and lbl.endswith(f"· {len(seen) - 1} parça") and "ara sonuçlar" in seen[-1]
