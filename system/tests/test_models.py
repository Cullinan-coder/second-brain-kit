"""Yerel model yöneticisi: donanım ayrıştırma, profil eşikleri, llm.yaml yazımı, model listesi, sınav. Ağ ve komut yok."""
import io
import json

import pytest

from sb import models

YAML = """tasks:
  chat: ollama   # asistan
ollama:
  host: http://localhost:11434
  model: qwen3:14b         # 16 GB'a sığar
  num_ctx: 24576           # bağlam
  max_chars: 66000
  vision_model: qwen3-vl:8b   # görüntü
other:
  model: dokunma
"""


def test_nvidia_smi_ayristirma():
    assert models.parse_nvidia_smi("NVIDIA GeForce RTX 4080, 16376\n") == ("NVIDIA GeForce RTX 4080", 16.0)
    assert models.parse_nvidia_smi("A, 4096\nB, 8192\n") == ("B", 8.0)
    assert models.parse_nvidia_smi("") == (None, None)


def test_win32_tasma():
    out = json.dumps([{"Name": "NVIDIA GeForce RTX 4080", "AdapterRAM": 4293918720},
                      {"Name": "Microsoft Basic Display Adapter", "AdapterRAM": 0}])
    name, gb, over = models.parse_win32(out)
    assert name.startswith("NVIDIA") and gb >= 3.9 and over
    # eksiye dönen 32 bit değer
    n2, g2, o2 = models.parse_win32(json.dumps({"Name": "Intel UHD", "AdapterRAM": -2147483648}))
    assert g2 == 2.0 and not o2
    assert models.parse_win32("bozuk") == (None, None, False)


def test_mac_birlesik_bellek(monkeypatch):
    monkeypatch.setattr(models.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(models.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(models, "_run", lambda cmd, timeout=10: str(32 * models.GB))
    hw = models.hardware()
    assert hw["vram_gb"] == pytest.approx(22.4) and "birleşik" in hw["vram_note"]
    assert models.recommend(hw)["profile"] == "full"


def test_hardware_komut_yok(monkeypatch):
    monkeypatch.setattr(models.platform, "system", lambda: "Linux")
    monkeypatch.setattr(models, "_run", lambda cmd, timeout=10: "")
    hw = models.hardware()
    assert hw["gpu"] is None and hw["vram_gb"] is None
    assert models.recommend(hw)["profile"] == "cloud"


@pytest.mark.parametrize("vram,profil", [(24, "full"), (14, "full"), (13.9, "medium"), (8, "medium"),
                                          (7.9, "small"), (4, "small"), (3.9, "cloud"), (None, "cloud")])
def test_profil_esikleri(vram, profil):
    r = models.recommend({"vram_gb": vram})
    assert r["profile"] == profil and r["why"] and r["download_gb"] > 0
    assert r["ollama"]["num_ctx"] > 0
    if profil == "cloud":
        assert r["tasks"]["chat"].startswith("openai:") and r["ollama"]["model"] == "qwen3:1.7b"
    if profil == "small":
        assert r["ollama"]["vision_model"] == "" and r["ollama"]["num_ctx"] == 8192


def test_apply_profile_sadece_uc_anahtar(tmp_path):
    p = tmp_path / "llm.yaml"
    p.write_text(YAML, encoding="utf-8")
    r = models.apply_profile("small", dry_run=True, path=p)
    assert {c[0] for c in r["changes"]} == {"model", "vision_model", "num_ctx"} and not r["written"]
    assert p.read_text(encoding="utf-8") == YAML           # dry-run dosyaya dokunmaz
    models.apply_profile("small", dry_run=False, path=p)
    new = p.read_text(encoding="utf-8")
    assert "model: qwen3:4b" in new and 'vision_model: ""' in new and "num_ctx: 8192" in new
    assert "# 16 GB'a sığar" in new and "# bağlam" in new and "# görüntü" in new
    assert "model: dokunma" in new and "max_chars: 66000" in new and "chat: ollama   # asistan" in new
    old_lines, new_lines = YAML.splitlines(), new.splitlines()
    assert sum(a != b for a, b in zip(old_lines, new_lines)) == 3 and len(old_lines) == len(new_lines)
    # ikinci uygulama fark üretmez
    assert models.apply_profile("small", dry_run=True, path=p)["changes"] == []
    with pytest.raises(ValueError):
        models.apply_profile("yok", path=p)


class R:
    def __init__(self, data, status=200):
        self.data, self.status = data, status

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def __iter__(self):
        return iter(self.data.splitlines())


def test_list_local(monkeypatch):
    tags = {"models": [{"name": "qwen3:14b", "size": 9 * models.GB, "modified_at": "2026-10-01T10:00:00Z"}]}
    lm = {"data": [{"id": "gemma-3"}]}

    def fake(req, timeout=0):
        url = req if isinstance(req, str) else req.full_url
        if "11434" in url:
            return R(json.dumps(tags).encode())
        if "1234" in url:
            return R(json.dumps(lm).encode())
        raise OSError("kapalı")
    monkeypatch.setattr(models.urllib.request, "urlopen", fake)
    out = models.list_local()
    assert {"provider": "ollama", "name": "qwen3:14b", "size_gb": 9.0, "modified": "2026-10-01"} in out
    assert any(m["provider"] == "lmstudio" and m["name"] == "gemma-3" for m in out)
    assert not any(m["provider"] in ("llamacpp", "vllm") for m in out)


def test_pull_ve_remove(monkeypatch):
    seen = []

    def fake(req, timeout=0):
        seen.append((req.get_method(), req.full_url, json.loads(req.data)))
        return R(b'{"status":"pulling","total":10,"completed":5}\n{"status":"success"}\n')
    monkeypatch.setattr(models.urllib.request, "urlopen", fake)
    evs = list(models.pull("qwen3:4b"))
    assert evs[-1]["status"] == "success" and seen[0][0] == "POST" and seen[0][2]["model"] == "qwen3:4b"
    assert models.remove("qwen3:4b") and seen[1][0] == "DELETE" and seen[1][1].endswith("/api/delete")


def _vault(tmp_path):
    long = "Toplantı 5 Kasım 2026'da yapılacak. " * 20
    (tmp_path / "A.md").write_text("---\ntype: not\n---\n" + long, encoding="utf-8")
    (tmp_path / "B.md").write_text("---\ntype: not\n---\n" + long, encoding="utf-8")
    (tmp_path / "gizli.md").write_text("---\nvisibility: private\n---\n" + long, encoding="utf-8")
    (tmp_path / "kisa.md").write_text("kısa", encoding="utf-8")
    (tmp_path / "_system").mkdir()
    (tmp_path / "_system" / "x.md").write_text(long, encoding="utf-8")
    return tmp_path


def test_pick_notes_private_atlar_sabit(tmp_path):
    v = _vault(tmp_path)
    a = models.pick_notes(5, v)
    assert {p.name for p in a} == {"A.md", "B.md"}
    assert models.pick_notes(1, v) == models.pick_notes(1, v)


def test_bench_json_olcumu_ve_private(tmp_path, monkeypatch):
    v = _vault(tmp_path)
    sent = []

    def fake_chat(spec, messages, **kw):
        sent.append(messages[0]["content"])
        if "JSON" in messages[0]["content"]:
            return {"content": '```json\n["2026-11-05"]\n```' if spec.endswith("iyi") else "tarih yok", "usage": {"output": 50}}
        return {"content": "Özet.", "usage": {"output": 20}}
    monkeypatch.setattr("sb.providers.chat", fake_chat)
    rows = models.bench(["ollama:iyi", "ollama:kotu", "openai:gpt-5-mini"], n=2, vault=v)
    iyi, kotu, bulut = rows
    assert iyi["json_ok"] == "2/2" and kotu["json_ok"] == "0/2" and iyi["calls"] == 4
    assert iyi["tok_s"] is not None and iyi["avg_sec"] is not None
    assert bulut["calls"] == 0 and "bulut" in bulut["error"]
    assert not any("visibility" in s for s in sent)
    assert "iyi" in models.format_bench(rows)


def test_cli_onay_istiyor(monkeypatch, capsys):
    import argparse
    a = argparse.Namespace(pull="x:1b", rm="", bench="", apply="", yes=False, n=5)
    called = []
    monkeypatch.setattr(models, "pull", lambda n: called.append(n) or iter([]))
    assert models.cli(a) == 1 and not called
    a2 = argparse.Namespace(pull="", rm="x:1b", bench="", apply="", yes=False, n=5)
    monkeypatch.setattr(models, "remove", lambda n: called.append(n) or True)
    assert models.cli(a2) == 1 and not called
