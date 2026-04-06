param(
  [Parameter(Mandatory = $true)][string]$TaskSize,
  [string]$Risk = "normal",
  [string]$NeedsResearch = "no"
)

if ($Risk -eq "high") { "security-first" }
elseif ($NeedsResearch -eq "yes") { "research-first" }
elseif ($TaskSize -eq "small") { "direct-local" }
elseif ($TaskSize -eq "large") { "coding-specialist" }
else { "review-first" }
