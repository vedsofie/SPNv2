"""Create display name on keywords

Revision ID: a3dfad7bcabc
Revises: 1e91a8ebb7fe
Create Date: 2016-04-19 16:12:44.373773

"""

# revision identifiers, used by Alembic.
revision = 'a3dfad7bcabc'
down_revision = '1e91a8ebb7fe'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Keywords", sa.Column("DisplayFormat", sa.String(160)))


def downgrade():
    op.drop_column("Keywords", "DisplayFormat")
