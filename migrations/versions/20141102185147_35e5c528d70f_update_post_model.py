"""Update Post model.

Revision ID: 35e5c528d70f
Revises: cebfc404b8f
Create Date: 2014-11-02 18:51:47.914477

"""

# revision identifiers, used by Alembic.
revision = '35e5c528d70f'
down_revision = 'cebfc404b8f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('updated_at', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'updated_at')
    ### end Alembic commands ###