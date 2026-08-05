from app.extensions import db
from datetime import datetime

class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False) # e.g. "home", "about", "contact"
    title = db.Column(db.String(100), nullable=False)
    meta_description = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships to content blocks for this page
    hero = db.relationship('HeroSection', backref='page', uselist=False, cascade='all, delete-orphan')
    content_sections = db.relationship('ContentSection', backref='page', lazy=True, cascade='all, delete-orphan', order_by='ContentSection.order')

    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'meta_description': self.meta_description,
            'is_published': self.is_published,
            'hero': self.hero.to_dict() if self.hero else None,
            'content_sections': [section.to_dict() for section in self.content_sections]
        }
