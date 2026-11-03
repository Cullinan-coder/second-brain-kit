#!/usr/bin/env bash
# Second Brain Kit — macOS (ve Linux) tek komut kurulum.
# Tek satır:           curl -LsSf https://raw.githubusercontent.com/<hesap>/second-brain-kit/main/install.sh | bash
#   macOS varsayılanı: son Release'ten "Second Brain Setup.app" (zip) Masaüstüne indirilir ve açılır (sihirbaz).
#   Depo gizli: önce `gh` CLI (gh auth login), yoksa GITHUB_TOKEN / SB_GH_TOKEN ile API; ikisi de yoksa yol anlatılır ve
#   kaynak koddan kuruluma (uv + setup/app.py) düşülür. Linux'ta doğrudan kaynak koddan kurulur.
# Repo klasöründe:     bash install.sh --source   (kaynak koddan kurulum paneli)
# Eski soru-cevap:     bash install.sh --cli      (ya da install.py argümanları: --yes, --answers ...)
# Ortam: SB_REPO (varsayılan Cullinan-coder/second-brain-kit), SB_GH_TOKEN/GITHUB_TOKEN, SB_REPO_ZIP, SB_REPO_GIT, SB_DIR (varsayılan ~/SecondBrainKit)
set -euo pipefail
REPO="${SB_REPO:-Cullinan-coder/second-brain-kit}"
ASSET="Second-Brain-Setup-macOS.zip"
WANT_CLI=0; WANT_SOURCE=0; REST=()
for a in "$@"; do
  case "$a" in --cli) WANT_CLI=1 ;; --source) WANT_SOURCE=1 ;; *) REST+=("$a") ;; esac
done
SRC="${BASH_SOURCE[0]:-}"
ROOT=""
[ -n "$SRC" ] && [ -f "$SRC" ] && ROOT="$(cd "$(dirname "$SRC")" && pwd)"

download_setup() {   # indirilen zip yolunu yazdırır; olmazsa 1 döner
  local tmp; tmp="$(mktemp -d)"
  if command -v gh >/dev/null 2>&1; then
    echo "gh CLI ile son sürüm indiriliyor ($REPO)..." >&2
    if gh release download --repo "$REPO" --pattern "$ASSET" --dir "$tmp" --clobber >&2 && [ -f "$tmp/$ASSET" ]; then
      echo "$tmp/$ASSET"; return 0
    fi
  fi
  local token="${SB_GH_TOKEN:-${GITHUB_TOKEN:-}}"
  if [ -n "$token" ] && command -v python3 >/dev/null 2>&1; then
    echo "GitHub API ile son sürüm indiriliyor ($REPO)..." >&2
    local json url
    json="$(curl -fsSL -H "Authorization: Bearer $token" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$REPO/releases/latest")" || json=""
    url="$(printf '%s' "$json" | ASSET="$ASSET" python3 -c 'import json,os,sys
try:
    d=json.load(sys.stdin)
    print(next((a["url"] for a in d.get("assets",[]) if a["name"]==os.environ["ASSET"]),""))
except Exception:
    print("")')"
    if [ -n "$url" ] && curl -fsSL -H "Authorization: Bearer $token" -H "Accept: application/octet-stream" "$url" -o "$tmp/$ASSET"; then
      echo "$tmp/$ASSET"; return 0
    fi
  fi
  return 1
}

if [ "$(uname -s)" = "Darwin" ] && [ "$WANT_CLI" = 0 ] && [ "$WANT_SOURCE" = 0 ] && [ "${#REST[@]}" = 0 ]; then
  if ZIP="$(download_setup)"; then
    DEST="$HOME/Desktop/Second Brain Setup.app"
    rm -rf "$DEST"
    ditto -x -k "$ZIP" "$HOME/Desktop"
    xattr -dr com.apple.quarantine "$DEST" 2>/dev/null || true
    echo "Masaüstüne indirildi: $DEST"
    echo "İlk açılışta macOS uyarı verirse: sağ tık > Aç (uygulama imzasız)."
    open "$DEST"
    exit 0
  fi
  cat >&2 <<EOF

Setup indirilemedi. Depo gizli olduğu için giriş gerekir. Şu yollardan biri:
  1) GitHub CLI: brew install gh && gh auth login   (sonra bu komutu yeniden çalıştır)
  2) Erişim jetonu (repo okuma yetkili):  SB_GH_TOKEN=ghp_... bash install.sh
  3) Tarayıcıdan indir: https://github.com/$REPO/releases/latest  ($ASSET)
Şimdilik kaynak koddan kurulum deneniyor (uv + setup/app.py)...
EOF
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv (Python paket yöneticisi) kuruluyor..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v git >/dev/null 2>&1 || echo "Uyarı: git yok (macOS: xcode-select --install)."
# Repo yoksa (curl | bash ile çalıştırıldı) indir: önce git clone, olmazsa zip.
if [ -z "$ROOT" ] || [ ! -f "$ROOT/install.py" ]; then
  DEST="${SB_DIR:-$HOME/SecondBrainKit}"
  GIT_URL="${SB_REPO_GIT:-https://github.com/$REPO.git}"
  ZIP_URL="${SB_REPO_ZIP:-https://github.com/$REPO/archive/refs/heads/main.zip}"
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
if [ "$WANT_CLI" = 1 ] || [ "${#REST[@]}" -gt 0 ]; then
  uv run --no-project --python 3.12 --with pyyaml install.py ${REST[@]+"${REST[@]}"}
else
  SYS=""; for d in "$ROOT" "$ROOT/system" "$ROOT/_system"; do [ -f "$d/setup/app.py" ] && SYS="$d" && break; done
  [ -n "$SYS" ] || { echo "setup/app.py bulunamadı ($ROOT)" >&2; exit 1; }
  uv run --directory "$SYS" --python 3.12 --with pywebview python setup/app.py
fi
