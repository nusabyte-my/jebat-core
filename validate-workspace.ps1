$ErrorActionPreference = 'Stop'

Write-Host "Validating adapters..."
python adapters/validate.py

Write-Host ""
Write-Host "Checking CLI package..."
$requiredCliAssets = @(
  'package.json',
  'README.md',
  'bin/jebatcore.js',
  'lib/cli.js',
  'lib/constants.js',
  'lib/detect.js',
  'lib/install.js',
  'lib/mcp-server.js',
  'lib/prompt.js'
)

foreach ($path in $requiredCliAssets) {
  if (-not (Test-Path $path)) {
    throw "Missing required CLI asset: $path"
  }
  Write-Host "OK: $path"
}

Write-Host ""
Write-Host "Checking playbooks..."
$requiredPlaybooks = @(
  'vault/playbooks/dispatch-matrix.md',
  'vault/playbooks/feature-delivery.md',
  'vault/playbooks/launch-flow.md',
  'vault/playbooks/support-flow.md',
  'vault/playbooks/security-review.md',
  'vault/playbooks/client-proposal.md',
  'vault/playbooks/sales-enablement.md',
  'vault/playbooks/discovery-call.md',
  'vault/playbooks/retainer-ops.md',
  'vault/playbooks/monthly-review.md',
  'vault/playbooks/quarterly-planning.md',
  'vault/playbooks/renewal-strategy.md'
)

foreach ($path in $requiredPlaybooks) {
  if (-not (Test-Path $path)) {
    throw "Missing required playbook: $path"
  }
  Write-Host "OK: $path"
}

Write-Host ""
Write-Host "Checking templates..."
$requiredTemplates = @(
  'vault/templates/feature-brief.md',
  'vault/templates/campaign-brief.md',
  'vault/templates/seo-audit.md',
  'vault/templates/acceptance-spec.md',
  'vault/templates/proposal-brief.md',
  'vault/templates/sales-brief.md',
  'vault/templates/discovery-brief.md',
  'vault/templates/retainer-brief.md',
  'vault/templates/monthly-review.md',
  'vault/templates/quarterly-plan.md',
  'vault/templates/renewal-brief.md'
)

foreach ($path in $requiredTemplates) {
  if (-not (Test-Path $path)) {
    throw "Missing required template: $path"
  }
  Write-Host "OK: $path"
}

Write-Host ""
Write-Host "Checking checklists..."
$requiredChecklists = @(
  'vault/checklists/engineering-verification.md',
  'vault/checklists/security-verification.md',
  'vault/checklists/database-verification.md',
  'vault/checklists/automation-verification.md',
  'vault/checklists/uiux-verification.md',
  'vault/checklists/seo-verification.md',
  'vault/checklists/content-copy-verification.md',
  'vault/checklists/analytics-verification.md',
  'vault/checklists/product-support-verification.md'
)

foreach ($path in $requiredChecklists) {
  if (-not (Test-Path $path)) {
    throw "Missing required checklist: $path"
  }
  Write-Host "OK: $path"
}

Write-Host ""
Write-Host "Workspace validation passed."
