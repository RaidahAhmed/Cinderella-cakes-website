from app.extensions import db
from datetime import datetime, timezone


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(60), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    review_text = db.Column(db.String(800), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Review {self.id} - {self.customer_name} ({self.rating}/5)>"

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'rating': self.rating,
            'review_text': self.review_text,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
