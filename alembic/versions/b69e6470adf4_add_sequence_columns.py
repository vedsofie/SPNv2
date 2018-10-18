"""Add Sequence columns

Revision ID: b69e6470adf4
Revises: b43a5a43354e
Create Date: 2016-03-15 12:17:57.351514

"""

# revision identifiers, used by Alembic.
revision = 'b69e6470adf4'
down_revision = 'b43a5a43354e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Sequences", sa.Column("PurificationMethod", sa.String(30)))
    op.add_column("Sequences", sa.Column("SynthesisTime", sa.Integer()))
    op.add_column("Sequences", sa.Column("NumberOfSteps", sa.Integer()))
    op.add_column("Sequences", sa.Column("SpecificActivity", sa.Float()))
    op.add_column("Sequences", sa.Column("Yield", sa.Float()))


def downgrade():
    op.drop_column("Sequences", "PurificationMethod")
    op.drop_column("Sequences", "SynthesisTime")
    op.drop_column("Sequences", "NumberOfSteps")
    op.drop_column("Sequences", "SpecificActivity")
    op.drop_column("Sequences", "Yield")
