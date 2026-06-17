"""
Ghost command — Ghost database operations for JEBAT.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any


def ghost_command(args: Any) -> int:
    """Ghost database operations."""
    subcommand = getattr(args, "ghost_command", None)

    if subcommand == "status":
        return _status(args)
    elif subcommand == "list":
        return _list_dbs(args)
    elif subcommand == "create":
        return _create_db(args)
    elif subcommand == "fork":
        return _fork_db(args)
    elif subcommand == "delete":
        return _delete_db(args)
    elif subcommand == "sql":
        return _sql(args)
    elif subcommand == "pause":
        return _pause_db(args)
    elif subcommand == "resume":
        return _resume_db(args)
    elif subcommand == "workspace":
        return _workspace(args)
    elif subcommand == "checkpoint":
        return _checkpoint(args)
    elif subcommand == "cleanup":
        return _cleanup(args)
    else:
        print("Usage: jebat ghost {list|create|fork|delete|sql|pause|resume|workspace|checkpoint|cleanup}")
        print()
        print("Commands:")
        print("  list        List all Ghost databases")
        print("  create      Create a new database")
        print("  fork        Fork a database")
        print("  delete      Delete a database")
        print("  sql         Execute SQL query")
        print("  pause       Pause a database")
        print("  resume      Resume a database")
        print("  workspace   Create agent workspace")
        print("  checkpoint  Create checkpoint")
        print("  cleanup     Clean old workspaces")
        return 1


def _list_dbs(args: Any) -> int:
    from jebat.features.ghost import ghost_list_databases

    async def run():
        try:
            dbs = await ghost_list_databases()
            print(f"{len(dbs)} databases:")
            for db in dbs:
                status = db.status
                dedicated = " (dedicated)" if db.is_dedicated else ""
                print(f"  {db.name} [{status}]{dedicated}")
                if db.connection_string:
                    print(f"    {db.connection_string}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _create_db(args: Any) -> int:
    from jebat.features.ghost import ghost_create_db

    async def run():
        try:
            db = await ghost_create_db(args.name, args.dedicated)
            print(f"Created database: {db.name}")
            print(f"  Connection: {db.connection_string}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _fork_db(args: Any) -> int:
    from jebat.features.ghost import ghost_fork_db

    async def run():
        try:
            db = await ghost_fork_db(args.source, args.name, args.dedicated)
            print(f"Forked {args.source} -> {db.name}")
            print(f"  Connection: {db.connection_string}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _delete_db(args: Any) -> int:
    from jebat.features.ghost import ghost_delete_db

    async def run():
        try:
            success = await ghost_delete_db(args.name, args.force)
            if success:
                print(f"Deleted database: {args.name}")
            else:
                print(f"Failed to delete: {args.name}")
                return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _sql(args: Any) -> int:
    from jebat.features.ghost import ghost_sql, GhostQueryResult

    async def run():
        try:
            result = await ghost_sql(args.database, args.query)
            if isinstance(result, GhostQueryResult):
                if result.error:
                    print(f"Error: {result.error}")
                    return 1
                print(f"Rows: {result.row_count}, Columns: {len(result.columns)}")
                for row in result.rows[:10]:
                    print(row)
                if result.row_count > 10:
                    print(f"... and {result.row_count - 10} more rows")
            else:
                if result.get("error"):
                    print(f"Error: {result['error']}")
                    return 1
                print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _pause_db(args: Any) -> int:
    from jebat.features.ghost import ghost_pause_db_tool

    async def run():
        try:
            await ghost_pause_db_tool({"name": args.name})
            print(f"Paused database: {args.name}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _resume_db(args: Any) -> int:
    from jebat.features.ghost import ghost_resume_db_tool

    async def run():
        try:
            await ghost_resume_db_tool({"name": args.name})
            print(f"Resumed database: {args.name}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _workspace(args: Any) -> int:
    from jebat.features.ghost import ghost_agent_workspace_tool

    async def run():
        try:
            result = await ghost_agent_workspace_tool(args.agent, args.task, args.base)
            print(f"Created workspace: {result['workspace_name']}")
            print(f"  Database: {result['database']['name']}")
            print(f"  Connection: {result['connection_string']}")
            print(f"  Usage: {result['usage']}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _checkpoint(args: Any) -> int:
    from jebat.features.ghost import ghost_checkpoint_tool

    async def run():
        try:
            result = await ghost_checkpoint_tool(args.source, args.name)
            print(f"Created checkpoint: {result['checkpoint']['name']}")
            print(f"  Source: {result['source_db']}")
            print(f"  Recovery: {result['recovery']}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _cleanup(args: Any) -> int:
    from jebat.features.ghost import ghost_cleanup_agent_workspaces_tool

    async def run():
        try:
            result = await ghost_cleanup_agent_workspaces_tool(args.prefix, args.hours, args.dry_run)
            if args.dry_run:
                print(f"Dry run - would delete {result['count']} databases:")
                for name in result['would_delete']:
                    print(f"  {name}")
            else:
                print(f"Deleted {result['count']} databases:")
                for name in result['deleted']:
                    print(f"  {name}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _cleanup(args: Any) -> int:
    from jebat.features.ghost import ghost_cleanup_agent_workspaces_tool

    async def run():
        try:
            result = await ghost_cleanup_agent_workspaces_tool(args.prefix, args.hours, args.dry_run)
            if args.dry_run:
                print(f"Dry run - would delete {result['count']} databases:")
                for name in result['would_delete']:
                    print(f"  {name}")
            else:
                print(f"Deleted {result['count']} databases:")
                for name in result['deleted']:
                    print(f"  {name}")
        except Exception as e:
            print(f"Error: {e}")
            return 1
        return 0

    return asyncio.run(run())


def _status(args: Any) -> int:
    """Check Ghost CLI availability."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["ghost", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            print(f"Ghost CLI: {result.stdout.strip()}")
            # Check if authenticated
            auth_result = subprocess.run(
                ["ghost", "id"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if auth_result.returncode == 0:
                print(f"Authenticated: {auth_result.stdout.strip()}")
            else:
                print("Not authenticated - run 'ghost init'")
        else:
            print("Ghost CLI not found")
            print("Install: curl -fsSL https://install.ghost.build | sh")
    except FileNotFoundError:
        print("Ghost CLI not found")
        print("Install: curl -fsSL https://install.ghost.build | sh")
    except Exception as e:
        print(f"Error checking Ghost: {e}")
        return 1
    return 0


__all__ = ["ghost_command"]