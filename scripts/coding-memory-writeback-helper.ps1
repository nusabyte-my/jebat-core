param(
  [Parameter(Mandatory = $true)][string]$Outcome,
  [string]$DurableImpact = "",
  [string]$Target = "daily"
)

@"
# Coding Memory Writeback
- Outcome: $Outcome
- Durable impact: $DurableImpact
- Suggested memory target: $Target
"@
