from app.extensions import db
from datetime import datetime

class GalleryItem(db.Model):
    __tablename__ = "gallery_items"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, title, image_url, description=None, category=None):
        self.title = title
        self.image_url = image_url
        self.description = description
        self.category = category

    def __repr__(self) -> str:
        return f"<GalleryItem {self.id} - {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "image_url": f"/static/uploads/inspiration/{self.image_url}" if self.image_url else None,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
