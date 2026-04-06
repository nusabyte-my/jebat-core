param(
  [Parameter(Mandatory = $true)][string]$OldFile,
  [Parameter(Mandatory = $true)][string]$NewFile
)

if (!(Test-Path $OldFile)) { throw "Old file not found: $OldFile" }
if (!(Test-Path $NewFile)) { throw "New file not found: $NewFile" }

$old = Get-Content $OldFile -Raw | ConvertFrom-Json
$new = Get-Content $NewFile -Raw | ConvertFrom-Json

$report = @()

foreach ($newSkill in $new.reviewedSkills) {
  $oldSkill = $old.reviewedSkills | Where-Object { $_.name -eq $newSkill.name }
  if ($null -eq $oldSkill) {
    $report += [pscustomobject]@{ name = $newSkill.name; change = "NEW"; note = "Skill added to reviewed set" }
    continue
  }

  $changes = @()
  if ($oldSkill.score -ne $newSkill.score) { $changes += "score: $($oldSkill.score) -> $($newSkill.score)" }
  if ($oldSkill.verdict -ne $newSkill.verdict) { $changes += "verdict: $($oldSkill.verdict) -> $($newSkill.verdict)" }
  if ($oldSkill.trustClass -ne $newSkill.trustClass) { $changes += "trustClass: $($oldSkill.trustClass) -> $($newSkill.trustClass)" }

  if ($changes.Count -gt 0) {
    $report += [pscustomobject]@{ name = $newSkill.name; change = "UPDATED"; note = ($changes -join "; ") }
  }
}

$removed = $old.reviewedSkills | Where-Object { $_.name -notin $new.reviewedSkills.name }
foreach ($item in $removed) {
  $report += [pscustomobject]@{ name = $item.name; change = "REMOVED"; note = "Skill no longer present in reviewed set" }
}

$report | ConvertTo-Json -Depth 4
