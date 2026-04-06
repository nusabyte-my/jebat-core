param(
  [string]$DailyFile = ".\memory\$(Get-Date -Format 'yyyy-MM-dd').md"
)

@"
# Memory Consolidation Review
- Source daily file: $DailyFile
- Look for: repeated facts, stable preferences, durable decisions, reusable workflows
- Promote durable truths to MEMORY.md
- Promote named durable subjects to brain/
- Move reusable workflows into procedures/skills/docs
"@
