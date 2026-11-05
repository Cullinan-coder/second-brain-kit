"""Kit özet dosyası (SHA256SUMS) ve `sb verify`: özet, git'in DEPODA SAKLAYACAĞI içerikten hesaplanır.

Windows çalışma kopyası CRLF olabilir; kit deposunun `.gitattributes` dosyası `* text=auto eol=lf` der. Bu yüzden temiz bir
`git clone` ile Linux/macOS'ta ya da `git show HEAD:<dosya>` ile görülen bayt dizisi, Windows diskindekinden farklıdır.
Burada git'in `convert.c` sezgisi uygulanır:
  - `binary` / `-text` işaretli kalıp: olduğu gibi.
  - `text` (ya da `eol=` ile birlikte `text`) işaretli kalıp: CRLF → LF (yalın CR'ye dokunulmaz).
  - `text=auto`: dosya ikili sayılırsa (NUL var, yalın CR var ya da yazdırılamayan baytlar çoğunlukta) olduğu gibi, değilse CRLF → LF.
Kurulu kopyayı doğrulamak: `sb verify` (kuruluma kitin `SHA256SUMS` dosyası `_system/SHA256SUMS` olarak kopyalanır).
"""
from __future__ import annotations

import fnmatch
import hashlib
import re
from pathlib import Path

# build_kit.py bunu kit kökündeki .gitattributes olarak yazar; `sb verify` kurulu kopyada aynı kuralları kullanır.
DEFAULT_GITATTRIBUTES = "* text=auto eol=lf\n*.ps1 text eol=crlf\n"

# Kurulumdan sonra değişmesi/oluşması NORMAL olanlar (üst düzey klasör/dosya adı ya da yol bileşeni): doğrulamaya girmez.
SKIP_TOP = ("config", ".venv", "data", "logs", ".pytest_cache", "SHA256SUMS")
SKIP_ANY = ("__pycache__", ".pytest_cache", ".venv", "node_modules", ".git")
SKIP_SUFFIX = (".pyc", ".pyo", ".tmp", ".bak", ".part")
SKIP_NOTE = ("config (kişisel ayarlar)", ".venv (sanal ortam)", "data (yerel veri)", "logs", "__pycache__ / *.pyc (derleme önbelleği)",
             ".pytest_cache", "*.tmp / *.bak / *.part")


# ------------------------------------------------------------------ .gitattributes
def parse_gitattributes(text: str, base: str = "") -> list[tuple[str, dict, str]]:
    """[(kalıp, {text: True|False|'auto'|None, ...}, klasör)] — dosyadaki sırayla; sonraki kalıp öncekini geçersiz kılar.
    `base`: bu .gitattributes dosyasının kit köküne göre klasörü (iç içe dosyalar yalnız kendi klasörlerini etkiler)."""
    rules = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pat, *attrs = line.split()
        a: dict = {}
        for t in attrs:
            if t == "binary":
                a["text"] = False
            elif t == "text":
                a["text"] = True
            elif t == "-text":
                a["text"] = False
            elif t == "!text":
                a["text"] = None
            elif t == "text=auto":
                a["text"] = "auto"
            elif t.startswith("eol="):
                a["eol"] = t[4:]
        rules.append((pat, a, base))
    return rules


def _glob_re(pat: str) -> re.Pattern:
    """gitattributes kalıbı → düzenli ifade (yalnız `*`, `?`, `[..]`, `**`)."""
    out, i = "", 0
    while i < len(pat):
        c = pat[i]
        if pat.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
            continue
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c == "[":
            j = pat.find("]", i + 1)
            if j > 0:
                out += pat[i:j + 1]
                i = j
            else:
                out += re.escape(c)
        else:
            out += re.escape(c)
        i += 1
    return re.compile("^" + out + "$")


def load_gitattributes(root: Path, prefix: str = "", include_root: bool = True) -> list[tuple[str, dict, str]]:
    """`root` altındaki tüm .gitattributes dosyaları (kök önce, derindekiler sonra: derin olan baskın). `prefix`: root'un kit köküne göre yolu."""
    root = Path(root)
    files = sorted((p for p in root.rglob(".gitattributes") if ".git" not in p.relative_to(root).parts[:-1]),
                   key=lambda p: len(p.relative_to(root).parts))
    rules: list = []
    for p in files:
        rel_dir = "/".join(p.relative_to(root).parts[:-1])
        if not rel_dir and not include_root:
            continue
        base = "/".join(x for x in (prefix.strip("/"), rel_dir) if x)
        rules += parse_gitattributes(p.read_text(encoding="utf-8", errors="replace"), base)
    return rules


def _attrs_for(relpath: str, rules: list) -> dict:
    out: dict = {}
    for pat, a, base in rules:
        if base:
            if not relpath.startswith(base + "/"):
                continue
            sub = relpath[len(base) + 1:]
        else:
            sub = relpath
        anchored = "/" in pat.strip("/")
        rx = _glob_re(pat.lstrip("/").rstrip("/"))
        if rx.match(sub if anchored else sub.rsplit("/", 1)[-1]):
            out.update(a)
    return out


# ------------------------------------------------------------------ git'in ikili sezgisi (convert.c gather_stats / convert_is_binary)
def _is_binary(b: bytes) -> bool:
    nul = lonecr = printable = nonprintable = 0
    n, i = len(b), 0
    while i < n:
        c = b[i]
        if c == 13:
            if i + 1 < n and b[i + 1] == 10:
                i += 1
            else:
                lonecr += 1
        elif c == 10:
            pass
        elif c == 127:
            nonprintable += 1
        elif c < 32:
            if c in (8, 9, 27, 12):
                printable += 1
            else:
                if c == 0:
                    nul += 1
                nonprintable += 1
        else:
            printable += 1
        i += 1
    if n >= 1 and b[-1] == 0x1A:
        nonprintable -= 1
    if lonecr or nul:
        return True
    return (printable >> 7) < nonprintable


def normalized_bytes(data: bytes, relpath: str, rules: list | None = None) -> bytes:
    """Dosyanın git deposunda SAKLANACAK bayt dizisi."""
    rules = parse_gitattributes(DEFAULT_GITATTRIBUTES) if rules is None else rules
    a = _attrs_for(relpath.replace("\\", "/"), rules)
    t = a.get("text")
    if t is False or t is None:
        return data
    if b"\r\n" not in data:
        return data
    if t == "auto" and _is_binary(data):
        return data
    return data.replace(b"\r\n", b"\n")


def checkout_bytes(data: bytes, relpath: str, rules: list | None = None) -> bytes:
    """Temiz bir `git clone` sonrası DİSKE düşecek bayt dizisi: saklanan içerik + `eol=crlf` kuralı (ör. `*.ps1`).
    Özet bununla hesaplanır; böylece kullanıcı klonda dosyayı doğrudan özetleyince tutar (her işletim sisteminde aynı,
    çünkü kalıpların hepsinde `eol` açıkça verilmiştir)."""
    rules = parse_gitattributes(DEFAULT_GITATTRIBUTES) if rules is None else rules
    stored = normalized_bytes(data, relpath, rules)
    a = _attrs_for(relpath.replace("\\", "/"), rules)
    t = a.get("text")
    if a.get("eol") != "crlf" or t is False or t is None or (t == "auto" and _is_binary(stored)):
        return stored
    return stored.replace(b"\n", b"\r\n")


def sha256_normalized(data: bytes, relpath: str, rules: list | None = None) -> str:
    return hashlib.sha256(checkout_bytes(data, relpath, rules)).hexdigest()


# ------------------------------------------------------------------ kurulu kopyayı doğrulama
def parse_sums(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+?)\s*$", line.strip())
        if m:
            out[m.group(2)] = m.group(1).lower()
    return out


def _skipped(rel: str) -> str | None:
    parts = rel.split("/")
    if parts[0] in SKIP_TOP:
        return parts[0]
    for p in parts:
        if p in SKIP_ANY:
            return p
    if rel.endswith(SKIP_SUFFIX):
        return "*" + rel[rel.rfind("."):]
    return None


def verify_install(system: Path) -> dict:
    """Kurulu `_system` klasörünü kitin SHA256SUMS dosyasıyla (`system/…` satırları) karşılaştırır.
    Döner: {ok: True|False|None, checked, changed, missing, extra, skipped, message}. ok=None: SHA256SUMS yok."""
    system = Path(system)
    f = system / "SHA256SUMS"
    skipped: set[str] = set()
    if not f.is_file():
        return {"ok": None, "checked": 0, "changed": [], "missing": [], "extra": [], "skipped": [],
                "message": "SHA256SUMS bulunamadı (_system/SHA256SUMS). Kiti güncelleyip kurucuyu yeniden çalıştır: `sb update`."}
    sums = {k[len("system/"):]: v for k, v in parse_sums(f.read_text(encoding="utf-8")).items() if k.startswith("system/")}
    rules = parse_gitattributes(DEFAULT_GITATTRIBUTES) + load_gitattributes(system, "system", include_root=False)
    changed, missing, checked = [], [], 0
    for rel, want in sorted(sums.items()):
        s = _skipped(rel)
        if s:
            skipped.add(s)
            continue
        p = system / rel
        if not p.is_file():
            missing.append(rel)
            continue
        checked += 1
        if sha256_normalized(p.read_bytes(), "system/" + rel, rules) != want:
            changed.append(rel)
    extra = []
    for p in sorted(system.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(system).as_posix()
        s = _skipped(rel)
        if s:
            skipped.add(s)
        elif rel not in sums:
            extra.append(rel)
    ok = not changed and not missing
    return {"ok": ok, "checked": checked, "changed": changed, "missing": missing, "extra": extra, "skipped": sorted(skipped),
            "message": "yerel değişiklik yok" if ok and not extra else "uyuşuyor (fazla dosyalar var)" if ok else "farklar var"}


def cli(args=None) -> int:
    from .config import SYSTEM
    r = verify_install(SYSTEM)
    if r["ok"] is None:
        print(r["message"])
        return 2
    print(f"Kurulu kopya: {SYSTEM}")
    print(f"Denetlenen dosya: {r['checked']}")
    print("Atlananlar (kurulumdan sonra değişmesi normal): " + ", ".join(SKIP_NOTE))
    for title, key in (("Yerel olarak DEĞİŞMİŞ", "changed"), ("EKSİK", "missing"), ("Kitte olmayan FAZLA", "extra")):
        if r[key]:
            print(f"\n{title} ({len(r[key])}):")
            for x in r[key][:200]:
                print("  " + x)
    if r["ok"]:
        print("\nSonuç: " + ("kit ile uyuşuyor, yerel değişiklik yok." if not r["extra"] else "kit ile uyuşuyor (fazla dosyalar yalnız bilgi)."))
        return 0
    print("\nSonuç: kit ile UYUŞMUYOR. Beklenmedik farklar varsa `sb update` ile kodu yeniden kur; kendi değişikliklerini önce sakla.")
    return 1
