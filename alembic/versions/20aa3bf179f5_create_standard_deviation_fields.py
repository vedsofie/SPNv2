"""create_standard_deviation_fields

Revision ID: 20aa3bf179f5
Revises: 88f3a859bd75
Create Date: 2017-04-21 10:36:58.151845

"""

# revision identifiers, used by Alembic.
revision = '20aa3bf179f5'
down_revision = '88f3a859bd75'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Sequences", sa.Column("StartingActivityStandardDeviation", sa.Float()))
    op.add_column("Sequences", sa.Column("SpecificActivityStandardDeviation", sa.Float()))
    op.add_column("Sequences", sa.Column("YieldStandardDeviation", sa.Float()))
    op.add_column("Sequences", sa.Column("SynthesisTimeStandardDeviation", sa.Float()))
    op.add_column("Sequences", sa.Column("NumberOfRuns", sa.Integer()))
    
    


def downgrade():
    pass
