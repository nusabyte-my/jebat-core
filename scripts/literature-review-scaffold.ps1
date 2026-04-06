param(
  [Parameter(Mandatory = $true)][string]$Topic,
  [string]$Output = "summary"
)

@"
# Literature Review Scaffold

- Topic: $Topic
- Output target: $Output

## Search plan
- identify core terms
- identify synonym expansions
- gather strongest sources first
- note disagreement and gaps

## Paper log
- title
- source
- relevance
- notes

## Synthesis
- key themes
- strongest evidence
- disagreements
- next reading
"@
