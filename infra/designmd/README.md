# JEBAT × DESIGNmd CLI integration

Adds a `design` subcommand to the JEBAT CLI that wraps the
[DESIGNmd](https://designmd.ai) registry of DESIGN.md design systems:

    jebat design search "dark fintech" --limit 5   # browse (no key)
    jebat design tags                              # tag cloud
    jebat design get <owner/name>                  # view (needs DESIGNMD_API_KEY)
    jebat design download <owner/name> -o ./DESIGN.md
    jebat design upload ./DESIGN.md --name "My Kit" --tags dark,saas

## Install (one-time, user-space)
    npm install -g designmd
    export DESIGNMD_API_KEY=***        # from https://designmd.ai/api-keys
                                       # (search/tags need no key; get/download/upload do)

## Source of truth
The live, working code lives in the canonical center (`jebat-core/`, which is
gitignored in this repo), so it is NOT tracked directly:
    jebat-core/jebat_cli_new/designmd_cli.py   # new wrapper module
    jebat-core/jebat_cli_new/main.py           # design subcommand wired in
    jebat-core/adapters/profiles/jebat-designer.md  # documents the subcommand

This `infra/designmd/` directory is the TRACKED MIRROR of those three files:
    designmd_cli.py            = jebat-core/jebat_cli_new/designmd_cli.py
    main.py.jebat-cli          = jebat-core/jebat_cli_new/main.py (reference copy)
    jebat-designer.profile.md  = jebat-core/adapters/profiles/jebat-designer.md

When you change the integration, update `jebat-core/` (where it runs) AND
re-copy here so the repo keeps a committable copy. If `jebat-core/` ever stops
being gitignored, delete this mirror and track the originals instead.

## Verification
Ad-hoc (no canonical CI test for this change):
    python -m jebat_cli_new.main design --help      # lists 5 actions
    python -m jebat_cli_new.main design tags        # live: 50-tag cloud
    python -m jebat_cli_new.main design search "dark fintech" --limit 3
Live checks confirmed: tags + search return real data; get/download/upload
correctly surface the upstream "DESIGNMD_API_KEY required" error when unset.
