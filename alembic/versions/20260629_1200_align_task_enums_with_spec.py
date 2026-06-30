"""align task enums with spec

Revision ID: 20260629_1200
Revises: 40ac44e74642
Create Date: 2026-06-29 12:00:00.000000

"""
from alembic import op


revision = "20260629_1200"
down_revision = "40ac44e74642"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE tasks SET status = 'new' WHERE status = 'todo'")
    op.execute("UPDATE tasks SET priority = 'normal' WHERE priority = 'medium'")


def downgrade() -> None:
    op.execute("UPDATE tasks SET status = 'todo' WHERE status = 'new'")
    op.execute("UPDATE tasks SET priority = 'medium' WHERE priority = 'normal'")
