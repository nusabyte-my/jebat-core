# Provenance and Lifecycle Append Guide

## Goal

Append generated entries directly into Jebat's running logs.

---

## Append provenance entry
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\append-provenance-entry.ps1 \
  -Decision "Strengthen lifecycle tooling" \
  -Context "Jebat needed stronger internal ops support"
```

## Append lifecycle entry
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\append-lifecycle-entry.ps1 \
  -ObjectChanged "jebat-admin.ps1" \
  -ChangeType "capability expansion" \
  -Reason "Added provenance/lifecycle/status commands"
```
