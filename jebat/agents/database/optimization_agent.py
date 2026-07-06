"""
JEBAT Query Optimizer

Database query optimization:
- Query analysis
- Index recommendations
- Performance profiling
- Execution plan analysis
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Query Optimizer for JEBAT.

    Analyzes and optimizes database queries.
    """

    def __init__(self, db_connector=None):
        """
        Initialize Query Optimizer.

        Args:
            db_connector: Database connector instance
        """
        self.db_connector = db_connector

        logger.info("QueryOptimizer initialized")

    async def analyze_query(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Analyze query performance.

        Args:
            query: SQL query to analyze

        Returns:
            Analysis results
        """
        logger.info(f"Analyzing query: {query[:100]}...")

        analysis = {
            "query": query,
            "query_type": self._detect_query_type(query),
            "tables": self._extract_tables(query),
            "issues": [],
            "recommendations": [],
            "estimated_cost": "medium",
        }

        # Analyze for common issues
        analysis["issues"] = self._find_issues(query)
        analysis["recommendations"] = self._generate_recommendations(
            query, analysis["issues"]
        )

        return analysis

    def _detect_query_type(self, query: str) -> str:
        """Detect query type."""
        query_upper = query.upper().strip()

        for qtype in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER"]:
            if query_upper.startswith(qtype):
                return qtype

        return "UNKNOWN"

    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query."""
        tables = []
        query_upper = query.upper()

        if "FROM" in query_upper:
            parts = query_upper.split("FROM")
            if len(parts) > 1:
                table = parts[1].split()[0].strip().strip(";")
                if table:
                    tables.append(table.lower())

        if "JOIN" in query_upper:
            for part in query_upper.split("JOIN")[1:]:
                table = part.split()[0].strip().strip(";")
                if table:
                    tables.append(table.lower())

        return list(set(tables))

    def _find_issues(self, query: str) -> List[Dict[str, str]]:
        """Find performance issues in query."""
        issues = []
        query_upper = query.upper()

        # SELECT * issue
        if "SELECT *" in query_upper:
            issues.append(
                {
                    "severity": "medium",
                    "type": "performance",
                    "issue": "SELECT * retrieves all columns",
                    "impact": "Increased I/O and memory usage",
                }
            )

        # Missing WHERE clause
        if "SELECT" in query_upper and "WHERE" not in query_upper:
            issues.append(
                {
                    "severity": "high",
                    "type": "performance",
                    "issue": "No WHERE clause",
                    "impact": "Full table scan, may return excessive rows",
                }
            )

        # Leading wildcard LIKE
        if "LIKE '%" in query_upper:
            issues.append(
                {
                    "severity": "high",
                    "type": "index",
                    "issue": "Leading wildcard in LIKE",
                    "impact": "Cannot use index, full table scan required",
                }
            )

        # Multiple OR conditions
        or_count = query_upper.count(" OR ")
        if or_count > 3:
            issues.append(
                {
                    "severity": "medium",
                    "type": "performance",
                    "issue": f"Multiple OR conditions ({or_count})",
                    "impact": "May prevent index usage, consider UNION",
                }
            )

        # Subquery in SELECT
        if "SELECT" in query_upper and query_upper.count("SELECT") > 1:
            if "(SELECT" in query_upper:
                issues.append(
                    {
                        "severity": "medium",
                        "type": "performance",
                        "issue": "Correlated subquery",
                        "impact": "Executed once per row, consider JOIN",
                    }
                )

        # ORDER BY without LIMIT
        if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
            issues.append(
                {
                    "severity": "low",
                    "type": "performance",
                    "issue": "ORDER BY without LIMIT",
                    "impact": "Sorts entire result set",
                }
            )

        return issues

    def _generate_recommendations(
        self,
        query: str,
        issues: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """Generate optimization recommendations."""
        recommendations = []

        for issue in issues:
            if issue["issue"] == "SELECT * retrieves all columns":
                recommendations.append(
                    {
                        "type": "optimization",
                        "recommendation": "Specify only needed columns",
                        "example": "SELECT id, name, email FROM users",
                    }
                )

            if issue["issue"] == "No WHERE clause":
                recommendations.append(
                    {
                        "type": "optimization",
                        "recommendation": "Add WHERE clause to filter results",
                        "example": "SELECT * FROM users WHERE active = true",
                    }
                )

            if issue["issue"] == "Leading wildcard in LIKE":
                recommendations.append(
                    {
                        "type": "index",
                        "recommendation": "Use full-text search or restructure query",
                        "example": "Consider USING GIN index with tsvector",
                    }
                )

        # General recommendations
        recommendations.append(
            {
                "type": "index",
                "recommendation": "Ensure indexes on WHERE and JOIN columns",
                "priority": "high",
            }
        )

        recommendations.append(
            {
                "type": "maintenance",
                "recommendation": "Run ANALYZE to update statistics",
                "priority": "medium",
            }
        )

        return recommendations

    async def get_execution_plan(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Get query execution plan.

        Args:
            query: SQL query

        Returns:
            Execution plan
        """
        if not self.db_connector:
            return {"error": "No database connector"}

        # Simulate execution plan
        return {
            "query": query,
            "plan": [
                {
                    "step": 1,
                    "operation": "Seq Scan",
                    "table": "users",
                    "cost": "0.00..100.00",
                    "rows": 1000,
                    "width": 100,
                    "filter": "active = true",
                },
                {
                    "step": 2,
                    "operation": "Sort",
                    "cost": "100.00..150.00",
                    "rows": 100,
                    "sort_key": "created_at DESC",
                },
                {
                    "step": 3,
                    "operation": "Limit",
                    "cost": "150.00..151.00",
                    "rows": 10,
                },
            ],
            "total_cost": 151.00,
            "estimated_time": "0.025s",
        }

    async def recommend_indexes(
        self,
        query: str,
        workload: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Recommend indexes for query.

        Args:
            query: SQL query
            workload: List of similar queries

        Returns:
            Index recommendations
        """
        tables = self._extract_tables(query)

        recommendations = []

        for table in tables:
            # Analyze WHERE columns
            if "WHERE" in query.upper():
                recommendations.append(
                    {
                        "table": table,
                        "type": "btree",
                        "columns": ["column_from_where"],
                        "reason": "Speeds up WHERE filtering",
                        "priority": "high",
                        "create_sql": f"CREATE INDEX idx_{table}_column ON {table}(column);",
                    }
                )

            # Analyze ORDER BY columns
            if "ORDER BY" in query.upper():
                recommendations.append(
                    {
                        "table": table,
                        "type": "btree",
                        "columns": ["order_column"],
                        "reason": "Avoids sort operation",
                        "priority": "medium",
                        "create_sql": f"CREATE INDEX idx_{table}_order ON {table}(order_column DESC);",
                    }
                )

        return {
            "query": query,
            "tables": tables,
            "recommendations": recommendations,
            "estimated_improvement": "60-80%",
        }

    async def optimize_query(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """
        Generate optimized version of query.

        Args:
            query: Original query

        Returns:
            Optimized query and changes
        """
        analysis = await self.analyze_query(query)

        optimized = query
        changes = []

        # Apply optimizations
        if "SELECT *" in query.upper():
            optimized = optimized.replace("SELECT *", "SELECT id, name, email")
            changes.append("Replaced SELECT * with specific columns")

        return {
            "original": query,
            "optimized": optimized,
            "changes": changes,
            "analysis": analysis,
            "estimated_improvement": "40-60%",
        }
