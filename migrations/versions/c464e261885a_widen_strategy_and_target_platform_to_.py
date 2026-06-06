"""widen strategy and target_platform to varchar50

Revision ID: c464e261885a
Revises: d84ba0e08272
Create Date: 2026-06-06 20:19:06.879106
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c464e261885a"
down_revision = "d84ba0e08272"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "generated_contexts",
        "strategy",
        existing_type=sa.Enum(
            "full",
            "concise",
            "technical",
            "creative",
            name="context_strategy_enum",
        ),
        type_=sa.String(length=50),
        existing_nullable=False,
    )

    op.alter_column(
        "generated_contexts",
        "target_platform",
        existing_type=sa.Enum(
            "chatgpt",
            "claude",
            "gemini",
            "generic",
            name="target_platform_enum",
        ),
        type_=sa.String(length=50),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "generated_contexts",
        "target_platform",
        existing_type=sa.String(length=50),
        type_=sa.Enum(
            "chatgpt",
            "claude",
            "gemini",
            "generic",
            name="target_platform_enum",
        ),
        existing_nullable=False,
    )

    op.alter_column(
        "generated_contexts",
        "strategy",
        existing_type=sa.String(length=50),
        type_=sa.Enum(
            "full",
            "concise",
            "technical",
            "creative",
            name="context_strategy_enum",
        ),
        existing_nullable=False,
    )