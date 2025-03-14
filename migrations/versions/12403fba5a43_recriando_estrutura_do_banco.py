"""Recriando estrutura do banco

Revision ID: 12403fba5a43
Revises: af2f8513fa83
Create Date: 2025-03-12 22:31:22.123249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12403fba5a43'
down_revision = 'af2f8513fa83'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('evento', schema=None) as batch_op:
        batch_op.alter_column('link_mapa',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.Text(),
               existing_nullable=True)

    with op.batch_alter_table('inscricao', schema=None) as batch_op:
        batch_op.add_column(sa.Column('evento_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'evento', ['evento_id'], ['id'])

    with op.batch_alter_table('inscricao_tipo', schema=None) as batch_op:
        batch_op.alter_column('nome',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('preco',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               nullable=True)

    with op.batch_alter_table('link_cadastro', schema=None) as batch_op:
        batch_op.add_column(sa.Column('evento_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('slug_customizado', sa.String(length=50), nullable=True))
        batch_op.create_unique_constraint(None, ['slug_customizado'])
        batch_op.create_foreign_key(None, 'evento', ['evento_id'], ['id'])

    with op.batch_alter_table('oficina', schema=None) as batch_op:
        batch_op.add_column(sa.Column('evento_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'evento', ['evento_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('oficina', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('evento_id')

    with op.batch_alter_table('link_cadastro', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('slug_customizado')
        batch_op.drop_column('evento_id')

    with op.batch_alter_table('inscricao_tipo', schema=None) as batch_op:
        batch_op.alter_column('preco',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               nullable=False)
        batch_op.alter_column('nome',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)

    with op.batch_alter_table('inscricao', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('evento_id')

    with op.batch_alter_table('evento', schema=None) as batch_op:
        batch_op.alter_column('link_mapa',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)

    # ### end Alembic commands ###
