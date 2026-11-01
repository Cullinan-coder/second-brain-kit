"""Faz 4b Paket J: ajan pazarı, kum havuzu, izleme, akış şablonları, kod ajanı köprüsü, gece raporu.
Ajan araçları YALNIZ salt okunur kasa araçlarıdır; yazma = tek sonuç notu `00-Inbox/Ajan çıktıları/`."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from . import config, vault_ops

OUT_DIR = "00-Inbox/Ajan çıktıları"
READ_TOOLS = ("brain_find", "read_note", "list_notes", "research")
PRIVATE_RE = re.compile(r"^visibility:\s*private\s*$", re.M | re.I)

AGENTS: list[dict] = [
    {"id": "ders", "ad": "Ders asistanı", "aciklama": "Ders notlarından soruya cevap ve çalışma önerisi verir.",
     "araclar": ["brain_find", "read_note"], "okuma": ["10-Dersler"],
     "istem": "Sen bir ders asistanısın. Yalnız verilen ders notlarına dayan, Türkçe ve kısa yanıtla.\nSoru: {girdi}\n\nNotlar:\n{baglam}"},
    {"id": "proje", "ad": "Proje durum raporu", "aciklama": "Proje notlarından durum raporu çıkarır.",
     "araclar": ["brain_find", "read_note", "list_notes"], "okuma": ["20-Projeler", "25-Görevler"],
     "istem": "Aşağıdaki proje notlarından '{girdi}' için kısa durum raporu yaz: yapılanlar, açıklar, sıradaki.\n\n{baglam}"},
    {"id": "mail", "ad": "Mail özetleyici", "aciklama": "Kasadaki mail kayıtlarını özetler (salt okunur).",
     "araclar": ["brain_find"], "okuma": ["40-Kaynaklar"],
     "istem": "Şu konudaki mail/yazışma parçalarını özetle, yapılacakları listele: {girdi}\n\n{baglam}"},
    {"id": "arastirmaci", "ad": "Araştırmacı", "aciklama": "Kasada ve (isteğe bağlı) webde kaynaklı araştırma yapar.",
     "araclar": ["research"], "okuma": ["40-Kaynaklar"], "istem": ""},
    {"id": "planlayici", "ad": "Haftalık planlayıcı", "aciklama": "Görev ve günlük notlarından haftalık plan önerir.",
     "araclar": ["brain_find", "list_notes", "read_note"], "okuma": ["25-Görevler", "50-Günlük", "20-Projeler"],
     "istem": "Aşağıdaki görev/günlük notlarından '{girdi}' için gerçekçi haftalık plan öner.\n\n{baglam}"},
]
SOON = [{"id": "tarayici", "ad": "Tarayıcı otomasyonu", "aciklama": "yakında (izinli tarayıcı)", "durum": "yakında",
         "araclar": [], "okuma": []}]

FLOWS: dict[str, dict] = {
    "ders-arastir": {"ad": "Ders sorusu → araştırma özeti", "adimlar": [
        {"ajan": "ders", "girdi_sablonu": "{girdi}"},
        {"ajan": "arastirmaci", "girdi_sablonu": "Şu taslağı doğrula ve derinleştir:\n{onceki}"}]},
    "proje-plan": {"ad": "Proje durumu → haftalık plan", "adimlar": [
        {"ajan": "proje", "girdi_sablonu": "{girdi}"},
        {"ajan": "planlayici", "girdi_sablonu": "Bu duruma göre plan:\n{onceki}"}]},
}


def _runs_path() -> Path:
    return config.DATA / "agent_runs.jsonl"


def catalog() -> list[dict]:
    pub = [{k: a[k] for k in ("id", "ad", "aciklama", "araclar", "okuma")} | {"durum": "hazır"} for a in AGENTS]
    return pub + SOON


def get(agent_id: str) -> dict:
    for a in AGENTS:
        if a["id"] == agent_id:
            return a
    raise KeyError(agent_id)


def runs(limit: int = 50) -> list[dict]:
    p = _runs_path()
    if not p.exists():
        return []
    rows = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(ln))
        except ValueError:
            pass
    return rows[-limit:][::-1]


def _log(row: dict) -> None:
    p = _runs_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


class Sandbox:
    """Ajan başına izin listesi: yalnız izinli araçlar, yalnız izinli klasörler. İhlal reddedilir ve kaydedilir."""

    def __init__(self, agent: dict, run_id: str):
        self.agent, self.run_id, self.steps, self.denied = agent, run_id, 0, []

    def _deny(self, what: str) -> None:
        self.denied.append(what)
        _log({"id": self.run_id, "ajan": self.agent["id"], "olay": "reddedildi", "ayrinti": what,
              "zaman": datetime.now().isoformat(timespec="seconds")})
        raise PermissionError(f"izin dışı: {what}")

    def _folder_ok(self, rel: str) -> bool:
        rel = rel.replace("\\", "/").lstrip("/")
        if ".." in rel.split("/"):
            return False
        return any(rel == f or rel.startswith(f + "/") for f in self.agent["okuma"])

    def call(self, tool: str, **kw):
        if tool not in READ_TOOLS or tool not in self.agent["araclar"]:
            self._deny(f"araç {tool}")
        self.steps += 1
        if tool == "research":
            from . import search
            return search.research(str(kw.get("question", "")), web=bool(kw.get("web")), save=False)
        if tool == "brain_find":
            from . import brain
            hits = brain.find(str(kw.get("query", "")), k=int(kw.get("k", 6)))
            return [x for x in hits if self._folder_ok(str(x.get("path", "")))]
        rel = str(kw.get("path", ""))
        if not self._folder_ok(rel):
            self._deny(f"klasör {rel}")
        p = vault_ops.VAULT / rel
        if tool == "list_notes":
            return sorted(x.relative_to(vault_ops.VAULT).as_posix() for x in p.rglob("*.md"))[:50] if p.is_dir() else []
        if not p.is_file() or p.suffix != ".md":
            return ""
        txt = p.read_text(encoding="utf-8", errors="replace")
        return "" if PRIVATE_RE.search(txt[:600]) else txt[:4000]


def _context(sb: Sandbox, query: str) -> str:
    """Salt okunur araçlarla bağlam toplar (her çağrı kum havuzundan geçer)."""
    parts: list[str] = []
    tools = sb.agent["araclar"]
    if "brain_find" in tools:
        for h in sb.call("brain_find", query=query)[:5]:
            parts.append(f"[{h.get('path', '')}] {str(h.get('text') or h.get('snippet') or '')[:700]}")
    if "list_notes" in tools and "read_note" in tools and not parts:
        for folder in sb.agent["okuma"][:2]:
            for rel in sb.call("list_notes", path=folder)[:4]:
                parts.append(f"[{rel}] {sb.call('read_note', path=rel)[:700]}")
    return "\n\n".join(parts) or "(ilgili not bulunamadı)"


def _write_result(agent: dict, run_id: str, query: str, body: str, sources: list[str]) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rel = f"{OUT_DIR}/{agent['ad']} {stamp}.md"
    p = vault_ops.VAULT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    src = "".join(f"- {s}\n" for s in sources)
    p.write_text(f"---\ntype: ajan-ciktisi\nagent: {agent['id']}\nrun: {run_id}\ncreated: {datetime.now():%Y-%m-%d}\n---\n"
                 f"# {agent['ad']}\n\nGirdi: {query}\n\n{body.strip()}\n" + (f"\n## Kaynaklar\n{src}" if src else ""), encoding="utf-8")
    vault_ops.commit([rel], f"ajan çıktısı: {agent['id']}")
    return rel


def run(agent_id: str, text: str, web: bool = False) -> dict:
    """Bir ajanı çalıştırır; tek sonuç notu yazar; çalışmayı `agent_runs.jsonl`'e kaydeder."""
    from . import llm
    agent = get(agent_id)
    text = (text or "").strip()
    if not text:
        raise ValueError("girdi boş")
    if vault_ops.SENSITIVE_RE.search(text):
        raise ValueError("hassas veri ajana verilmez")
    run_id = f"{agent_id}-{int(time.time() * 1000)}"
    start = datetime.now().isoformat(timespec="seconds")
    sb = Sandbox(agent, run_id)
    model, sources, status, path, out = "", [], "tamam", "", ""
    try:
        if "research" in agent["araclar"]:
            r = sb.call("research", question=text, web=web)
            out = r.get("report", "")
            sources = [str(s.get("path") or s.get("url") or s) if isinstance(s, dict) else str(s) for s in r.get("sources", [])]
            model = "research"
        else:
            ctx = _context(sb, text)
            out, model = llm.complete("agent", agent["istem"].format(girdi=text, baglam=ctx), private=True)
            sb.steps += 1
            sources = [m.group(1) for m in re.finditer(r"^\[([^\]]+)\]", ctx, re.M)]
        path = _write_result(agent, run_id, text, out, sources)
    except Exception as e:  # noqa: BLE001
        status, out = "hata", str(e)
    row = {"id": run_id, "ajan": agent_id, "baslangic": start, "bitis": datetime.now().isoformat(timespec="seconds"),
           "durum": status, "adim": sb.steps, "model": model, "cikti": path, "reddedilen": len(sb.denied)}
    _log(row)
    if status == "hata":
        raise ValueError(out)
    return row | {"text": out}


def run_flow(template, text: str = "") -> dict:
    """Sıralı zincir: önceki çıktı sonrakinin girdisi. `template` ad ya da {adimlar:[...]}."""
    tpl = FLOWS.get(template) if isinstance(template, str) else template
    if not tpl or not tpl.get("adimlar"):
        raise KeyError(template if isinstance(template, str) else "şablon")
    prev, results = "", []
    for st in tpl["adimlar"]:
        girdi = str(st.get("girdi_sablonu", "{girdi}")).replace("{onceki}", prev).replace("{girdi}", text)
        r = run(st["ajan"], girdi)
        prev = r["text"]
        results.append({k: r[k] for k in ("id", "ajan", "durum", "cikti")})
    return {"adimlar": results, "text": prev}


def code_bridge(task: str, where: str = "") -> dict:
    """Kod ajanı köprüsü: YALNIZ gece işi listesine ekler, çalıştırmaz."""
    from . import worker
    msg = worker.night_add(task, where)
    if msg.startswith(("Hata", "Hassas")):
        raise ValueError(msg)
    return {"message": msg, "queued": True, "ran": False, "plan": worker.night_plan()}


def night_report() -> dict:
    """Sabah özeti: gece işleri notu + son gece logu + onay bekleyen değişiklik önerileri."""
    from . import worker
    note = vault_ops.VAULT / worker.NIGHT_NOTE
    done, failed, pending = [], [], []
    if note.exists():
        for ln in note.read_text(encoding="utf-8").splitlines():
            s = ln.strip()
            if s.startswith("- [x]"):
                done.append(s[5:].strip())
            elif s.startswith("- [!]"):
                failed.append(s[5:].strip())
            elif s.startswith("- [ ]"):
                pending.append(s[5:].strip())
    logs = sorted((config.DATA / "logs").glob("night-*.log")) if (config.DATA / "logs").is_dir() else []
    tail = logs[-1].read_text(encoding="utf-8", errors="replace").splitlines()[-15:] if logs else []
    try:
        changes = list(vault_ops.recent(hours=14))
    except Exception:  # noqa: BLE001
        changes = []
    approvals = [{"oge": c.get("path", ""), "islem": c.get("action", ""), "ayrinti": c.get("detail", "")} for c in changes][:30]
    summary = f"{len(done)} bitti, {len(failed)} hata, {len(pending)} bekliyor; {len(approvals)} değişiklik onay bekliyor."
    return {"summary": summary, "done": done, "failed": failed, "pending": pending,
            "log": logs[-1].name if logs else "", "log_tail": tail, "approvals": approvals}
