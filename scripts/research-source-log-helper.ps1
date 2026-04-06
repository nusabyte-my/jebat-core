param(
  [Parameter(Mandatory = $true)][string]$Source,
  [string]$WhyItMatters = "",
  [string]$Confidence = "",
  [string]$Notes = ""
)

@"
## Source Log Entry
- Source: $Source
- Why it matters: $WhyItMatters
- Confidence: $Confidence
- Notes: $Notes
"@
