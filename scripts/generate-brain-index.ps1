param(
  [string]$BrainRoot = ".\brain",
  [string]$OutputFile = ".\brain\INDEX.md"
)

if (!(Test-Path $BrainRoot)) {
  throw "Brain root not found: $BrainRoot"
}

$lines = @("# Brain Index", "")
$categories = Get-ChildItem $BrainRoot -Directory | Sort-Object Name

foreach ($category in $categories) {
  $lines += "## $($category.Name)"
  $files = Get-ChildItem $category.FullName -Filter "*.md" | Sort-Object Name
  foreach ($file in $files) {
    $lines += "- $($file.BaseName)"
  }
  $lines += ""
}

Set-Content -Path $OutputFile -Value ($lines -join "`r`n")
Write-Host "Generated brain index: $OutputFile"
