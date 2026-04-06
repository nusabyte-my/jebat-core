param(
  [Parameter(Mandatory = $true)][string]$Objective,
  [string]$Status = "in progress",
  [string]$Artifacts = "",
  [string]$OpenQuestions = "",
  [string]$SuccessCriteria = ""
)

@"
## Handoff
- Objective: $Objective
- Status: $Status
- Artifacts: $Artifacts
- Open questions: $OpenQuestions
- Success criteria: $SuccessCriteria
"@
