"""
JEBAT Database System

Database connection management, models, and repositories.

Requires: sqlalchemy, asyncpg (PostgreSQL) or aiosqlite (SQLite)
All imports are optional — the rest of JEBAT works without a database.
"""

import logging

logger = logging.getLogger(__name__)

DatabaseManager = None
RepositoryManager = None
get_db_models = None

try:
    from .connection_manager import DatabaseManager
    from .models import Base, get_async_session_factory, get_db_models, get_engine
    from .repositories import RepositoryManager

    async def init_database():
        """Create all tables from ORM models. Call once at startup if DB is enabled."""
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")

    async def check_database_health() -> dict:
        """Quick health check — can we connect and query?"""
        try:
            from sqlalchemy import text
            engine = get_engine()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"healthy": True, "error": None}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

except ImportError as e:
    logger.debug(f"Database layer unavailable: {e}")

    async def init_database():
        raise RuntimeError("Database dependencies not installed (pip install sqlalchemy asyncpg)")

    async def check_database_health() -> dict:
        return {"healthy": False, "error": "Database dependencies not installed"}

__all__ = [
    "DatabaseManager",
    "RepositoryManager",
    "get_db_models",
    "init_database",
    "check_database_health",
]
