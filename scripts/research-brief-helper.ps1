param(
  [Parameter(Mandatory = $true)][string]$Question,
  [string]$Scope = "",
  [string]$Output = "summary",
  [string]$Constraints = ""
)

@"
# Research Brief

- Question: $Question
- Scope: $Scope
- Output needed: $Output
- Constraints: $Constraints
- Source expectations: strongest sources first, note disagreement, cite where useful
"@
