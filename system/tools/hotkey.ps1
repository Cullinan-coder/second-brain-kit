# "Beyne at" kisayollari:
#  - Ctrl+Alt+B: panodaki baglanti/metni (ya da ekran goruntusunu) kasaya kaydeder (sb capture)
#  - Sag tik > Gonder > "Beyne At": secilen dosyayi kasaya kaydeder (sb capture --file)
# Baslat menusunde kisayol tusu atanmis bir .lnk olusturur (Windows kisayol tuslarini yalniz Baslat/Masaustu kisayollarinda dinler).
# Calistirma: powershell -ExecutionPolicy Bypass -File hotkey.ps1 [-Remove] [-Key "CTRL+ALT+B"]
param([switch]$Remove, [string]$Key = "CTRL+ALT+B")
$ErrorActionPreference = "Stop"
$lnk = Join-Path ([Environment]::GetFolderPath("Programs")) "Beyne at.lnk"
$sendto = Join-Path ([Environment]::GetFolderPath("SendTo")) "Beyne At.lnk"
if ($Remove) {
    Remove-Item $lnk, $sendto -ErrorAction SilentlyContinue
    Write-Host "Kisayollar kaldirildi."
    exit 0
}
$sys = Split-Path $PSScriptRoot -Parent
$pyw = Join-Path $sys ".venv\Scripts\pythonw.exe"      # pencere acmadan calisir; sonuc bildirimle gelir
if (-not (Test-Path $pyw)) { throw "pythonw bulunamadi: $pyw (once 'uv sync' calistir)" }
$sh = New-Object -ComObject WScript.Shell
$s = $sh.CreateShortcut($lnk)
$s.TargetPath = $pyw
$s.Arguments = "-X utf8 -m sb capture"
$s.WorkingDirectory = $sys
$s.Hotkey = $Key
$s.Description = "Second Brain: panodakini kasaya at"
$s.Save()
# Gonder menusu: Windows secilen dosyanin yolunu sona ekler -> sb capture --file <yol>
$t = $sh.CreateShortcut($sendto)
$t.TargetPath = $pyw
$t.Arguments = "-X utf8 -m sb capture --file"
$t.WorkingDirectory = $sys
$t.Description = "Second Brain: dosyayi kasaya at"
$t.Save()
Write-Host "Kaydedildi: $Key -> Beyne at ($lnk) + Gonder > Beyne At ($sendto)"
