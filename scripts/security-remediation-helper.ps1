param(
  [Parameter(Mandatory = $true)][string]$Finding,
  [string]$Action = "",
  [string]$Priority = "",
  [string]$Owner = "",
  [string]$Status = "open"
)

@"
## Remediation
- Finding: $Finding
- Action: $Action
- Priority: $Priority
- Owner: $Owner
- Status: $Status
"@
