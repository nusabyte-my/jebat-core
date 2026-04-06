param(
  [Parameter(Mandatory = $true)][string]$Subject,
  [Parameter(Mandatory = $true)][string]$Type
)

switch ($Type.ToLower()) {
  "entity" { "brain/ (entity memory)" }
  "daily" { "memory/YYYY-MM-DD.md" }
  "longterm" { "MEMORY.md" }
  "procedure" { "AGENTS.md / TOOLS.md / skill docs" }
  default { "undecided - inspect context manually" }
}
