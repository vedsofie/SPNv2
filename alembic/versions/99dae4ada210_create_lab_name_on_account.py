"""Create Lab Name on Account

Revision ID: 99dae4ada210
Revises: fcad64c4c92e
Create Date: 2016-03-17 02:17:25.741844

"""

# revision identifiers, used by Alembic.
revision = '99dae4ada210'
down_revision = 'fcad64c4c92e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Account", sa.Column("LabName", sa.String(100)))


def downgrade():
    op.drop_column("Account", "LabName")
