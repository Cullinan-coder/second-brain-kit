# Second Brain Kit — Windows tek komut kurulum.
# Tek satir (PowerShell):  irm https://raw.githubusercontent.com/<hesap>/second-brain-kit/main/install.ps1 | iex
# Repo klasorunde:         powershell -ExecutionPolicy Bypass -File install.ps1        (kurulum paneli)
# Eski soru-cevap kurucu:  powershell -ExecutionPolicy Bypass -File install.ps1 --cli  (ya da install.py argumanlari: --yes, --answers ...)
# Ortam: SB_REPO_ZIP (repo zip adresi), SB_REPO_GIT (git adresi), SB_DIR (indirme klasoru, varsayilan ~\SecondBrainKit)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv (Python paket yoneticisi) kuruluyor..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Uyari: git yok. 'winget install Git.Git' ile kurman onerilir (geri alma ve yedek icin)."
}
# Repo yoksa (irm | iex ile calistirildi) indir: once git clone, olmazsa zip.
if (-not $root -or -not (Test-Path (Join-Path $root "install.py"))) {
    $dest = if ($env:SB_DIR) { $env:SB_DIR } else { Join-Path $env:USERPROFILE "SecondBrainKit" }
    $gitUrl = if ($env:SB_REPO_GIT) { $env:SB_REPO_GIT } else { "https://github.com/kullanici/second-brain-kit.git" }
    $zipUrl = if ($env:SB_REPO_ZIP) { $env:SB_REPO_ZIP } else { "https://github.com/kullanici/second-brain-kit/archive/refs/heads/main.zip" }
    if (Test-Path (Join-Path $dest "install.py")) {
        Write-Host "Mevcut kit kullaniliyor: $dest"
    } elseif (Get-Command git -ErrorAction SilentlyContinue) {
        git clone --depth 1 $gitUrl $dest
    } else {
        $tmp = Join-Path $env:TEMP "sb-kit.zip"
        Invoke-WebRequest -Uri $zipUrl -OutFile $tmp
        $x = Join-Path $env:TEMP "sb-kit-x"
        if (Test-Path $x) { Remove-Item -Recurse -Force $x }
        Expand-Archive -Path $tmp -DestinationPath $x
        New-Item -ItemType Directory -Force $dest | Out-Null
        Copy-Item -Path (Join-Path (Get-ChildItem $x | Select-Object -First 1).FullName "*") -Destination $dest -Recurse -Force
    }
    $root = $dest
}
Set-Location $root
if ($args.Count -gt 0) {
    $rest = @($args | Where-Object { $_ -ne "--cli" })
    uv run --no-project --python 3.12 --with pyyaml install.py @rest
} else {
    $sys = @($root, (Join-Path $root "system"), (Join-Path $root "_system")) | Where-Object { Test-Path (Join-Path $_ "setup\app.py") } | Select-Object -First 1
    if (-not $sys) { Write-Error "setup/app.py bulunamadı ($root)"; exit 1 }
    uv run --directory $sys --python 3.12 --with pywebview python setup/app.py
}
