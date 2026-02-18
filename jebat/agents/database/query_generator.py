"""
JEBAT Query Generator

Natural language to SQL/NoSQL:
- SQL query generation
- NoSQL query generation
- Query validation
- Query optimization suggestions
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QueryGenerator:
    """
    Intelligent Query Generator for JEBAT.

    Converts natural language to database queries.
    """

    def __init__(self, db_type: str = "postgresql"):
        """
        Initialize Query Generator.

        Args:
            db_type: Database type
        """
        self.db_type = db_type

        logger.info(f"QueryGenerator initialized for {db_type}")

    async def generate_sql(
        self,
        description: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate SQL from natural language.

        Args:
            description: Natural language description
            schema: Database schema info

        Returns:
            Generated SQL query
        """
        logger.info(f"Generating SQL for: {description[:50]}...")

        # Simulate SQL generation
        query = self._generate_query_from_description(description, schema)

        return {
            "status": "success",
            "query": query,
            "db_type": self.db_type,
            "description": description,
            "tables_used": self._extract_tables(query),
            "query_type": self._detect_query_type(query),
        }

    def _generate_query_from_description(
        self,
        description: str,
        schema: Optional[Dict[str, Any]],
    ) -> str:
        """Generate query based on description."""
        desc_lower = description.lower()

        # Simple pattern matching (in production, use NLP/ML)
        if "count" in desc_lower and "users" in desc_lower:
            return "SELECT COUNT(*) FROM users;"

        if "get" in desc_lower and "users" in desc_lower:
            return "SELECT * FROM users ORDER BY created_at DESC LIMIT 10;"

        if "join" in desc_lower or "posts" in desc_lower:
            return """SELECT u.*, p.title, p.content
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE u.active = true
ORDER BY u.created_at DESC;"""

        # Default query
        return "SELECT * FROM table_name WHERE condition = true;"

    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query."""
        # Simple extraction (in production, use proper SQL parser)
        tables = []
        query_upper = query.upper()

        if "FROM" in query_upper:
            parts = query_upper.split("FROM")
            if len(parts) > 1:
                table_part = parts[1].split()[0] if parts[1].split() else ""
                if table_part:
                    tables.append(table_part.lower().strip(";"))

        if "JOIN" in query_upper:
            parts = query_upper.split("JOIN")
            for part in parts[1:]:
                table = part.split()[0] if part.split() else ""
                if table:
                    tables.append(table.lower().strip(";"))

        return list(set(tables))

    def _detect_query_type(self, query: str) -> str:
        """Detect query type (SELECT, INSERT, UPDATE, DELETE)."""
        query_upper = query.upper().strip()

        if query_upper.startswith("SELECT"):
            return "SELECT"
        elif query_upper.startswith("INSERT"):
            return "INSERT"
        elif query_upper.startswith("UPDATE"):
            return "UPDATE"
        elif query_upper.startswith("DELETE"):
            return "DELETE"
        elif query_upper.startswith("CREATE"):
            return "CREATE"
        elif query_upper.startswith("ALTER"):
            return "ALTER"
        else:
            return "UNKNOWN"

    async def generate_nosql(
        self,
        description: str,
        database: str = "mongodb",
    ) -> Dict[str, Any]:
        """
        Generate NoSQL query from natural language.

        Args:
            description: Natural language description
            database: NoSQL database type

        Returns:
            Generated NoSQL query
        """
        logger.info(f"Generating {database} query for: {description[:50]}...")

        if database == "mongodb":
            query = self._generate_mongodb_query(description)
        elif database == "redis":
            query = self._generate_redis_query(description)
        else:
            query = {"error": f"Unsupported NoSQL database: {database}"}

        return {
            "status": "success",
            "query": query,
            "database": database,
            "description": description,
        }

    def _generate_mongodb_query(self, description: str) -> Dict[str, Any]:
        """Generate MongoDB query."""
        desc_lower = description.lower()

        if "find" in desc_lower and "users" in desc_lower:
            return {
                "collection": "users",
                "operation": "find",
                "filter": {"active": True},
                "projection": {"_id": 0, "name": 1, "email": 1},
                "sort": {"created_at": -1},
                "limit": 10,
            }

        return {
            "collection": "documents",
            "operation": "find",
            "filter": {},
        }

    def _generate_redis_query(self, description: str) -> str:
        """Generate Redis command."""
        desc_lower = description.lower()

        if "get" in desc_lower:
            return "GET key_name"
        elif "set" in desc_lower:
            return "SET key_name value"
        elif "list" in desc_lower or "all" in desc_lower:
            return "KEYS *"

        return "GET key_name"

    async def validate_query(
        self,
        query: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate query syntax and semantics.

        Args:
            query: Query to validate
            schema: Database schema

        Returns:
            Validation result
        """
        # Simulate validation
        is_valid = True
        errors = []
        warnings = []

        # Check for common issues
        if "SELECT *" in query.upper():
            warnings.append("Consider specifying columns instead of SELECT *")

        if "WHERE" not in query.upper() and "SELECT" in query.upper():
            warnings.append("Query has no WHERE clause - may return all rows")

        if not query.strip().endswith(";"):
            warnings.append("Query missing semicolon")

        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "query_type": self._detect_query_type(query),
        }

    async def optimize_query(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Suggest query optimizations.

        Args:
            query: Query to optimize

        Returns:
            Optimization suggestions
        """
        suggestions = []

        query_upper = query.upper()

        if "SELECT *" in query_upper:
            suggestions.append(
                {
                    "type": "performance",
                    "suggestion": "Specify columns instead of SELECT *",
                    "impact": "medium",
                }
            )

        if "WHERE" not in query_upper:
            suggestions.append(
                {
                    "type": "performance",
                    "suggestion": "Add WHERE clause to limit results",
                    "impact": "high",
                }
            )

        if "LIKE '%" in query_upper:
            suggestions.append(
                {
                    "type": "performance",
                    "suggestion": "Leading wildcard prevents index usage",
                    "impact": "high",
                }
            )

        return {
            "original_query": query,
            "suggestions": suggestions,
            "optimized_query": query,  # Would apply optimizations
        }
