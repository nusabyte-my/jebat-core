"""
JEBAT Migration Agent

Database schema migrations:
- Auto-generate migrations
- Migration versioning
- Rollback support
- Multi-database migrations
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """Migration definition."""

    id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    up_sql: str = ""
    down_sql: str = ""
    status: str = "pending"  # pending, applied, rolled_back


class MigrationAgent:
    """
    Database Migration Agent for JEBAT.

    Manages schema changes with version control.
    """

    def __init__(self, db_connector=None):
        """
        Initialize Migration Agent.

        Args:
            db_connector: Database connector instance
        """
        self.db_connector = db_connector
        self.migrations: List[Migration] = []
        self.migrations_table = "schema_migrations"

        logger.info("MigrationAgent initialized")

    async def create_migration(
        self,
        name: str,
        changes: Dict[str, Any],
    ) -> Migration:
        """
        Create a new migration.

        Args:
            name: Migration name
            changes: Schema changes

        Returns:
            Migration object
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        migration_id = f"{timestamp}_{name.lower().replace(' ', '_')}"

        # Generate UP and DOWN SQL
        up_sql = self._generate_up_sql(changes)
        down_sql = self._generate_down_sql(changes)

        migration = Migration(
            id=migration_id,
            name=name,
            up_sql=up_sql,
            down_sql=down_sql,
        )

        self.migrations.append(migration)

        logger.info(f"Created migration: {migration_id}")

        return migration

    def _generate_up_sql(self, changes: Dict[str, Any]) -> str:
        """Generate UP migration SQL."""
        sql_parts = []

        if "create_table" in changes:
            table = changes["create_table"]
            sql_parts.append(f"CREATE TABLE {table['name']} (")
            columns = []
            for col in table.get("columns", []):
                col_def = f"  {col['name']} {col['type']}"
                if col.get("primary_key"):
                    col_def += " PRIMARY KEY"
                if col.get("auto_increment"):
                    col_def += " AUTO_INCREMENT"
                if not col.get("nullable", True):
                    col_def += " NOT NULL"
                columns.append(col_def)
            sql_parts.append(",\n".join(columns))
            sql_parts.append(");")

        if "add_column" in changes:
            col = changes["add_column"]
            sql_parts.append(
                f"ALTER TABLE {col['table']} ADD COLUMN {col['name']} {col['type']};"
            )

        if "add_index" in changes:
            idx = changes["add_index"]
            sql_parts.append(
                f"CREATE INDEX {idx['name']} ON {idx['table']} ({idx['column']});"
            )

        return "\n".join(sql_parts)

    def _generate_down_sql(self, changes: Dict[str, Any]) -> str:
        """Generate DOWN migration SQL (rollback)."""
        sql_parts = []

        if "create_table" in changes:
            table = changes["create_table"]
            sql_parts.append(f"DROP TABLE IF EXISTS {table['name']};")

        if "add_column" in changes:
            col = changes["add_column"]
            sql_parts.append(
                f"ALTER TABLE {col['table']} DROP COLUMN IF EXISTS {col['name']};"
            )

        if "add_index" in changes:
            idx = changes["add_index"]
            sql_parts.append(f"DROP INDEX IF EXISTS {idx['name']};")

        return "\n".join(sql_parts)

    async def apply_migration(self, migration: Migration) -> Dict[str, Any]:
        """
        Apply a migration.

        Args:
            migration: Migration to apply

        Returns:
            Result
        """
        logger.info(f"Applying migration: {migration.id}")

        if not self.db_connector:
            return {"error": "No database connector available"}

        # Execute UP SQL
        result = await self.db_connector.execute(migration.up_sql)

        if result.get("status") == "success":
            migration.status = "applied"

            # Record migration
            await self._record_migration(migration)

        return {
            "status": "success",
            "migration": migration.id,
            "execution_time": result.get("execution_time", 0),
        }

    async def rollback_migration(self, migration: Migration) -> Dict[str, Any]:
        """
        Rollback a migration.

        Args:
            migration: Migration to rollback

        Returns:
            Result
        """
        logger.info(f"Rolling back migration: {migration.id}")

        if not self.db_connector:
            return {"error": "No database connector available"}

        # Execute DOWN SQL
        result = await self.db_connector.execute(migration.down_sql)

        if result.get("status") == "success":
            migration.status = "rolled_back"

        return {
            "status": "success",
            "migration": migration.id,
        }

    async def _record_migration(self, migration: Migration) -> bool:
        """Record migration in database."""
        if not self.db_connector:
            return False

        # Create migrations table if not exists
        await self.db_connector.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255),
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50)
            )
        """)

        # Insert migration record
        await self.db_connector.execute(
            f"INSERT INTO {self.migrations_table} (id, name, status) VALUES (?, ?, ?)",
            {"id": migration.id, "name": migration.name, "status": migration.status},
        )

        return True

    async def get_pending_migrations(self) -> List[Migration]:
        """Get all pending migrations."""
        return [m for m in self.migrations if m.status == "pending"]

    async def get_applied_migrations(self) -> List[Migration]:
        """Get all applied migrations."""
        return [m for m in self.migrations if m.status == "applied"]

    async def migrate_all(self) -> Dict[str, Any]:
        """Apply all pending migrations."""
        pending = await self.get_pending_migrations()

        if not pending:
            return {"status": "success", "message": "No pending migrations"}

        results = []
        for migration in pending:
            result = await self.apply_migration(migration)
            results.append(result)

        return {
            "status": "success",
            "migrations_applied": len(results),
            "results": results,
        }

    async def generate_migration_from_diff(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
    ) -> Migration:
        """
        Generate migration from schema difference.

        Args:
            old_schema: Current schema
            new_schema: Target schema

        Returns:
            Generated migration
        """
        changes = self._calculate_schema_diff(old_schema, new_schema)

        return await self.create_migration(
            name=f"schema_update_{datetime.now().strftime('%Y%m%d')}",
            changes=changes,
        )

    def _calculate_schema_diff(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate difference between schemas."""
        # Simplified diff calculation
        changes = {}

        old_tables = {t["name"]: t for t in old_schema.get("tables", [])}
        new_tables = {t["name"]: t for t in new_schema.get("tables", [])}

        # New tables
        for name, table in new_tables.items():
            if name not in old_tables:
                changes["create_table"] = table

        # New columns in existing tables
        for name, table in new_tables.items():
            if name in old_tables:
                old_cols = {c["name"] for c in old_tables[name].get("columns", [])}
                new_cols = {c["name"] for c in table.get("columns", [])}

                for col in table.get("columns", []):
                    if col["name"] not in old_cols:
                        changes["add_column"] = {
                            "table": name,
                            **col,
                        }

        return changes
