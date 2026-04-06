param(
  [string]$ScriptsRoot = ".\scripts"
)

$required = @(
  'memory-router-helper.ps1',
  'memory-query-helper.ps1',
  'memory-consolidation-helper.ps1',
  'orchestration-handoff-helper.ps1',
  'task-record-helper.ps1',
  'append-task-record.ps1',
  'research-brief-helper.ps1',
  'research-source-log-helper.ps1',
  'literature-review-scaffold.ps1',
  'cybersecurity-finding-helper.ps1',
  'security-remediation-helper.ps1',
  'append-remediation-entry.ps1',
  'coding-task-intake-helper.ps1',
  'coding-route-helper.ps1',
  'coding-verification-helper.ps1',
  'coding-memory-writeback-helper.ps1'
)

$groups = [ordered]@{
  'Memory' = @('memory-router-helper.ps1','memory-query-helper.ps1','memory-consolidation-helper.ps1')
  'Orchestration' = @('orchestration-handoff-helper.ps1','task-record-helper.ps1','append-task-record.ps1')
  'Research' = @('research-brief-helper.ps1','research-source-log-helper.ps1','literature-review-scaffold.ps1')
  'Cybersecurity' = @('cybersecurity-finding-helper.ps1','security-remediation-helper.ps1','append-remediation-entry.ps1')
  'Coding' = @('coding-task-intake-helper.ps1','coding-route-helper.ps1','coding-verification-helper.ps1','coding-memory-writeback-helper.ps1')
}

$present = @()
$missing = @()

foreach ($name in $required) {
  $path = Join-Path $ScriptsRoot $name
  if (Test-Path $path) { $present += $name } else { $missing += $name }
}

$groupLines = foreach ($group in $groups.Keys) {
  $items = $groups[$group]
  $groupPresent = ($items | Where-Object { Test-Path (Join-Path $ScriptsRoot $_) }).Count
  "- ${group}: $groupPresent/$($items.Count)"
}

$missingText = if ($missing.Count -eq 0) { '- none' } else { ($missing | ForEach-Object { "- $_" }) -join "`r`n" }

@"
# JEBAT Runtime Status

## Summary
- helper coverage: $($present.Count)/$($required.Count)
- missing helpers: $($missing.Count)
- generated at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Coverage by area
$($groupLines -join "`r`n")

## Missing helpers
$missingText

## Readiness
$(if ($missing.Count -eq 0) {
"- Runtime helper baseline is intact
- Admin runtime audit should pass
- Safe to use helper-driven workflows for memory, orchestration, research, cybersecurity, and coding dispatch"
} else {
"- Runtime helper baseline is incomplete
- Repair missing helpers before depending on the full Phase 2/3 workflow surface"
})
"@