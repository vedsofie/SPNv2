"""create active on users

Revision ID: 62486884fcd8
Revises: fdc0ce67ea9d
Create Date: 2017-05-04 08:30:08.985592

"""

# revision identifiers, used by Alembic.
revision = '62486884fcd8'
down_revision = 'fdc0ce67ea9d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("user", sa.Column("Active", sa.Boolean(True)))


def downgrade():
    pass
