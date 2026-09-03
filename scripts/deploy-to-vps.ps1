<# 
.SYNOPSIS
JEBAT VPS Deployer - PowerShell version for Windows
Deploys jebatcore to VPS at 72.62.254.65 (.206)
#>

param(
    [string]$VpsHost = "root@72.62.254.65",
    [string]$VpsCodeDir = "/var/www/jebat-core",
    [string]$VpsWebDir = "/var/www/jebat.online"
)

$LocalDir = Split-Path -Parent $MyInvocation.MyCommand.Definition | Split-Path -Parent

Write-Host "`n⚔️  JEBAT VPS Deployer" -ForegroundColor Cyan
Write-Host "======================`n" -ForegroundColor Cyan
Write-Host "Source: $LocalDir"
Write-Host "VPS Code: ${VpsHost}:${VpsCodeDir}"
Write-Host "VPS Web:  ${VpsHost}:${VpsWebDir}`n"

# Exclusion patterns
$ExcludePatterns = @(
    "node_modules",
    ".next",
    ".git",
    "jebat-core",
    "jebat-online",
    "out",
    "__pycache__",
    "*.pyc",
    ".env",
    ".claude",
    ".gemini",
    "*.egg-info"
)

# Step 1: Create code directory on VPS
Write-Host "📁 Setting up VPS code directory..." -ForegroundColor Yellow
ssh $VpsHost "mkdir -p '$VpsCodeDir' '$VpsWebDir'"

# Step 2: Sync code to VPS using tar + scp (Windows-compatible)
Write-Host "🔄 Syncing code to VPS..." -ForegroundColor Yellow

$TarExcludeArgs = $ExcludePatterns | ForEach-Object { "--exclude=$_" } -join " "

Push-Location $LocalDir
try {
    Write-Host "   Creating archive..." -ForegroundColor Gray
    if (Test-Path ".git") {
        git archive --format=tar HEAD | gzip | ssh $VpsHost "tar -xzf - -C '$VpsCodeDir' $TarExcludeArgs"
    } else {
        tar -czf - $TarExcludeArgs * .[^.]* 2>$null | ssh $VpsHost "tar -xzf - -C '$VpsCodeDir'"
    }
    Write-Host "✅ Code synced to $VpsCodeDir" -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 3: Build frontend on VPS
Write-Host "`n🔨 Building frontend on VPS..." -ForegroundColor Yellow
$BuildCmd = 'cd \'' + $VpsCodeDir + '/apps/web\' && npm install && npx next build'
ssh $VpsHost $BuildCmd | Write-Host

# Step 4: Deploy frontend build to web directory
Write-Host "`n🚀 Deploying frontend to web directory..." -ForegroundColor Yellow
$RemoveDirs = @("_next", "dashboard", "demo", "docs", "onboarding", "setup", "integration", "gelanggang", "guides")
$RemoveFiles = @("index.html", "*.svg", "*.ico", "*.txt", "__next*", "404", "404.html", "_not-found")

$RemoveCmd = @()
foreach ($d in $RemoveDirs) { $RemoveCmd += "rm -rf '" + $VpsWebDir + "/" + $d + "'" }
foreach ($f in $RemoveFiles) { $RemoveCmd += "rm -f '" + $VpsWebDir + "/" + $f + "'" }
$RemoveCmd = ($RemoveCmd -join "; ") + " 2>/dev/null"

ssh $VpsHost $RemoveCmd
$CopyCmd = 'cp -r \'' + $VpsCodeDir + '/apps/web/out/*\' \'' + $VpsWebDir + '/\' && chown -R www-data:www-data \'' + $VpsWebDir + '/\''
ssh $VpsHost $CopyCmd

# Step 5: Restart backend API
Write-Host "`n🔄 Restarting backend API..." -ForegroundColor Yellow
$ApiCmd = 'cd \'' + $VpsCodeDir + '/apps/api\' && pkill -f jebat_api 2>/dev/null || true; nohup python -m services.api.jebat_api > /var/log/jebat-api.log 2>&1 &'
ssh $VpsHost $ApiCmd

# Step 6: Verify deployment
Write-Host "`n🔍 Verifying deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$Health = ssh $VpsHost "curl -s http://localhost:8000/api/v1/health" 2>$null
if (-not $Health) { $Health = "API offline" }

$Landing = ssh $VpsHost "curl -s -o /dev/null -w '%{http_code}' https://jebat.online/" 2>$null
if (-not $Landing) { $Landing = "000" }

$Gelanggang = ssh $VpsHost "curl -s -o /dev/null -w '%{http_code}' https://jebat.online/gelanggang/" 2>$null
if (-not $Gelanggang) { $Gelanggang = "000" }

Write-Host "`n📊 Deployment Results:" -ForegroundColor Cyan
Write-Host "   API Health: $Health"
Write-Host "   Landing: HTTP $Landing"
Write-Host "   Gelanggang: HTTP $Gelanggang`n"

if ($Landing -eq "200" -and $Gelanggang -eq "200") {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host "   🌐 https://jebat.online"
    Write-Host "   🏛️ https://jebat.online/gelanggang/"
} else {
    Write-Host "⚠️  Some services may need attention" -ForegroundColor Yellow
    Write-Host "   SSH: ssh $VpsHost"
    Write-Host "   Check: tail -f /var/log/nginx/error.log"
    Write-Host "   Check: tail -f /var/log/jebat-api.log"
}