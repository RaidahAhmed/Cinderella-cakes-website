"""Add order tracking, reviews, gallery categories, order-gallery link

Revision ID: 2b82845ea46d
Revises: 201fa049ee30
Create Date: 2026-11-17 04:00:08.583321

"""
from datetime import datetime, timezone
import secrets
import string

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b82845ea46d'
down_revision = '201fa049ee30'
branch_labels = None
depends_on = None


def _prepare_order_backfill(connection):
    """Validate and allocate everything before MySQL can implicitly commit DDL."""
    legacy_orders = sa.table(
        'orders', sa.column('id', sa.Integer), sa.column('status', sa.String),
        sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime),
    )
    status_map = {
        'pending': 'new', 'contacted': 'confirmed', 'in_progress': 'baking',
        'completed': 'delivered',
        **{status: status for status in (
            'new', 'confirmed', 'baking', 'ready', 'out_for_delivery',
            'delivered', 'cancelled',
        )},
    }
    rows = connection.execute(sa.select(legacy_orders).order_by(legacy_orders.c.id)).mappings().all()
    if any(row['status'] not in status_map for row in rows):
        raise RuntimeError(
            'Unrecognized legacy order status. Review and explicitly map unknown statuses '
            'before retrying this migration; no schema or order changes were made.'
        )

    allocated = set()
    alphabet = string.ascii_uppercase + string.digits
    migrated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    backfill = []
    for row in rows:
        for _ in range(100):
            reference = 'CC-' + ''.join(secrets.choice(alphabet) for _ in range(5))
            if reference not in allocated:
                allocated.add(reference)
                break
        else:
            raise RuntimeError('Unable to allocate unique order references; migration stopped before changes.')
        backfill.append({
            'order_id': row['id'],
            'order_reference': reference,
            'status': status_map[row['status']],
            'note': 'Status snapshot imported from the previous order system.',
            'created_at': row['updated_at'] or row['created_at'] or migrated_at,
        })
    return backfill


def upgrade():
    connection = op.get_bind()
    backfill = _prepare_order_backfill(connection)

    # --- Reviews (customer testimonials) ---
    op.create_table('reviews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('customer_name', sa.String(length=60), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('review_text', sa.String(length=800), nullable=False),
    sa.Column('is_approved', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # --- Order status timeline ---
    op.create_table('order_status_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('note', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'],
                            name='fk_order_status_history_order_id_orders',
                            ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

    # --- Orders: public reference + optional link to inspiring gallery item ---
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order_reference', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('gallery_item_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint('uq_orders_order_reference', ['order_reference'])
        batch_op.create_foreign_key('fk_orders_gallery_item_id_gallery_items',
                                    'gallery_items', ['gallery_item_id'], ['id'],
                                    ondelete='SET NULL')

    order_table = sa.table(
        'orders', sa.column('id', sa.Integer), sa.column('status', sa.String),
        sa.column('order_reference', sa.String),
    )
    for snapshot in backfill:
        connection.execute(
            order_table.update().where(order_table.c.id == snapshot['order_id']).values(
                order_reference=snapshot['order_reference'], status=snapshot['status'],
            )
        )
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('order_reference', existing_type=sa.String(length=10),
                              existing_nullable=True, nullable=False)

    history_table = sa.table(
        'order_status_history', sa.column('order_id', sa.Integer),
        sa.column('status', sa.String), sa.column('note', sa.String),
        sa.column('created_at', sa.DateTime),
    )
    if backfill:
        op.bulk_insert(history_table, [
            {key: value for key, value in snapshot.items() if key != 'order_reference'}
            for snapshot in backfill
        ])

    # --- Gallery categories: default new/unset items to 'other' ---
    with op.batch_alter_table('gallery_items', schema=None) as batch_op:
        batch_op.alter_column('category',
                              existing_type=sa.String(length=100),
                              existing_nullable=True,
                              server_default='other')
    op.execute("UPDATE gallery_items SET category = 'other' WHERE category IS NULL")


def downgrade():
    # --- Gallery categories: drop the server-side default ---
    with op.batch_alter_table('gallery_items', schema=None) as batch_op:
        batch_op.alter_column('category',
                              existing_type=sa.String(length=100),
                              existing_nullable=True,
                              server_default=None)

    # --- Order status timeline ---
    op.drop_table('order_status_history')

    # --- Orders: drop reference + gallery link ---
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_orders_gallery_item_id_gallery_items', type_='foreignkey')
        batch_op.drop_constraint('uq_orders_order_reference', type_='unique')
        batch_op.drop_column('gallery_item_id')
        batch_op.drop_column('order_reference')

    # --- Reviews ---
    op.drop_table('reviews')
