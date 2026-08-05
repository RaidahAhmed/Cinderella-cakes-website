from app.extensions import db

class FooterColumn(db.Model):
    __tablename__ = 'footer_columns'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, default=0)
    
    links = db.relationship('FooterLink', backref='column', lazy=True, cascade='all, delete-orphan', order_by='FooterLink.order')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'order': self.order,
            'links': [link.to_dict() for link in self.links]
        }

class FooterLink(db.Model):
    __tablename__ = 'footer_links'
    id = db.Column(db.Integer, primary_key=True)
    column_id = db.Column(db.Integer, db.ForeignKey('footer_columns.id'), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, default=0)
    is_external = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'column_id': self.column_id,
            'label': self.label,
            'url': self.url,
            'order': self.order,
            'is_external': self.is_external
        }

class SocialLink(db.Model):
    __tablename__ = 'social_links'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False) # e.g. "instagram", "facebook"
    url = db.Column(db.String(255), nullable=False)
    icon_class = db.Column(db.String(50)) # e.g. "fab fa-instagram"
    order = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'url': self.url,
            'icon_class': self.icon_class,
            'order': self.order
        }
