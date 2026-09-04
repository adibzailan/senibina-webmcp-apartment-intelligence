# Bootstrap v2 on a VM that has no git: download main.zip from GitHub, replace the app folder, run install-v2.ps1.
#   iwr https://raw.githubusercontent.com/adibzailan/senibina-webmcp-apartment-intelligence/main/deploy/archive/windows/bootstrap-v2.ps1 -OutFile $env:TEMP\b.ps1; powershell -ep bypass -f $env:TEMP\b.ps1
$ErrorActionPreference = "Stop"
$Root = "C:\ApartmentIntelligence"
$App = Join-Path $Root "app"
$Zip = Join-Path $Root "installers\main.zip"
$Stage = Join-Path $Root "stage"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
New-Item -ItemType Directory -Force -Path (Split-Path $Zip) | Out-Null
Stop-ScheduledTask -TaskName "Apartment Intelligence" -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$Root*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Invoke-WebRequest -Uri "https://github.com/adibzailan/senibina-webmcp-apartment-intelligence/archive/refs/heads/main.zip" -OutFile $Zip
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
Expand-Archive -Path $Zip -DestinationPath $Stage -Force
$Src = Get-ChildItem $Stage | Select-Object -First 1
if (Test-Path $App) {
  $Backup = Join-Path $Root ("app-v1-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
  Move-Item $App $Backup
}
Move-Item $Src.FullName $App
Remove-Item $Stage -Recurse -Force
Write-Host "Source in place at $App; running installer"
& powershell -ExecutionPolicy Bypass -File (Join-Path $App "deploy\archive\windows\install-v2.ps1") *>&1 | Tee-Object (Join-Path $Root "install-v2.log")
