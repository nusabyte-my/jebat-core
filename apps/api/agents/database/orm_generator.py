"""
JEBAT ORM Generator

Auto-generate ORM models:
- SQLAlchemy models
- Django ORM
- Prisma schema
- Type-safe models
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ORMGenerator:
    """
    ORM Model Generator for JEBAT.

    Generates type-safe ORM models from database schema.
    """

    SUPPORTED_ORMS = [
        "sqlalchemy",
        "django",
        "prisma",
        "tortoise",
        "pony",
    ]

    def __init__(self, orm_type: str = "sqlalchemy"):
        """
        Initialize ORM Generator.

        Args:
            orm_type: ORM framework to use
        """
        self.orm_type = orm_type

        logger.info(f"ORMGenerator initialized for {orm_type}")

    async def generate_models(
        self,
        schema: Dict[str, Any],
        output_path: str = "./models",
    ) -> Dict[str, Any]:
        """
        Generate ORM models from schema.

        Args:
            schema: Database schema
            output_path: Output directory

        Returns:
            Generation result
        """
        logger.info(f"Generating {self.orm_type} models...")

        if self.orm_type == "sqlalchemy":
            models = self._generate_sqlalchemy_models(schema)
        elif self.orm_type == "django":
            models = self._generate_django_models(schema)
        elif self.orm_type == "prisma":
            models = self._generate_prisma_schema(schema)
        else:
            return {"error": f"Unsupported ORM: {self.orm_type}"}

        return {
            "status": "success",
            "orm": self.orm_type,
            "models": models,
            "output_path": output_path,
            "files_generated": len(models),
        }

    def _generate_sqlalchemy_models(
        self,
        schema: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Generate SQLAlchemy models."""
        models = []

        for table in schema.get("tables", []):
            model_code = self._create_sqlalchemy_model(table)
            models.append(
                {
                    "name": table["name"],
                    "code": model_code,
                    "filename": f"{table['name']}.py",
                }
            )

        return models

    def _create_sqlalchemy_model(self, table: Dict[str, Any]) -> str:
        """Create single SQLAlchemy model."""
        class_name = self._to_pascal_case(table["name"])

        columns = []
        for col in table.get("columns", []):
            col_type = self._map_sqlalchemy_type(col.get("type", "VARCHAR"))
            col_def = f"    {col['name']} = Column({col_type}"

            if col.get("primary_key"):
                col_def += ", primary_key=True"
            if col.get("nullable") == False:
                col_def += ", nullable=False"

            col_def += ")"
            columns.append(col_def)

        return f"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class {class_name}(Base):
    __tablename__ = '{table["name"]}'

{chr(10).join(columns)}

    def __repr__(self):
        return f"<{class_name}(id={{self.id}})>"
"""

    def _generate_django_models(self, schema: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate Django ORM models."""
        models = []

        for table in schema.get("tables", []):
            model_code = self._create_django_model(table)
            models.append(
                {
                    "name": table["name"],
                    "code": model_code,
                    "filename": f"{table['name']}.py",
                }
            )

        return models

    def _create_django_model(self, table: Dict[str, Any]) -> str:
        """Create single Django model."""
        class_name = self._to_pascal_case(table["name"])

        fields = []
        for col in table.get("columns", []):
            field_type = self._map_django_field(col.get("type", "VARCHAR"))
            field_def = f"    {col['name']} = {field_type}"

            if col.get("primary_key"):
                field_def += "(primary_key=True)"
            else:
                field_def += "()"

            fields.append(field_def)

        return f"""
from django.db import models


class {class_name}(models.Model):
{chr(10).join(fields)}

    class Meta:
        db_table = '{table["name"]}'

    def __str__(self):
        return f"{class_name}({{self.id}})"
"""

    def _generate_prisma_schema(self, schema: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate Prisma schema."""
        models = []

        schema_content = '// Prisma Schema\n\ngenerator client {\n  provider = "prisma-client-js"\n}\n\ndatasource db {\n  provider = "postgresql"\n  url      = env("DATABASE_URL")\n}\n\n'

        for table in schema.get("tables", []):
            schema_content += self._create_prisma_model(table)

        models.append(
            {
                "name": "schema",
                "code": schema_content,
                "filename": "schema.prisma",
            }
        )

        return models

    def _create_prisma_model(self, table: Dict[str, Any]) -> str:
        """Create single Prisma model."""
        model_name = self._to_pascal_case(table["name"])

        fields = []
        for col in table.get("columns", []):
            field_type = self._map_prisma_type(col.get("type", "String"))
            field_def = f"  {col['name']} {field_type}"

            if col.get("primary_key"):
                field_def += " @id"

            fields.append(field_def)

        return f"""
model {model_name} {{
{chr(10).join(fields)}
}}
"""

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase."""
        return "".join(word.capitalize() for word in name.split("_"))

    def _map_sqlalchemy_type(self, sql_type: str) -> str:
        """Map SQL type to SQLAlchemy type."""
        type_mapping = {
            "INTEGER": "Integer",
            "INT": "Integer",
            "BIGINT": "BigInteger",
            "VARCHAR": "String",
            "TEXT": "Text",
            "BOOLEAN": "Boolean",
            "TIMESTAMP": "DateTime",
            "DATETIME": "DateTime",
            "DATE": "Date",
            "FLOAT": "Float",
            "DECIMAL": "Numeric",
        }
        return type_mapping.get(sql_type.upper(), "String")

    def _map_django_field(self, sql_type: str) -> str:
        """Map SQL type to Django field."""
        type_mapping = {
            "INTEGER": "IntegerField",
            "BIGINT": "BigIntegerField",
            "VARCHAR": "CharField",
            "TEXT": "TextField",
            "BOOLEAN": "BooleanField",
            "TIMESTAMP": "DateTimeField",
            "DATE": "DateField",
            "FLOAT": "FloatField",
            "DECIMAL": "DecimalField",
        }
        return type_mapping.get(sql_type.upper(), "CharField")

    def _map_prisma_type(self, sql_type: str) -> str:
        """Map SQL type to Prisma type."""
        type_mapping = {
            "INTEGER": "Int",
            "BIGINT": "BigInt",
            "VARCHAR": "String",
            "TEXT": "String",
            "BOOLEAN": "Boolean",
            "TIMESTAMP": "DateTime",
            "DATE": "DateTime",
            "FLOAT": "Float",
            "DECIMAL": "Decimal",
        }
        return type_mapping.get(sql_type.upper(), "String")
