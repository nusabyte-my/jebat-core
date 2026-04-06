param(
  [Parameter(Mandatory = $true)][string]$EntityName,
  [Parameter(Mandatory = $true)][string]$Category,
  [string]$Notes = "",
  [string]$BrainRoot = ".\brain"
)

$categoryPath = Join-Path $BrainRoot $Category
if (!(Test-Path $categoryPath)) {
  New-Item -ItemType Directory -Path $categoryPath -Force | Out-Null
}

$safeName = ($EntityName -replace '[^a-zA-Z0-9\- ]', '').Trim() -replace ' ', '-'
$filePath = Join-Path $categoryPath ("$safeName.md")

if (!(Test-Path $filePath)) {
  Set-Content -Path $filePath -Value "# $EntityName`r`n`r`n## Notes`r`n- $Notes`r`n"
  Write-Host "Created entity memory: $filePath"
} else {
  Add-Content -Path $filePath -Value "- $Notes"
  Write-Host "Updated entity memory: $filePath"
}
