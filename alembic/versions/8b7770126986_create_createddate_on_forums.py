"""create createddate on forums

Revision ID: 8b7770126986
Revises: 62486884fcd8
Create Date: 2017-05-08 16:41:34.591494

"""

# revision identifiers, used by Alembic.
revision = '8b7770126986'
down_revision = '62486884fcd8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Forums", sa.Column("CreationDate", sa.DateTime()))


def downgrade():
    pass
