param(
  [Parameter(Mandatory = $true)][string]$ObjectChanged,
  [Parameter(Mandatory = $true)][string]$ChangeType,
  [Parameter(Mandatory = $true)][string]$Reason,
  [string]$Impact = "",
  [string]$ReplacementOrRollback = ""
)

$entry = @"
### $(Get-Date -Format 'yyyy-MM-dd') — $ObjectChanged
- **Object changed:** $ObjectChanged
- **Change type:** $ChangeType
- **Reason:** $Reason
- **Impact:** $Impact
- **Replacement / rollback:** $ReplacementOrRollback
"@

$entry
