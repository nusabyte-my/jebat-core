# Remote bash over SSH from Windows — the `windows-ssh-bash` failure class

**Status:** RESOLVED 2026-11-15 by `scripts/Invoke-RemoteBash.ps1` (+ self-test).
**Applies to:** every SSH-to-Linux op from a Windows PowerShell host — deploys,
prod DB surgery, health checks, `jq`/`grep`/`head` pipelines, `docker exec -i ... psql`.

## The 5 recorded failures (AutoMimpi `windows-ssh-bash`, 2026-11-14/15)

| # | Symptom | Root cause |
|---|---|---|
| 1 | `bash: $'\r': command not found` | PowerShell writes CRLF; bash sees the stray `\r` as a command. |
| 2 | `syntax error near unexpected token` / `grep`\|`head` "not recognized" | `\|`, `$(...)`, backticks, `for/do` were placed **inside the `ssh "command"` argument**, so PowerShell parsed them locally before ssh. |
| 3 | `ParserError on @{u}` / `@()` | PowerShell-looking tokens in an inline ssh string. |
| 4 | `Cannot find module jsonwebtoken` | (separate) pnpm hoists deps to `node_modules/.pnpm`; minted JWT from wrong path. |
| 5 | `bash: $'\r' ... (CRLF artifact)` again | The heredoc/pipe pattern re-introduced CRLF. |

Root cause of the recurring class: **the complex script was being smuggled
through the ssh `argv` string, where two interpreters (PowerShell → remote bash)
fight over the same metacharacters.**

## The fix — three rules

1. **The remote command is constant and dumb:** `bash -s` (or `docker exec -i ... psql`).
   No `|`, `$(...)`, `@`, backtick, or `$VAR` ever appears in the ssh command string.
2. **The script travels over STDIN**, written as **raw UTF-8 LF bytes** via a
   `StreamWriter` on `StandardInput.BaseStream` — never through PowerShell's
   `Get-Content | ssh` pipeline (that pipeline re-encodes and re-adds CRLF).
3. **argv is built with `.ArgumentList`** (pwsh 7 / .NET Core), which escapes each
   token correctly — no hand-rolled quoting. Windows PowerShell 5.1 gets a
   minimal quoting fallback. stdout/stderr drains start **before** stdin is written
   (avoids pipe deadlock on large output).

## Canonical usage

```powershell
# Default: remote = bash -s (reads script from stdin)
.\scripts\Invoke-RemoteBash.ps1 `
  -Target "ssh -6 -o BatchMode=yes -i ~/.ssh/id_ed25519-hostinger opsadmin@2a02:4780:5e:20bd::1" `
  -ScriptFile .\deploy.sh

# Inline script with pipes / $() / for-do (all safe — they live in stdin, not argv):
.\scripts\Invoke-RemoteBash.ps1 -Target "ssh ... opsadmin@host" `
  -ScriptBlock 'curl -sI https://qpos.erawanwellness.com/api/health | head -1'

# Run the remote side as root:
.\scripts\Invoke-RemoteBash.ps1 -Target "ssh ... opsadmin@host" `
  -ScriptFile .\deploy.sh -RemoteCommand "sudo -H -u root bash -s"

# SQL surgery — script is SQL, remote command is the psql client (NOT bash):
.\scripts\Invoke-RemoteBash.ps1 -Target "ssh ... opsadmin@host" `
  -RemoteCommand "docker exec -i erawanqpos-postgres-1 psql -U erawan -d erawan_qsys" `
  -ScriptFile .\fix.sql
```

Put ALL ssh options (`-6`, `-i`, `-o`, ...) inside `-Target`, before the host —
that's where ssh expects them. `-Target`'s first token is the executable; the
rest are argv. The `-RemoteCommand` tokens are appended last and ssh joins them
into the remote command string.

## Verified 2026-11-15

- `scripts/Test-InvokeRemoteBash.ps1` — **5/5 pass** against a local `bash -s`
  (CRLF, pipes/`$()`/`for-do`, `@{u}`/`@()` literal tokens, exit-code propagation,
  no-trailing-newline last line). No SSH/credentials needed.
- Real prod SSH (Avenue K Hostinger box, IPv6 hostinger key):
  - plain `bash -s` script → `SSH_PATH_OK` / `opsadmin` / UTC timestamp
  - pipe inside script → `HTTP/2 200` (was failure #2)
  - `docker exec -i ... psql` over stdin → `SELECT 1` returned (non-bash RemoteCommand)

## Related (not this helper's job)

- **pnpm hoisting:** mint JWTs from `node_modules/.pnpm/jsonwebtoken@*/node_modules/jsonwebtoken`
  (see `verify-vip4-api` pattern) — resolve the module path, don't assume a local
  `node_modules`.
- Legacy Erawan deploy specifics (nvm sourcing, `sudo -H -u root bash -lc`, core
  build before api) live in the Erawan `AGENTS.md` — those are app constraints,
  independent of how the script reaches the box.
