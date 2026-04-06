# JEBAT Admin

## Goal

Provide one operator entrypoint for common Jebat maintenance and review routines.

---

## Supported routines
- daily memory review
- session wrap-up file creation
- reviewed-skill audit
- skill review entry generation
- memory promotion
- generated ops dashboard writing
- generated runtime status writing
- helper-surface runtime audit

---

## Commands

### Daily memory review
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 memory-review
```

### Session wrap-up scaffold
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 wrap-up
```

### Reviewed skill audit
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 skill-audit
```

### Generate skill review entry
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 skill-entry -Name "skill-name" -Source "https://example.com" -Score 24 -TrustClass "adapt with caution" -Verdict "APPROVE WITH CAUTION"
```

### Promote memory
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 promote -SourceFile .\memory\2026-03-30.md -Text "Hermes became the routing layer for Jebat"
```

### Write generated ops dashboard
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 write-ops-dashboard
```

### Write generated runtime status
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 runtime-status
```

### Audit runtime helper surface
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\jebat-admin.ps1 runtime-audit
```
