param(
  [Parameter(Mandatory = $true)][string]$SkillName,
  [int]$Provenance = 0,
  [int]$Structure = 0,
  [int]$ToolRealism = 0,
  [int]$Safety = 0,
  [int]$Usefulness = 0,
  [int]$VersionIntegrity = 0
)

$fields = @{
  Provenance = $Provenance
  Structure = $Structure
  ToolRealism = $ToolRealism
  Safety = $Safety
  Usefulness = $Usefulness
  VersionIntegrity = $VersionIntegrity
}

foreach ($k in $fields.Keys) {
  if ($fields[$k] -lt 0 -or $fields[$k] -gt 5) {
    throw "$k score must be between 0 and 5"
  }
}

$total = ($fields.Values | Measure-Object -Sum).Sum
$max = 30

$trustClass = if ($total -ge 26) {
  "strong candidate"
} elseif ($total -ge 20) {
  "adapt with caution"
} elseif ($total -ge 13) {
  "pattern extraction only"
} else {
  "reject"
}

$verdict = if ($total -ge 26) {
  "APPROVE"
} elseif ($total -ge 20) {
  "APPROVE WITH CAUTION"
} elseif ($total -ge 13) {
  "PATTERN ONLY"
} else {
  "REJECT"
}

[pscustomobject]@{
  SkillName = $SkillName
  Provenance = $Provenance
  Structure = $Structure
  ToolRealism = $ToolRealism
  Safety = $Safety
  Usefulness = $Usefulness
  VersionIntegrity = $VersionIntegrity
  Total = $total
  Max = $max
  TrustClass = $trustClass
  Verdict = $verdict
} | ConvertTo-Json -Depth 3
