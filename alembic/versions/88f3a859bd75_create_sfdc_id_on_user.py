"""Create SFDC Id on User

Revision ID: 88f3a859bd75
Revises: b8dbcfbf952b
Create Date: 2016-10-01 12:22:47.017463

"""

# revision identifiers, used by Alembic.
revision = '88f3a859bd75'
down_revision = 'b8dbcfbf952b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("user", sa.Column("SFDC_ID", sa.String(30)))


def downgrade():
    pass