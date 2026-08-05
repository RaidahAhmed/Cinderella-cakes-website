import os
from flask import Flask, jsonify
from config import config_by_name

# Import extensions
from app.extensions import db, migrate, cors, jwt, bcrypt

# Import all models to ensure they are registered with SQLAlchemy
from app import models

# Import blueprint list
from app.controllers import all_blueprints

def create_app(env_name="development"):
    # Create the Flask application instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_by_name[env_name])

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Apply CORS only to specified origins from config
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}})
    
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Register all blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
        
    # JWT error handlers are provided by flask-jwt-extended automatically,
    # but we can customize them if needed here

    # Create upload directory if it doesn't exist
    upload_path = os.path.join(app.root_path, 'static', 'uploads', 'inspiration')
    os.makedirs(upload_path, exist_ok=True)

    return app
