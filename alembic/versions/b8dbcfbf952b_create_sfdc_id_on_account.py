"""Create SFDC Id on Account

Revision ID: b8dbcfbf952b
Revises: bb87e35d6b16
Create Date: 2016-10-01 11:25:05.270747

"""

# revision identifiers, used by Alembic.
revision = 'b8dbcfbf952b'
down_revision = 'bb87e35d6b16'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Account", sa.Column("SFDC_ID", sa.String(30)))


def downgrade():
    pass