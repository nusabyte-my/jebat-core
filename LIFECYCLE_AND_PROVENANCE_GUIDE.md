# Lifecycle and Provenance Guide

## Goal

Make lifecycle and decision tracking easy enough to use regularly.

---

## Generate provenance entry
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate-provenance-entry.ps1 \
  -Decision "Adopt lifecycle tracking" \
  -Context "Jebat stack became large enough to need change history"
```

## Generate lifecycle entry
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate-lifecycle-entry.ps1 \
  -ObjectChanged "jebat-admin.ps1" \
  -ChangeType "capability expansion" \
  -Reason "Added rollback and delta commands"
```

## Status sync summary
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\status-sync-helper.ps1
```
