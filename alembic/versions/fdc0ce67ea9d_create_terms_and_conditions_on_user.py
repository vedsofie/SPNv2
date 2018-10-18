"""create_terms_and_conditions_on_user

Revision ID: fdc0ce67ea9d
Revises: dcd20c4cf4b4
Create Date: 2017-05-03 12:52:30.757973

"""

# revision identifiers, used by Alembic.
revision = 'fdc0ce67ea9d'
down_revision = 'dcd20c4cf4b4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("user", sa.Column("TermsAndConditions", sa.DateTime()))


def downgrade():
    pass

