"""create subtitle on forum

Revision ID: 424821b2a679
Revises: cd10bbf68855
Create Date: 2016-03-29 09:01:17.862897

"""

# revision identifiers, used by Alembic.
revision = '424821b2a679'
down_revision = 'cd10bbf68855'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Forums", sa.Column("Subtitle", sa.String(160)))


def downgrade():
    op.drop_column("Forums", "Subtitle")

