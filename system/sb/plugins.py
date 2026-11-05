"""Eklenti tanımları (manifest): kurulum sihirbazı ve uygulama listelerini koddan değil bu tanımlardan çizer.

`plugins/<tür>/<id>.yaml` — tür: module (özellik/modül), source (veri kaynağı/içe aktarıcı), mcp, sector (sektör paketi).
`plugins/presets.yaml` — dört eksen (meslek, donanım, gizlilik, yoğunluk), `plugins/categories.yaml` — kategori adları.

Sorgu: `all()`, `get(id)`, `for_preset(...)`, `features_tree()`, `requirements(selection)`, `combine(...)`.
Doğrulama: `validate()` hata listesi döndürür (boş = tamam). Yalnız okur; hiçbir şey yazmaz, ağa çıkmaz.
Sektör paketi = çekirdek + tanım (modül/kaynak/MCP listesi, hazır seçim, roller, rapor şablonları, terimler); rol zorlaması bu katmanda YOK.
"""
from __future__ import annotations

import ast
import re
from functools import lru_cache
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CODE = HERE.parent
PLUGINS = CODE / "plugins"
TYPES = ("module", "source", "mcp", "sector")
AXES = ("meslek", "donanim", "gizlilik", "yogunluk")
KINDS = {"text", "path", "email", "secret", "url", "bool", "choice", "number"}
ACCOUNTS = {"google", "imap", "outlook", "icloud", "github", "telegram", "spotify", "tailscale", "openai", "anthropic", "gemini",
            "openrouter", "groq", "deepseek", "mistral", "school", "notion", "slack", "atlassian", "linear", "brave", "sentry",
            "figma", "whatsapp", "linkedin"}
# modül kapanırsa bağımlısı da kapanır
DEPENDS = {"wake_word": ["voice"], "screen_watch": ["vision"], "cards": [], "digest": ["gmail", "imap"], "dates": []}
_SECRETISH = re.compile(r"(password|token|_key|_pat|_secret)$")
_REF = re.compile(r"^\{([a-z0-9_]+)\}$")


# ------------------------------------------------------------------ yükleme
def _read(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _load() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for t in TYPES:
        for f in sorted((PLUGINS / t).glob("*.yaml")):
            m = _read(f)
            m.setdefault("id", f.stem)
            m["_file"] = f"{t}/{f.name}"
            if f"{t}:{m['id']}" in out:
                raise ValueError(f"yinelenen eklenti kimliği: {t}:{m['id']} ({f})")
            out[f"{t}:{m['id']}"] = m
    return out


def reload() -> None:
    _load.cache_clear()
    presets.cache_clear()
    categories.cache_clear()


@lru_cache(maxsize=1)
def presets() -> dict:
    return _read(PLUGINS / "presets.yaml")


@lru_cache(maxsize=1)
def categories() -> dict:
    return _read(PLUGINS / "categories.yaml")


def all(type: str | None = None) -> list[dict]:                      # noqa: A001
    items = list(_load().values())
    return [m for m in items if type is None or m["type"] == type]


def get(id: str, type: str | None = None) -> dict | None:           # noqa: A002
    """Kimlik türler arasında aynı olabilir (ör. modül `whatsapp` ve kaynak `whatsapp`): `type` verilmezse module, source, mcp,
    sector sırasıyla ilk eşleşme; `get("source:whatsapp")` ya da `get("whatsapp", "source")` kesin sonuç verir."""
    d = _load()
    if ":" in id:
        return d.get(id)
    for t in ([type] if type else TYPES):
        if f"{t}:{id}" in d:
            return d[f"{t}:{id}"]
    return None


def module_keys() -> set[str]:
    """`sb/features.py` MODULES anahtarları (içe aktarmadan, ast ile)."""
    for node in ast.parse((HERE / "features.py").read_text(encoding="utf-8")).body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "MODULES":
            return set(ast.literal_eval(node.value))
    return set()


def registry_names() -> set[str]:
    """`sb/connectors/__init__.py` REGISTRY anahtarları (içe aktarmadan, ast ile)."""
    for node in ast.parse((HERE / "connectors" / "__init__.py").read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "REGISTRY":
            return {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
    return set()


def catalog_ids() -> set[int]:
    from .features import catalog
    return {i["id"] for i in catalog()}


# ------------------------------------------------------------------ doğrulama
def _bi(v, where: str, errs: list[str], need: bool = True) -> None:
    if not isinstance(v, dict) or not v.get("tr") or not v.get("en"):
        if need:
            errs.append(f"{where}: {{tr, en}} ikisi de dolu olmalı")


def _check_requires(m: dict, errs: list[str]) -> None:
    r = m.get("requires")
    if not isinstance(r, dict):
        errs.append("requires: sözlük olmalı")
        return
    for a in r.get("accounts") or []:
        if a not in ACCOUNTS:
            errs.append(f"requires.accounts: bilinmeyen hesap türü {a}")
    keys, secret_keys = set(), set()
    for f in r.get("fields") or []:
        k = f.get("key")
        if not k or not re.fullmatch(r"[a-z0-9_]+", str(k)):
            errs.append(f"requires.fields: geçersiz anahtar {k!r}")
            continue
        keys.add(k)
        _bi(f.get("label"), f"fields.{k}.label", errs)
        if f.get("kind") not in KINDS:
            errs.append(f"fields.{k}: bilinmeyen tür {f.get('kind')!r}")
        if not isinstance(f.get("secret"), bool) or not isinstance(f.get("required"), bool):
            errs.append(f"fields.{k}: secret ve required bool olmalı")
        if f.get("secret") != (f.get("kind") == "secret"):
            errs.append(f"fields.{k}: secret bayrağı kind=secret ile tutarsız")
        if f.get("secret"):
            secret_keys.add(k)
        elif _SECRETISH.search(k) and f.get("kind") != "path":
            errs.append(f"fields.{k}: sır gibi görünüyor ama secret:true değil")
        if f.get("help") is not None:
            _bi(f["help"], f"fields.{k}.help", errs, need=False)
    for s in r.get("secrets") or []:
        if s not in secret_keys:
            errs.append(f"requires.secrets: {s} secret:true bir alan olarak tanımlı değil")
    for k in secret_keys:
        if k not in (r.get("secrets") or []):
            errs.append(f"requires.secrets: secret alan {k} listede yok")
    hw = r.get("hardware") or {}
    for k in hw:
        if k not in ("gpu_vram_gb", "ram_gb", "sensor"):
            errs.append(f"requires.hardware: bilinmeyen anahtar {k}")
    if not isinstance(r.get("apps", []), list):
        errs.append("requires.apps: liste olmalı")


APP_METHODS = ("nsis-silent", "zip-extract")


def _check_app(a, errs: list[str]) -> None:
    """Modül manifestindeki `app:` bölümü (sb/apps.py okur): resmî sürüm paketi + kurulum + veri yolu."""
    if not isinstance(a, dict):
        errs.append("app: sözlük olmalı")
        return
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", str(a.get("repo") or "")):
        errs.append("app.repo 'sahip/depo' biçiminde olmalı")
    if not isinstance(a.get("size_mb"), (int, float)) or a["size_mb"] <= 0:
        errs.append("app.size_mb pozitif sayı olmalı")
    try:
        re.compile(str(a.get("tag_pattern") or ""))
    except re.error:
        errs.append("app.tag_pattern geçerli düzenli ifade olmalı")
    _bi(a.get("about"), "app.about", errs)
    if not any(a.get(k) for k in ("win", "mac")):
        errs.append("app: en az bir platform (win/mac) gerekli")
    for plat_ in ("win", "mac"):
        s = a.get(plat_)
        if s is None:
            continue
        need = ("version", "tag", "asset", "sums", "method", "exe", "process", "data")
        miss = [k for k in need if not s.get(k)]
        if miss:
            errs.append(f"app.{plat_}: eksik alan {', '.join(miss)}")
        if s.get("method") not in APP_METHODS:
            errs.append(f"app.{plat_}.method {APP_METHODS} içinden olmalı")
        if s.get("method") == "zip-extract" and not s.get("install_dir"):
            errs.append(f"app.{plat_}: zip-extract için install_dir gerekli")
        if "/" in str(s.get("asset", "")) or "\\" in str(s.get("asset", "")):
            errs.append(f"app.{plat_}.asset dosya adı olmalı (yol değil)")
        if not re.fullmatch(r"[0-9a-f]{64}", str(s.get("sha256") or "")):
            errs.append(f"app.{plat_}.sha256 gerekli: bilinen iyi dosyanın 64 haneli küçük harfli SHA-256 özeti (güven zinciri sabitlemesi)")


def validate_manifest(m: dict, ids: set[str] | None = None) -> list[str]:
    errs: list[str] = []
    t, id_ = m.get("type"), m.get("id")
    if t not in TYPES:
        return [f"type geçersiz: {t!r}"]
    if not id_ or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", str(id_)):
        errs.append(f"id geçersiz: {id_!r}")
    if m.get("_file") and m["_file"] != f"{t}/{id_}.yaml":
        errs.append(f"dosya adı id ile aynı olmalı ({m['_file']})")
    _bi(m.get("name"), "name", errs)
    _bi(m.get("desc"), "desc", errs)
    if m.get("category") not in categories():
        errs.append(f"category bilinmiyor: {m.get('category')!r}")
    if not isinstance(m.get("default_on", True), bool):
        errs.append("default_on bool olmalı")
    _check_requires(m, errs)
    h = m.get("health")
    if not (isinstance(h, dict) and str(h.get("cli", "")).startswith("sb ")):
        errs.append("health.cli 'sb ...' ile başlamalı")
    if m.get("docs") and not (CODE / m["docs"]).exists():
        errs.append(f"docs bulunamadı: {m['docs']}")
    known = ids if ids is not None else {k.split(":", 1)[1] for k, v in _load().items() if v["type"] == "module"}
    ps = presets()
    if t in ("module", "source", "mcp"):
        for p in m.get("presets") or []:
            ax, _, val = str(p).partition(":")
            if ax not in AXES or val not in (ps.get("axes", {}).get(ax) or {}):
                errs.append(f"presets: bilinmeyen hazır seçim {p}")
        for i in m.get("catalog_ids") or []:
            if not isinstance(i, int):
                errs.append(f"catalog_ids: tamsayı olmalı ({i!r})")
    if t == "module":
        mod = m.get("module")
        if mod is not None and mod not in module_keys():
            errs.append(f"module: {mod!r} sb/features.py MODULES içinde yok")
        if mod is not None and mod != id_:
            errs.append("module anahtarı id ile aynı olmalı")
        if not isinstance(m.get("catalog_ids"), list):
            errs.append("catalog_ids liste olmalı")
        if m.get("app") is not None:
            _check_app(m["app"], errs)
    elif t == "source":
        imp = m.get("import") or {}
        if not imp.get("formats") or not isinstance(imp["formats"], list):
            errs.append("import.formats dolu liste olmalı")
        ht = imp.get("how_to") or {}
        for lang in ("tr", "en"):
            txt = ht.get(lang) or ""
            if len(txt) < 150 or not re.search(r"^1\. ", txt, re.M) or not re.search(r"^2\. ", txt, re.M):
                errs.append(f"import.how_to.{lang}: adım adım (1. 2. …) ve ayrıntılı olmalı")
        c = imp.get("connector")
        if c is not None and c not in registry_names():
            errs.append(f"import.connector REGISTRY'de yok: {c}")
        if m.get("parent") not in known:
            errs.append(f"parent bulunamadı: {m.get('parent')!r}")
    elif t == "mcp":
        mc = m.get("mcp") or {}
        if not isinstance(mc.get("args", []), list) or not isinstance(mc.get("env", {}), dict):
            errs.append("mcp.args liste, mcp.env sözlük olmalı")
        if mc.get("install") is not None and not isinstance(mc["install"], str):
            errs.append("mcp.install metin ya da null olmalı")
        if mc.get("install") is None and not mc.get("docs_url"):
            errs.append("mcp.install null ise docs_url zorunlu")
        if not str(mc.get("docs_url") or "").startswith(("http", "docs/")):
            errs.append("mcp.docs_url gerekli (http... ya da docs/...)")
        if not mc.get("command") and not mc.get("remote"):
            errs.append("mcp.command boşsa remote:true olmalı")
        fkeys = {f["key"] for f in (m.get("requires") or {}).get("fields") or []}
        for v in list((mc.get("env") or {}).values()) + [a for a in mc.get("args") or []]:
            mm = _REF.match(str(v))
            if mm and mm.group(1) not in fkeys:
                errs.append(f"mcp: {{{mm.group(1)}}} için requires.fields tanımı yok")
    elif t == "sector":
        for k in ("modules", "sources", "mcp"):
            for x in m.get(k) or []:
                want = {"modules": "module", "sources": "source", "mcp": "mcp"}[k]
                if not get(x, want):
                    errs.append(f"sector.{k}: {x} bulunamadı ya da türü yanlış")
        for x in m.get("disabled") or []:
            if not get(x, "module"):
                errs.append(f"sector.disabled: {x} bir modül değil")
            if x in (m.get("modules") or []):
                errs.append(f"sector.disabled: {x} hem modules hem disabled içinde")
        pr = m.get("presets") or {}
        for ax, val in pr.items():
            if ax not in AXES or (val is not None and val not in (ps.get("axes", {}).get(ax) or {})):
                errs.append(f"sector.presets: {ax}={val!r} geçersiz")
        for r in m.get("roles") or []:
            _bi(r.get("name"), f"roles.{r.get('id')}.name", errs)
        rids = {r["id"] for r in m.get("roles") or []}
        rep_ids = {r["id"] for r in m.get("reports") or []}
        for r in m.get("roles") or []:
            for x in r.get("reports") or []:
                if x not in rep_ids:
                    errs.append(f"sector.roles.{r['id']}: bilinmeyen rapor {x}")
        if not rids:
            errs.append("sector.roles boş olamaz")
    return errs


def validate() -> list[str]:
    errs: list[str] = []
    ids = {m["id"] for m in all("module")}
    for m in all():
        errs += [f"{m['id']}: {e}" for e in validate_manifest(m, ids)]
    return errs


# ------------------------------------------------------------------ hazır seçimler (4 eksen)
def _axis(ax: str, val):
    if val is None:
        return None
    d = (presets().get("axes", {}).get(ax) or {})
    if val not in d:
        raise ValueError(f"Bilinmeyen {ax} seçimi: {val} (seçenekler: {', '.join(d)})")
    return d[val]


def combine(meslek: str | None = None, donanim: str | None = None, gizlilik: str | None = None, yogunluk: str | None = None,
            ram_gb: float | None = None) -> dict:
    """Sıra: yoğunluk tabanı → meslek ekler → gizlilik/donanım kısıtlar.
    Dönüş: {modules: {MODULES anahtarı: bool}, extras: {yol haritası grubu: bool}, models, privacy_profile, warnings}."""
    dflt = presets().get("defaults") or {}
    donanim = donanim or dflt.get("donanim")
    gizlilik = gizlilik or dflt.get("gizlilik")
    yogunluk = yogunluk or dflt.get("yogunluk")
    warnings: list[str] = []
    on: set[str] = set(_axis("yogunluk", yogunluk)["modules"])
    if meslek:
        on |= set(_axis("meslek", meslek)["add"])
    gz, dn = _axis("gizlilik", gizlilik), _axis("donanim", donanim)
    for d in (gz, dn):
        for k in (d or {}).get("off") or []:
            if k in on:
                warnings.append(f"{k} kapatıldı ({'gizlilik' if d is gz else 'donanım'} kısıtı)")
            on.discard(k)
    changed = True
    while changed:                                            # bağımlılık: gereken modül kapalıysa bağımlı da kapanır
        changed = False
        for k, deps in DEPENDS.items():
            if k in on and deps and not any(x in on for x in deps):
                on.discard(k)
                changed = True
                warnings.append(f"{k} kapatıldı (gereken modül kapalı: {', '.join(deps)})")
    models = {"profile": "medium", "local_model": True, "cloud": True, "prefer_cloud": False}
    if dn:
        dm = dict(dn.get("models") or {})
        ge = dm.pop("profile_if_ram_gb_ge", None)
        if ge and ram_gb is not None:
            for thr, prof in sorted(ge.items(), key=lambda kv: float(kv[0])):
                if ram_gb >= float(thr):
                    dm["profile"] = prof
        models.update(dm)
    if gz:
        models.update(gz.get("models") or {})
        if gz["privacy_profile"]["mode"] == "tam_yerel" and models["profile"] == "cloud":
            models.update({"profile": "small", "local_model": True})
            warnings.append("Tam yerel gizlilik + zayıf donanım: küçük yerel model kullanılır, kalite düşebilir")
    if models["profile"] == "cloud" and not models["cloud"]:
        models["cloud"] = True
    mk = module_keys()
    return {"modules": {k: k in on for k in sorted(mk)}, "extras": {k: True for k in sorted(on - mk)},
            "models": models, "privacy_profile": dict(gz["privacy_profile"]) if gz else None, "warnings": warnings,
            "axes": {"meslek": meslek, "donanim": donanim, "gizlilik": gizlilik, "yogunluk": yogunluk}}


def for_preset(*specs: str, **axes: str | None) -> list[dict]:
    """Seçime göre manifestler. `for_preset("meslek:ogrenci")` ya da `for_preset(meslek="ogrenci", yogunluk="gunluk")`.
    Modüller birleşik sonuca (combine) göre; kaynak ve MCP'ler `presets` listesi seçilen eksen değerlerinden birini içeriyorsa."""
    for s in specs:
        ax, _, val = s.partition(":")
        if ax not in AXES:
            raise ValueError(f"Bilinmeyen eksen: {ax}")
        axes[ax] = val
    res = combine(**{k: axes.get(k) for k in AXES})
    on = {k for k, v in {**res["modules"], **res["extras"]}.items() if v}
    chosen = {f"{k}:{v}" for k, v in axes.items() if v}
    out = []
    for m in all():
        if m["type"] == "module":
            if m["id"] in on:
                out.append(m)
        elif m["type"] == "sector":
            continue
        elif chosen & set(m.get("presets") or []) or (m["type"] == "source" and m.get("parent") in on):
            out.append(m)
    return out


# ------------------------------------------------------------------ özellik ağacı
def features_tree() -> list[dict]:
    """Kategori → modül → katalog maddeleri (kurulum sihirbazındaki 'bütün özellikler' ekranı)."""
    from .features import catalog
    items = {i["id"]: i for i in catalog()}
    cats = categories()
    tree: dict[str, dict] = {c: {"category": c, "name": n, "modules": []} for c, n in cats.items()}
    for m in all("module"):
        node = {"id": m["id"], "name": m["name"], "desc": m["desc"], "module": m.get("module"), "default_on": m.get("default_on", True),
                "roadmap": bool(m.get("roadmap")), "requires": m["requires"],
                "items": [{k: items[i][k] for k in ("id", "ad", "faz", "durum")} for i in m.get("catalog_ids") or [] if i in items]}
        tree[m["category"]]["modules"].append(node)
    return [t for t in tree.values() if t["modules"]]


def tree_item_count() -> int:
    return sum(len(m["items"]) for c in features_tree() for m in c["modules"])


# ------------------------------------------------------------------ gereksinimler
def requirements(selection: dict) -> dict:
    """Seçime göre gereken şeyler. selection = {"modules": {id: bool} | [id], "sources": [id], "mcp": [id]}.
    Dönüş: {accounts, fields (anahtara göre tekil; required herhangi birinde true ise true), secrets, imports, mcps, apps, hardware}."""
    mods = selection.get("modules") or []
    mods = [k for k, v in mods.items() if v] if isinstance(mods, dict) else list(mods)
    picked = [get(x, "module") for x in mods] + [get(x, "source") for x in selection.get("sources") or []] + [get(x, "mcp") for x in selection.get("mcp") or []]
    unknown = [x for x, g in zip(list(mods) + list(selection.get("sources") or []) + list(selection.get("mcp") or []), picked) if g is None]
    accounts: list[str] = []
    fields: dict[str, dict] = {}
    apps: list[str] = []
    hw: dict[str, float] = {}
    imports, mcps = [], []
    for m in picked:
        if not m:
            continue
        r = m.get("requires") or {}
        accounts += [a for a in r.get("accounts") or [] if a not in accounts]
        for f in r.get("fields") or []:
            if f["key"] in fields:
                fields[f["key"]]["required"] = fields[f["key"]]["required"] or f["required"]
                fields[f["key"]]["needed_by"].append(m["id"])
            else:
                fields[f["key"]] = {**f, "needed_by": [m["id"]]}
        apps += [a for a in r.get("apps") or [] if a not in apps]
        for k, v in (r.get("hardware") or {}).items():
            if isinstance(v, (int, float)):
                hw[k] = max(hw.get(k, 0), v)
        if m["type"] == "source":
            imports.append({"id": m["id"], "name": m["name"], "formats": m["import"]["formats"], "how_to": m["import"]["how_to"],
                            "connector": m["import"].get("connector")})
        if m["type"] == "mcp":
            mcps.append({"id": m["id"], "name": m["name"], "install": m["mcp"].get("install"), "docs_url": m["mcp"].get("docs_url")})
    return {"accounts": accounts, "fields": list(fields.values()), "secrets": [k for k, f in fields.items() if f["secret"]],
            "imports": imports, "mcps": mcps, "apps": apps, "hardware": hw, "unknown": unknown}
