"""Account address fields

Revision ID: 5854cb830e69
Revises: c7b6d619231f
Create Date: 2016-03-16 18:51:32.456963

"""

# revision identifiers, used by Alembic.
revision = '5854cb830e69'
down_revision = 'c7b6d619231f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("Account", sa.Column("City", sa.String(100)))
    op.add_column("Account", sa.Column("State", sa.String(100)))
    op.add_column("Account", sa.Column("ZipCode", sa.String(20)))
    op.add_column("Account", sa.Column("Address", sa.String(100)))
    op.add_column("Account", sa.Column("Latitude", sa.Float()))
    op.add_column("Account", sa.Column("Longitude", sa.Float()))

def downgrade():
    op.drop_column("Account", "City")
    op.drop_column("Account", "State")
    op.drop_column("Account", "ZipCode")
    op.drop_column("Account", "Address")
    op.drop_column("Account", "Latitude")
    op.drop_column("Account", "Longitude")

