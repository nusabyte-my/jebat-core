param(
  [Parameter(Mandatory = $true)][string]$Finding,
  [Parameter(Mandatory = $true)][string]$Action,
  [string]$Priority = "",
  [string]$Owner = "",
  [string]$Status = "open",
  [string]$TargetFile = ".\records\security\remediation-log.md"
)

$targetDir = Split-Path -Parent $TargetFile
if ($targetDir -and !(Test-Path $targetDir)) {
  New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

$entry = & "$PSScriptRoot\security-remediation-helper.ps1" -Finding $Finding -Action $Action -Priority $Priority -Owner $Owner -Status $Status
Add-Content -Path $TargetFile -Value "`r`n$entry`r`n"
Write-Host "Appended remediation entry to $TargetFile"
