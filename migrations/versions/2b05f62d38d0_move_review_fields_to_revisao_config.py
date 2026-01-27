"""move review fields to revisao_config

Revision ID: 2b05f62d38d0
Revises: 64f77f3899ea
Create Date: 2024-08-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '2b05f62d38d0'
down_revision = '64f77f3899ea'
branch_labels = None
depends_on = None

def upgrade():
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if 'revisao_config' not in tables:
        evento_fk = (
            sa.ForeignKey('evento.id') if 'evento' in tables else None
        )
        evento_id_column = sa.Column(
            'evento_id',
            sa.Integer(),
            evento_fk,
            nullable=False,
            unique=True,
        )
        op.create_table(
            'revisao_config',
            sa.Column('id', sa.Integer(), primary_key=True),
            evento_id_column,
            sa.Column(
                'permitir_checkin_global',
                sa.Boolean(),
                nullable=True,
                server_default=sa.text('false'),
            ),
            sa.Column(
                'habilitar_feedback',
                sa.Boolean(),
                nullable=True,
                server_default=sa.text('false'),
            ),
            sa.Column(
                'habilitar_certificado_individual',
                sa.Boolean(),
                nullable=True,
                server_default=sa.text('false'),
            ),
            sa.Column(
                'habilitar_qrcode_evento_credenciamento',
                sa.Boolean(),
                nullable=True,
                server_default=sa.text('false'),
            ),
            sa.Column(
                'habilitar_submissao_trabalhos',
                sa.Boolean(),
                nullable=True,
                server_default=sa.text('false'),
            ),
            sa.Column(
                'mostrar_taxa',
                sa.Boolean(),
                nullable=True,
                server_default=sa.text('true'),
            ),
            sa.Column(
                'numero_revisores',
                sa.Integer(),
                nullable=True,
                server_default='2',
            ),
            sa.Column('prazo_revisao', sa.DateTime(), nullable=True),
            sa.Column(
                'modelo_blind',
                sa.String(length=20),
                nullable=True,
                server_default='single',
            ),
        )
    else:
        existing_columns = {
            column['name'] for column in inspector.get_columns('revisao_config')
        }
        if 'numero_revisores' not in existing_columns:
            op.add_column(
                'revisao_config',
                sa.Column(
                    'numero_revisores',
                    sa.Integer(),
                    nullable=True,
                    server_default='2',
                ),
            )
        if 'prazo_revisao' not in existing_columns:
            op.add_column(
                'revisao_config',
                sa.Column('prazo_revisao', sa.DateTime(), nullable=True),
            )
        if 'modelo_blind' not in existing_columns:
            op.add_column(
                'revisao_config',
                sa.Column(
                    'modelo_blind',
                    sa.String(length=20),
                    nullable=True,
                    server_default='single',
                ),
            )

    if 'reviewer_application' in tables:
        reviewer_columns = {
            column['name']
            for column in inspector.get_columns('reviewer_application')
        }
        with op.batch_alter_table('reviewer_application') as batch_op:
            if 'numero_revisores' in reviewer_columns:
                batch_op.drop_column('numero_revisores')
            if 'prazo_revisao' in reviewer_columns:
                batch_op.drop_column('prazo_revisao')
            if 'modelo_blind' in reviewer_columns:
                batch_op.drop_column('modelo_blind')


def downgrade():
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if 'revisao_config' in tables:
        existing_columns = {
            column['name'] for column in inspector.get_columns('revisao_config')
        }
        if 'modelo_blind' in existing_columns:
            op.drop_column('revisao_config', 'modelo_blind')
        if 'prazo_revisao' in existing_columns:
            op.drop_column('revisao_config', 'prazo_revisao')
        if 'numero_revisores' in existing_columns:
            op.drop_column('revisao_config', 'numero_revisores')

    if 'reviewer_application' in tables:
        reviewer_columns = {
            column['name']
            for column in inspector.get_columns('reviewer_application')
        }
        if 'numero_revisores' not in reviewer_columns:
            op.add_column(
                'reviewer_application',
                sa.Column('numero_revisores', sa.Integer(), nullable=True),
            )
        if 'prazo_revisao' not in reviewer_columns:
            op.add_column(
                'reviewer_application',
                sa.Column('prazo_revisao', sa.DateTime(), nullable=True),
            )
        if 'modelo_blind' not in reviewer_columns:
            op.add_column(
                'reviewer_application',
                sa.Column('modelo_blind', sa.String(length=20), nullable=True),
            )
