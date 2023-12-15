from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func
from lib.telegram.tokenizer import Tokenizer

# Revision identifiers
revision = '1e2238b0dde0'
down_revision = 'd8331a6a7854'

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
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
        sa.Column('balance', sa.DECIMAL(precision=10, scale=5), default=Tokenizer.START_BALANCE)
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
        sa.Column('updated_at', sa.DateTime(timezone=True)),  # Original default value
        sa.Column('balance', sa.DECIMAL(precision=10, scale=5), default=Tokenizer.START_BALANCE)
    )

    op.execute('INSERT INTO old_conversations SELECT * FROM conversations')

    op.drop_table('conversations')
    op.rename_table('old_conversations', 'conversations')
