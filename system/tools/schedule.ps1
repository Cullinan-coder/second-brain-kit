# Second Brain zamanlanmis gorevleri (Windows Gorev Zamanlayici). macOS icin: tools/schedule_macos.py
# Calistirma: powershell -ExecutionPolicy Bypass -File schedule.ps1 [-Remove]
# Gorevler sadece kullanici oturum aciksa calisir (sifreler Windows Kimlik Yoneticisi'nde); kacirilan calisma
# bilgisayar acilinca / oturum acilinca yapilir (StartWhenAvailable). Cift calisma sb icindeki kilitle engellenir.
param([switch]$Remove)
$ErrorActionPreference = "Stop"
$tasks = @("SecondBrain-Daily", "SecondBrain-Weekly")
if ($Remove) {
    foreach ($t in ($tasks + "SecondBrain-Syncthing", "SecondBrain-Chat")) { Unregister-ScheduledTask -TaskName $t -Confirm:$false -ErrorAction SilentlyContinue }
    & (Join-Path $PSScriptRoot "hotkey.ps1") -Remove
    Write-Host "Gorevler kaldirildi."
    exit 0
}
$uv = (Get-Command uv).Source
$sys = Split-Path $PSScriptRoot -Parent          # bu betik _system/tools içinde; kasa nerede olursa olsun çalışır
# Tek tirnakli PowerShell dizgesine gomulecek yol: ' -> '' (yolda O'Brien gibi bir ad ic komutu bozmasin / kaydirmasin)
function Quote-Ps([string]$v) { return "'" + $v.Replace("'", "''") + "'" }

function Register-Brain($name, $cmd, $trigger, $desc, $limitHours = 8) {
    $inner = "& $(Quote-Ps $uv) run --directory $(Quote-Ps $sys) python -X utf8 -m sb $cmd"
    $action = New-ScheduledTaskAction -Execute "conhost.exe" -Argument "--headless powershell.exe -NoProfile -Command `"$inner`""
    # 0 = süre sınırı yok (sürekli çalışan asistan sunucusu için; 8 saatte Windows kapatıyordu)
    $limit = if ($limitHours -gt 0) { New-TimeSpan -Hours $limitHours } else { New-TimeSpan -Seconds 0 }
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit $limit -MultipleInstances IgnoreNew
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
        -Description $desc -Force | Out-Null
    Write-Host "Kaydedildi: $name -> sb $cmd"
}

# Gunluk: oturum acildiktan 10 dk sonra (acilis yuku gecsin) + bilgisayar zaten aciksa 13:00.
# Ayni gun ikinci kez calismaz (sb daily "bugun calisti" kaydi tutar). Ayşe bilgisayari genelde 12-13 arasi aciyor.
$logon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$logon.Delay = "PT10M"
$noon = New-ScheduledTaskTrigger -Daily -At "13:00"
Register-Brain "SecondBrain-Daily" "daily" @($logon, $noon) "Second Brain: tum kaynaklari guncelle, ozet maili gonder"
Register-Brain "SecondBrain-Weekly" "weekly" (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "15:00") "Second Brain: haftalik denetim ve ozet"
# Yerel asistan sunucusu (Obsidian > Asistan.md): oturum acilinca arka planda baslar.
# Gece kosusu zamanlanmaz: kullanici asistana "gece kosusunu baslat" deyince baslar (sb night --start).
Register-Brain "SecondBrain-Chat" "chat" (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME) "Second Brain: yerel asistan sunucusu" 0
$tasks += "SecondBrain-Chat"
# Syncthing (telefon eslemesi): oturum acilinca arka planda baslar, surekli calisir.
# Ikili YALNIZ bilinen kurulum yollarindan ya da PATH'ten alinir (eskiden ev klasorunde "ilk bulunan" calistirilirdi: Downloads\...\syncthing.exe).
$st = $null
$known = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Syncthing\syncthing.exe"),
    (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\syncthing.exe"),
    (Join-Path $env:ProgramFiles "Syncthing\syncthing.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Syncthing\syncthing.exe")
)
foreach ($c in $known) { if ($c -and (Test-Path -LiteralPath $c)) { $st = $c; break } }
if (-not $st) { $st = (Get-Command syncthing -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source }
if ($st -and (Test-Path $st)) {
    $action = New-ScheduledTaskAction -Execute "conhost.exe" -Argument "--headless `"$st`" --no-browser --no-console"
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -MultipleInstances IgnoreNew
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName "SecondBrain-Syncthing" -Action $action -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME) `
        -Settings $settings -Principal $principal -Description "Second Brain: telefon eslemesi (Syncthing)" -Force | Out-Null
    Write-Host "Kaydedildi: SecondBrain-Syncthing (oturum acilinca baslar)"
    $tasks += "SecondBrain-Syncthing"
}
& (Join-Path $PSScriptRoot "hotkey.ps1")      # Ctrl+Alt+B: Beyne at
Get-ScheduledTask -TaskName $tasks | Get-ScheduledTaskInfo | Select-Object TaskName, NextRunTime | Format-Table -AutoSize
