# "Beyne at" kisayolu: Ctrl+Alt+B panodaki baglanti/metni kasaya kaydeder (sb capture).
# Baslat menusunde kisayol tusu atanmis bir .lnk olusturur (Windows kisayol tuslarini yalniz Baslat/Masaustu kisayollarinda dinler).
# Calistirma: powershell -ExecutionPolicy Bypass -File hotkey.ps1 [-Remove] [-Key "CTRL+ALT+B"]
param([switch]$Remove, [string]$Key = "CTRL+ALT+B")
$ErrorActionPreference = "Stop"
$lnk = Join-Path ([Environment]::GetFolderPath("Programs")) "Beyne at.lnk"
if ($Remove) {
    Remove-Item $lnk -ErrorAction SilentlyContinue
    Write-Host "Kisayol kaldirildi."
    exit 0
}
$sys = Split-Path $PSScriptRoot -Parent
$pyw = Join-Path $sys ".venv\Scripts\pythonw.exe"      # pencere acmadan calisir; sonuc bildirimle gelir
if (-not (Test-Path $pyw)) { throw "pythonw bulunamadi: $pyw (once 'uv sync' calistir)" }
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
$s.TargetPath = $pyw
$s.Arguments = "-X utf8 -m sb capture"
$s.WorkingDirectory = $sys
$s.Hotkey = $Key
$s.Description = "Second Brain: panodakini kasaya at"
$s.Save()
Write-Host "Kaydedildi: $Key -> Beyne at ($lnk)"
