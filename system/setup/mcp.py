"""MCP sunucuları: katalog + kurulu olanlar (`claude mcp list`, Claude Desktop yapılandırması), kurma, özel ekleme, kaldırma.

Komutlar yalnız `engine._run_capture/_run_stream` üzerinden; sırlar anahtar zincirine (`mcp-<id>-<alan>`) yazılır, günlükte maskelenir.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
from pathlib import Path

try:
    from . import accounts as A
    from . import engine as E
except ImportError:                                           # pragma: no cover
    import accounts as A  # type: ignore
    import engine as E  # type: ignore

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")
ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
REF_RE = re.compile(r"\{([a-z0-9_]+)\}")

def _uv() -> str:
    """PATH'te uv yoksa paketli Setup'ın gömülü/kalıcı uv'si (SB_UV) — engine.uv_bin ile aynı kural."""
    p = os.environ.get("SB_UV")
    return p if p and Path(p).is_file() and not shutil.which("uv") else "uv"



def desktop_config_path() -> Path:
    if E.WIN:
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "Claude" / "claude_desktop_config.json"
    if E.MAC:
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def installed() -> list[dict]:
    """[{name, source: claude-code|claude-desktop, command, status}] — ortam değişkeni DEĞERLERİ asla döndürülmez."""
    out: list[dict] = []
    if shutil.which("claude"):
        rc, txt = E._run_capture(["claude", "mcp", "list"], 60)
        if rc == 0:
            for ln in txt.splitlines():
                m = re.match(r"^([A-Za-z0-9][\w.-]*):\s+(.*?)(?:\s+-\s+(.*))?$", ln.strip())
                if m:
                    out.append({"name": m.group(1), "source": "claude-code", "command": m.group(2)[:200], "status": (m.group(3) or "").strip("✓✗! ")})
    try:
        cfg = json.loads(desktop_config_path().read_text(encoding="utf-8"))
        for name, v in (cfg.get("mcpServers") or {}).items():
            cmd = " ".join([str(v.get("command") or "")] + [str(a) for a in v.get("args") or []]) if isinstance(v, dict) else ""
            out.append({"name": str(name), "source": "claude-desktop", "command": cmd[:200], "status": ""})
    except (OSError, ValueError):
        pass
    return out


def overview(lang: str = "tr") -> dict:
    cat = E.catalog(lang)["mcps"]
    inst = installed()
    names = {i["name"] for i in inst}
    for m in cat:
        m["installed"] = m["id"] in names
        m["installable"] = m["install"] is not None
    return {"catalog": cat, "installed": inst, "claude_cli": bool(shutil.which("claude"))}


def _runner(cmd: str, args: list[str]) -> tuple[str, list[str]]:
    """Windows'ta npx/uvx .cmd olduğu için Claude Code `cmd /c` ister."""
    if E.WIN and cmd in ("npx", "npm", "uvx"):
        return "cmd", ["/c", cmd, *args]
    return cmd, args


def _add(name: str, command: str, args: list[str], env: dict[str, str], log) -> int:
    cmd, args = _runner(command, args)
    full = ["claude", "mcp", "add", name, "--scope", "user"]
    for k, v in env.items():
        full += ["-e", f"{k}={v}"]
    full += ["--", cmd, *args]
    return E._run_stream(full, log)


def install(eng, b: dict) -> dict:
    mid = str(b.get("id") or "")
    P = E.plugins_mod()
    m = P.get(mid, "mcp")
    if not m:
        raise ValueError(f"bilinmeyen MCP: {mid}")
    mc = m["mcp"]
    if mc.get("install") is None:
        return {"ok": False, "message": "Bu MCP elle bağlanır; belge bağlantısına bak.", "docs_url": mc.get("docs_url")}
    if not shutil.which("claude"):
        return {"ok": False, "message": "claude komutu bulunamadı (Claude Code kurulu değil)"}
    given = b.get("env") if isinstance(b.get("env"), dict) else {}
    fields = {f["key"]: f for f in (m.get("requires") or {}).get("fields") or []}
    vals: dict[str, str] = {}
    kr = E._keyring()
    for k, f in fields.items():
        v = given.get(k)
        ring = f"mcp-{mid}-{k}".replace("_", "-")
        if isinstance(v, str) and v:
            vals[k] = v
            if f.get("secret"):
                A._remember(eng, v)
                if not kr:
                    raise ValueError("şifre kasası (keyring) yok")
                kr.set_password(E.KEYRING_SERVICE, ring, v)
        elif f.get("secret") and kr:
            try:
                vals[k] = kr.get_password(E.KEYRING_SERVICE, ring) or ""
            except Exception:                                 # noqa: BLE001
                vals[k] = ""
        if f.get("required") and not vals.get(k):
            raise ValueError(f"gerekli alan eksik: {k}")
    log: list[str] = []

    def lg(line):
        log.append(E.redact(str(line), eng._secrets))
        eng.log(line)
    if mid == "second-brain":                                 # kaynak komut <python> yer tutucusu içerir: kasadaki ortamı kullan
        cmd, args = _uv(), ["run", "--directory", str(eng.code_root()), "python", "-m", "sb.mcp_server"]
    else:
        pre = shlex.split(mc["install"], posix=not E.WIN) if not mc["install"].startswith("claude ") else []
        if pre and E._run_stream(pre, lg):                    # ön koşul (npm view / docker pull / uvx --help)
            return {"ok": False, "message": f"Ön koşul başarısız: {pre[0]} kurulu mu? ({' '.join(pre)[:80]})", "log": log[-20:]}
        sub = lambda s: REF_RE.sub(lambda mm: vals.get(mm.group(1), ""), str(s))     # noqa: E731
        cmd, args = mc["command"], [sub(a) for a in mc.get("args") or []]
    env = {k: sub(v) for k, v in (mc.get("env") or {}).items()} if mid != "second-brain" else {}
    E._run_capture(["claude", "mcp", "remove", mid, "-s", "user"], 30)
    rc = _add(mid, cmd, args, env, lg)
    return {"ok": rc == 0, "message": "MCP eklendi" if rc == 0 else "claude mcp add başarısız", "log": log[-20:]}


def custom(eng, b: dict) -> dict:
    name, command = str(b.get("name") or ""), str(b.get("command") or "").strip()
    args, env = b.get("args") or [], b.get("env") or {}
    if not NAME_RE.match(name):
        raise ValueError("ad: harf/rakam/-/_ (en çok 40)")
    if not command or "\n" in command:
        raise ValueError("komut gerekli")
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        raise ValueError("args metin listesi olmalı")
    if not isinstance(env, dict) or not all(ENV_RE.match(str(k)) and isinstance(v, str) for k, v in env.items()):
        raise ValueError("env: {ORTAM_ADI: değer}")
    if not shutil.which("claude"):
        return {"ok": False, "message": "claude komutu bulunamadı (Claude Code kurulu değil)"}
    A._remember(eng, *env.values())                           # değerlerin hepsi sır sayılır
    log: list[str] = []
    rc = _add(name, command, list(args), dict(env), lambda l: (log.append(E.redact(str(l), eng._secrets)), eng.log(l)))
    return {"ok": rc == 0, "message": "MCP eklendi" if rc == 0 else "claude mcp add başarısız", "log": log[-20:]}


def remove(eng, b: dict) -> dict:
    name = str(b.get("name") or "")
    if not NAME_RE.match(name):
        raise ValueError("geçersiz ad")
    if not shutil.which("claude"):
        return {"ok": False, "message": "claude komutu bulunamadı"}
    rc, out = E._run_capture(["claude", "mcp", "remove", name, "-s", "user"], 30)
    return {"ok": rc == 0, "message": "MCP kaldırıldı" if rc == 0 else E.redact(out.strip()[-200:], eng._secrets)}
