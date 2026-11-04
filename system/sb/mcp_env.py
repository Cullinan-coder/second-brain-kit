"""MCP sunucusu sarmalayıcısı (denetim D-16): sırları `claude mcp add -e KEY=değer` ile ~/.claude.json'a DÜZ METİN yazmak yerine
çalışma anında şifre kasasından (keyring) okur ve asıl komutu o ortamla başlatır.

Kullanım (kurulum motoru üretir):
    python -m sb.mcp_env --env BRAVE_API_KEY=@ring:mcp-brave-search-brave-key -- npx -y paket@1.2.3 @ring:mcp-postgres-postgres-url

- `--env AD=@ring:ANAHTAR`: AD ortam değişkeni, keyring'deki `ANAHTAR` kaydının değeri olur.
- Komut bağımsız değişkenlerinde TAM eşleşen `@ring:ANAHTAR` öğeleri değerle değiştirilir (ör. bağlantı adresi).
Değerler ne yapılandırmada ne de süreç bağımsız değişkeni listesinde (yalnız çocuk sürecin kendi argv'sinde, gerekiyorsa) görünür.
"""
from __future__ import annotations

import os
import subprocess
import sys

PREFIX = "@ring:"


def _secret(name: str) -> str:
    import keyring

    from .config import KEYRING_SERVICE
    v = keyring.get_password(KEYRING_SERVICE, name)
    if not v:
        raise SystemExit(f"şifre kasasında '{name}' kaydı yok (Kurulum > MCP'den yeniden kur)")
    return v


def resolve(argv: list[str], getter=_secret) -> tuple[dict[str, str], list[str]]:
    """(ek ortam, çözülmüş komut). `--env AD=@ring:K` ... `--` komut bağımsız değişkenleri."""
    env: dict[str, str] = {}
    i = 0
    while i < len(argv) and argv[i] != "--":
        a = argv[i]
        if a == "--env" and i + 1 < len(argv):
            k, _, ref = argv[i + 1].partition("=")
            if not ref.startswith(PREFIX):
                raise SystemExit(f"geçersiz --env: {k}")
            env[k] = getter(ref[len(PREFIX):])
            i += 2
        else:
            raise SystemExit(f"beklenmeyen bağımsız değişken: {a}")
    cmd = [getter(a[len(PREFIX):]) if a.startswith(PREFIX) else a for a in argv[i + 1:]]
    if not cmd:
        raise SystemExit("çalıştırılacak komut yok")
    return env, cmd


def main(argv: list[str] | None = None) -> int:
    extra, cmd = resolve(list(sys.argv[1:] if argv is None else argv))
    return subprocess.call(cmd, env={**os.environ, **extra})


if __name__ == "__main__":
    raise SystemExit(main())
