$WshShell = New-Object -ComObject WScript.Shell
$StartupFolder = [Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupFolder "Pipnex_AI_247_Supervisor.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "c:\Users\USER\Desktop\START_PIPNEX_247.bat"
$Shortcut.WorkingDirectory = "c:\Users\USER\Desktop\pipnex_ai"
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.Description = "Pipnex AI 24/7 Watchdog Supervisor"
$Shortcut.Save()
Write-Host "✅ Pipnex AI 24/7 auto-start shortcut created successfully in Windows Startup folder!"
Write-Host "   Path: $ShortcutPath"
