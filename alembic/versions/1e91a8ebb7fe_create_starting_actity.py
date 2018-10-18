"""Create Starting Actity

Revision ID: 1e91a8ebb7fe
Revises: 62f445e2ca18
Create Date: 2016-04-15 10:24:01.266071

"""

# revision identifiers, used by Alembic.
revision = '1e91a8ebb7fe'
down_revision = '62f445e2ca18'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Sequences", sa.Column("StartingActivity", sa.Float()))


def downgrade():
    pass
