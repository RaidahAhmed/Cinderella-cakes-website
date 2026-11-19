from app.extensions import db
from datetime import datetime, timezone


class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    order = db.relationship(
        'Order',
        backref=db.backref('status_history', lazy='dynamic', order_by='OrderStatusHistory.created_at.desc()')
    )

    def __repr__(self) -> str:
        return f"<OrderStatusHistory {self.id} - Order {self.order_id} - {self.status}>"

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'status': self.status,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
