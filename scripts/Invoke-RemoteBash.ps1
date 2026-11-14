<#
.SYNOPSIS
    Invoke-RemoteBash.ps1 — run a bash script on a remote host over SSH, safely, from Windows PowerShell.

.DESCRIPTION
    Canonical fix for the recurring "windows-ssh-bash" failure class (5 recorded
    occurrences, 2026-11-14/15). It eliminates all root causes:

      1. `bash: $'\r': command not found`  -> PowerShell writes CRLF; bash sees
         the stray \r as a command. FIX: script is LF-normalized and written to
         stdin as raw UTF-8 bytes via a StreamWriter (no PowerShell pipeline
         re-encoding, which is the actual source of the CRLF).
      2. `syntax error near unexpected token` / `grep|head` parsed LOCALLY /
         `$(...)` / for-do / backticks -> putting shell-meta inside the ssh
         "command" string makes PowerShell interpret it BEFORE ssh sees it.
         FIX: the ssh argv contains ONLY plain tokens; the complex script travels
         over STDIN. The remote command is the constant `bash -s`. Nothing
         shell-meta ever sits in the ssh command string.
      3. `@{u}` / `@()` PowerShell ParserError -> impossible (see #2).
      4. quoting / `$TOKEN` expansion surprises -> stdin needs no nested quoting;
         .ArgumentList (pwsh 7) escapes argv correctly with no manual quoting.

    Usage:
        # real SSH (default remote command = "bash -s"):
        .\Invoke-RemoteBash.ps1 -Target "ssh -6 -i ~/.ssh/id_ed25519-hostinger opsadmin@2a02:4780:5e:20bd::1" -ScriptFile .\deploy.sh

        # inline script:
        .\Invoke-RemoteBash.ps1 -Target "ssh ... opsadmin@host" -ScriptBlock 'echo hi; whoami'

        # run the remote side as root (remote command = "sudo -H -u root bash -s"):
        .\Invoke-RemoteBash.ps1 -Target "ssh ... opsadmin@host" -ScriptFile .\deploy.sh -RemoteCommand "sudo -H -u root bash -s"

        # feed a Postgres container instead of a shell (script = SQL over stdin):
        .\Invoke-RemoteBash.ps1 -Target "ssh ... opsadmin@host" -ScriptFile .\fix.sql -RemoteCommand "docker exec -i erawanqpos-postgres-1 psql -U erawan -d erawan_qsys"

    Pass ALL ssh options (-o, -i, -6, etc.) inside -Target; they are argv tokens
    before the host, exactly where ssh expects them. -Target's first token is the
    executable (FileName); everything after it is ssh argv. The remote command
    tokens are appended last and ssh joins them into the command string.

.NOTES
    Author : JEBAT (Laksamana / Panglima) — canonical SSH-over-Windows helper
    Created: 2026-11-15
    Test   : .\Test-InvokeRemoteBash.ps1  (self-test against local bash, no SSH needed)
    See    : docs/remote-bash-over-ssh.md (failure-class write-up + recipes)
#>
[CmdletBinding()]
param(
    # Full ssh client invocation INCLUDING options and host, e.g.
    #   "ssh -6 -o BatchMode=yes -i ~/.ssh/key opsadmin@2a02:4780:5e:20bd::1"
    # First token = executable; rest = argv. Quoted tokens with spaces are kept intact.
    [Parameter(Mandatory = $true)]
    [string] $Target,

    # Local bash script path (CRLF or LF — normalized here).
    [Parameter(Mandatory = $true, ParameterSetName = "File")]
    [string] $ScriptFile,

    # Inline bash script text.
    [Parameter(Mandatory = $true, ParameterSetName = "Block")]
    [string] $ScriptBlock,

    # Command executed on the REMOTE side. Default "bash -s" (reads script from stdin).
    # For a LOCAL bash self-test, pass "-s" (see Test-InvokeRemoteBash.ps1).
    [string] $RemoteCommand = "bash -s"
)

$ErrorActionPreference = "Stop"

# ---- Tokenize an argv line (NOT a script interpreter) ------------------------
# Splits on whitespace, honours single/double quotes, strips the quote chars, but
# NEVER evaluates $, |, @, (, backtick, etc. Backslashes are preserved literally
# so Windows key paths like C:\Users\...\id_ed25519 stay intact.
function Split-Argv([string] $line) {
    $tokens = New-Object System.Collections.Generic.List[string]
    $cur = New-Object System.Text.StringBuilder
    $inSingle = $false; $inDouble = $false
    foreach ($ch in $line.ToCharArray()) {
        if ($ch -eq "'" -and -not $inDouble) { $inSingle = -not $inSingle; continue }
        if ($ch -eq '"' -and -not $inSingle) { $inDouble = -not $inDouble; continue }
        if ($ch -eq ' ' -and -not $inSingle -and -not $inDouble) {
            if ($cur.Length -gt 0) { $tokens.Add($cur.ToString()); [void]$cur.Clear() }
            continue
        }
        [void]$cur.Append($ch)
    }
    if ($cur.Length -gt 0) { $tokens.Add($cur.ToString()) }
    return ,$tokens.ToArray()
}

# ---- 1. Script text -----------------------------------------------------------
if ($PSCmdlet.ParameterSetName -eq "File") {
    $resolved = (Resolve-Path -LiteralPath $ScriptFile).Path
    $script = [System.IO.File]::ReadAllText($resolved)
} else {
    $script = $ScriptBlock
}

# ---- 2. LF-normalize (kills the $'\r' failure) -------------------------------
$script = $script -replace "`r`n", "`n" -replace "`r", "`n"
$script = $script.TrimEnd("`n") + "`n"   # exactly one trailing newline

# ---- 3. Build argv: FileName + ssh argv + remote command tokens --------------
$tokens = New-Object System.Collections.Generic.List[string]
foreach ($t in (Split-Argv $Target))          { $tokens.Add($t) }          # ssh ... host
foreach ($t in (Split-Argv $RemoteCommand))   { $tokens.Add($t) }          # bash -s (or sudo ... / docker exec ...)
if ($tokens.Count -lt 2) { throw "Target + RemoteCommand must produce at least a FileName and one argument." }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $tokens[0]
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8

# pwsh 7 (.NET Core): .ArgumentList escapes each token correctly — no manual
# quoting. Windows PowerShell 5.1 (.NET Framework): fall back to manual quoting.
$useArgList = ($null -ne $psi.ArgumentList)
if ($useArgList) {
    for ($i = 1; $i -lt $tokens.Count; $i++) { [void]$psi.ArgumentList.Add([string]$tokens[$i]) }
} else {
    $parts = for ($i = 1; $i -lt $tokens.Count; $i++) {
        $t = [string]$tokens[$i]
        if ($t -match '\s') { '"' + ($t -replace '"', '\"') + '"' } else { $t }
    }
    $psi.Arguments = $parts -join ' '
}

# ---- 4. Run with stdin = raw LF bytes, drain stdout/stderr async -------------
$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
[void]$proc.Start()

$outTask = $proc.StandardOutput.ReadToEndAsync()   # start drains BEFORE writing stdin (no deadlock)
$errTask = $proc.StandardError.ReadToEndAsync()

$stdin = New-Object System.IO.StreamWriter($proc.StandardInput.BaseStream, (New-Object System.Text.UTF8Encoding($false)))
$stdin.NewLine = "`n"
$stdin.Write($script)
$stdin.Flush()
$stdin.Close()

$proc.WaitForExit()
$stdout = $outTask.GetAwaiter().GetResult()
$stderr = $errTask.GetAwaiter().GetResult()

# Emit stdout on the SUCCESS stream (composable / capturable). It stays ONE
# multi-line string object. stderr goes to the host error stream. A non-zero
# remote exit throws — callers rely on no-throw for success.
if ($stdout) { Write-Output $stdout }
if ($stderr) { [Console]::Error.Write($stderr) }

if ($proc.ExitCode -ne 0) {
    throw "Remote command exited with code $($proc.ExitCode). argv: $($tokens -join ' ')"
}
# Success: no return object in the stream (output was already emitted above).
