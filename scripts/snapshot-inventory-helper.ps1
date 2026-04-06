param(
  [string]$SnapshotRoot = ".\skill-snapshots"
)

if (!(Test-Path $SnapshotRoot)) {
  Write-Output "[]"
  exit 0
}

$items = Get-ChildItem $SnapshotRoot | Sort-Object LastWriteTime -Descending | ForEach-Object {
  [pscustomobject]@{
    Name = $_.Name
    LastWriteTime = $_.LastWriteTime.ToString("o")
    FullName = $_.FullName
  }
}

$items | ConvertTo-Json -Depth 3
