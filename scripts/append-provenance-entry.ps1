param(
  [Parameter(Mandatory = $true)][string]$Decision,
  [Parameter(Mandatory = $true)][string]$Context,
  [string]$Evidence = "",
  [string]$Alternatives = "",
  [string]$Outcome = "",
  [string]$FollowUp = "",
  [string]$TargetFile = ".\records\changes\DECISION_PROVENANCE_LOG.md"
)

$targetDir = Split-Path -Parent $TargetFile
if ($targetDir -and !(Test-Path $targetDir)) {
  New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

$entry = & "$PSScriptRoot\generate-provenance-entry.ps1" -Decision $Decision -Context $Context -Evidence $Evidence -Alternatives $Alternatives -Outcome $Outcome -FollowUp $FollowUp
Add-Content -Path $TargetFile -Value "`r`n$entry`r`n"
Write-Host "Appended provenance entry to $TargetFile"
