#!/bin/bash
# auto-deploy.sh — thin wrapper: the real script lives in scripts/auto-deploy.sh.
#
# deploy-webhook.py prefers this directory (infra/deploy/) and falls back to
# scripts/. Keeping a real script here invited silent drift between the two
# copies, so this file only resolves and execs the canonical one. Never edit
# deploy logic here; edit scripts/auto-deploy.sh.
#
# Resolution order (first hit wins):
#   1. $JEBAT_AUTO_DEPLOY          — explicit override
#   2. $0-relative                 — <this dir>/../../scripts/auto-deploy.sh
#                                    (works whenever this file is checked out
#                                    in the repo; fails when the webhook runs
#                                    this wrapper from a staged /tmp copy)
#   3. cwd-relative                — $PWD/../../scripts/auto-deploy.sh
#                                    (the webhook runs the staged script with
#                                    cwd = its own dir = <repo>/infra/deploy,
#                                    so the repo root is two levels up; this
#                                    is the staged-copy path)
# If none resolve, fail loudly rather than guessing. When the target runs, it
# is copied to a temp file first (same reason the webhook stages this wrapper:
# auto-deploy.sh performs `git reset --hard` and must not be read in place).
#
# Set JEBAT_WRAPPER_DRY_RUN=1 to print the resolved script and exit without
# executing it (used by tests).

set -euo pipefail

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"

resolve() {
    if [ -n "${JEBAT_AUTO_DEPLOY:-}" ]; then
        if [ -f "$JEBAT_AUTO_DEPLOY" ]; then
            echo "$JEBAT_AUTO_DEPLOY"
            return 0
        fi
    fi
    if [ -f "$SELF_DIR/../../scripts/auto-deploy.sh" ]; then
        echo "$SELF_DIR/../../scripts/auto-deploy.sh"
        return 0
    fi
    if [ -f "$PWD/../../scripts/auto-deploy.sh" ]; then
        echo "$PWD/../../scripts/auto-deploy.sh"
        return 0
    fi
    return 1
}

TARGET="$(resolve)" || {
    echo "auto-deploy wrapper: cannot locate scripts/auto-deploy.sh" >&2
    echo "  looked at: \$JEBAT_AUTO_DEPLOY, $SELF_DIR/../../scripts/, $PWD/../../scripts/" >&2
    echo "  set JEBAT_AUTO_DEPLOY=/path/to/scripts/auto-deploy.sh and retry" >&2
    exit 1
}

if [ "${JEBAT_WRAPPER_DRY_RUN:-0}" = "1" ]; then
    echo "$TARGET"
    exit 0
fi

# Stage the target before running: auto-deploy.sh does `git reset --hard`,
# which replaces the very file bash would be reading incrementally. The
# webhook already stages THIS wrapper; staging the target preserves that
# invariant one level down.
STAGED="$(mktemp "${TMPDIR:-/tmp}/jebat-auto-deploy.XXXXXX.sh")"
cp "$TARGET" "$STAGED"
chmod 755 "$STAGED"

set +e
bash "$STAGED" "$@"
RC=$?
rm -f "$STAGED"
exit $RC
