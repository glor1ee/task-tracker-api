"""drop global unique constraint on projects.name

Revision ID: 8c2187d90e60
Revises: d69d3f6dd6ad
Create Date: 2026-09-10 15:37:42.061478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c2187d90e60'
down_revision: Union[str, Sequence[str], None] = 'd69d3f6dd6ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _global_name_unique() -> list[dict]:
    """Unique constraints covering only projects.name (left over from 222329729b66)."""
    inspector = sa.inspect(op.get_bind())
    return [
        uc for uc in inspector.get_unique_constraints("projects")
        if uc["column_names"] == ["name"]
    ]


def upgrade() -> None:
    """Upgrade schema."""
    leftovers = _global_name_unique()
    if not leftovers:
        return
    if op.get_bind().dialect.name == "sqlite":
        # SQLite keeps this constraint unnamed; the naming convention names the
        # reflected constraint so batch mode can drop it while rebuilding the table.
        with op.batch_alter_table(
            "projects",
            naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"},
        ) as batch_op:
            batch_op.drop_constraint("uq_projects_name", type_="unique")
    else:
        op.drop_constraint(leftovers[0]["name"], "projects", type_="unique")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.create_unique_constraint("uq_projects_name", ["name"])
