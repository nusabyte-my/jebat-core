param(
  [Parameter(Mandatory = $true)][string]$ObjectChanged,
  [Parameter(Mandatory = $true)][string]$ChangeType,
  [Parameter(Mandatory = $true)][string]$Reason,
  [string]$Impact = "",
  [string]$ReplacementOrRollback = "",
  [string]$TargetFile = ".\records\changes\LIFECYCLE_NOTES.md"
)

$targetDir = Split-Path -Parent $TargetFile
if ($targetDir -and !(Test-Path $targetDir)) {
  New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

$entry = & "$PSScriptRoot\generate-lifecycle-entry.ps1" -ObjectChanged $ObjectChanged -ChangeType $ChangeType -Reason $Reason -Impact $Impact -ReplacementOrRollback $ReplacementOrRollback
Add-Content -Path $TargetFile -Value "`r`n$entry`r`n"
Write-Host "Appended lifecycle entry to $TargetFile"
