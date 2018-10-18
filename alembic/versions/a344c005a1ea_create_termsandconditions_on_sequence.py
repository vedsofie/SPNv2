"""Create TermsAndConditions on Sequence

Revision ID: a344c005a1ea
Revises: a3dfad7bcabc
Create Date: 2016-05-09 12:53:37.402175

"""

# revision identifiers, used by Alembic.
revision = 'a344c005a1ea'
down_revision = 'a3dfad7bcabc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Sequences", sa.Column("TermsAndConditions", sa.DateTime()))


def downgrade():
    pass
