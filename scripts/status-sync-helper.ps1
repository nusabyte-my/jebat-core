param(
  [string]$StatusFile = ".\JEBAT_STATUS.md",
  [string]$ReviewedSkillsFile = ".\reviewed-skills.json"
)

if (!(Test-Path $StatusFile)) { throw "Status file not found: $StatusFile" }
if (!(Test-Path $ReviewedSkillsFile)) { throw "Reviewed skills file not found: $ReviewedSkillsFile" }

$data = Get-Content $ReviewedSkillsFile -Raw | ConvertFrom-Json
$summary = [pscustomobject]@{
  totalReviewed = $data.reviewedSkills.Count
  approveWithCaution = ($data.reviewedSkills | Where-Object { $_.verdict -eq 'APPROVE WITH CAUTION' }).Count
  patternOnly = ($data.reviewedSkills | Where-Object { $_.verdict -eq 'PATTERN ONLY' }).Count
  reject = ($data.reviewedSkills | Where-Object { $_.verdict -eq 'REJECT' }).Count
}

$summary | ConvertTo-Json -Depth 3
