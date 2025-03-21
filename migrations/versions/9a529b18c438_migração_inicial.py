"""Migração inicial

Revision ID: 9a529b18c438
Revises: 
Create Date: 2025-03-22 07:38:24.374173

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a529b18c438'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.add_column(sa.Column('evento_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'evento', ['evento_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('evento_id')

    # ### end Alembic commands ###
