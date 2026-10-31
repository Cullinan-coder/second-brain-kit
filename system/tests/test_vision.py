"""Paket C: görüntü uçları. ollama, mss, pypdf ve sağlayıcı ağı taklit edilir."""
import base64
import io
import json
import time
from datetime import datetime

import pytest

from sb import config, features, llm, vault_ops, vision, webroutes
from sb.webroutes import Ctx


def png(w=64, h=32, color="white"):
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (w, h), color).save(b, "PNG")
    return b.getvalue()


def call(method, path, **kw):
    r = webroutes.find(method, path)
    assert r, path
    code, body, ctype, _ = webroutes.call(r, Ctx(method=method, path=path, **kw))
    return code, (json.loads(body) if "json" in ctype else body)


@pytest.fixture
def ollama(monkeypatch):
    sent = []
    monkeypatch.setattr(llm, "ensure_ollama", lambda cfg, wait=60: None)

    def http(host, path, payload, timeout):
        sent.append(payload)
        return {"message": {"content": "<think>x</think>Bir MERHABA yazısı"}}

    monkeypatch.setattr(llm, "_http", http)
    return sent


@pytest.fixture
def vault(monkeypatch, tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    monkeypatch.setattr(vault_ops, "VAULT", v)
    monkeypatch.setattr(vault_ops, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(vault_ops, "commit", lambda paths, msg: "abc123")
    return v


def test_routes_registered():
    for m, p in [("POST", "/api/v2/vision/ask"), ("POST", "/api/v2/vision/ocr"), ("POST", "/api/v2/screen/start"),
                 ("POST", "/api/v2/screen/stop"), ("GET", "/api/v2/screen/status"), ("GET", "/api/v2/screen/summary"),
                 ("POST", "/api/v2/pdf/ask"), ("POST", "/api/v2/image/gen"), ("GET", "/api/v2/image/file")]:
        assert webroutes.find(m, p)
    assert webroutes.find("POST", "/api/v2/screen/start").local_only


def test_describe_and_shrink(ollama):
    assert vision.describe(png(4000, 1000)) == "Bir MERHABA yazısı"
    from PIL import Image
    img = Image.open(io.BytesIO(base64.b64decode(ollama[0]["messages"][0]["images"][0])))
    assert max(img.size) == 2048 and ollama[0]["model"] == llm.config()["ollama"]["vision_model"]


def test_ask_route(ollama):
    code, out = call("POST", "/api/v2/vision/ask", raw=png(), ctype="image/png", query={"q": "Ne yazıyor?"})
    assert code == 200 and out["answer"] == "Bir MERHABA yazısı"
    assert "Ne yazıyor?" in ollama[0]["messages"][0]["content"]


def test_bad_image(ollama):
    assert call("POST", "/api/v2/vision/ask", raw=b"not an image", ctype="image/png", query={"q": "x"})[0] == 400


def test_no_vision_model(monkeypatch):
    cfg = llm.config()
    cfg["ollama"]["vision_model"] = ""
    monkeypatch.setattr(llm, "config", lambda: cfg)
    out = call("POST", "/api/v2/vision/ask", raw=png(), ctype="image/png", query={"q": "x"})[1]
    assert out["available"] is False


def test_ocr_save(ollama, vault):
    code, out = call("POST", "/api/v2/vision/ocr", raw=png(), ctype="image/png", query={"save": "1", "title": "Tahta"})
    assert out["text"] == "Bir MERHABA yazısı" and out["path"] == "00-Inbox/Taramalar/Tahta.md"
    assert "MERHABA" in (vault / out["path"]).read_text(encoding="utf-8")
    assert len(list((config.DATA / "scans").glob("*.png"))) == 1
    out2 = call("POST", "/api/v2/vision/ocr", raw=png(), ctype="image/png")[1]
    assert "path" not in out2 and out2["text"]


def test_screen_watch_lifecycle(monkeypatch, ollama):
    import sb.convstore as cs
    notes = []
    monkeypatch.setattr(cs, "notify", lambda *a, **k: notes.append(a), raising=False)
    monkeypatch.setattr(vision, "_grab", lambda: png())
    code, st = call("POST", "/api/v2/screen/start", data={"interval_s": 5, "minutes": 1})
    assert st["running"] is True
    for _ in range(100):
        if vision._W.frames:
            break
        time.sleep(0.05)
    assert vision._W.frames >= 1
    assert call("GET", "/api/v2/screen/status")[1]["frames"] >= 1
    assert call("POST", "/api/v2/screen/stop", data={})[1]["running"] is False
    f = next((config.DATA / "screen").glob("*.jsonl"))
    assert json.loads(f.read_text(encoding="utf-8").splitlines()[0])["desc"]
    assert not list((config.DATA / "screen").glob("*.png")) and notes


def test_screen_skips_sensitive(monkeypatch):
    monkeypatch.setattr(vision, "_grab", lambda: png())
    monkeypatch.setattr(vision, "describe", lambda b: "şifre kodu 123456 görünüyor")
    vision._W.frames = vision._W.skipped = 0
    vision._watch_once()
    assert vision._W.frames == 0 and vision._W.skipped == 1


def test_screen_auto_stop(monkeypatch):
    monkeypatch.setattr(vision, "_watch_once", lambda: None)
    vision.screen_start(5, 1)
    vision._W.until = time.time() - 1          # süre doldu
    vision._W.stop_ev.set()
    vision._W.thread.join(timeout=5)
    assert vision.screen_status()["running"] is False


def test_screen_summary(monkeypatch):
    assert call("GET", "/api/v2/screen/summary")[1]["count"] == 0
    d = config.DATA / "screen"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{datetime.now():%Y-%m-%d}.jsonl").write_text(json.dumps({"ts": "2026-11-01T10:00:00", "desc": "VS Code açık"}) + "\n",
                                                        encoding="utf-8")
    seen = {}
    monkeypatch.setattr(llm, "complete", lambda t, p, **k: seen.update(k=k) or ("- kod yazıldı", "yerel"))
    out = call("GET", "/api/v2/screen/summary")[1]
    assert out["count"] == 1 and "kod" in out["summary"] and seen["k"]["private"] is True


def _pdf(monkeypatch, vault, pages):
    (vault / "belge.pdf").write_bytes(b"%PDF-fake")
    monkeypatch.setattr(vision, "extract_pages", lambda p: pages)


def test_pdf_ask_cites(monkeypatch, vault):
    _pdf(monkeypatch, vault, ["Giriş bölümü genel bilgi.", "Kira bedeli aylık 5000 TL olarak belirlenmiştir.", "Fesih şartları ve ceza."])
    seen = {}
    monkeypatch.setattr(llm, "complete", lambda t, p, **k: seen.update(p=p) or ("Kira 5000 TL. [s. 2]", "yerel"))
    code, out = call("POST", "/api/v2/pdf/ask", data={"path": "belge.pdf", "q": "Kira bedeli ne kadar?"})
    assert code == 200 and "[s. 2]" in out["answer"]
    p2 = [p for p in out["pages"] if p["page"] == 2][0]
    assert "5000" in p2["snippet"] and "[s. 2]" in seen["p"]


def test_pdf_ask_adds_missing_citation(monkeypatch, vault):
    _pdf(monkeypatch, vault, ["alakasız", "kira bedeli beş bin"])
    monkeypatch.setattr(llm, "complete", lambda *a, **k: ("Beş bin.", "yerel"))
    out = call("POST", "/api/v2/pdf/ask", data={"path": "belge.pdf", "q": "kira bedeli"})[1]
    assert out["answer"].endswith("[s. 2]")


def test_pdf_ask_att_id(monkeypatch, vault):
    d = config.DATA / "uploads" / "att1234"
    d.mkdir(parents=True)
    (d / "x.pdf").write_bytes(b"%PDF")
    monkeypatch.setattr(vision, "extract_pages", lambda p: ["merhaba dünya"])
    monkeypatch.setattr(llm, "complete", lambda *a, **k: ("Selam [s. 1]", "yerel"))
    assert call("POST", "/api/v2/pdf/ask", data={"att_id": "att1234", "q": "merhaba"})[0] == 200


def test_pdf_ask_path_escape(vault, tmp_path):
    (tmp_path / "dis.pdf").write_bytes(b"%PDF")
    assert call("POST", "/api/v2/pdf/ask", data={"path": "../dis.pdf", "q": "x"})[0] == 404
    assert call("POST", "/api/v2/pdf/ask", data={"att_id": "../x", "q": "x"})[0] == 400
    assert call("POST", "/api/v2/pdf/ask", data={"path": "a.pdf"})[0] == 400


def test_pdf_real_pypdf(vault):
    from pypdf import PdfWriter
    w = PdfWriter()
    w.add_blank_page(200, 200)
    with (vault / "bos.pdf").open("wb") as f:
        w.write(f)
    assert vision.extract_pages(vault / "bos.pdf") == [""]
    assert call("POST", "/api/v2/pdf/ask", data={"path": "bos.pdf", "q": "x"})[0] == 422


def test_image_gen_off_by_default(monkeypatch):
    monkeypatch.setattr(features, "_choices", lambda: {})
    out = call("POST", "/api/v2/image/gen", data={"prompt": "kedi"})[1]
    assert out["available"] is False and "image_gen" in out["hint"]


def test_image_gen_no_key(monkeypatch):
    from sb import providers
    monkeypatch.setattr(features, "_choices", lambda: {"image_gen": True})
    monkeypatch.setattr(providers, "api_key", lambda *a, **k: None)
    assert call("POST", "/api/v2/image/gen", data={"prompt": "kedi"})[1]["available"] is False


def test_image_gen_and_file(monkeypatch):
    from sb import providers
    monkeypatch.setattr(features, "_choices", lambda: {"image_gen": True})
    monkeypatch.setattr(providers, "api_key", lambda p, spec=None: "k" if p == "openai" else None)
    seen = {}
    monkeypatch.setattr(vision, "_post", lambda url, body, headers, timeout=180: seen.update(body=body) or
                        {"data": [{"b64_json": base64.b64encode(png()).decode()}]})
    out = call("POST", "/api/v2/image/gen", data={"prompt": "kedi", "size": "999x1"})[1]
    assert out["url"].startswith("/api/v2/image/file?id=") and seen["body"]["model"] == "gpt-image-1"
    assert seen["body"]["size"] == "1024x1024"
    code, body = call("GET", "/api/v2/image/file", query={"id": out["url"].split("=")[1]})
    assert code == 200 and body[:4] == b"\x89PNG"
    assert call("GET", "/api/v2/image/file", query={"id": "../x"})[0] == 400
