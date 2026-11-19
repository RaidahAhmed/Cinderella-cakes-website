"""Add blog posts so the bakery can publish cake notes from the admin dashboard.

Revision ID: a4e91c3b7d20
Revises: 7c42e1f9a015
"""
from alembic import op
import sqlalchemy as sa

revision = 'a4e91c3b7d20'
down_revision = '7c42e1f9a015'
branch_labels = None
depends_on = None


def upgrade():
    # A brand-new table: no existing gallery, order or account data is touched.
    op.create_table(
        'blog_posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(180), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('category', sa.String(60), nullable=True),
        sa.Column('excerpt', sa.String(400), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('cover_image', sa.String(255), nullable=True),
        sa.Column('published', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_blog_posts_slug', 'blog_posts', ['slug'], unique=True)


def downgrade():
    op.drop_index('ix_blog_posts_slug', table_name='blog_posts')
    op.drop_table('blog_posts')
