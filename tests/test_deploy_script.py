"""Tests for scripts/deploy-tar-over-ssh.sh.

Runs the real script against a fake `ssh` shim, so the deploy pipeline
(payload selection, server backup, extraction, backup retention) is
exercised end-to-end inside a sandbox — no server touched. The script is
copied into a mini source tree so LOCAL_DIR resolves there and payloads
stay tiny.

Invariants under test:
- fail closed: a failed server-side backup aborts BEFORE extraction
- success: payload lands in the target dir; .env and *.png never leak
- retention: KEEP_LAST prunes the oldest backups and never the fresh one
- no BACKUP: plain overlay deploy with no backup side effects

Note: bash is invoked with POSIX-style paths (as_posix) — on Windows,
backslash paths are eaten by bash as escape characters.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "deploy-tar-over-ssh.sh"

pytestmark = pytest.mark.unit


def _find_bash() -> str | None:
    """Locate a Git-Bash/MSYS bash.exe.

    Bare `bash` on PATH from Windows Python resolves to System32's WSL
    launcher, which cannot open C:/... paths (its root is /mnt/c). Prefer
    the Git for Windows installs; JEBAT_TEST_BASH overrides.
    """
    override = os.environ.get("JEBAT_TEST_BASH")
    if override and Path(override).exists():
        return override
    for cand in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ):
        if Path(cand).exists():
            return cand
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        return found
    return None


BASH = _find_bash()
pytestmark = [pytest.mark.unit]
skip_without_bash = pytest.mark.skipif(
    BASH is None, reason="Git Bash (MSYS) not found; WSL bash cannot run these"
)


def _msys_path(p: Path) -> str:
    """Map a Windows path to its MSYS/Git-Bash form (C:/x -> /c/x).

    Required because GNU tar interprets a colon in a path as a remote
    host:file specifier (`tar -xf - -C C:/dir` -> "Cannot connect to C:").
    """
    s = str(Path(p).resolve())
    if os.name != "nt" or ":" not in s:
        return s
    drive, rest = s.split(":", 1)
    return "/" + drive.lower().lstrip("/") + rest.replace("\\", "/")

SSH_SHIM = textwrap.dedent("""\
    #!/bin/bash
    # Fake ssh: args are [-o BatchMode=yes] HOST COMMAND... Sandbox paths come
    # from FAKE_ROOT / FAKE_SERVER_DIR / FAKE_TAR_RC in the environment.
    while [ $# -gt 0 ]; do
      case "$1" in
        -o|-p) shift 2 ;;
        -*) shift ;;
        *) HOST="$1"; shift; break ;;
      esac
    done
    CMD="$*"
    # Emulate remote bash: comment lines are not executed, so detection must
    # ignore them too.
    CODE=$(echo "$CMD" | grep -v '^[[:space:]]*#')
    case "$CODE" in
      *"tar -xf -"*)
        # Faithful emulation: the script transmits its backup flag as text
        # (`if [ '0' = '1' ]`), so read THAT instead of grepping for tar -czf,
        # which also matches the never-executed branch of a plain deploy.
        DO_BACKUP=$(echo "$CODE" | sed -n "s/.*if \\['\\([01]\\{1,\\}\\)' = '1'\\].*/\\1/p" | head -1)
        [ -n "$DO_BACKUP" ] || DO_BACKUP=$(echo "$CODE" | sed -n "s/.*if \\[ '\\([01]\\{1,\\}\\)' = '1' \\].*/\\1/p" | head -1)
        if [ "$DO_BACKUP" = "1" ]; then
          if [ "${FAKE_TAR_RC:-0}" != "0" ]; then
            echo "   ❌ server-side backup FAILED (simulated)" >&2
            echo "   deploy aborted — nothing was extracted" >&2
            exit 1
          fi
          STAMP=$(echo "$CODE" | sed -n 's/.*jebat-runtime-backup-\\([0-9][0-9]*\\)\\.tar\\.gz.*/\\1/p' | head -1)
          tar -czf "$FAKE_ROOT/jebat-runtime-backup-${STAMP:-shim}.tar.gz" -C "$FAKE_SERVER_DIR" .
        fi
        tar -xf - -C "$FAKE_SERVER_DIR"
        echo "   ok extracted"
        ;;
      *"jebat-runtime-backup-*.tar.gz"*)
        # Retention prune: actually execute it against the sandbox root,
        # substituting the fake paths for /root and the live server dir.
        PRUNE_CMD=$(echo "$CMD" | sed "s|cd /root|cd \"$FAKE_ROOT\"|; s|jebat-runtime-backup-\\*.tar\\.gz|jebat-runtime-backup-*.tar.gz 2>/dev/null|")
        eval "$PRUNE_CMD"
        ;;
      *)
        echo "fake-ssh: unexpected command: $CMD" >&2
        exit 99
        ;;
    esac
""")


@pytest.fixture
def sandbox(tmp_path: Path, monkeypatch):
    """Mini source tree + fake ssh on PATH + server/root sandbox dirs.

    Returns only sandbox paths and the extra env the tests must set; the full
    environment is merged inside run_deploy so secrets from os.environ never
    appear in pytest failure output.
    """
    src = tmp_path / "src"
    (src / "scripts").mkdir(parents=True)
    (src / "jebat" / "core").mkdir(parents=True)
    (src / ".git").mkdir()  # must be pruned by the payload finder
    (src / "scripts" / "deploy-tar-over-ssh.sh").write_text(
        SCRIPT.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (src / "pyproject.toml").write_text("[project]\nname = 'mini'\n", encoding="utf-8")
    (src / "jebat" / "core" / "x.py").write_text("VALUE = 1\n", encoding="utf-8")
    (src / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (src / ".env").write_text("SECRET=1\n", encoding="utf-8")   # must never ship
    (src / "x.png").write_bytes(b"\x89PNG\r\n")                 # must never ship

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "ssh").write_text(SSH_SHIM, encoding="utf-8")

    fake_root = tmp_path / "root"
    fake_server = tmp_path / "server"
    fake_root.mkdir()
    fake_server.mkdir()
    (fake_server / "sentinel.txt").write_text("pre-existing\n", encoding="utf-8")

    return {
        "src": src,
        "root": fake_root,
        "server": fake_server,
        "bin_dir": bin_dir,
    }


def run_deploy(sandbox: dict, *extra_env: tuple[str, str]) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PATH"] = f"{sandbox['bin_dir']}{os.pathsep}{os.environ.get('PATH', '')}"
    env["VPS_HOST"] = "fakeserver"
    # Point the script's remote command at the sandboxed server dir; without
    # this the shim would extract into MSYS's literal /var/www/jebat-core.
    # Paths are mapped to MSYS form so GNU tar never sees a C:/ colon.
    env["VPS_CODE_DIR"] = _msys_path(sandbox["server"])
    env["FAKE_ROOT"] = _msys_path(sandbox["root"])
    env["FAKE_SERVER_DIR"] = _msys_path(sandbox["server"])
    env["FAKE_TAR_RC"] = "0"
    env["KEEP_LAST"] = "5"
    env["SSH_BIN"] = (sandbox["bin_dir"] / "ssh").as_posix()  # the shim, by path
    env.update(dict(extra_env))
    script = sandbox["src"] / "scripts" / "deploy-tar-over-ssh.sh"
    return subprocess.run(
        [BASH, script.as_posix()],
        env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=120,
    )


@skip_without_bash
def test_backup_failure_aborts_before_extraction(sandbox):
    result = run_deploy(sandbox, ("BACKUP", "1"), ("KEEP_LAST", "0"), ("FAKE_TAR_RC", "1"))

    assert result.returncode != 0
    # The abort notice is emitted on the remote's stderr.
    assert "aborted" in result.stderr
    server: Path = sandbox["server"]
    # Nothing was extracted: only the sentinel remains.
    assert [p.name for p in server.iterdir()] == ["sentinel.txt"]
    # And no (partial) backup pretends to be a rollback option.
    assert list(sandbox["root"].iterdir()) == []


@skip_without_bash
def test_successful_deploy_extracts_and_never_leaks_secrets(sandbox):
    result = run_deploy(sandbox, ("BACKUP", "1"), ("KEEP_LAST", "0"))
    assert result.returncode == 0, result.stdout + result.stderr
    server: Path = sandbox["server"]
    assert (server / "pyproject.toml").exists()
    assert (server / "jebat" / "core" / "x.py").exists()
    assert (server / "sentinel.txt").read_text() == "pre-existing\n"  # overlay, not wipe
    # Exclusions hold end-to-end.
    assert not (server / ".env").exists()
    assert not (server / "x.png").exists()
    assert not (server / ".git").exists()
    # The backup exists and is a readable gzip tarball.
    backups = list(sandbox["root"].glob("jebat-runtime-backup-*.tar.gz"))
    assert len(backups) == 1
    probe = subprocess.run(["tar", "-tzf", backups[0].as_posix()], capture_output=True)
    assert probe.returncode == 0


@skip_without_bash
def test_retention_prunes_oldest_and_keeps_fresh(sandbox):
    root: Path = sandbox["root"]
    old_stamp = 1_000_000_000
    for i in range(3):
        bk = root / f"jebat-runtime-backup-{old_stamp + i}.tar.gz"
        bk.write_bytes(b"")
        os.utime(bk, (1_700_000_000 + i * 60, 1_700_000_000 + i * 60))

    result = run_deploy(sandbox, ("BACKUP", "1"), ("KEEP_LAST", "2"))

    assert result.returncode == 0, result.stdout + result.stderr
    remaining = sorted(p.name for p in root.glob("jebat-runtime-backup-*.tar.gz"))
    assert len(remaining) == 2
    # The fresh backup (created by this run, newest mtime) must survive.
    assert remaining[-1] != f"jebat-runtime-backup-{old_stamp}.tar.gz"
    assert not (root / f"jebat-runtime-backup-{old_stamp}.tar.gz").exists()


@skip_without_bash
def test_plain_deploy_has_no_backup_side_effects(sandbox):
    result = run_deploy(sandbox)  # BACKUP unset

    assert result.returncode == 0, result.stdout + result.stderr
    assert (sandbox["server"] / "pyproject.toml").exists()
    assert list(sandbox["root"].iterdir()) == []
