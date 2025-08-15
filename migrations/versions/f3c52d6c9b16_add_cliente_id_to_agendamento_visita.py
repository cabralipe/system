"""add cliente_id to agendamento_visita

Revision ID: f3c52d6c9b16
Revises: 15b6b890ce1d
Create Date: 2025-02-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "f3c52d6c9b16"
down_revision = "15b6b890ce1d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agendamento_visita") as batch_op:
        batch_op.add_column(sa.Column("cliente_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_agendamento_visita_cliente_id",
            "cliente",
            ["cliente_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("agendamento_visita") as batch_op:
        batch_op.drop_constraint(
            "fk_agendamento_visita_cliente_id",
            type_="foreignkey",
        )
        batch_op.drop_column("cliente_id")
