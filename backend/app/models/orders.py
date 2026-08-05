# stores the order model
from app.extensions import db # To get access to the database instance created in extensions.py, we import the db object from app.extensions.
from datetime import datetime


class Order(db.Model):  # Order class is a subclass inheriting from the base Model class
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(30), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    flavor = db.Column(db.String(100), nullable=False)
    cake_size = db.Column(db.String(100), nullable=False)
    inspiration_image = db.Column(db.String(255), nullable=True) 
    special_instructions = db.Column(db.String(500), nullable=True)
    delivery_type = db.Column(db.String(20), nullable=False, default="pickup")  # pickup or delivery
    delivery_address = db.Column(db.String(250), nullable=True)  # required only when delivery_type is 'delivery'
    status = db.Column(db.String(20), nullable=False, default="new")  # new, contacted, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

#Constructor method for the Order class, which initializes an instance of the Order model with the provided attributes for a new order.
    def __init__(self, full_name, phone_number, event_type, event_date, flavor, cake_size,
                 special_instructions=None, inspiration_image=None,
                 delivery_type='pickup', delivery_address=None):
        super(Order, self).__init__() #Sets up the parent class (db.Model) constructor to ensure that the Object is properly tracked by SQLAlchemy.
        self.full_name = full_name
        self.phone_number = phone_number
        self.event_type = event_type
        self.event_date = event_date
        self.flavor = flavor
        self.cake_size = cake_size
        self.special_instructions = special_instructions
        self.inspiration_image = inspiration_image
        self.delivery_type = delivery_type
        self.delivery_address = delivery_address

    def __repr__(self) -> str:
        return f"<Order {self.id} - {self.full_name}>"

    def to_dict(self): #converts the Order object into a dictionary representation, which can be easily serialized to JSON for API responses.
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "flavor": self.flavor,
            "cake_size": self.cake_size,
            "inspiration_image": self.inspiration_image,
            "special_instructions": self.special_instructions,
            "delivery_type": self.delivery_type,
            "delivery_address": self.delivery_address,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
