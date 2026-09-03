# v2 runner used by the "Apartment Intelligence" scheduled task (non-admin ApartmentIntel account).
$ErrorActionPreference = "Stop"
$Root = "C:\ApartmentIntelligence"
$App = Join-Path $Root "app"

$env:RADIANCE_PATH = Join-Path $Root "radiance"
$env:AI_WEB_DIST = Join-Path $App "apps\web\dist"
$env:AI_EXPECTED_ORIGINS = "https://apartments.senibina.com.sg,https://apartment.senibina.com.sg"
$env:AI_COOKIE_SECURE = "true"
$env:AI_ANALYSIS_TIMEOUT_S = "15"

Set-Location $App
& (Join-Path $Root "venv\Scripts\python.exe") -m uvicorn ai_api.main:app `
  --host 127.0.0.1 `
  --port 8000 `
  --no-access-log

exit $LASTEXITCODE
