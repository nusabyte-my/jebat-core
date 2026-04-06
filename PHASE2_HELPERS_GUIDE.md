# Phase 2 Helpers Guide

## Memory router
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\memory-router-helper.ps1 -Subject "Hermes" -Type entity
```

## Memory query helper
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\memory-query-helper.ps1 -Query "What do we know about Hermes?"
```

## Memory consolidation helper
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\memory-consolidation-helper.ps1
```

## Orchestration handoff
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\orchestration-handoff-helper.ps1 -Objective "Review research output" -Artifacts "notes.md"
```

## Task record
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\task-record-helper.ps1 -Task "Audit reviewed skills" -State in-progress
```

## Append task record
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\append-task-record.ps1 -Task "Audit reviewed skills"
```

## Research brief
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\research-brief-helper.ps1 -Question "What are the best memory architectures for AI assistants?"
```

## Research source log
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\research-source-log-helper.ps1 -Source "OpenAlex paper" -WhyItMatters "Supports memory layering"
```

## Literature review scaffold
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\literature-review-scaffold.ps1 -Topic "AI assistant memory architectures"
```

## Cybersecurity finding
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cybersecurity-finding-helper.ps1 -Title "Weak auth boundary" -Severity high
```

## Remediation tracker
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\security-remediation-helper.ps1 -Finding "Weak auth boundary" -Action "Add authz checks"
```

## Append remediation entry
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\append-remediation-entry.ps1 -Finding "Weak auth boundary" -Action "Add authz checks"
```
