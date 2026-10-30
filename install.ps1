# Second Brain Kit — Windows tek komut kurulum.
# Kullanim (PowerShell, repo klasorunde):  powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv (Python paket yoneticisi) kuruluyor..."
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Uyari: git yok. 'winget install Git.Git' ile kurman onerilir (geri alma ve yedek icin)."
}
uv run --no-project --python 3.12 --with pyyaml install.py @args
