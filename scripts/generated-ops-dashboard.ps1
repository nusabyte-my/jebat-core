param(
  [string]$ReviewedSkillsFile = ".\reviewed-skills.json",
  [string]$SnapshotRoot = ".\skill-snapshots",
  [string]$LifecycleFile = ".\LIFECYCLE_NOTES.md",
  [string]$ProvenanceFile = ".\DECISION_PROVENANCE_LOG.md"
)

$reviewed = if (Test-Path $ReviewedSkillsFile) {
  Get-Content $ReviewedSkillsFile -Raw | ConvertFrom-Json
} else {
  $null
}

$totalReviewed = if ($reviewed) { $reviewed.reviewedSkills.Count } else { 0 }
$approveWithCaution = if ($reviewed) { ($reviewed.reviewedSkills | Where-Object { $_.verdict -eq 'APPROVE WITH CAUTION' }).Count } else { 0 }
$patternOnly = if ($reviewed) { ($reviewed.reviewedSkills | Where-Object { $_.verdict -eq 'PATTERN ONLY' }).Count } else { 0 }
$recentSkills = if ($reviewed) { ($reviewed.reviewedSkills | Select-Object -Last 5 | ForEach-Object { $_.name }) -join ", " } else { "none" }

$snapshots = if (Test-Path $SnapshotRoot) { (Get-ChildItem $SnapshotRoot).Count } else { 0 }
$lifecycleEntries = if (Test-Path $LifecycleFile) { (Select-String -Path $LifecycleFile -Pattern '^### ').Count } else { 0 }
$provenanceEntries = if (Test-Path $ProvenanceFile) { (Select-String -Path $ProvenanceFile -Pattern '^### ').Count } else { 0 }

@"
# Generated JEBAT Ops Dashboard

## Core status
- reviewed skills: $totalReviewed
- approve with caution: $approveWithCaution
- pattern only: $patternOnly
- local snapshots: $snapshots
- lifecycle entries: $lifecycleEntries
- provenance entries: $provenanceEntries
- generated at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Recent reviewed skills
- $recentSkills
"@
