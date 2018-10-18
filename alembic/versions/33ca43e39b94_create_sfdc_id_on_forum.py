"""Create SFDC_ID on Forum

Revision ID: 33ca43e39b94
Revises: a344c005a1ea
Create Date: 2016-05-14 10:05:01.034770

"""

# revision identifiers, used by Alembic.
revision = '33ca43e39b94'
down_revision = 'a344c005a1ea'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Forums", sa.Column("SFDC_ID", sa.Integer()))


def downgrade():
    pass
