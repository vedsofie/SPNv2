"""Create Category on Keyword

Revision ID: 6276ee82945c
Revises: 3340ef772d65
Create Date: 2016-03-17 12:31:16.148998

"""

# revision identifiers, used by Alembic.
revision = '6276ee82945c'
down_revision = '3340ef772d65'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Keywords", sa.Column("Category", sa.String(160)))

def downgrade():
    op.drop_column("Keywords", sa.Column("Category"))
