"""Fix submission model constraints

Revision ID: fix_submission_001
Revises:
Create Date: 2024-01-20 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fix_submission_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema to fix submission model constraints."""

    # ------------------------------------------------------------
    # 0) Garantir FK review/assignment -> submission com CASCADE
    #    (usamos SQL bruto p/ IF EXISTS e depois recriamos via Alembic)
    # ------------------------------------------------------------
    op.execute("ALTER TABLE review DROP CONSTRAINT IF EXISTS review_submission_id_fkey;")
    op.create_foreign_key(
        "review_submission_id_fkey",
        source_table="review",
        referent_table="submission",
        local_cols=["submission_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    op.execute("ALTER TABLE assignment DROP CONSTRAINT IF EXISTS assignment_submission_id_fkey;")
    op.create_foreign_key(
        "assignment_submission_id_fkey",
        source_table="assignment",
        referent_table="submission",
        local_cols=["submission_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    # ------------------------------------------------------------
    # 1) Remover filhos que apontam para submissions inválidos
    # ------------------------------------------------------------
    op.execute(
        """
        DELETE FROM review r
        USING submission s
        WHERE r.submission_id = s.id
          AND (s.author_id IS NULL OR s.evento_id IS NULL);
        """
    )

    op.execute(
        """
        DELETE FROM assignment a
        USING submission s
        WHERE a.submission_id = s.id
          AND (s.author_id IS NULL OR s.evento_id IS NULL);
        """
    )

    # ------------------------------------------------------------
    # 2) Remover submissions inválidos (sem autor ou evento)
    # ------------------------------------------------------------
    op.execute(
        """
        DELETE FROM submission
        WHERE author_id IS NULL OR evento_id IS NULL;
        """
    )

    # ------------------------------------------------------------
    # 3) Tornar campos obrigatórios
    # ------------------------------------------------------------
    op.alter_column(
        "submission",
        "author_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "submission",
        "evento_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # ------------------------------------------------------------
    # 4) Constraint de identificação de revisor em review (idempotente)
    # ------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'check_reviewer_identification'
            ) THEN
                ALTER TABLE review 
                ADD CONSTRAINT check_reviewer_identification 
                CHECK (reviewer_id IS NOT NULL OR reviewer_name IS NOT NULL);
            END IF;
        END$$;
        """
    )

    # ------------------------------------------------------------
    # 5) Índices (idempotentes)
    # ------------------------------------------------------------
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_submission_author_evento ON submission(author_id, evento_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_submission_status ON submission(status);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_review_submission ON review(submission_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_assignment_reviewer ON assignment(reviewer_id);"
    )

    # ------------------------------------------------------------
    # 6) UNIQUE (author_id, evento_id) na submission (idempotente)
    # ------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_submission_author_evento'
            ) THEN
                ALTER TABLE submission
                ADD CONSTRAINT uq_submission_author_evento
                UNIQUE (author_id, evento_id);
            END IF;
        END$$;
        """
    )


def downgrade():
    """Downgrade database schema."""

    # Reverter UNIQUE
    op.execute("ALTER TABLE submission DROP CONSTRAINT IF EXISTS uq_submission_author_evento;")

    # Remover índices
    op.execute("DROP INDEX IF EXISTS idx_assignment_reviewer;")
    op.execute("DROP INDEX IF EXISTS idx_review_submission;")
    op.execute("DROP INDEX IF EXISTS idx_submission_status;")
    op.execute("DROP INDEX IF EXISTS idx_submission_author_evento;")

    # Remover check
    op.execute("ALTER TABLE review DROP CONSTRAINT IF EXISTS check_reviewer_identification;")

    # Reverter NOT NULL
    op.alter_column("submission", "evento_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("submission", "author_id", existing_type=sa.Integer(), nullable=True)

    # Restaurar FKs sem CASCADE (estado anterior genérico)
    op.execute("ALTER TABLE review DROP CONSTRAINT IF EXISTS review_submission_id_fkey;")
    op.create_foreign_key(
        "review_submission_id_fkey",
        source_table="review",
        referent_table="submission",
        local_cols=["submission_id"],
        remote_cols=["id"],
        ondelete=None,
    )
    op.execute("ALTER TABLE assignment DROP CONSTRAINT IF EXISTS assignment_submission_id_fkey;")
    op.create_foreign_key(
        "assignment_submission_id_fkey",
        source_table="assignment",
        referent_table="submission",
        local_cols=["submission_id"],
        remote_cols=["id"],
        ondelete=None,
    )
