param(
  [Parameter(Mandatory = $true)][string]$Title,
  [Parameter(Mandatory = $true)][string]$Severity,
  [string]$Evidence = "",
  [string]$Impact = "",
  [string]$Remediation = ""
)

@"
## Finding: $Title
- Severity: $Severity
- Evidence: $Evidence
- Impact: $Impact
- Remediation: $Remediation
"@
