$ErrorActionPreference = "Stop"

$Root = "C:\ApartmentIntelligence"
$App = Join-Path $Root "app"
$Account = "ApartmentIntel"
$TaskName = "Apartment Intelligence"
$Runner = Join-Path $App "deploy\windows\run-apartment-intelligence.ps1"

if (-not (Test-Path $Runner)) {
  throw "Deployment runner is missing: $Runner"
}

$RandomBytes = New-Object byte[] 32
$Generator = [Security.Cryptography.RandomNumberGenerator]::Create()
$Generator.GetBytes($RandomBytes)
$Generator.Dispose()
$Password = [Convert]::ToBase64String($RandomBytes) + "aA1!"
$SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$Existing = Get-LocalUser -Name $Account -ErrorAction SilentlyContinue

if ($Existing) {
  Set-LocalUser -Name $Account -Password $SecurePassword
} else {
  New-LocalUser -Name $Account -Password $SecurePassword `
    -AccountNeverExpires -PasswordNeverExpires -UserMayNotChangePassword | Out-Null
}

$Identity = "$env:COMPUTERNAME\$Account"
$Outputs = Join-Path $App "outputs"
New-Item -ItemType Directory -Path $Outputs -Force | Out-Null

icacls $App /inheritance:r /grant:r `
  "SYSTEM:(OI)(CI)F" `
  "BUILTIN\Administrators:(OI)(CI)F" `
  "${Identity}:(OI)(CI)RX" | Out-Null
icacls (Join-Path $Root "venv") /inheritance:r /grant:r `
  "SYSTEM:(OI)(CI)F" `
  "BUILTIN\Administrators:(OI)(CI)F" `
  "${Identity}:(OI)(CI)RX" | Out-Null
icacls $Outputs /grant:r "${Identity}:(OI)(CI)M" | Out-Null

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument (
  "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`""
)
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet `
  -RestartCount 999 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
  -Settings $Settings -User ".\$Account" -Password $Password -RunLevel Limited `
  -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName
