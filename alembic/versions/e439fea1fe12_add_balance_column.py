"""Add balance column

Revision ID: e439fea1fe12
Revises: 
Create Date: 2023-12-01 14:30:33.225797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e439fea1fe12'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('balance', sa.Float(precision=5), nullable=True, server_default="1.0"))

def downgrade() -> None:
    op.drop_column('conversations', 'balance')
