#!/usr/bin/env bash
# Second Brain Kit — macOS (ve Linux) tek komut kurulum.
# Tek satır:           curl -LsSf https://raw.githubusercontent.com/<hesap>/second-brain-kit/main/install.sh | bash
# Repo klasöründe:     bash install.sh          (kurulum paneli)
# Eski soru-cevap:     bash install.sh --cli    (ya da install.py argümanları: --yes, --answers ...)
# Ortam: SB_REPO_ZIP (zip adresi), SB_REPO_GIT (git adresi), SB_DIR (indirme klasörü, varsayılan ~/SecondBrainKit)
set -euo pipefail
SRC="${BASH_SOURCE[0]:-}"
ROOT=""
[ -n "$SRC" ] && [ -f "$SRC" ] && ROOT="$(cd "$(dirname "$SRC")" && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv (Python paket yöneticisi) kuruluyor..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v git >/dev/null 2>&1 || echo "Uyarı: git yok (macOS: xcode-select --install)."
# Repo yoksa (curl | bash ile çalıştırıldı) indir: önce git clone, olmazsa zip.
if [ -z "$ROOT" ] || [ ! -f "$ROOT/install.py" ]; then
  DEST="${SB_DIR:-$HOME/SecondBrainKit}"
  GIT_URL="${SB_REPO_GIT:-https://github.com/kullanici/second-brain-kit.git}"
  ZIP_URL="${SB_REPO_ZIP:-https://github.com/kullanici/second-brain-kit/archive/refs/heads/main.zip}"
  if [ -f "$DEST/install.py" ]; then
    echo "Mevcut kit kullanılıyor: $DEST"
  elif command -v git >/dev/null 2>&1; then
    git clone --depth 1 "$GIT_URL" "$DEST"
  else
    TMP="$(mktemp -d)"
    curl -LsSf "$ZIP_URL" -o "$TMP/kit.zip"
    unzip -q "$TMP/kit.zip" -d "$TMP/x"
    mkdir -p "$DEST"
    cp -R "$TMP"/x/*/. "$DEST"/
  fi
  ROOT="$DEST"
fi
cd "$ROOT"
if [ "$#" -gt 0 ]; then
  [ "$1" = "--cli" ] && shift
  uv run --no-project --python 3.12 --with pyyaml install.py "$@"
else
  SYS=""; for d in "$ROOT" "$ROOT/system" "$ROOT/_system"; do [ -f "$d/setup/app.py" ] && SYS="$d" && break; done
  [ -n "$SYS" ] || { echo "setup/app.py bulunamadı ($ROOT)" >&2; exit 1; }
  uv run --directory "$SYS" --python 3.12 --with pywebview python setup/app.py
fi
