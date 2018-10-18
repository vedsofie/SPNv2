"""Create read only field on Forums

Revision ID: bb87e35d6b16
Revises: 97e3656096f6
Create Date: 2016-07-22 17:00:39.874312

"""

# revision identifiers, used by Alembic.
revision = 'bb87e35d6b16'
down_revision = '97e3656096f6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Forums", sa.Column("ReadOnly", sa.Boolean()))


def downgrade():
    pass
