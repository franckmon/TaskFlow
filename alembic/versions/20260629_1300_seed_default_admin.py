"""seed default admin user

Revision ID: 20260629_1300
Revises: 20260629_1200
Create Date: 2026-06-29 13:00:00.000000

"""
from alembic import op
from sqlalchemy.orm import Session

from app.core.bootstrap import ensure_default_admin


revision = "20260629_1300"
down_revision = "20260629_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        ensure_default_admin(session)
    finally:
        session.close()


def downgrade() -> None:
    pass
