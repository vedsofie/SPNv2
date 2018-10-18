"""create comment render type

Revision ID: 8539f3b10c07
Revises: e3823b99982d
Create Date: 2016-03-19 08:55:51.555564

"""

# revision identifiers, used by Alembic.
revision = '8539f3b10c07'
down_revision = 'e3823b99982d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Comments", sa.Column("RenderType", sa.String(8)))


def downgrade():
    op.drop_column("Comments", "RenderType")

