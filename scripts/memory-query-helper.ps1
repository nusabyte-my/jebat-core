param(
  [Parameter(Mandatory = $true)][string]$Query,
  [string]$SuggestedScope = "entity,daily,longterm"
)

@"
# Memory Query
- Query: $Query
- Suggested scope: $SuggestedScope
- Retrieval order: entity memory -> daily memory -> long-term memory
- Next step: search the smallest likely scope first, then widen only if needed
"@
