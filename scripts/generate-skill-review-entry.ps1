param(
  [Parameter(Mandatory = $true)][string]$Name,
  [Parameter(Mandatory = $true)][string]$Source,
  [Parameter(Mandatory = $true)][int]$Score,
  [Parameter(Mandatory = $true)][string]$TrustClass,
  [Parameter(Mandatory = $true)][string]$Verdict,
  [string]$PlannedUse = "pattern adaptation"
)

$entry = [pscustomobject]@{
  name = $Name
  source = $Source
  reviewedAt = (Get-Date).ToString("o")
  score = $Score
  max = 30
  trustClass = $TrustClass
  verdict = $Verdict
  plannedUse = $PlannedUse
}

$entry | ConvertTo-Json -Depth 3
