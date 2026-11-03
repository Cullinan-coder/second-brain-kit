"""Yerel model yöneticisi: donanım tarayıcı, profil önerisi, model listesi/indirme/silme, profil uygulama, kendi verinle sınav.

`sb models` donanımı okur ve uygun profili önerir; `--apply <profil> --yes` config/llm.yaml'daki yalnız
ollama.model / vision_model / num_ctx değerlerini yazar (yorumlar korunur). Komut ya da ağ yoksa sessizce "bilinmiyor".
Sınav (`--bench`) yalnız HIZ ve BİÇİM UYUMUNU ölçer, cevap kalitesini değil; `visibility: private` notlar ve bulut modeller dışarıda.
"""
from __future__ import annotations

import json
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from .config import SYSTEM, VAULT

GB = 1024 ** 3
LOCAL_PROVIDERS = ("ollama", "lmstudio", "llamacpp", "vllm")

# eşikler (GB VRAM): full ≥ 14, medium ≥ 8, small ≥ 4, altı/GPU yok → cloud
PROFILES: dict[str, dict] = {
    "full": {"ollama": {"model": "qwen3:14b", "vision_model": "qwen3-vl:8b", "num_ctx": 24576},
             "tasks": {}, "download_gb": 15.4,
             "why": "16 GB sınıfı ekran kartı: 14B yazı modeli ve 8B görüntü modeli birlikte rahat sığar."},
    "medium": {"ollama": {"model": "qwen3:8b", "vision_model": "qwen3-vl:4b", "num_ctx": 16384},
               "tasks": {}, "download_gb": 8.5,
               "why": "8-14 GB VRAM: 8B yazı modeli ve 4B görüntü modeli sığar; bağlam penceresi daraltıldı."},
    "small": {"ollama": {"model": "qwen3:4b", "vision_model": "", "num_ctx": 8192},
              "tasks": {}, "download_gb": 2.6,
              "why": "4-8 GB VRAM: yalnız 4B yazı modeli; görüntü modeli yok (ekran görüntüsünde yalnız OCR yazısı okunur)."},
    "cloud": {"ollama": {"model": "qwen3:1.7b", "vision_model": "", "num_ctx": 8192},
              "tasks": {"chat": "openai:gpt-5-mini"}, "alt_tasks": {"chat": "gemini:gemini-2.5-flash"},
              "download_gb": 1.4,
              "why": "Ekran kartı yok ya da < 4 GB: asistan için bulut API önerilir (gizli notlar yine yerelde kalır); "
                     "yerel model yalnız özetler için qwen3:1.7b."},
}
KEYS = ("model", "vision_model", "num_ctx")


# ---------------------------------------------------------------- donanım

def _run(cmd: list[str], timeout: int = 10) -> str:
    """Komutu çalıştırıp çıktısını döndürür; yoksa/hata verirse boş metin (sessiz)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace",
                           creationflags=0x08000000 if sys.platform == "win32" else 0)   # pencere açılmasın (pythonw/zamanlayıcı)
        return (r.stdout or "") if r.returncode == 0 else ""
    except Exception:
        return ""


def parse_nvidia_smi(out: str) -> tuple[str | None, float | None]:
    """`name, memory.total(MiB)` satırları → en büyük kartın (ad, GB)."""
    best: tuple[str | None, float | None] = (None, None)
    for line in (out or "").splitlines():
        if "," not in line:
            continue
        name, _, mem = line.rpartition(",")
        try:
            gb = round(float(mem.strip()) / 1024, 1)
        except ValueError:
            continue
        if best[1] is None or gb > best[1]:
            best = (name.strip(), gb)
    return best


def parse_win32(out: str) -> tuple[str | None, float | None, bool]:
    """Win32_VideoController JSON → (ad, GB, taşmış_mı). AdapterRAM 32 bit: 4 GB'de taşar/eksiye döner."""
    try:
        data = json.loads(out) if (out or "").strip() else []
    except ValueError:
        return None, None, False
    if isinstance(data, dict):
        data = [data]
    best: tuple[str | None, float | None, bool] = (None, None, False)
    for d in data:
        if not isinstance(d, dict):
            continue
        try:
            ram = int(d.get("AdapterRAM") or 0)
        except (TypeError, ValueError):
            continue
        if ram < 0:
            ram += 2 ** 32
        name = str(d.get("Name") or "").strip()
        if re.search(r"microsoft basic|remote|virtual|parsec", name, re.I) or not name:
            continue
        over = ram >= 4 * GB - (16 << 20)           # ≈ 4 GB tavanı: gerçek değer bilinmiyor, en az bu kadar
        gb = round(ram / GB, 1)
        if best[1] is None or gb > best[1]:
            best = (name, gb, over)
    return best


def hardware() -> dict:
    """RAM, CPU, GPU adı, VRAM (GB), boş disk. Bilinmeyen alan None. `vram_note`: tahmin/taşma uyarısı."""
    hw: dict = {"os": platform.system(), "ram_gb": None, "cpu_cores": None, "gpu": None, "vram_gb": None,
                "vram_note": "", "disk_free_gb": None}
    try:
        import psutil
        hw["ram_gb"] = round(psutil.virtual_memory().total / GB, 1)
        hw["cpu_cores"] = psutil.cpu_count(logical=False) or psutil.cpu_count()
    except Exception:
        pass
    try:
        hw["disk_free_gb"] = round(shutil.disk_usage(Path.home()).free / GB, 1)
    except Exception:
        pass
    if hw["os"] == "Darwin" and platform.machine() == "arm64":
        raw = _run(["sysctl", "-n", "hw.memsize"]).strip()
        total = int(raw) / GB if raw.isdigit() else hw["ram_gb"]
        if total:
            hw["ram_gb"] = round(total, 1)
            hw["gpu"] = "Apple Silicon (birleşik bellek)"
            hw["vram_gb"] = round(total * 0.7, 1)
            hw["vram_note"] = "birleşik bellek: RAM'in ~%70'i VRAM sayıldı"
        return hw
    name, gb = parse_nvidia_smi(_run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"], timeout=30))   # dizüstü: GPU uyanırken ilk çağrı yavaş
    if gb is not None:
        hw["gpu"], hw["vram_gb"] = name, gb
        return hw
    if hw["os"] == "Windows":
        out = _run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json"], 20)
        name, gb, over = parse_win32(out)
        if name:
            hw["gpu"], hw["vram_gb"] = name, gb
            if over:
                hw["vram_note"] = "Windows 4 GB'de taşıyor: gerçek VRAM daha büyük olabilir (nvidia-smi yoksa doğrulanamadı)"
    return hw


def recommend(hw: dict) -> dict:
    """Donanıma göre profil: {"profile", ...PROFILES[profil]}. VRAM bilinmiyor/GPU yok → cloud."""
    v = hw.get("vram_gb")
    if v is None or v < 4:
        name = "cloud"
    elif v >= 14:
        name = "full"
    elif v >= 8:
        name = "medium"
    else:
        name = "small"
    p = json.loads(json.dumps(PROFILES[name]))
    p["profile"] = name
    return p


# ---------------------------------------------------------------- yerel modeller

def _get_json(url: str, timeout: int = 3):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def _bases() -> dict[str, str]:
    from . import providers
    t = providers.table()
    return {p: t[p]["base_url"].rstrip("/") for p in LOCAL_PROVIDERS if p in t and t[p].get("base_url")}


def list_local() -> list[dict]:
    """Yerel sunuculardaki modeller: {"provider", "name", "size_gb", "modified"}. Erişilemeyen sunucu atlanır."""
    out: list[dict] = []
    for prov, base in _bases().items():
        try:
            if prov == "ollama":
                for m in _get_json(base + "/api/tags").get("models", []):
                    out.append({"provider": prov, "name": m.get("name", ""),
                                "size_gb": round((m.get("size") or 0) / GB, 1),
                                "modified": str(m.get("modified_at") or "")[:10]})
            else:
                for m in _get_json(base + "/models").get("data", []):
                    out.append({"provider": prov, "name": m.get("id", ""), "size_gb": None, "modified": ""})
        except Exception:
            continue
    return out


def pull(name: str):
    """Ollama'ya model indirir; ilerleme olaylarını ({"status", "completed", "total"}) üretir. CANLI ÇAĞRI: yalnız kullanıcı isterse."""
    base = _bases().get("ollama", "http://localhost:11434")
    req = urllib.request.Request(base + "/api/pull", data=json.dumps({"model": name, "stream": True}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=3600) as r:
        for line in r:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def remove(name: str) -> bool:
    """Ollama'dan modeli siler (/api/delete). CANLI ÇAĞRI: yalnız kullanıcı onayıyla."""
    base = _bases().get("ollama", "http://localhost:11434")
    req = urllib.request.Request(base + "/api/delete", data=json.dumps({"model": name}).encode(),
                                 headers={"Content-Type": "application/json"}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


# ---------------------------------------------------------------- profil uygulama

def _llm_path() -> Path:
    return SYSTEM / "config" / "llm.yaml"


def _fmt(key: str, val) -> str:
    return str(val) if key == "num_ctx" else (json.dumps(val) if val == "" else str(val))


def _edit(text: str, values: dict) -> tuple[str, list[tuple[str, str, str]]]:
    """`ollama:` bloğunda yalnız KEYS satırlarının değerini değiştirir (satır sonu yorumu ve girinti korunur)."""
    lines = text.splitlines(keepends=True)
    changes: list[tuple[str, str, str]] = []
    in_block = False
    for i, ln in enumerate(lines):
        if re.match(r"^ollama:\s*(#.*)?$", ln):
            in_block = True
            continue
        if in_block and re.match(r"^\S", ln) and not ln.startswith("#"):
            in_block = False
        if not in_block:
            continue
        m = re.match(r"^(\s+)(model|vision_model|num_ctx):(\s*)([^#\r\n]*?)(\s*)(#.*)?(\r?\n?)$", ln)
        if not m or m.group(2) not in values:
            continue
        key, old = m.group(2), m.group(4).strip()
        new = _fmt(key, values[key])
        if old.strip("\"'") != new.strip("\""):
            changes.append((key, old, new))
        gap = m.group(5) if m.group(6) else ""
        lines[i] = f"{m.group(1)}{key}:{m.group(3) or ' '}{new}{gap or ('   ' if m.group(6) else '')}{m.group(6) or ''}{m.group(7)}"
    return "".join(lines), changes


def apply_profile(name: str, dry_run: bool = True, path: Path | None = None) -> dict:
    """Profili config/llm.yaml'a uygular. dry_run=True: yalnız farkı döner. {"changes": [(anahtar, eski, yeni)], "tasks_hint", "written"}."""
    if name not in PROFILES:
        raise ValueError(f"bilinmeyen profil: {name} (tanımlılar: {', '.join(PROFILES)})")
    p = path or _llm_path()
    text = p.read_text(encoding="utf-8")
    new, changes = _edit(text, PROFILES[name]["ollama"])
    written = False
    if not dry_run and changes:
        p.write_text(new, encoding="utf-8", newline="")
        written = True
    hint = dict(PROFILES[name].get("tasks") or {})
    return {"profile": name, "changes": changes, "tasks_hint": hint, "written": written}


# ---------------------------------------------------------------- kendi verinle sınav

def pick_notes(n: int = 5, vault: Path | None = None, seed: int = 42) -> list[Path]:
    """Sabit tohumla n not: `visibility: private`, kısa (<300 karakter) ve sistem klasörleri dışarıda."""
    from .notes import is_private, split_note
    root = vault or VAULT
    skip = {"_system", ".obsidian", ".git", ".trash", "node_modules"}
    cands = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root).parts
        if any(part in skip for part in rel[:-1]) or is_private(p):
            continue
        try:
            body = split_note(p.read_text(encoding="utf-8"))[1]
        except Exception:
            continue
        if len(body.strip()) >= 300:
            cands.append(p)
    random.Random(seed).shuffle(cands)
    return cands[:n]


def _json_ok(text: str) -> bool:
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t).strip()
    try:
        return isinstance(json.loads(t), list)
    except ValueError:
        return False


def bench(models: list[str], n: int = 5, vault: Path | None = None) -> list[dict]:
    """Her model için hız (sn, token/sn) ve JSON biçim uyumu. Kalite ölçülmez. Yalnız yerel sağlayıcılar kabul edilir."""
    from . import providers
    from .notes import split_note
    notes = pick_notes(n, vault)
    docs = []
    for p in notes:
        body = split_note(p.read_text(encoding="utf-8"))[1].strip()
        docs.append(body[:3000])
    rows = []
    for spec in models:
        prov = providers.split_spec(spec)[0]
        row = {"model": spec, "notes": len(docs), "calls": 0, "avg_sec": None, "tok_s": None, "json_ok": "0/0", "error": ""}
        if prov not in LOCAL_PROVIDERS:
            row["error"] = "bulut modeline kasa notu gönderilmez (yalnız yerel sağlayıcılar)"
            rows.append(row)
            continue
        secs, toks, ok, tot = 0.0, 0, 0, 0
        for doc in docs:
            for kind in ("summary", "dates"):
                prompt = (f"Bu notu 2 cümlede özetle.\n\n{doc}" if kind == "summary" else
                          f"Bu nottaki tarihleri YALNIZ bir JSON listesi olarak yaz (örn. [\"2026-10-31\"]); tarih yoksa [].\n\n{doc}")
                t0 = time.perf_counter()
                try:
                    r = providers.chat(spec, [{"role": "user", "content": prompt}], timeout=600)
                except Exception as e:
                    row["error"] = str(e)[:120]
                    continue
                dt = time.perf_counter() - t0
                row["calls"] += 1
                secs += dt
                out_tok = int((r.get("usage") or {}).get("output") or 0) or max(1, len(r.get("content") or "") // 4)
                toks += out_tok
                if kind == "dates":
                    tot += 1
                    ok += 1 if _json_ok(r.get("content") or "") else 0
        if row["calls"]:
            row["avg_sec"] = round(secs / row["calls"], 1)
            row["tok_s"] = round(toks / secs, 1) if secs > 0 else None
        row["json_ok"] = f"{ok}/{tot}"
        rows.append(row)
    return rows


def format_bench(rows: list[dict]) -> str:
    lines = [f"{'model':32} {'not':>3} {'sn/çağrı':>9} {'tok/sn':>7} {'JSON':>6}  not"]
    for r in rows:
        lines.append(f"{r['model']:32} {r['notes']:>3} {str(r['avg_sec'] if r['avg_sec'] is not None else '-'):>9} "
                     f"{str(r['tok_s'] if r['tok_s'] is not None else '-'):>7} {r['json_ok']:>6}  {r['error']}")
    lines.append("(Yalnız hız ve biçim uyumu ölçüldü; cevap kalitesi ölçülmedi.)")
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI

def _show(hw: dict, rec: dict) -> str:
    L = ["Donanım:",
         f"  RAM {hw['ram_gb'] or '?'} GB · CPU {hw['cpu_cores'] or '?'} çekirdek · boş disk {hw['disk_free_gb'] or '?'} GB",
         f"  GPU {hw['gpu'] or 'yok/bilinmiyor'} · VRAM {hw['vram_gb'] if hw['vram_gb'] is not None else '?'} GB"
         + (f"  ({hw['vram_note']})" if hw.get("vram_note") else ""),
         f"Önerilen profil: {rec['profile']}  (~{rec['download_gb']} GB indirme)",
         f"  {rec['why']}"]
    o = rec["ollama"]
    L.append(f"  ollama.model={o['model']} vision_model={o['vision_model'] or '(yok)'} num_ctx={o['num_ctx']}")
    for k, v in rec.get("tasks", {}).items():
        alt = (rec.get("alt_tasks") or {}).get(k)
        L.append(f"  önerilen görev: tasks.{k}: {v}" + (f"  (ya da {alt})" if alt else ""))
    L.append("Yerel modeller:")
    loc = list_local()
    L += [f"  {m['provider']:9} {m['name']:30} {m['size_gb'] if m['size_gb'] is not None else '-':>6} GB  {m['modified']}" for m in loc] \
        or ["  (yerel sunucu bulunamadı)"]
    return "\n".join(L)


def cli(a) -> int:
    if getattr(a, "pull", ""):
        if not a.yes:
            print(f"'{a.pull}' indirilecek (boyutlu olabilir). Onay için --yes ekle.")
            return 1
        last = ""
        for ev in pull(a.pull):
            s = ev.get("status", "")
            if ev.get("total"):
                s += f" {ev.get('completed', 0) * 100 // ev['total']}%"
            if s != last:
                print(s)
                last = s
        return 0
    if getattr(a, "rm", ""):
        if not a.yes:
            print(f"'{a.rm}' silinecek. Onay için --yes ekle.")
            return 1
        ok = remove(a.rm)
        print("silindi" if ok else "silinemedi")
        return 0 if ok else 1
    if getattr(a, "bench", ""):
        print(format_bench(bench([s.strip() for s in a.bench.split(",") if s.strip()], a.n)))
        return 0
    if getattr(a, "apply", ""):
        r = apply_profile(a.apply, dry_run=not a.yes)
        if not r["changes"]:
            print("llm.yaml zaten bu profile uygun.")
        for k, old, new in r["changes"]:
            print(f"  ollama.{k}: {old} → {new}")
        for k, v in r["tasks_hint"].items():
            print(f"  (öneri, uygulanmadı) tasks.{k}: {v}")
        if r["changes"]:
            print("yazıldı." if r["written"] else "Yazmak için --yes ekle.")
        return 0
    hw = hardware()
    print(_show(hw, recommend(hw)))
    return 0
