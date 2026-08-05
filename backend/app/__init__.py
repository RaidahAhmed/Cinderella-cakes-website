# __init__.py enables us to initialize and work with the different imported modules under the app folder eg: Flask-SQLAlchemy, Flask-Migrate.

from flask import Flask
from app.extensions import db, migrate, cors
from app.controllers.orders.orders_controller import orders
from app.controllers.auth.auth_controller import auth
from app.controllers.gallery.gallery_controller import gallery

# application factory function
# helps us work with different 3rd party libraries and blueprints.

def create_app():

    app = Flask(__name__)  # stores the flask application
    app.config.from_object('config.Config')

    db.init_app(app) # initializes the SQLAlchemy extension with the Flask application instance, allowing us to interact with the database using Python objects instead of writing raw SQL queries.
    migrate.init_app(app, db) #Shows the migration extension theFlask application it will be working with and the database instance it will be managing. This allows us to generate and run database migrations.

    # Application will allow requests from React using CORS rules. This is important because the React dev server runs on a different port than the Flask API, and without CORS, the browser would block requests from the React app to the Flask API due to the same-origin policy.
    cors.init_app(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://localhost:3000"]}})

    # importing and registering models which tells SQLAlchemy about the models we have defined in our application. This is necessary for SQLAlchemy to create the corresponding tables in the database and manage the relationships between them.
    from app.models import Order, GalleryItem, AdminUser

    # registering the blueprints to make the routes available to the application.
    app.register_blueprint(orders)
    app.register_blueprint(auth)
    app.register_blueprint(gallery)

    @app.route("/")  # decorator - modifies another function
    def home():
        return "Cinderella Cakes API is running"

    return app
