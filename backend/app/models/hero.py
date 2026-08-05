from app.extensions import db

class HeroSection(db.Model):
    __tablename__ = 'hero_sections'
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    
    # Hero content
    eyebrow = db.Column(db.String(100)) # e.g. "Bespoke Bakery"
    heading = db.Column(db.String(255), nullable=False)
    heading_accent = db.Column(db.String(100)) # e.g. "Dreams" to highlight in teal
    subheading = db.Column(db.Text)
    
    # Images (assuming URLs to Media or static strings)
    primary_image_url = db.Column(db.String(255))
    secondary_image_url = db.Column(db.String(255))
    
    # Action buttons
    primary_button_text = db.Column(db.String(50))
    primary_button_url = db.Column(db.String(255))
    secondary_button_text = db.Column(db.String(50))
    secondary_button_url = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'id': self.id,
            'page_id': self.page_id,
            'eyebrow': self.eyebrow,
            'heading': self.heading,
            'heading_accent': self.heading_accent,
            'subheading': self.subheading,
            'primary_image_url': self.primary_image_url,
            'secondary_image_url': self.secondary_image_url,
            'primary_button_text': self.primary_button_text,
            'primary_button_url': self.primary_button_url,
            'secondary_button_text': self.secondary_button_text,
            'secondary_button_url': self.secondary_button_url
        }
