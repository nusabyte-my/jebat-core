param(
  [Parameter(Mandatory = $true)][string]$Task,
  [string]$Scope = "",
  [string]$Constraints = "",
  [string]$Verification = ""
)

@"
# Coding Task Intake
- Task: $Task
- Scope: $Scope
- Constraints: $Constraints
- Verification: $Verification
"@
