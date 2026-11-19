from app.extensions import db
from datetime import datetime
from pathlib import PurePosixPath
from urllib.parse import quote, unquote, urlsplit


def gallery_media_url(value):
    """Normalize both legacy basenames and already-prefixed local URLs exactly once."""
    if not value:
        return None
    value = value.replace('\\', '/')
    if value.startswith(('https://', 'http://', '//')):
        return value
    path = value.lstrip('/')
    if path.startswith('static/'):
        return '/' + quote(unquote(path), safe='/')
    if path.startswith('gallery/'):
        return '/static/uploads/' + quote(unquote(path), safe='/')
    return '/static/uploads/inspiration/' + quote(unquote(path), safe='/')


CATEGORY_CHOICES = [
    'wedding', 'birthday', 'kids', 'baby', 'graduation',
    'anniversary', 'corporate', 'holiday', 'sculpted', 'cupcakes', 'other'
]

CATEGORY_LABELS = {
    'wedding': 'Wedding',
    'birthday': 'Birthday',
    'kids': 'Kids',
    'baby': 'Baby & Christening',
    'graduation': 'Graduation',
    'anniversary': 'Anniversary',
    'corporate': 'Corporate',
    'holiday': 'Holiday',
    'sculpted': 'Sculpted & Custom',
    'cupcakes': 'Cupcakes',
    'other': 'Other',
}


class GalleryItem(db.Model):
    __tablename__ = "gallery_items"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True, default='other')
    created_at = db.Column(db.DateTime, default=datetime.now)
    # One-time curation marker and original identity; administrator edits never clear it.
    catalog_filename = db.Column(db.String(255), nullable=True)
    __table_args__ = (db.Index('uq_gallery_catalog_filename', 'catalog_filename', unique=True),)

    @property
    def media_type(self):
        path = urlsplit((self.image_url or '').replace('\\', '/')).path
        return 'video' if PurePosixPath(unquote(path)).suffix.lower() == '.mp4' else 'image'

    def __init__(self, title, image_url, description=None, category='other'):
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
            "image_url": gallery_media_url(self.image_url),
            "media_type": self.media_type,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
