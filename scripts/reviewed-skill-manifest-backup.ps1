param(
  [string]$ManifestPath = ".\reviewed-skills.json",
  [string]$BackupRoot = ".\reviewed-skills-backups"
)

if (!(Test-Path $ManifestPath)) {
  throw "Manifest not found: $ManifestPath"
}

if (!(Test-Path $BackupRoot)) {
  New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $BackupRoot "reviewed-skills-$timestamp.json"
Copy-Item $ManifestPath $target -Force
Write-Host "Manifest backup created: $target"
