# initializes the models folder as a module.
# a model is a representation of the structure of a database table.
# flask-sqlalchemy is our ORM (object relational mapper) - it lets us work with
# Python objects instead of writing raw SQL.

from .orders import Order
from .gallery import GalleryItem
from .user import AdminUser
