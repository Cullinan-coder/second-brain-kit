#!/usr/bin/env bash
# Second Brain Kit — macOS (ve Linux) tek komut kurulum.
# Kullanım (repo klasöründe):  bash install.sh
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv (Python paket yöneticisi) kuruluyor..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v git >/dev/null 2>&1 || echo "Uyarı: git yok (macOS: xcode-select --install)."
uv run --no-project --python 3.12 --with pyyaml install.py "$@"
