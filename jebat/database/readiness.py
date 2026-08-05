"""Non-invasive database schema readiness checks."""

from __future__ import annotations

from typing import Any, Iterable


MEMORY_TABLES = (
    "users",
    "memory_m0",
    "memory_m1",
    "memory_m2",
    "memory_m3",
    "memory_m4",
)


async def check_schema_readiness(
    manager: Any, required_tables: Iterable[str] = MEMORY_TABLES
) -> dict[str, Any]:
    """Report schema state without changing it.

    Databases initialized by the existing ``create_tables`` path are considered
    ready when their required tables exist, even before they are Alembic-stamped.
    """
    required = tuple(required_tables)
    async with manager.get_postgres_connection() as connection:
        version_table = await connection.fetchval("SELECT to_regclass('alembic_version')")
        revision = None
        if version_table:
            revision = await connection.fetchval("SELECT version_num FROM alembic_version")

        missing_tables = []
        for table in required:
            exists = await connection.fetchval("SELECT to_regclass($1)", table)
            if not exists:
                missing_tables.append(table)

    return {
        "is_ready": not missing_tables,
        "migration_state": "current" if revision else "unversioned",
        "revision": revision,
        "required_tables": required,
        "missing_tables": missing_tables,
    }
