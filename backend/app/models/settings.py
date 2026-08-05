from app.extensions import db
from datetime import datetime

class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    
    # Singleton pattern - typically only row id=1 is used
    site_name = db.Column(db.String(100), default="Cinderella Cakes")
    logo_url = db.Column(db.String(255))
    favicon_url = db.Column(db.String(255))
    
    # Global contact info
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    
    # Brand colors
    primary_color = db.Column(db.String(20), default="#8B3FA0")
    secondary_color = db.Column(db.String(20), default="#2FBFC0")
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'site_name': self.site_name,
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'address': self.address,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    mime_type = db.Column(db.String(100))
    size_bytes = db.Column(db.Integer)
    url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Assuming relation to user
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'mime_type': self.mime_type,
            'size_bytes': self.size_bytes,
            'url': self.url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'uploaded_by': self.uploaded_by
        }
