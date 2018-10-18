"""Create Case Number of Forum

Revision ID: d5cc249819f0
Revises: 8b7770126986
Create Date: 2017-05-09 15:24:05.632764

"""

# revision identifiers, used by Alembic.
revision = 'd5cc249819f0'
down_revision = '8b7770126986'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Forums", sa.Column("CaseNumber", sa.String(50)))

def downgrade():
    pass
