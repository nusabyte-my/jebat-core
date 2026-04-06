param(
  [Parameter(Mandatory = $true)][string]$SkillName,
  [Parameter(Mandatory = $true)][string]$Source,
  [Parameter(Mandatory = $true)][int]$Score,
  [Parameter(Mandatory = $true)][string]$TrustClass,
  [Parameter(Mandatory = $true)][string]$Verdict,
  [string]$Reviewer = "Jebat",
  [string]$Scope = "pattern adaptation only"
)

$attestation = [pscustomobject]@{
  skillName = $SkillName
  source = $Source
  reviewedAt = (Get-Date).ToString("o")
  reviewer = $Reviewer
  score = $Score
  maxScore = 30
  trustClass = $TrustClass
  verdict = $Verdict
  evidence = @()
  concerns = @()
  plannedUse = @()
  scope = $Scope
}

$attestation | ConvertTo-Json -Depth 5
