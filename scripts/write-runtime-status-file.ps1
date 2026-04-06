param(
  [string]$OutputFile = ".\records\ops\RUNTIME_STATUS.generated.md"
)

$outputDir = Split-Path -Parent $OutputFile
if ($outputDir -and !(Test-Path $outputDir)) {
  New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$content = & "$PSScriptRoot\generate-runtime-status.ps1"
Set-Content -Path $OutputFile -Value $content
Write-Host "Wrote runtime status to $OutputFile"