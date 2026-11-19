"""Remember original gallery identity without changing media or existing metadata.

Revision ID: 7c42e1f9a015
Revises: 2b82845ea46d
"""
from alembic import op
import sqlalchemy as sa

revision = '7c42e1f9a015'
down_revision = '2b82845ea46d'
branch_labels = None
depends_on = None


def upgrade():
    # ADD COLUMN and CREATE INDEX avoid rebuilding the parent of existing order FKs on SQLite.
    op.add_column('gallery_items', sa.Column('catalog_filename', sa.String(255), nullable=True))
    op.create_index('uq_gallery_catalog_filename', 'gallery_items', ['catalog_filename'], unique=True)


def downgrade():
    op.drop_index('uq_gallery_catalog_filename', table_name='gallery_items')
    op.drop_column('gallery_items', 'catalog_filename')
