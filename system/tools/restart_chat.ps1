# Asistan sunucusunu yeniden baslatir (kod degisikliginden sonra).
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "-m sb chat" -and $_.ProcessId -ne $PID } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep 3
Stop-ScheduledTask SecondBrain-Chat -ErrorAction SilentlyContinue
Start-ScheduledTask SecondBrain-Chat
Start-Sleep 12
(Invoke-WebRequest http://127.0.0.1:8765/ -UseBasicParsing).StatusCode
