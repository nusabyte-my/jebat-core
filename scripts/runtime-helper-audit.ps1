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

$missing = @()
$present = @()

foreach ($name in $required) {
  $path = Join-Path $PSScriptRoot $name
  if (Test-Path $path) {
    $present += $name
  }
  else {
    $missing += $name
  }
}

@"
# Runtime Helper Audit
- Required helpers: $($required.Count)
- Present: $($present.Count)
- Missing: $($missing.Count)

## Present
$($present | ForEach-Object { "- $_" } | Out-String)
## Missing
$($(if ($missing.Count -eq 0) { '- none' } else { $missing | ForEach-Object { "- $_" } }) | Out-String)
"@