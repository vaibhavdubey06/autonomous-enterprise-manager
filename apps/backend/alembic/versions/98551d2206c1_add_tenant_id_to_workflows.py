"""add tenant_id to workflows

Revision ID: 98551d2206c1
Revises: 8b76718ce3b8
Create Date: 2026-06-29 15:00:18.416149

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "98551d2206c1"
down_revision: Union[str, Sequence[str], None] = "8b76718ce3b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("workflows", sa.Column("tenant_id", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_workflows_tenant_id"), "workflows", ["tenant_id"], unique=False
    )
    op.add_column("workflow_tasks", sa.Column("tenant_id", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_workflow_tasks_tenant_id"),
        "workflow_tasks",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_workflow_tasks_tenant_id"), table_name="workflow_tasks")
    op.drop_column("workflow_tasks", "tenant_id")
    op.drop_index(op.f("ix_workflows_tenant_id"), table_name="workflows")
    op.drop_column("workflows", "tenant_id")
