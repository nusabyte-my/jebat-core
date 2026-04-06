param(
  [Parameter(Mandatory = $true)][string]$Task,
  [string]$Owner = "Jebat",
  [string]$State = "inbox",
  [string]$Notes = "",
  [string]$TargetFile = ".\records\tasks\task-records.md"
)

$targetDir = Split-Path -Parent $TargetFile
if ($targetDir -and !(Test-Path $targetDir)) {
  New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

$entry = & "$PSScriptRoot\task-record-helper.ps1" -Task $Task -Owner $Owner -State $State -Notes $Notes
Add-Content -Path $TargetFile -Value "`r`n$entry`r`n"
Write-Host "Appended task record to $TargetFile"
