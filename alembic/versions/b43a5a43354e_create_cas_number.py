"""create cas number

Revision ID: b43a5a43354e
Revises: 
Create Date: 2016-03-10 21:14:36.999066

"""

# revision identifiers, used by Alembic.
revision = 'b43a5a43354e'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('Molecules', sa.Column('CAS', sa.String(300)))
    try:
        op.create_unique_constraint("uq_cas", "Molecules", ["CAS"])
    except NotImplementedError:
        print "Not Implemented"

def downgrade():
    op.drop_constraint('uq_cas', "Molecules")
    try:
        op.drop_column("Molecules", "CAS")
    except NotImplementedError:
        print "Not Implemented"
