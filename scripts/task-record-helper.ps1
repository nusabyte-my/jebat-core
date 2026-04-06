param(
  [Parameter(Mandatory = $true)][string]$Task,
  [string]$Owner = "Jebat",
  [string]$State = "inbox",
  [string]$Notes = ""
)

@"
## Task Record
- Task: $Task
- Owner: $Owner
- State: $State
- Notes: $Notes
"@
