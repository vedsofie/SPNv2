"""Create User ID on probe

Revision ID: 40d4c2ce9f7a
Revises: e42dbe8bf9e6
Create Date: 2016-04-13 10:54:29.859599

"""

# revision identifiers, used by Alembic.
revision = '40d4c2ce9f7a'
down_revision = 'e42dbe8bf9e6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Molecules", sa.Column("UserID", sa.Integer()))
    try:
        op.create_foreign_key("molecule_userid_constraint", "Molecules", "user", ["UserID"], ["UserID"])
    except Exception as e:
        print str(e)

def downgrade():
    pass
