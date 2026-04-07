"""
Advanced SQL Skill
Comprehensive SQL skill for database management, query optimization, schema design,
data analysis, and advanced database operations.
"""

import asyncio
import json
import logging
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import psycopg2
import pymongo
import pymysql
import redis
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .base_skill import BaseSkill, SkillParameter, SkillResult, SkillType


class AdvancedSQLSkill(BaseSkill):
    """
    Advanced SQL skill for comprehensive database operations.

    Capabilities:
    - Multi-database support (PostgreSQL, MySQL, SQLite, MongoDB)
    - Query optimization and performance analysis
    - Schema design and migrations
    - Data modeling and relationships
    - Advanced queries (CTEs, window functions, stored procedures)
    - Database administration and maintenance
    - Data analysis and reporting
    - Backup and recovery operations
    """

    def __init__(
        self,
        skill_id: str = "advanced_sql_001",
        name: str = "Advanced SQL",
        description: str = "Comprehensive SQL and database management capabilities",
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            skill_id=skill_id,
            name=name,
            skill_type=SkillType.DATABASE,
            description=description,
            version=version,
            config=config or {},
        )

        # Default configuration
        default_config = {
            "supported_databases": {
                "postgresql": {
                    "driver": "psycopg2",
                    "port": 5432,
                    "features": [
                        "window_functions",
                        "cte",
                        "json",
                        "arrays",
                        "stored_procedures",
                    ],
                },
                "mysql": {
                    "driver": "pymysql",
                    "port": 3306,
                    "features": [
                        "window_functions",
                        "cte",
                        "json",
                        "stored_procedures",
                    ],
                },
                "sqlite": {
                    "driver": "sqlite3",
                    "features": ["window_functions", "cte", "json"],
                },
                "mongodb": {
                    "driver": "pymongo",
                    "port": 27017,
                    "features": ["aggregation", "indexing", "transactions"],
                },
            },
            "query_optimization": {
                "enable_explain": True,
                "analyze_performance": True,
                "suggest_indexes": True,
                "cache_plans": True,
            },
            "security": {
                "sanitize_queries": True,
                "log_queries": True,
                "restrict_dangerous_operations": True,
            },
            "performance": {
                "connection_pool_size": 10,
                "query_timeout": 300,
                "batch_size": 1000,
                "enable_caching": True,
            },
            "backup": {
                "auto_backup": False,
                "backup_directory": "./db_backups",
                "retention_days": 30,
            },
        }

        # Merge with provided config
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value

        # Initialize connections and state
        self.connections = {}
        self.query_cache = {}
        self.performance_metrics = {
            "queries_executed": 0,
            "avg_query_time": 0.0,
            "slow_queries": [],
            "errors": 0,
        }
        self.schema_cache = {}

        # Create backup directory
        os.makedirs(self.config["backup"]["backup_directory"], exist_ok=True)

    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        """Execute SQL operation"""
        operation = parameters.get("operation", "").lower()

        try:
            # Connection operations
            if operation == "connect":
                return await self._connect_database(parameters)
            elif operation == "disconnect":
                return await self._disconnect_database(parameters)
            elif operation == "test_connection":
                return await self._test_connection(parameters)

            # Query operations
            elif operation == "execute_query":
                return await self._execute_query(parameters)
            elif operation == "execute_batch":
                return await self._execute_batch_queries(parameters)
            elif operation == "analyze_query":
                return await self._analyze_query(parameters)
            elif operation == "optimize_query":
                return await self._optimize_query(parameters)

            # Schema operations
            elif operation == "create_table":
                return await self._create_table(parameters)
            elif operation == "alter_table":
                return await self._alter_table(parameters)
            elif operation == "drop_table":
                return await self._drop_table(parameters)
            elif operation == "create_index":
                return await self._create_index(parameters)
            elif operation == "analyze_schema":
                return await self._analyze_schema(parameters)

            # Data operations
            elif operation == "insert_data":
                return await self._insert_data(parameters)
            elif operation == "update_data":
                return await self._update_data(parameters)
            elif operation == "delete_data":
                return await self._delete_data(parameters)
            elif operation == "bulk_import":
                return await self._bulk_import(parameters)
            elif operation == "bulk_export":
                return await self._bulk_export(parameters)

            # Analysis operations
            elif operation == "analyze_performance":
                return await self._analyze_performance(parameters)
            elif operation == "generate_report":
                return await self._generate_report(parameters)
            elif operation == "data_profiling":
                return await self._profile_data(parameters)

            # Maintenance operations
            elif operation == "backup_database":
                return await self._backup_database(parameters)
            elif operation == "restore_database":
                return await self._restore_database(parameters)
            elif operation == "vacuum_analyze":
                return await self._vacuum_analyze(parameters)
            elif operation == "reindex":
                return await self._reindex_database(parameters)

            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            self.performance_metrics["errors"] += 1
            return SkillResult(
                success=False,
                error=f"SQL operation failed: {str(e)}",
                skill_used=self.name,
            )

    async def _connect_database(self, parameters: Dict[str, Any]) -> SkillResult:
        """Connect to a database"""
        db_type = parameters.get("database_type", "postgresql").lower()
        connection_params = parameters.get("connection_params", {})
        connection_name = parameters.get("connection_name", "default")

        try:
            if db_type == "postgresql":
                connection_string = self._build_postgres_connection_string(
                    connection_params
                )
                engine = create_engine(
                    connection_string,
                    pool_size=self.config["performance"]["connection_pool_size"],
                )

            elif db_type == "mysql":
                connection_string = self._build_mysql_connection_string(
                    connection_params
                )
                engine = create_engine(
                    connection_string,
                    pool_size=self.config["performance"]["connection_pool_size"],
                )

            elif db_type == "sqlite":
                db_path = connection_params.get("database", ":memory:")
                connection_string = f"sqlite:///{db_path}"
                engine = create_engine(connection_string)

            elif db_type == "mongodb":
                client = pymongo.MongoClient(
                    host=connection_params.get("host", "localhost"),
                    port=connection_params.get("port", 27017),
                    username=connection_params.get("username"),
                    password=connection_params.get("password"),
                )
                database = client[connection_params.get("database")]
                self.connections[connection_name] = {
                    "client": client,
                    "database": database,
                    "type": "mongodb",
                }

                return SkillResult(
                    success=True,
                    data={
                        "connection_name": connection_name,
                        "database_type": db_type,
                        "status": "connected",
                        "collections": database.list_collection_names()
                        if hasattr(database, "list_collection_names")
                        else [],
                    },
                    metadata={"operation": "connect", "database_type": db_type},
                )

            else:
                raise ValueError(f"Unsupported database type: {db_type}")

            # Test connection for SQL databases
            if db_type != "mongodb":
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                Session = sessionmaker(bind=engine)
                self.connections[connection_name] = {
                    "engine": engine,
                    "session": Session,
                    "type": db_type,
                }

                # Get database information
                db_info = await self._get_database_info(connection_name)

            return SkillResult(
                success=True,
                data={
                    "connection_name": connection_name,
                    "database_type": db_type,
                    "status": "connected",
                    "database_info": db_info if db_type != "mongodb" else {},
                },
                metadata={"operation": "connect", "database_type": db_type},
            )

        except Exception as e:
            raise Exception(f"Failed to connect to {db_type} database: {str(e)}")

    async def _execute_query(self, parameters: Dict[str, Any]) -> SkillResult:
        """Execute SQL query"""
        query = parameters.get("query")
        connection_name = parameters.get("connection_name", "default")
        query_params = parameters.get("parameters", {})
        fetch_results = parameters.get("fetch_results", True)
        explain_plan = parameters.get("explain", False)

        if not query:
            raise ValueError("query is required")

        if connection_name not in self.connections:
            raise ValueError(f"Connection '{connection_name}' not found")

        try:
            start_time = time.time()
            connection = self.connections[connection_name]

            if connection["type"] == "mongodb":
                # Handle MongoDB operations differently
                return await self._execute_mongodb_operation(
                    query, connection, parameters
                )

            # SQL databases
            engine = connection["engine"]
            results = []
            row_count = 0
            execution_plan = None

            with engine.connect() as conn:
                # Get execution plan if requested
                if explain_plan and connection["type"] in ["postgresql", "mysql"]:
                    explain_query = (
                        f"EXPLAIN ANALYZE {query}"
                        if connection["type"] == "postgresql"
                        else f"EXPLAIN {query}"
                    )
                    plan_result = conn.execute(text(explain_query), query_params)
                    execution_plan = [dict(row) for row in plan_result]

                # Execute main query
                result = conn.execute(text(query), query_params)

                if fetch_results:
                    if result.returns_rows:
                        results = [dict(row) for row in result]
                        row_count = len(results)
                    else:
                        row_count = result.rowcount

            execution_time = time.time() - start_time

            # Update performance metrics
            self.performance_metrics["queries_executed"] += 1
            self.performance_metrics["avg_query_time"] = (
                self.performance_metrics["avg_query_time"]
                * (self.performance_metrics["queries_executed"] - 1)
                + execution_time
            ) / self.performance_metrics["queries_executed"]

            # Track slow queries
            if execution_time > 5.0:  # 5 seconds threshold
                self.performance_metrics["slow_queries"].append(
                    {
                        "query": query[:200] + "..." if len(query) > 200 else query,
                        "execution_time": execution_time,
                        "timestamp": time.time(),
                    }
                )

            return SkillResult(
                success=True,
                data={
                    "results": results,
                    "row_count": row_count,
                    "execution_time": execution_time,
                    "execution_plan": execution_plan,
                    "query": query,
                },
                metadata={
                    "operation": "execute_query",
                    "database_type": connection["type"],
                    "rows_affected": row_count,
                },
            )

        except Exception as e:
            self.performance_metrics["errors"] += 1
            raise Exception(f"Failed to execute query: {str(e)}")

    async def _create_table(self, parameters: Dict[str, Any]) -> SkillResult:
        """Create database table"""
        table_name = parameters.get("table_name")
        columns = parameters.get("columns", [])
        constraints = parameters.get("constraints", [])
        indexes = parameters.get("indexes", [])
        connection_name = parameters.get("connection_name", "default")

        if not table_name or not columns:
            raise ValueError("table_name and columns are required")

        try:
            connection = self.connections[connection_name]
            db_type = connection["type"]

            # Generate CREATE TABLE SQL
            if db_type == "postgresql":
                create_sql = self._generate_postgresql_create_table(
                    table_name, columns, constraints
                )
            elif db_type == "mysql":
                create_sql = self._generate_mysql_create_table(
                    table_name, columns, constraints
                )
            elif db_type == "sqlite":
                create_sql = self._generate_sqlite_create_table(
                    table_name, columns, constraints
                )
            else:
                raise ValueError(f"Table creation not supported for {db_type}")

            # Execute CREATE TABLE
            execute_result = await self._execute_query(
                {
                    "query": create_sql,
                    "connection_name": connection_name,
                    "fetch_results": False,
                }
            )

            # Create indexes
            index_results = []
            for index in indexes:
                index_sql = self._generate_create_index_sql(table_name, index, db_type)
                index_result = await self._execute_query(
                    {
                        "query": index_sql,
                        "connection_name": connection_name,
                        "fetch_results": False,
                    }
                )
                index_results.append(
                    {
                        "index_name": index.get(
                            "name", f"idx_{table_name}_{index['columns'][0]}"
                        ),
                        "success": index_result.success,
                    }
                )

            return SkillResult(
                success=True,
                data={
                    "table_name": table_name,
                    "columns": columns,
                    "constraints": constraints,
                    "create_sql": create_sql,
                    "indexes_created": index_results,
                },
                metadata={
                    "operation": "create_table",
                    "database_type": db_type,
                    "columns_count": len(columns),
                },
            )

        except Exception as e:
            raise Exception(f"Failed to create table: {str(e)}")

    async def _analyze_query(self, parameters: Dict[str, Any]) -> SkillResult:
        """Analyze query performance and suggest optimizations"""
        query = parameters.get("query")
        connection_name = parameters.get("connection_name", "default")

        if not query:
            raise ValueError("query is required")

        try:
            connection = self.connections[connection_name]
            db_type = connection["type"]

            analysis = {
                "query": query,
                "analysis_timestamp": time.time(),
                "database_type": db_type,
                "issues": [],
                "suggestions": [],
                "complexity_score": 0,
                "estimated_cost": 0,
            }

            # Basic query analysis
            query_lower = query.lower().strip()

            # Check for common performance issues
            if "select *" in query_lower:
                analysis["issues"].append("Using SELECT * - specify columns explicitly")
                analysis["suggestions"].append(
                    "List only required columns in SELECT clause"
                )

            if "where" not in query_lower and any(
                keyword in query_lower for keyword in ["update", "delete"]
            ):
                analysis["issues"].append("UPDATE/DELETE without WHERE clause")
                analysis["suggestions"].append(
                    "Always use WHERE clause with UPDATE/DELETE"
                )

            if query_lower.count("join") > 3:
                analysis["issues"].append(
                    "Multiple JOINs detected - may impact performance"
                )
                analysis["suggestions"].append(
                    "Consider denormalization or query restructuring"
                )

            if "order by" in query_lower and "limit" not in query_lower:
                analysis["issues"].append(
                    "ORDER BY without LIMIT - may be inefficient for large datasets"
                )
                analysis["suggestions"].append("Add LIMIT clause to ORDER BY queries")

            # Complexity scoring
            complexity_factors = {
                "select": 1,
                "join": 2,
                "subquery": 3,
                "union": 2,
                "group by": 2,
                "order by": 1,
                "having": 2,
                "case": 1,
            }

            for keyword, weight in complexity_factors.items():
                count = query_lower.count(keyword)
                analysis["complexity_score"] += count * weight

            # Get execution plan if supported
            execution_plan = None
            if db_type in ["postgresql", "mysql"]:
                try:
                    plan_result = await self._execute_query(
                        {
                            "query": query,
                            "connection_name": connection_name,
                            "explain": True,
                            "fetch_results": False,
                        }
                    )
                    execution_plan = plan_result.data.get("execution_plan")

                    # Analyze execution plan
                    if execution_plan:
                        analysis.update(
                            self._analyze_execution_plan(execution_plan, db_type)
                        )

                except Exception as e:
                    analysis["issues"].append(f"Could not get execution plan: {str(e)}")

            # Generate optimization suggestions
            analysis["suggestions"].extend(
                self._generate_optimization_suggestions(query, db_type)
            )

            return SkillResult(
                success=True,
                data=analysis,
                metadata={
                    "operation": "analyze_query",
                    "database_type": db_type,
                    "complexity_score": analysis["complexity_score"],
                },
            )

        except Exception as e:
            raise Exception(f"Failed to analyze query: {str(e)}")

    async def _profile_data(self, parameters: Dict[str, Any]) -> SkillResult:
        """Profile data quality and characteristics"""
        table_name = parameters.get("table_name")
        columns = parameters.get("columns", [])  # Empty means all columns
        connection_name = parameters.get("connection_name", "default")
        sample_size = parameters.get("sample_size", 10000)

        if not table_name:
            raise ValueError("table_name is required")

        try:
            connection = self.connections[connection_name]

            # Get table schema if columns not specified
            if not columns:
                schema_query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                """

                schema_result = await self._execute_query(
                    {"query": schema_query, "connection_name": connection_name}
                )

                columns = [row["column_name"] for row in schema_result.data["results"]]

            profile_results = {
                "table_name": table_name,
                "profile_timestamp": time.time(),
                "total_rows": 0,
                "columns_analyzed": len(columns),
                "column_profiles": {},
                "data_quality": {
                    "completeness": 0.0,
                    "uniqueness": 0.0,
                    "consistency": 0.0,
                },
            }

            # Get total row count
            count_result = await self._execute_query(
                {
                    "query": f"SELECT COUNT(*) as total_rows FROM {table_name}",
                    "connection_name": connection_name,
                }
            )
            profile_results["total_rows"] = count_result.data["results"][0][
                "total_rows"
            ]

            # Profile each column
            for column in columns:
                column_profile = await self._profile_column(
                    table_name, column, connection_name, sample_size
                )
                profile_results["column_profiles"][column] = column_profile

            # Calculate overall data quality metrics
            total_cells = profile_results["total_rows"] * len(columns)
            total_null_cells = sum(
                prof.get("null_count", 0)
                for prof in profile_results["column_profiles"].values()
            )
            profile_results["data_quality"]["completeness"] = (
                (total_cells - total_null_cells) / total_cells * 100
                if total_cells > 0
                else 100
            )

            return SkillResult(
                success=True,
                data=profile_results,
                metadata={
                    "operation": "data_profiling",
                    "table_name": table_name,
                    "columns_analyzed": len(columns),
                },
            )

        except Exception as e:
            raise Exception(f"Failed to profile data: {str(e)}")

    # Helper methods
    def _build_postgres_connection_string(self, params: Dict[str, Any]) -> str:
        """Build PostgreSQL connection string"""
        host = params.get("host", "localhost")
        port = params.get("port", 5432)
        database = params.get("database", "postgres")
        username = params.get("username", "postgres")
        password = params.get("password", "")

        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    def _build_mysql_connection_string(self, params: Dict[str, Any]) -> str:
        """Build MySQL connection string"""
        host = params.get("host", "localhost")
        port = params.get("port", 3306)
        database = params.get("database", "mysql")
        username = params.get("username", "root")
        password = params.get("password", "")

        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"

    def _generate_postgresql_create_table(
        self, table_name: str, columns: List[Dict], constraints: List[str]
    ) -> str:
        """Generate PostgreSQL CREATE TABLE statement"""
        column_definitions = []

        for column in columns:
            col_def = f"{column['name']} {column['type']}"

            if not column.get("nullable", True):
                col_def += " NOT NULL"

            if column.get("primary_key", False):
                col_def += " PRIMARY KEY"

            if column.get("unique", False):
                col_def += " UNIQUE"

            if "default" in column:
                col_def += f" DEFAULT {column['default']}"

            column_definitions.append(col_def)

        create_sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(
            column_definitions
        )

        if constraints:
            create_sql += ",\n  " + ",\n  ".join(constraints)

        create_sql += "\n);"

        return create_sql

    def _generate_mysql_create_table(
        self, table_name: str, columns: List[Dict], constraints: List[str]
    ) -> str:
        """Generate MySQL CREATE TABLE statement"""
        # Similar to PostgreSQL but with MySQL-specific syntax
        return self._generate_postgresql_create_table(table_name, columns, constraints)

    def _generate_sqlite_create_table(
        self, table_name: str, columns: List[Dict], constraints: List[str]
    ) -> str:
        """Generate SQLite CREATE TABLE statement"""
        # Similar to PostgreSQL but with SQLite-specific syntax
        return self._generate_postgresql_create_table(table_name, columns, constraints)

    def _generate_create_index_sql(
        self, table_name: str, index_def: Dict, db_type: str
    ) -> str:
        """Generate CREATE INDEX statement"""
        index_name = index_def.get(
            "name", f"idx_{table_name}_{index_def['columns'][0]}"
        )
        columns = index_def["columns"]
        unique = "UNIQUE " if index_def.get("unique", False) else ""

        columns_str = ", ".join(columns)

        return f"CREATE {unique}INDEX {index_name} ON {table_name} ({columns_str});"

    async def _get_database_info(self, connection_name: str) -> Dict[str, Any]:
        """Get database information"""
        connection = self.connections[connection_name]
        db_type = connection["type"]

        info = {
            "database_type": db_type,
            "version": "unknown",
            "tables": [],
            "schemas": [],
        }

        try:
            if db_type == "postgresql":
                version_result = await self._execute_query(
                    {"query": "SELECT version()", "connection_name": connection_name}
                )
                info["version"] = version_result.data["results"][0]["version"]

                tables_result = await self._execute_query(
                    {
                        "query": "SELECT tablename FROM pg_tables WHERE schemaname = 'public'",
                        "connection_name": connection_name,
                    }
                )
                info["tables"] = [
                    row["tablename"] for row in tables_result.data["results"]
                ]

            elif db_type == "mysql":
                version_result = await self._execute_query(
                    {
                        "query": "SELECT VERSION() as version",
                        "connection_name": connection_name,
                    }
                )
                info["version"] = version_result.data["results"][0]["version"]

                tables_result = await self._execute_query(
                    {"query": "SHOW TABLES", "connection_name": connection_name}
                )
                info["tables"] = [
                    list(row.values())[0] for row in tables_result.data["results"]
                ]

            elif db_type == "sqlite":
                tables_result = await self._execute_query(
                    {
                        "query": "SELECT name FROM sqlite_master WHERE type='table'",
                        "connection_name": connection_name,
                    }
                )
                info["tables"] = [row["name"] for row in tables_result.data["results"]]

        except Exception as e:
            info["error"] = str(e)

        return info

    def _analyze_execution_plan(self, plan: List[Dict], db_type: str) -> Dict[str, Any]:
        """Analyze execution plan for optimization opportunities"""
        analysis = {
            "plan_issues": [],
            "cost_estimate": 0,
            "scan_types": [],
        }

        for step in plan:
            if db_type == "postgresql":
                # Analyze PostgreSQL execution plan
                if "Seq Scan" in str(step):
                    analysis["plan_issues"].append(
                        "Sequential scan detected - consider adding index"
                    )
                    analysis["scan_types"].append("sequential")

                if "Nested Loop" in str(step):
                    analysis["plan_issues"].append(
                        "Nested loop join - may be inefficient for large datasets"
                    )

                # Extract cost if available
                if "cost" in str(step).lower():
                    # This is a simplified extraction - real implementation would parse properly
                    pass

        return analysis

    def _generate_optimization_suggestions(self, query: str, db_type: str) -> List[str]:
        """Generate query optimization suggestions"""
        suggestions = []
        query_lower = query.lower()

        # Index suggestions
        if "where" in query_lower:
            suggestions.append(
                "Consider adding indexes on columns used in WHERE clauses"
            )

        if "join" in query_lower:
            suggestions.append("Ensure JOIN columns are indexed")

        if "group by" in query_lower:
            suggestions.append("Consider indexes on GROUP BY columns")

        if "order by" in query_lower:
            suggestions.append("Consider indexes on ORDER BY columns")

        # Query rewriting suggestions
        if "in (select" in query_lower:
            suggestions.append("Consider rewriting IN subquery as JOIN or EXISTS")

        if query_lower.count("or") > 2:
            suggestions.append(
                "Consider breaking complex OR conditions into UNION queries"
            )

        return suggestions

    async def _profile_column(
        self, table_name: str, column_name: str, connection_name: str, sample_size: int
    ) -> Dict[str, Any]:
        """Profile individual column"""
        queries = {
            "stats": f"""
                SELECT
                    COUNT(*) as total_count,
                    COUNT({column_name}) as non_null_count,
                    COUNT(*) - COUNT({column_name}) as null_count,
                    COUNT(DISTINCT {column_name}) as distinct_count
                FROM {table_name}
                LIMIT {sample_size}
            """,
            "sample_values": f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT 10",
        }

        profile = {
            "column_name": column_name,
            "total_count": 0,
            "null_count": 0,
            "distinct_count": 0,
            "sample_values": [],
        }

        try:
            # Get basic statistics
            stats_result = await self._execute_query(
                {"query": queries["stats"], "connection_name": connection_name}
            )

            if stats_result.data["results"]:
                stats = stats_result.data["results"][0]
                profile.update(
                    {
                        "total_count": stats["total_count"],
                        "null_count": stats["null_count"],
                        "distinct_count": stats["distinct_count"],
                    }
                )

            # Get sample values
            sample_result = await self._execute_query(
                {"query": queries["sample_values"], "connection_name": connection_name}
            )

            profile["sample_values"] = [
                row[column_name] for row in sample_result.data["results"]
            ]

            # Calculate metrics
            if profile["total_count"] > 0:
                profile["null_percentage"] = (
                    profile["null_count"] / profile["total_count"]
                ) * 100
                profile["uniqueness"] = (
                    profile["distinct_count"] / profile["total_count"]
                ) * 100

        except Exception as e:
            profile["error"] = str(e)

        return profile

    def get_parameters(self) -> List[SkillParameter]:
        """Get list of parameters this skill accepts"""
        return [
            SkillParameter(
                name="operation",
                param_type=str,
                required=True,
                description="Type of SQL operation to perform",
            ),
            SkillParameter(
                name="database_type",
                param_type=str,
                required=False,
                default="postgresql",
                description="Type of database (postgresql, mysql, sqlite, mongodb)",
            ),
            SkillParameter(
                name="connection_name",
                param_type=str,
                required=False,
                default="default",
                description="Name of the database connection",
            ),
            SkillParameter(
                name="connection_params",
                param_type=dict,
                required=False,
                default={},
                description="Database connection parameters",
            ),
            SkillParameter(
                name="query",
                param_type=str,
                required=False,
                description="SQL query to execute",
            ),
            SkillParameter(
                name="table_name",
                param_type=str,
                required=False,
                description="Name of the database table",
            ),
            SkillParameter(
                name="columns",
                param_type=list,
                required=False,
                default=[],
                description="Column definitions for table operations",
            ),
            SkillParameter(
                name="parameters",
                param_type=dict,
                required=False,
                default={},
                description="Query parameters for parameterized queries",
            ),
        ]
