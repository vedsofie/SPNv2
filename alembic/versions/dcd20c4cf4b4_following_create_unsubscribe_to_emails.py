"""following create unsubscribe to emails

Revision ID: dcd20c4cf4b4
Revises: 20aa3bf179f5
Create Date: 2017-04-26 10:37:39.527143

"""

# revision identifiers, used by Alembic.
revision = 'dcd20c4cf4b4'
down_revision = '20aa3bf179f5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Followers", sa.Column("EmailSubscribed", sa.Boolean(True)))


def downgrade():
    pass
