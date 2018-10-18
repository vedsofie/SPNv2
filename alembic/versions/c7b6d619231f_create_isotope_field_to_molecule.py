"""create isotope field to molecule

Revision ID: c7b6d619231f
Revises: b69e6470adf4
Create Date: 2016-03-15 16:19:34.353336

"""

# revision identifiers, used by Alembic.
revision = 'c7b6d619231f'
down_revision = 'b69e6470adf4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('Molecules', sa.Column('Isotope', sa.String(100)))


def downgrade():
    op.drop_column("Molecules", "Isotope")
