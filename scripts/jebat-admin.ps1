param(
  [Parameter(Position = 0)][string]$Command,
  [string]$Name,
  [string]$Source,
  [int]$Score,
  [string]$TrustClass,
  [string]$Verdict,
  [string]$SourceFile,
  [string]$Text,
  [string]$SkillPath,
  [string]$Tag,
  [string]$SnapshotPath,
  [string]$TargetSkillPath,
  [string]$OldFile,
  [string]$NewFile,
  [string]$Reviewer,
  [string]$Scope,
  [string]$Decision,
  [string]$Context,
  [string]$Evidence,
  [string]$Alternatives,
  [string]$Outcome,
  [string]$FollowUp,
  [string]$ObjectChanged,
  [string]$ChangeType,
  [string]$Reason,
  [string]$Impact,
  [string]$ReplacementOrRollback,
  [string]$EntityName,
  [string]$Category,
  [string]$Notes,
  [string]$OldText,
  [string]$NewText,
  [string[]]$PlannedUse
)

switch ($Command) {
  "memory-review" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\daily-memory-review-helper.ps1"
  }
  "wrap-up" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\session-wrap-up-helper.ps1"
  }
  "skill-audit" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\reviewed-skill-audit.ps1"
  }
  "skill-entry" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\generate-skill-review-entry.ps1" -Name $Name -Source $Source -Score $Score -TrustClass $TrustClass -Verdict $Verdict
  }
  "promote" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\memory-promote-helper.ps1" -SourceFile $SourceFile -Text $Text
  }
  "snapshot-skill" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\skill-snapshot-helper.ps1" -SkillPath $SkillPath -Tag $Tag
  }
  "rollback-skill" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\skill-rollback-helper.ps1" -SnapshotPath $SnapshotPath -TargetSkillPath $TargetSkillPath
  }
  "skill-delta" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\reviewed-skill-delta-checker.ps1" -OldFile $OldFile -NewFile $NewFile
  }
  "skill-attest" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\generate-reviewed-skill-attestation.ps1" -SkillName $Name -Source $Source -Score $Score -TrustClass $TrustClass -Verdict $Verdict -Reviewer $Reviewer -Scope $Scope
  }
  "provenance-entry" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\generate-provenance-entry.ps1" -Decision $Decision -Context $Context -Evidence $Evidence -Alternatives $Alternatives -Outcome $Outcome -FollowUp $FollowUp
  }
  "lifecycle-entry" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\generate-lifecycle-entry.ps1" -ObjectChanged $ObjectChanged -ChangeType $ChangeType -Reason $Reason -Impact $Impact -ReplacementOrRollback $ReplacementOrRollback
  }
  "status-sync" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\status-sync-helper.ps1"
  }
  "append-provenance" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\append-provenance-entry.ps1" -Decision $Decision -Context $Context -Evidence $Evidence -Alternatives $Alternatives -Outcome $Outcome -FollowUp $FollowUp
  }
  "append-lifecycle" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\append-lifecycle-entry.ps1" -ObjectChanged $ObjectChanged -ChangeType $ChangeType -Reason $Reason -Impact $Impact -ReplacementOrRollback $ReplacementOrRollback
  }
  "ops-dashboard" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\generated-ops-dashboard.ps1"
  }
  "lifecycle-diff" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\lifecycle-diff-helper.ps1" -OldText $OldText -NewText $NewText
  }
  "update-reviewed-skill" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\reviewed-skill-manifest-updater.ps1" -Name $Name -Score $Score -TrustClass $TrustClass -Verdict $Verdict -PlannedUse $PlannedUse
  }
  "entity-memory" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\entity-memory-helper.ps1" -EntityName $EntityName -Category $Category -Notes $Notes
  }
  "append-entity-memory" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\append-entity-memory.ps1" -EntityName $EntityName -Category $Category -Note $Notes
  }
  "backup-reviewed-skills" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\reviewed-skill-manifest-backup.ps1"
  }
  "write-ops-dashboard" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\write-ops-dashboard-file.ps1"
  }
  "runtime-status" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\write-runtime-status-file.ps1"
  }
  "brain-index" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\generate-brain-index.ps1"
  }
  "brain-status" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\generate-brain-status.ps1"
  }
  "memory-route" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\memory-router-helper.ps1" -Subject $EntityName -Type $Category
  }
  "handoff" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\orchestration-handoff-helper.ps1" -Objective $Decision -Status $Context -Artifacts $Evidence -OpenQuestions $Alternatives -SuccessCriteria $Outcome
  }
  "research-brief" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\research-brief-helper.ps1" -Question $Decision -Scope $Context -Output $Outcome -Constraints $Evidence
  }
  "security-finding" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\cybersecurity-finding-helper.ps1" -Title $Decision -Severity $Context -Evidence $Evidence -Impact $Outcome -Remediation $FollowUp
  }
  "memory-query" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\memory-query-helper.ps1" -Query $Decision -SuggestedScope $Context
  }
  "source-log" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\research-source-log-helper.ps1" -Source $Decision -WhyItMatters $Context -Confidence $Evidence -Notes $Outcome
  }
  "remediation" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\security-remediation-helper.ps1" -Finding $Decision -Action $Context -Priority $Evidence -Owner $Outcome -Status $FollowUp
  }
  "task-record" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\task-record-helper.ps1" -Task $Decision -Owner $Context -State $Outcome -Notes $Evidence
  }
  "memory-consolidation" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\memory-consolidation-helper.ps1"
  }
  "literature-review" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\literature-review-scaffold.ps1" -Topic $Decision -Output $Outcome
  }
  "append-remediation" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\append-remediation-entry.ps1" -Finding $Decision -Action $Context -Priority $Evidence -Owner $Outcome -Status $FollowUp
  }
  "append-task" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\append-task-record.ps1" -Task $Decision -Owner $Context -State $Outcome -Notes $Evidence
  }
  "coding-intake" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\coding-task-intake-helper.ps1" -Task $Decision -Scope $Context -Constraints $Evidence -Verification $Outcome
  }
  "coding-route" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\coding-route-helper.ps1" -TaskSize $Context -Risk $Evidence -NeedsResearch $Outcome
  }
  "coding-verify" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\coding-verification-helper.ps1" -Objective $Decision -Checks $Context -Risks $Evidence
  }
  "coding-writeback" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\coding-memory-writeback-helper.ps1" -Outcome $Decision -DurableImpact $Context -Target $Outcome
  }
  "runtime-audit" {
    powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\runtime-helper-audit.ps1"
  }
  default {
    Write-Host "Usage: jebat-admin.ps1 [memory-review|wrap-up|skill-audit|skill-entry|promote|snapshot-skill|rollback-skill|skill-delta|skill-attest|provenance-entry|lifecycle-entry|status-sync|append-provenance|append-lifecycle|ops-dashboard|lifecycle-diff|update-reviewed-skill|entity-memory|append-entity-memory|backup-reviewed-skills|write-ops-dashboard|runtime-status|brain-index|brain-status|memory-route|handoff|research-brief|security-finding|memory-query|source-log|remediation|task-record|memory-consolidation|literature-review|append-remediation|append-task|coding-intake|coding-route|coding-verify|coding-writeback|runtime-audit]"
  }
}
