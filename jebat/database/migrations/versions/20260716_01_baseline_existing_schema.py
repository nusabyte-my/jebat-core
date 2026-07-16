"""Baseline stamp for schemas previously initialized with create_tables().

Revision ID: 20260716_01
Revises: None
Create Date: 2026-07-16
"""


revision = "20260716_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Establish Alembic versioning without modifying an existing schema."""


def downgrade() -> None:
    """Removing a stamp does not remove application tables."""
