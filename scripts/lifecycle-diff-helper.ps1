param(
  [Parameter(Mandatory = $true)][string]$OldText,
  [Parameter(Mandatory = $true)][string]$NewText
)

$oldLines = $OldText -split "`n"
$newLines = $NewText -split "`n"

$added = $newLines | Where-Object { $_ -and ($_ -notin $oldLines) }
$removed = $oldLines | Where-Object { $_ -and ($_ -notin $newLines) }

[pscustomobject]@{
  Added = $added
  Removed = $removed
} | ConvertTo-Json -Depth 5
