param(
  [Parameter(Mandatory = $true)][string]$SkillPath,
  [string]$SnapshotRoot = ".\skill-snapshots",
  [string]$Tag = "manual"
)

if (!(Test-Path $SkillPath)) {
  throw "Skill path not found: $SkillPath"
}

$skillName = Split-Path $SkillPath -Leaf
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$targetDir = Join-Path $SnapshotRoot "$skillName-$Tag-$timestamp"

if (!(Test-Path $SnapshotRoot)) {
  New-Item -ItemType Directory -Path $SnapshotRoot | Out-Null
}

Copy-Item -Path $SkillPath -Destination $targetDir -Recurse -Force
Write-Host "Snapshot created: $targetDir"
