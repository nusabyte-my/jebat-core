param(
  [Parameter(Mandatory = $true)][string]$SnapshotPath,
  [Parameter(Mandatory = $true)][string]$TargetSkillPath
)

if (!(Test-Path $SnapshotPath)) {
  throw "Snapshot path not found: $SnapshotPath"
}

if (!(Test-Path $TargetSkillPath)) {
  throw "Target skill path not found: $TargetSkillPath"
}

Remove-Item -Path $TargetSkillPath -Recurse -Force
Copy-Item -Path $SnapshotPath -Destination $TargetSkillPath -Recurse -Force
Write-Host "Rolled back $TargetSkillPath from $SnapshotPath"
