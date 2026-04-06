param(
  [Parameter(Mandatory = $true)][string]$SourceFile,
  [Parameter(Mandatory = $true)][string]$Text,
  [string]$TargetFile = ".\MEMORY.md",
  [string]$Section = "## Imported Notes"
)

if (!(Test-Path $SourceFile)) {
  throw "Source file not found: $SourceFile"
}

if (!(Test-Path $TargetFile)) {
  throw "Target file not found: $TargetFile"
}

$targetContent = Get-Content $TargetFile -Raw
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$entry = "`r`n- [$stamp] From $SourceFile: $Text`r`n"

if ($targetContent -notmatch [regex]::Escape($Section)) {
  Add-Content -Path $TargetFile -Value "`r`n$Section`r`n"
}

Add-Content -Path $TargetFile -Value $entry
Write-Host "Promoted note into $TargetFile"
