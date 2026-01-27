"""add period columns to formulario"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "a4e781302f2b"
down_revision = "15b6b890ce1d"
branch_labels = None
depends_on = None

def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if 'formularios' not in inspector.get_table_names():
        return

    existing_columns = {
        column['name'] for column in inspector.get_columns('formularios')
    }
    with op.batch_alter_table('formularios') as batch_op:
        if 'data_inicio' not in existing_columns:
            batch_op.add_column(sa.Column('data_inicio', sa.DateTime(), nullable=True))
        if 'data_fim' not in existing_columns:
            batch_op.add_column(sa.Column('data_fim', sa.DateTime(), nullable=True))

def downgrade() -> None:
    inspector = inspect(op.get_bind())
    if 'formularios' not in inspector.get_table_names():
        return

    existing_columns = {
        column['name'] for column in inspector.get_columns('formularios')
    }
    with op.batch_alter_table('formularios') as batch_op:
        if 'data_fim' in existing_columns:
            batch_op.drop_column('data_fim')
        if 'data_inicio' in existing_columns:
            batch_op.drop_column('data_inicio')
