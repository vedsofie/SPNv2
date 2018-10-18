"""alter sfdc id to be string

Revision ID: e5a63d845d8d
Revises: c03f2375348d
Create Date: 2016-05-16 17:28:24.612817

"""

# revision identifiers, used by Alembic.
revision = 'e5a63d845d8d'
down_revision = 'c03f2375348d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('Forums', 'SFDC_ID')
    op.add_column('Forums', sa.Column('SFDC_ID', sa.String(30)))


def downgrade():
    pass
