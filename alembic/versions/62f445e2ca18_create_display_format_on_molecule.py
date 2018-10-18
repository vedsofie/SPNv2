"""Create Display Format on Molecule

Revision ID: 62f445e2ca18
Revises: 40d4c2ce9f7a
Create Date: 2016-04-13 13:48:27.324545

"""

# revision identifiers, used by Alembic.
revision = '62f445e2ca18'
down_revision = '40d4c2ce9f7a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Molecules", sa.Column("DisplayFormat", sa.String(300)))

def downgrade():
    op.drop_column("Molecules", "DisplayFormat")
