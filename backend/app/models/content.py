from app.extensions import db

class ContentSection(db.Model):
    __tablename__ = 'content_sections'
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    section_type = db.Column(db.String(50), nullable=False) # e.g. "feature_grid", "visit_split", "about_split"
    order = db.Column(db.Integer, default=0)
    
    # Optional section headers
    eyebrow = db.Column(db.String(100))
    heading = db.Column(db.String(255))
    subheading = db.Column(db.Text)
    
    # Blocks inside this section
    blocks = db.relationship('ContentBlock', backref='section', lazy=True, cascade='all, delete-orphan', order_by='ContentBlock.order')
    
    def to_dict(self):
        return {
            'id': self.id,
            'page_id': self.page_id,
            'section_type': self.section_type,
            'order': self.order,
            'eyebrow': self.eyebrow,
            'heading': self.heading,
            'subheading': self.subheading,
            'blocks': [block.to_dict() for block in self.blocks]
        }

class ContentBlock(db.Model):
    __tablename__ = 'content_blocks'
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('content_sections.id'), nullable=False)
    order = db.Column(db.Integer, default=0)
    
    # Block fields (used depending on section_type)
    title = db.Column(db.String(255))
    text = db.Column(db.Text)
    icon_or_image_url = db.Column(db.String(255))
    link_url = db.Column(db.String(255))
    link_text = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'section_id': self.section_id,
            'order': self.order,
            'title': self.title,
            'text': self.text,
            'icon_or_image_url': self.icon_or_image_url,
            'link_url': self.link_url,
            'link_text': self.link_text
        }
