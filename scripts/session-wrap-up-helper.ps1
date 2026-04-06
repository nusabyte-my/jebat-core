param(
  [string]$Date = "$(Get-Date -Format 'yyyy-MM-dd')"
)

$memoryDir = Join-Path $PSScriptRoot "..\memory"
$target = Join-Path $memoryDir "$Date.md"
$template = Join-Path $PSScriptRoot "session-wrap-up-template.md"

if (!(Test-Path $memoryDir)) {
  New-Item -ItemType Directory -Path $memoryDir | Out-Null
}

if (!(Test-Path $target)) {
  if (Test-Path $template) {
    $header = "# $Date - Session Wrap-Up`r`n`r`n"
    $content = Get-Content $template -Raw
    Set-Content -Path $target -Value ($header + $content)
  } else {
    Set-Content -Path $target -Value "# $Date - Session Wrap-Up`r`n"
  }
  Write-Host "Created $target"
} else {
  Write-Host "Already exists: $target"
}
