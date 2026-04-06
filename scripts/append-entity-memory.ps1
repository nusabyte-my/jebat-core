param(
  [Parameter(Mandatory = $true)][string]$EntityName,
  [Parameter(Mandatory = $true)][string]$Category,
  [Parameter(Mandatory = $true)][string]$Note,
  [string]$BrainRoot = ".\brain"
)

$categoryPath = Join-Path $BrainRoot $Category
$safeName = ($EntityName -replace '[^a-zA-Z0-9\- ]', '').Trim() -replace ' ', '-'
$filePath = Join-Path $categoryPath ("$safeName.md")

if (!(Test-Path $filePath)) {
  throw "Entity file not found: $filePath"
}

Add-Content -Path $filePath -Value "- $Note"
Write-Host "Appended entity memory: $filePath"
