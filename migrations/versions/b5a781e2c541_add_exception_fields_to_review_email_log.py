"""add exception details to review email log"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b5a781e2c541"
down_revision = "6d0c1bfa2e5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "review_email_log",
        sa.Column("error_type", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "review_email_log", sa.Column("error_message", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("review_email_log", "error_message")
    op.drop_column("review_email_log", "error_type")
