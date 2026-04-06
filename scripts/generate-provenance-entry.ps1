param(
  [Parameter(Mandatory = $true)][string]$Decision,
  [Parameter(Mandatory = $true)][string]$Context,
  [string]$Evidence = "",
  [string]$Alternatives = "",
  [string]$Outcome = "",
  [string]$FollowUp = ""
)

$entry = @"
### $(Get-Date -Format 'yyyy-MM-dd') — $Decision
- **Decision:** $Decision
- **Context:** $Context
- **Evidence:** $Evidence
- **Alternatives considered:** $Alternatives
- **Outcome:** $Outcome
- **Follow-up:** $FollowUp
"@

$entry
