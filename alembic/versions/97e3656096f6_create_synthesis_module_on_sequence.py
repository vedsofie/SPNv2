"""create_synthesis_module_on_sequence

Revision ID: 97e3656096f6
Revises: e5a63d845d8d
Create Date: 2016-06-07 16:14:01.844038

"""

# revision identifiers, used by Alembic.
revision = '97e3656096f6'
down_revision = 'e5a63d845d8d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Sequences", sa.Column("SynthesisModule", sa.String(35)))


def downgrade():
    pass
