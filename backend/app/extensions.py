# for creating instances of the different 3rd party libraries we'll be working with.

# ORM - lets us work with Python objects instead of raw SQL
from flask_sqlalchemy import SQLAlchemy
# generates and runs database migrations
from flask_migrate import Migrate
# allows the React dev server (a different port) to call this API
from flask_cors import CORS

db = SQLAlchemy()  # Creates an instance of the SQLAlchemy class, which is used as a database manager for the Flask application. It allows you to interact with the database using Python objects instead of writing raw SQL queries.
# Creates an instance of the Migrate class, which is used to generate and run database migrations.
migrate = Migrate()
# Creates an instance of the CORS class, which is used to allow cross-origin requests to the Flask application.
cors = CORS()
