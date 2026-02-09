"""Initial schema with all core tables

Revision ID: 001
Revises:
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=True),
        sa.Column('subscription_tier', sa.String(20), server_default='free', nullable=False),
        sa.Column('subscription_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('oauth_provider', sa.String(50), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('verification_token', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', pg.JSONB(), server_default='{}', nullable=False),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_subscription', 'users', ['subscription_tier'])

    # 2. categories table (before notes, as notes reference it)
    op.create_table(
        'categories',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('parent_id', pg.UUID(as_uuid=True), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('level', sa.Integer(), server_default='0', nullable=False),
        sa.Column('notes_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('children_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('user_id', 'name', 'parent_id', name='uq_user_name_parent'),
    )
    op.create_index('idx_categories_user', 'categories', ['user_id', 'parent_id'])

    # 3. notes table
    op.create_table(
        'notes',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('ocr_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('embedding', pg.Vector(1536), nullable=True),
        sa.Column('category_id', pg.UUID(as_uuid=True), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('mindmap_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('metadata', pg.JSONB(), server_default='{}', nullable=False),
    )
    op.create_index('idx_notes_user', 'notes', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_notes_category', 'notes', ['category_id'])
    # Vector index for similarity search (ivfflat)
    op.execute('CREATE INDEX idx_notes_embedding ON notes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);')

    # 4. mindmaps table
    op.create_table(
        'mindmaps',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('note_id', pg.UUID(as_uuid=True), sa.ForeignKey('notes.id', ondelete='CASCADE'), nullable=True),
        sa.Column('structure', pg.JSONB(), nullable=False),
        sa.Column('map_type', sa.String(20), server_default='user_generated', nullable=False),
        sa.Column('ai_model', sa.String(50), nullable=True),
        sa.Column('ai_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('compared_with_mindmap_id', pg.UUID(as_uuid=True), sa.ForeignKey('mindmaps.id'), nullable=True),
        sa.Column('comparison_result', pg.JSONB(), nullable=True),
        sa.Column('is_template', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('fork_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_mindmaps_user', 'mindmaps', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_mindmaps_note', 'mindmaps', ['note_id'])
    op.create_index('idx_mindmaps_type', 'mindmaps', ['map_type'])
    op.create_index('idx_mindmaps_template', 'mindmaps', ['is_template'], postgresql_where=sa.text('is_template = true'))

    # 5. mindmap_knowledge_points table
    op.create_table(
        'mindmap_knowledge_points',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('mindmap_id', pg.UUID(as_uuid=True), sa.ForeignKey('mindmaps.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', sa.String(100), nullable=False),
        sa.Column('knowledge_text', sa.Text(), nullable=False),
        sa.Column('embedding', pg.Vector(1536), nullable=True),
        sa.Column('related_note_id', pg.UUID(as_uuid=True), sa.ForeignKey('notes.id'), nullable=True),
        sa.Column('related_note_section', sa.String(100), nullable=True),
        sa.Column('mastery_level', sa.Numeric(3, 2), server_default='0', nullable=False),
        sa.Column('question_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('mistake_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('mindmap_id', 'node_id', name='uq_mindmap_node'),
    )
    op.create_index('idx_mindmap_kp_mindmap', 'mindmap_knowledge_points', ['mindmap_id'])
    op.create_index('idx_mindmap_kp_note', 'mindmap_knowledge_points', ['related_note_id'])
    op.execute('CREATE INDEX idx_mindmap_kp_embedding ON mindmap_knowledge_points USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);')

    # 6. quiz_questions table
    op.create_table(
        'quiz_questions',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('knowledge_point_id', pg.UUID(as_uuid=True), sa.ForeignKey('mindmap_knowledge_points.id', ondelete='CASCADE'), nullable=False),
        sa.Column('note_id', pg.UUID(as_uuid=True), sa.ForeignKey('notes.id'), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(20), nullable=False),
        sa.Column('options', pg.JSONB(), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('answer_explanation', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.String(10), server_default='medium', nullable=False),
        sa.Column('ai_generated', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ai_model', sa.String(50), nullable=True),
        sa.Column('attempt_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('correct_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_quiz_questions_kp', 'quiz_questions', ['knowledge_point_id'])
    op.create_index('idx_quiz_questions_note', 'quiz_questions', ['note_id'])
    op.create_index('idx_quiz_questions_difficulty', 'quiz_questions', ['difficulty'])

    # 7. user_quiz_records table
    op.create_table(
        'user_quiz_records',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', pg.UUID(as_uuid=True), sa.ForeignKey('quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_answer', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('time_spent', sa.Integer(), nullable=True),
        sa.Column('related_note_snippet', sa.Text(), nullable=True),
        sa.Column('related_note_section', sa.String(100), nullable=True),
        sa.UniqueConstraint('user_id', 'question_id', 'answered_at', name='uq_user_question_time'),
    )
    op.create_index('idx_quiz_records_user', 'user_quiz_records', ['user_id', sa.text('answered_at DESC')])
    op.create_index('idx_quiz_records_question', 'user_quiz_records', ['question_id'])
    op.create_index('idx_quiz_records_correct', 'user_quiz_records', ['user_id', 'is_correct'], postgresql_where=sa.text('is_correct = false'))

    # 8. mistakes table
    op.create_table(
        'mistakes',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', pg.UUID(as_uuid=True), sa.ForeignKey('quiz_questions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(20), nullable=False),
        sa.Column('options', pg.JSONB(), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=False),
        sa.Column('user_answer', sa.Text(), nullable=False),
        sa.Column('tags', pg.ARRAY(sa.String), nullable=True),
        sa.Column('category_id', pg.UUID(as_uuid=True), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('knowledge_point_id', pg.UUID(as_uuid=True), sa.ForeignKey('mindmap_knowledge_points.id'), nullable=True),
        sa.Column('related_note_id', pg.UUID(as_uuid=True), sa.ForeignKey('notes.id'), nullable=True),
        sa.Column('related_note_snippet', sa.Text(), nullable=True),
        sa.Column('mistake_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('last_mistake_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_mistakes_user', 'mistakes', ['user_id', sa.text('created_at DESC')])
    op.create_index('idx_mistakes_tags', 'mistakes', ['tags'], postgresql_using='gin')
    op.create_index('idx_mistakes_category', 'mistakes', ['category_id'])
    op.create_index('idx_mistakes_kp', 'mistakes', ['knowledge_point_id'])

    # 9. mistake_reviews table
    op.create_table(
        'mistake_reviews',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('mistake_id', pg.UUID(as_uuid=True), sa.ForeignKey('mistakes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('review_time', sa.Integer(), nullable=True),
        sa.Column('review_stage', sa.Integer(), server_default='0', nullable=False),
        sa.Column('next_review_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_mistake_reviews_mistake', 'mistake_reviews', ['mistake_id', sa.text('reviewed_at DESC')])
    op.create_index('idx_mistake_reviews_user', 'mistake_reviews', ['user_id', 'next_review_at'], postgresql_where=sa.text('next_review_at IS NOT NULL'))

    # 10. category_relations table
    op.create_table(
        'category_relations',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_a_id', pg.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_b_id', pg.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(20), nullable=False),
        sa.Column('weight', sa.Numeric(3, 2), server_default='0.5', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('category_a_id', 'category_b_id', name='uq_category_pair'),
        sa.CheckConstraint('category_a_id < category_b_id', name='check_ordered_pair'),
    )
    op.create_index('idx_category_relations_user', 'category_relations', ['user_id'])
    op.create_index('idx_category_relations_type', 'category_relations', ['relation_type'])

    # 11. note_shares table
    op.create_table(
        'note_shares',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('note_id', pg.UUID(as_uuid=True), sa.ForeignKey('notes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('share_id', sa.String(20), unique=True, nullable=False),
        sa.Column('access_type', sa.String(20), server_default='public', nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('allow_download', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('allow_merge', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('download_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('merge_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_note_shares_note', 'note_shares', ['note_id'])
    op.create_index('idx_note_shares_user', 'note_shares', ['user_id'])
    op.create_index('idx_note_shares_id', 'note_shares', ['share_id'])
    op.create_index('idx_note_shares_expires', 'note_shares', ['expires_at'], postgresql_where=sa.text('expires_at IS NOT NULL'))

    # 12. study_sessions table
    op.create_table(
        'study_sessions',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', pg.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_type', sa.String(20), nullable=False),
        sa.Column('related_note_id', pg.UUID(as_uuid=True), sa.ForeignKey('notes.id'), nullable=True),
        sa.Column('related_quiz_id', pg.UUID(as_uuid=True), sa.ForeignKey('quiz_questions.id'), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('questions_answered', sa.Integer(), server_default='0', nullable=False),
        sa.Column('questions_correct', sa.Integer(), server_default='0', nullable=False),
        sa.Column('notes_created', sa.Integer(), server_default='0', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_study_sessions_user', 'study_sessions', ['user_id', sa.text('started_at DESC')])
    op.create_index('idx_study_sessions_type', 'study_sessions', ['session_type'])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop tables in reverse order of creation (to handle foreign keys)
    op.drop_table('study_sessions')
    op.drop_table('note_shares')
    op.drop_table('category_relations')
    op.drop_table('mistake_reviews')
    op.drop_table('mistakes')
    op.drop_table('user_quiz_records')
    op.drop_table('quiz_questions')
    op.drop_table('mindmap_knowledge_points')
    op.drop_table('mindmaps')
    op.drop_table('notes')
    op.drop_table('categories')
    op.drop_table('users')

    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector;')
