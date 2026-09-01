$ErrorActionPreference = "Stop"
$Root = "C:\ApartmentIntelligence"
$App = Join-Path $Root "app"

$env:PYTHONPATH = Join-Path $App "server"
$env:EXPECTED_ORIGIN = "https://apartment.senibina.com.sg"
$env:COOKIE_SECURE = "true"

Set-Location $App
& (Join-Path $Root "venv\Scripts\python.exe") -m uvicorn app.main:app `
  --host 127.0.0.1 `
  --port 8000 `
  --no-access-log

exit $LASTEXITCODE
