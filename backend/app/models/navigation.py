from app.extensions import db

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False) # e.g. "Home", "About"
    url = db.Column(db.String(255), nullable=False) # e.g. "/", "/about"
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_button = db.Column(db.Boolean, default=False) # e.g. "Order Now" button
    
    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'url': self.url,
            'order': self.order,
            'is_active': self.is_active,
            'is_button': self.is_button
        }
