param(
  [string]$BrainRoot = ".\brain",
  [string]$OutputFile = ".\BRAIN_STATUS.generated.md"
)

if (!(Test-Path $BrainRoot)) {
  throw "Brain root not found: $BrainRoot"
}

$categories = Get-ChildItem $BrainRoot -Directory | Sort-Object Name
$totalFiles = (Get-ChildItem $BrainRoot -Recurse -File -Filter "*.md").Count

$lines = @("# Generated Brain Status", "", "- total markdown entries: $totalFiles", "- generated at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')", "")

foreach ($category in $categories) {
  $files = Get-ChildItem $category.FullName -Filter "*.md" | Sort-Object Name
  $lines += "## $($category.Name)"
  $lines += "- count: $($files.Count)"
  foreach ($file in $files) {
    $lines += "- $($file.BaseName)"
  }
  $lines += ""
}

Set-Content -Path $OutputFile -Value ($lines -join "`r`n")
Write-Host "Generated brain status: $OutputFile"
