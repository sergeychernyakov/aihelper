"""Change Conversation balance

Revision ID: d8331a6a7854
Revises: e439fea1fe12
Create Date: 2023-12-06 11:48:01.962245

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func  # Import func here

# revision identifiers, used by Alembic.
revision: str = 'd8331a6a7854'
down_revision: Union[str, None] = 'e439fea1fe12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create a new table with the desired structure
    op.create_table('new_conversations',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('assistant_id', sa.String, index=True),
        sa.Column('thread_id', sa.String, index=True),
        sa.Column('user_id', sa.Integer, index=True),
        sa.Column('username', sa.String, index=True),
        sa.Column('language_code', sa.String),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now()),
        sa.Column('balance', sa.DECIMAL(precision=10, scale=6), nullable=True)
    )

    # Copy data from old table to new table
    op.execute('INSERT INTO new_conversations SELECT * FROM conversations')

    # Drop the old table and rename the new table
    op.drop_table('conversations')
    op.rename_table('new_conversations', 'conversations')

def downgrade() -> None:
    # Similar steps but revert to the original structure
    op.create_table('old_conversations',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('assistant_id', sa.String, index=True),
        sa.Column('thread_id', sa.String, index=True),
        sa.Column('user_id', sa.Integer, index=True),
        sa.Column('username', sa.String, index=True),
        sa.Column('language_code', sa.String),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now()),
        sa.Column('balance', sa.Float(precision=5), nullable=True)
    )

    op.execute('INSERT INTO old_conversations SELECT * FROM conversations')

    op.drop_table('conversations')
    op.rename_table('old_conversations', 'conversations')
