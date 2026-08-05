"""Tests for non-mutating database migration readiness reporting."""

from contextlib import asynccontextmanager

import pytest

from jebat.database.readiness import check_schema_readiness


pytestmark = pytest.mark.unit


class FakeConnection:
    def __init__(self, tables, revision=None):
        self.tables = set(tables)
        self.revision = revision

    async def fetchval(self, query, *args):
        if "alembic_version" in query and "to_regclass" in query:
            return "alembic_version" if self.revision else None
        if "version_num" in query:
            return self.revision
        return args[0] if args[0] in self.tables else None


class FakeManager:
    def __init__(self, connection):
        self.connection = connection

    @asynccontextmanager
    async def get_postgres_connection(self):
        yield self.connection


@pytest.mark.asyncio
async def test_readiness_accepts_existing_unversioned_init_schema():
    manager = FakeManager(FakeConnection({"users", "memory_m0"}))

    result = await check_schema_readiness(manager, ("users", "memory_m0"))

    assert result["is_ready"] is True
    assert result["migration_state"] == "unversioned"


@pytest.mark.asyncio
async def test_readiness_reports_missing_tables_and_revision():
    manager = FakeManager(FakeConnection({"users"}, revision="20260716_01"))

    result = await check_schema_readiness(manager, ("users", "memory_m1"))

    assert result["is_ready"] is False
    assert result["migration_state"] == "current"
    assert result["missing_tables"] == ["memory_m1"]
