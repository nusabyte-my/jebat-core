param(
  [Parameter(Mandatory = $true)][string]$Name,
  [Parameter(Mandatory = $true)][int]$Score,
  [Parameter(Mandatory = $true)][string]$TrustClass,
  [Parameter(Mandatory = $true)][string]$Verdict,
  [string[]]$PlannedUse = @(),
  [string]$ManifestPath = ".\reviewed-skills.json"
)

if (!(Test-Path $ManifestPath)) {
  throw "Manifest not found: $ManifestPath"
}

$data = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$existing = $data.reviewedSkills | Where-Object { $_.name -eq $Name }

if ($existing) {
  $existing.score = $Score
  $existing.trustClass = $TrustClass
  $existing.verdict = $Verdict
  $existing.plannedUse = $PlannedUse
} else {
  $newEntry = [pscustomobject]@{
    name = $Name
    score = $Score
    max = 30
    trustClass = $TrustClass
    verdict = $Verdict
    plannedUse = $PlannedUse
  }
  $data.reviewedSkills += $newEntry
}

$data | ConvertTo-Json -Depth 6 | Set-Content $ManifestPath
Write-Host "Updated $ManifestPath for $Name"
