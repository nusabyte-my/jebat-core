param(
  [string]$OutputFile = ".\records\ops\OPS_DASHBOARD.generated.md"
)

$outputDir = Split-Path -Parent $OutputFile
if ($outputDir -and !(Test-Path $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$content = & "$PSScriptRoot\generated-ops-dashboard.ps1"
Set-Content -Path $OutputFile -Value $content
Write-Host "Wrote dashboard to $OutputFile"
