"""Add ondelete to revisor_process formulario

Revision ID: a16bd5bf6b16
Revises: 25eb3573df18
Create Date: 2025-08-16 03:00:16.552968

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a16bd5bf6b16'
down_revision = '25eb3573df18'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "revisor_process" not in insp.get_table_names():
        return

    desired_ondelete = "SET NULL"
    existing_fk = None
    for fk in insp.get_foreign_keys("revisor_process"):
        if (
            fk.get("referred_table") == "formularios"
            and fk.get("constrained_columns") == ["formulario_id"]
        ):
            existing_fk = fk
            break

    if existing_fk and existing_fk.get("options", {}).get("ondelete") == desired_ondelete:
        return

    if existing_fk and existing_fk.get("name"):
        op.drop_constraint(
            existing_fk["name"],
            "revisor_process",
            type_="foreignkey",
        )
    else:
        for name in {
            "fk_revisor_process_formulario_id_formularios",
            op.f("fk_revisor_process_formulario_id_formularios"),
        }:
            if any(fk.get("name") == name for fk in insp.get_foreign_keys("revisor_process")):
                op.drop_constraint(name, "revisor_process", type_="foreignkey")

    op.create_foreign_key(
        op.f("fk_revisor_process_formulario_id_formularios"),
        "revisor_process",
        "formularios",
        ["formulario_id"],
        ["id"],
        ondelete=desired_ondelete,
    )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "revisor_process" not in insp.get_table_names():
        return

    fk_name = op.f("fk_revisor_process_formulario_id_formularios")
    if any(fk.get("name") == fk_name for fk in insp.get_foreign_keys("revisor_process")):
        op.drop_constraint(fk_name, "revisor_process", type_="foreignkey")

    op.create_foreign_key(
        "fk_revisor_process_formulario_id_formularios",
        "revisor_process",
        "formularios",
        ["formulario_id"],
        ["id"],
    )
