# Apartment Intelligence v2 on the Windows VM (dev sprint host). Run from an elevated PowerShell:
#   Set-ExecutionPolicy -Scope Process Bypass; .\deploy\windows\install-v2.ps1
# Installs Python deps, Radiance (pinned), builds the web bundle, and restarts the scheduled task.
# Requires: Git, CPython 3.13 x86-64 (py -3.13-64), Node 22, an existing checkout at C:\ApartmentIntelligence\app.
$ErrorActionPreference = "Stop"
$Root = "C:\ApartmentIntelligence"
$App = Join-Path $Root "app"
$Venv = Join-Path $Root "venv"
$Radiance = Join-Path $Root "radiance"
$RadianceZip = Join-Path $Root "installers\Radiance_39b99660_Windows.zip"
$RadianceUrl = "https://github.com/LBNL-ETA/Radiance/releases/download/39b99660/Radiance_39b99660_Windows.zip"
$RadianceSha = "ab6858c6b4bfa71bf73d4a0979408a33307f8b7142585a1e64884957494290a5"

Set-Location $App
git fetch origin
git checkout main
git pull --ff-only origin main

# Python environment (x86-64 CPython under ARM emulation, as in v1)
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) { py -3.13-64 -m venv $Venv }
$Py = Join-Path $Venv "Scripts\python.exe"
& $Py -m pip install --upgrade pip | Out-Null
& $Py -m pip install -r (Join-Path $App "requirements.lock.txt")
& $Py -m pip install --no-deps -e $App

# Radiance, pinned by SHA-256 (x86-64 binaries; run under emulation)
New-Item -ItemType Directory -Force -Path (Split-Path $RadianceZip), $Radiance | Out-Null
if (-not (Test-Path $RadianceZip)) { Invoke-WebRequest -Uri $RadianceUrl -OutFile $RadianceZip }
$Hash = (Get-FileHash $RadianceZip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($Hash -ne $RadianceSha) { throw "Radiance zip hash mismatch: $Hash" }
if (-not (Test-Path (Join-Path $Radiance "bin\gendaymtx.exe"))) { Expand-Archive -Path $RadianceZip -DestinationPath $Radiance -Force }
$env:RADIANCE_PATH = $Radiance
& (Join-Path $Radiance "bin\rtrace.exe") -version

# Web bundle
Push-Location (Join-Path $App "apps\web")
npm ci --no-audit --no-fund
npm run build
Pop-Location

# Smoke test the engine in this shell before touching the service
& $Py -c "import ai_solar.radiance_env as r; assert r.RADIANCE_HOME, 'Radiance not found'; from ai_solar.sky import sky_matrix; sm = sky_matrix(); print('sky patches', len(sm.data[1]))"

# Permissions for the service account and restart
$Identity = "$env:COMPUTERNAME\ApartmentIntel"
icacls $App /grant:r "${Identity}:(OI)(CI)RX" | Out-Null
icacls $Venv /grant:r "${Identity}:(OI)(CI)RX" | Out-Null
icacls $Radiance /grant:r "${Identity}:(OI)(CI)RX" | Out-Null
Stop-ScheduledTask -TaskName "Apartment Intelligence" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskName "Apartment Intelligence"
Start-Sleep -Seconds 8
Invoke-RestMethod http://127.0.0.1:8000/healthz
