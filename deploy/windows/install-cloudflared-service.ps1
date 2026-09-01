param(
  [Parameter(Mandatory = $true)]
  [string]$ExpectedCredentialHash
)

$ErrorActionPreference = "Stop"
$Root = "C:\ApartmentIntelligence"
$CloudflaredData = "C:\ProgramData\cloudflared"
$CloudflaredProgram = "C:\Program Files\cloudflared"
$SourceExecutable = Join-Path $Root "installers\cloudflared-2026.8.3-amd64.exe"
$Executable = Join-Path $CloudflaredProgram "cloudflared.exe"
$Credential = Join-Path $CloudflaredData "connector.json"
$Config = Join-Path $CloudflaredData "config.yml"
$ExpectedExecutableHash = "83e726ed18ea78c5ad5213c4c3a3a27051393950d2bc8ed4de69bec12d14eaae"

New-Item -ItemType Directory -Force -Path $CloudflaredData, $CloudflaredProgram | Out-Null
Copy-Item $SourceExecutable $Executable -Force

$ExecutableHash = (Get-FileHash $Executable -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ExecutableHash -ne $ExpectedExecutableHash) {
  throw "cloudflared hash mismatch"
}

$CredentialHash = (Get-FileHash $Credential -Algorithm SHA256).Hash.ToLowerInvariant()
if ($CredentialHash -ne $ExpectedCredentialHash.ToLowerInvariant()) {
  throw "tunnel credential transfer hash mismatch"
}

icacls $CloudflaredData /inheritance:r /grant:r `
  "SYSTEM:(OI)(CI)F" `
  "BUILTIN\Administrators:(OI)(CI)F" | Out-Null

$Existing = Get-Service -Name cloudflared -ErrorAction SilentlyContinue
if ($Existing) {
  Stop-Service cloudflared -Force -ErrorAction SilentlyContinue
  sc.exe delete cloudflared | Out-Null
  Start-Sleep -Seconds 2
}

$Binary = ('"{0}" --config "{1}" tunnel run' -f $Executable, $Config)
New-Service -Name cloudflared -BinaryPathName $Binary `
  -DisplayName "Cloudflare Tunnel - Apartment Intelligence" `
  -StartupType Automatic | Out-Null
sc.exe failure cloudflared reset= 0 `
  actions= restart/60000/restart/60000/restart/60000 | Out-Null
Start-Service cloudflared
