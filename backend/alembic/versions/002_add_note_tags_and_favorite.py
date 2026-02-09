"""Add tags and is_favorited to notes table

Revision ID: 002_add_note_tags_and_favorite
Revises: 001_initial_schema
Create Date: 2026-02-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_note_tags_and_favorite'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add tags, is_favorited columns and rename metadata to meta_data."""
    # Add tags column
    op.add_column('notes', sa.Column('tags', sa.ARRAY(sa.String()), nullable=True))
    
    # Add is_favorited column
    op.add_column('notes', sa.Column('is_favorited', sa.Boolean(), nullable=True, server_default='false'))
    
    # Rename metadata to meta_data (metadata is reserved in SQLAlchemy)
    # Note: In PostgreSQL, we need to be careful with this
    op.execute('ALTER TABLE notes RENAME COLUMN metadata TO meta_data')


def downgrade():
    """Remove tags and is_favorited columns and revert meta_data name."""
    # Remove tags column
    op.drop_column('notes', 'tags')
    
    # Remove is_favorited column
    op.drop_column('notes', 'is_favorited')
    
    # Revert meta_data back to metadata
    op.execute('ALTER TABLE notes RENAME COLUMN meta_data TO metadata')
