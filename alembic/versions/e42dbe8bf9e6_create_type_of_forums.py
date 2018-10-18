"""Create type of Forums

Revision ID: e42dbe8bf9e6
Revises: 424821b2a679
Create Date: 2016-03-29 14:59:50.783579

"""

# revision identifiers, used by Alembic.
revision = 'e42dbe8bf9e6'
down_revision = '424821b2a679'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Forums", sa.Column("Type", sa.String(30)))


def downgrade():
    op.drop_column("Forums", "Type")
