"""create UserID on Forum

Revision ID: c03f2375348d
Revises: 33ca43e39b94
Create Date: 2016-05-15 19:06:14.531227

"""

# revision identifiers, used by Alembic.
revision = 'c03f2375348d'
down_revision = '33ca43e39b94'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Forums", sa.Column("UserID", sa.Integer()))
    try:
        op.create_foreign_key("forum_userid_constraint", "Forums", "user", ["UserID"], ["UserID"])
    except Exception as e:
        print str(e)

def downgrade():
    pass
