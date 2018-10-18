"""repurpose sequence attachment

Revision ID: cd10bbf68855
Revises: 8539f3b10c07
Create Date: 2016-03-24 12:06:55.259197

"""

# revision identifiers, used by Alembic.
revision = 'cd10bbf68855'
down_revision = '8539f3b10c07'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("sequence_attachment", sa.Column("Type", sa.String(150)))
    op.add_column("sequence_attachment", sa.Column("ParentID", sa.Integer()))


def downgrade():
    op.drop_column("sequence_attachment", "Type")
    op.drop_column("sequence_attachment", "ParentID")
