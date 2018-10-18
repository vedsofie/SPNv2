"""account drop short description

Revision ID: fcad64c4c92e
Revises: 5854cb830e69
Create Date: 2016-03-16 19:02:26.218873

"""

# revision identifiers, used by Alembic.
revision = 'fcad64c4c92e'
down_revision = '5854cb830e69'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    try:
        op.drop_column("Account", "short_description")
        op.drop_column("Account", "account_number")
    except Exception as e:
        print "Error"
        print str(e)


def downgrade():
    op.add_column("Account", sa.Column("short_description", sa.String(160)))
    op.add_column("Account", sa.Column("account_number", sa.String(50)))
