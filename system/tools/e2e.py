"""Uçtan uca test iskeleti (gerçek kasada, SALT OKUNUR): `sb e2e [--live]`.

Senaryo tablosu: (ad, sb argümanları, çıktıda beklenen parça). Yazan hiçbir komut çalıştırılmaz.
--live: çalışan asistana (127.0.0.1:8765) 5 salt okunur soru sorar; öneri kartı dönerse REDDEDER.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8765"

# (ad, argümanlar, çıktıda aranacak parça — küçük harf, "" = yalnız rc=0)
SCENARIOS: list[tuple[str, list[str], str]] = [
    ("version", ["version"], "."),
    ("doctor", ["doctor"], ""),
    ("roadmap", ["roadmap"], ""),
    ("features", ["features"], ""),
    ("recap", ["recap", "--days", "7"], ""),
    ("hygiene", ["hygiene"], ""),
    ("night --plan", ["night", "--plan"], ""),
    ("learn --list", ["learn", "--list"], ""),
    ("task list", ["task", "list"], ""),
    ("models", ["models"], ""),            # komut yoksa atlanır
    ("usage", ["usage"], ""),              # komut yoksa atlanır
    ("search test", ["search", "test"], ""),
]

# (soru, izde/cevapta aranacak işaretlerden biri; boş = yalnız boş olmama)
LIVE_QUESTIONS: list[tuple[str, tuple[str, ...]]] = [
    ("merhaba", ()),
    ("son mail neydi", ("mail",)),
    ("bu dönem derslerim", ("ders", "course")),
    ("son günlerde neler yaptık", ("recap", "makbuz", "brain_")),
    ("Burak kim", ("person", "kişi", "brain_", "burak")),
]


def run_cli(args: list[str], timeout: int = 180) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "-X", "utf8", "-m", "sb", *args], cwd=SYSTEM, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def check_cli() -> list[tuple[str, str, str, float]]:
    rows = []
    for name, args, expect in SCENARIOS:
        t0 = time.time()
        try:
            rc, out = run_cli(args)
        except subprocess.TimeoutExpired:
            rows.append((name, "KALDI", "zaman aşımı", time.time() - t0))
            continue
        if rc == 2 and "invalid choice" in out:
            rows.append((name, "ATLANDI", "komut yok", time.time() - t0))
        elif rc != 0 and not (name == "doctor" and "✗" in out and "Traceback" not in out):   # doctor eksik bulursa rc≠0 olabilir
            rows.append((name, "KALDI", f"rc={rc}: {out.strip()[-120:]}", time.time() - t0))
        elif "Traceback" in out:
            rows.append((name, "KALDI", "traceback", time.time() - t0))
        elif expect and expect not in out.lower():
            rows.append((name, "KALDI", f"'{expect}' yok", time.time() - t0))
        else:
            rows.append((name, "GEÇTİ", f"{len(out.splitlines())} satır", time.time() - t0))
    return rows


def _post(path: str, body: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(BASE + path, json.dumps(body).encode("utf-8"),
                                 {"Content-Type": "application/json", "X-SB": "1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def check_live() -> list[tuple[str, str, str, float]]:
    try:
        urllib.request.urlopen(BASE + "/", timeout=3).read(1)
    except Exception as e:
        return [("canlı asistan", "ATLANDI", f"sunucu yok ({type(e).__name__})", 0.0)]
    rows, sid = [], "e2e-test"
    for q, marks in LIVE_QUESTIONS:
        t0 = time.time()
        try:
            out = _post("/api/chat", {"sid": sid, "text": q})
        except Exception as e:
            rows.append((f"canlı: {q}", "KALDI", f"{type(e).__name__}: {str(e)[:80]}", time.time() - t0))
            continue
        reply = str(out.get("reply", "")).strip()
        hay = (reply + " " + " ".join(map(str, out.get("trace", [])))).lower()
        note = ""
        for pr in out.get("proposals") or []:                        # öneri kartı gelirse reddet
            try:
                _post("/api/decide", {"sid": sid, "id": pr.get("id"), "ok": False}, 30)
                note = " [öneri reddedildi]"
            except Exception:
                note = " [öneri reddedilemedi!]"
        if not reply or reply.startswith("Hata:"):
            rows.append((f"canlı: {q}", "KALDI", (reply or "boş cevap")[:100], time.time() - t0))
        elif marks and not any(m in hay for m in marks):
            rows.append((f"canlı: {q}", "KALDI", f"işaret yok {marks}{note}", time.time() - t0))
        else:
            rows.append((f"canlı: {q}", "GEÇTİ", f"{len(reply)} karakter{note}", time.time() - t0))
    try:
        _post("/api/reset", {"sid": sid}, 10)
    except Exception:
        pass
    return rows


def run(live: bool = False) -> int:
    t0 = time.time()
    rows = check_cli() + (check_live() if live else [])
    w = max(len(r[0]) for r in rows)
    print(f"{'senaryo':<{w}}  {'sonuç':<8} {'sn':>6}  ayrıntı")
    for name, st, note, dur in rows:
        print(f"{name:<{w}}  {st:<8} {dur:>6.1f}  {note}")
    n = {s: sum(1 for r in rows if r[1] == s) for s in ("GEÇTİ", "KALDI", "ATLANDI")}
    print(f"\nGeçti {n['GEÇTİ']} · Kaldı {n['KALDI']} · Atlandı {n['ATLANDI']} · toplam {time.time() - t0:.0f} sn")
    return 1 if n["KALDI"] else 0


if __name__ == "__main__":
    sys.exit(run("--live" in sys.argv))
