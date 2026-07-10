"""add tenant_id to memory_objects

Revision ID: a1b2c3d4e5f6
Revises: 98551d2206c1
Create Date: 2026-07-10 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "98551d2206c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tenant_id column
    op.add_column("memory_objects", sa.Column("tenant_id", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_memory_objects_tenant_id"), "memory_objects", ["tenant_id"], unique=False
    )


def downgrade() -> None:
    # Remove tenant_id column
    op.drop_index(op.f("ix_memory_objects_tenant_id"), table_name="memory_objects")
    op.drop_column("memory_objects", "tenant_id")
