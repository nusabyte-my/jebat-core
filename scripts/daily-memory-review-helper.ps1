param(
  [string]$MemoryDir = ".\memory"
)

if (!(Test-Path $MemoryDir)) {
  throw "Memory directory not found: $MemoryDir"
}

$files = Get-ChildItem $MemoryDir -Filter "*.md" | Sort-Object Name -Descending | Select-Object -First 5

$result = foreach ($file in $files) {
  $content = Get-Content $file.FullName -Raw
  [pscustomobject]@{
    File = $file.Name
    Lines = ($content -split "`n").Count
    HasDecisions = [bool]($content -match "Decision|Decisions|Important|Next Steps")
    HasFollowUps = [bool]($content -match "Follow-up|Follow up|Next Steps|TODO")
  }
}

$result | ConvertTo-Json -Depth 3
