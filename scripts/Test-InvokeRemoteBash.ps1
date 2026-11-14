<#
.SYNOPSIS
    Self-test for Invoke-RemoteBash.ps1 — proves the 4 windows-ssh-bash failure
    variants are eliminated. Uses a LOCAL bash (`bash -s`) so no SSH/credentials
    are needed; the helper's stdin+LF path is identical for local and remote.

    Run: pwsh -File .\Test-InvokeRemoteBash.ps1   (bash must be on PATH: Git Bash / WSL)
#>
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$helper = Join-Path $here "Invoke-RemoteBash.ps1"

$bash = Get-Command bash -ErrorAction SilentlyContinue
if (-not $bash) {
    Write-Host "SKIP: 'bash' not found on PATH (install Git Bash / WSL to run the self-test)." -ForegroundColor Yellow
    exit 0
}

# Local bash self-test: FileName = "bash" (from -Target), remote command = "-s"
# (reads stdin). The helper's -Target first token becomes the executable.
function Invoke-Local([string] $ScriptBlockText, [string] $ScriptFilePath) {
    if ($ScriptFilePath) {
        return (& $helper -Target "bash" -RemoteCommand "-s" -ScriptFile $ScriptFilePath)
    }
    return (& $helper -Target "bash" -RemoteCommand "-s" -ScriptBlock $ScriptBlockText)
}

$pass = 0; $fail = 0
function Check($name, [scriptblock]$body) {
    try { & $body; Write-Host "  ok   $name" -ForegroundColor Green; $script:pass++ }
    catch { Write-Host "  FAIL $name :: $_" -ForegroundColor Red; $script:fail++ }
}

Write-Host "=== Invoke-RemoteBash self-test (target: local bash -s) ===" -ForegroundColor Cyan

# 1. CRLF artifact: a script with CRLF must NOT produce `$'\r': command not found`.
Check "CRLF script has no stray carriage-return error" {
    $f = Join-Path $env:TEMP "irb_crlf_test.sh"
    [System.IO.File]::WriteAllText($f, "echo CRLF_OK`r`nwhoami`r`n", (New-Object System.Text.UTF8Encoding($false)))
    $out = Invoke-Local -ScriptFilePath $f
    Remove-Item $f -Force
    if ($out -notmatch "CRLF_OK") { throw "missing CRLF_OK in output: $out" }
}

# 2. Pipes / $() / for-do / backticks inside the SCRIPT (not argv) must survive
#    and be executed by bash, not PowerShell.
Check "pipes, command-substitution and for/do run remotely" {
    $sb = @'
echo "PIPE_TEST"
printf 'a b c\n' | tr ' ' '-'
x=$(echo SUBST_OK); echo "$x"
for i in 1 2 3; do echo "loop$i"; done
'@
    $out = Invoke-Local -ScriptBlockText $sb
    foreach ($needle in @("PIPE_TEST", "a-b-c", "SUBST_OK", "loop3")) {
        if ($out -notmatch $needle) { throw "missing '$needle' in output: $out" }
    }
}

# 3. `@{u}`-style / @() tokens inside the script are literal to bash (no PS ParserError).
Check "PowerShell-looking tokens stay literal in the script body" {
    $out = Invoke-Local -ScriptBlockText 'echo "@{u} and @() are just text"'
    if ($out -notmatch "are just text") { throw "output mangled: $out" }
}

# 4. Exit codes propagate (a failing remote script must throw).
Check "non-zero remote exit code is surfaced" {
    $threw = $false
    try { Invoke-Local -ScriptBlockText 'echo before; exit 7' } catch { $threw = $true }
    if (-not $threw) { throw "expected a throw on exit 7" }
}

# 5. Last line without trailing newline still executes (TrimEnd + newline fix).
Check "no-trailing-newline last line executes" {
    $f = Join-Path $env:TEMP "irb_nonl_test.sh"
    [System.IO.File]::WriteAllText($f, "echo LAST_LINE_OK", (New-Object System.Text.UTF8Encoding($false)))
    $out = Invoke-Local -ScriptFilePath $f
    Remove-Item $f -Force
    if ($out -notmatch "LAST_LINE_OK") { throw "last line did not run: $out" }
}

Write-Host "`n$pass passed, $fail failed" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Red" })
if ($fail -gt 0) { exit 1 }
