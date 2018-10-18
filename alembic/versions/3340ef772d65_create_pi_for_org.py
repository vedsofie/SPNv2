"""Create PI for org

Revision ID: 3340ef772d65
Revises: 99dae4ada210
Create Date: 2016-03-17 09:59:01.798574

"""

# revision identifiers, used by Alembic.
revision = '3340ef772d65'
down_revision = '99dae4ada210'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Account", sa.Column("PrincipalInvestigatorID", sa.Integer()))
    try:
        op.create_foreign_key("account_pi_constraint", "Account", "user", ["PrincipalInvestigatorID"], ["UserID"])
    except Exception as e:
        print str(e)

def downgrade():
    try:
        op.drop_constraint("Account", "account_pi_constraint")
        op.drop_column("Account", "PrincipalInvestigatorID")
    except Exception as e:
        print str(e)

