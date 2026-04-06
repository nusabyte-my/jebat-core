param(
  [string]$ManifestPath = ".\reviewed-skills.json"
)

if (!(Test-Path $ManifestPath)) {
  throw "Manifest not found: $ManifestPath"
}

$data = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$skills = $data.reviewedSkills

$summary = [pscustomobject]@{
  TotalReviewed = $skills.Count
  Approved = ($skills | Where-Object { $_.verdict -eq 'APPROVE' }).Count
  ApprovedWithCaution = ($skills | Where-Object { $_.verdict -eq 'APPROVE WITH CAUTION' }).Count
  PatternOnly = ($skills | Where-Object { $_.verdict -eq 'PATTERN ONLY' }).Count
  Rejected = ($skills | Where-Object { $_.verdict -eq 'REJECT' }).Count
  AverageScore = [math]::Round((($skills | Measure-Object -Property score -Average).Average), 2)
}

$result = [pscustomobject]@{
  Summary = $summary
  Skills = $skills
}

$result | ConvertTo-Json -Depth 5
