"""Add disabled column to conversations

Revision ID: 35b559533fd6
Revises: e3e87098f660
Create Date: 2024-01-29 11:19:59.971606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35b559533fd6'
down_revision: Union[str, None] = 'e3e87098f660'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add a 'disabled' column to 'conversations' table
    op.add_column('conversations', sa.Column('disabled', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    # Note: Ensure to adjust other commands if needed, especially if you have existing tables and data.

def downgrade() -> None:
    # Remove the 'disabled' column from 'conversations' table
    op.drop_column('conversations', 'disabled')
    # Note: Adjust any other necessary commands for downgrading.
