"""initial

Revision ID: 109211855214
Revises: 
Create Date: 2024-06-08 21:51:37.499920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '109211855214'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('articoluls',
    sa.Column('articolul_id', sa.Integer(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False),
    sa.Column('url', sa.VARCHAR(length=150), nullable=True),
    sa.PrimaryKeyConstraint('articolul_id')
    )
    op.create_table('pdfs',
    sa.Column('pdf_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('articolul_num', sa.Integer(), nullable=False),
    sa.Column('list_name', sa.VARCHAR(length=15), nullable=False),
    sa.Column('number_order', sa.VARCHAR(length=150), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('url', sa.VARCHAR(length=150), nullable=False),
    sa.Column('parsed_at', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('list_name', 'number_order', 'year')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pdfs')
    op.drop_table('articoluls')
    # ### end Alembic commands ###

# ruff: noqa