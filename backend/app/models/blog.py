import re
from datetime import datetime
from urllib.parse import quote, unquote

from app.extensions import db


def slugify(value):
    """Turn a title into a short, URL-safe slug (letters, digits and dashes)."""
    slug = re.sub(r'[^a-z0-9]+', '-', (value or '').lower()).strip('-')
    return slug[:150] or 'post'


def blog_media_url(value):
    """Public URL for a blog cover image stored as 'blog/<filename>'."""
    if not value:
        return None
    value = value.replace('\\', '/')
    if value.startswith(('https://', 'http://', '//')):
        return value
    path = value.lstrip('/')
    if path.startswith('static/'):
        return '/' + quote(unquote(path), safe='/')
    if path.startswith('blog/'):
        return '/static/uploads/' + quote(unquote(path), safe='/')
    return '/static/uploads/blog/' + quote(unquote(path), safe='/')


class BlogPost(db.Model):
    __tablename__ = 'blog_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True, index=True)
    category = db.Column(db.String(60), nullable=True, default='Cake notes')
    excerpt = db.Column(db.String(400), nullable=True)
    # Plain text. Blank lines separate paragraphs and a line starting with "## " is a heading.
    content = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(255), nullable=True)
    published = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<BlogPost {self.id} - {self.slug}>"

    def to_dict(self, include_content=False):
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "category": self.category or 'Cake notes',
            "excerpt": self.excerpt,
            "cover_image_url": blog_media_url(self.cover_image),
            "published": bool(self.published),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            data["content"] = self.content
        return data
