param(
  [Parameter(Mandatory = $true)][string]$Objective,
  [string]$Checks = "",
  [string]$Risks = ""
)

@"
# Coding Verification
- Objective: $Objective
- Checks: $Checks
- Risks: $Risks
- Verify behavior matches requested scope before accepting the change
"@
