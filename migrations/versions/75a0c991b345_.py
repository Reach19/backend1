"""empty message

Revision ID: 75a0c991b345
Revises: 
Create Date: 2025-02-21 05:31:01.250917

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '75a0c991b345'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('telegram_id', sa.Text(), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=True),
    sa.Column('last_name', sa.String(length=100), nullable=True),
    sa.Column('username', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('telegram_id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('channel',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=True),
    sa.Column('chat_id', sa.BigInteger(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('message', sa.String(length=500), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('sent', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('giveaway',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('prize_amount', sa.Float(), nullable=False),
    sa.Column('participants_count', sa.Integer(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=False),
    sa.Column('channel_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('announced', sa.Boolean(), nullable=True),
    sa.Column('winners_announced', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['channel_id'], ['channel.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('participant',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('giveaway_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['giveaway_id'], ['giveaway.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('winner',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('giveaway_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('prize_amount', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('notified', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['giveaway_id'], ['giveaway.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('subscriptions')
    op.execute("DROP TABLE IF EXISTS product_approvals CASCADE;")  # Raw SQL with CASCADE
    op.execute("DROP TABLE IF EXISTS products CASCADE;") 
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('product_approvals',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('admin_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('approved_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='product_approvals_product_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='product_approvals_pkey')
    )
    op.create_table('products',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('price', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('seller_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('featured', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=True),
    sa.Column('sold_out', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=True),
    sa.Column('posted', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='products_pkey')
    )
    op.create_table('subscriptions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('seller_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('subscribed_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='subscriptions_pkey')
    )
    op.drop_table('winner')
    op.drop_table('participant')
    op.drop_table('giveaway')
    op.drop_table('notification')
    op.drop_table('channel')
    op.drop_table('user')
    # ### end Alembic commands ###
