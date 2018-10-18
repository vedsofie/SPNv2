"""Create Molecule Approved Field

Revision ID: e3823b99982d
Revises: 6276ee82945c
Create Date: 2016-03-17 19:59:48.526628

"""

# revision identifiers, used by Alembic.
revision = 'e3823b99982d'
down_revision = '6276ee82945c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('Molecules', sa.Column('Approved', sa.Boolean(True)))


def downgrade():
    op.drop_column("Molecules", "Approved")
