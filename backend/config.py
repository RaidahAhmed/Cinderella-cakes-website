import os
from datetime import timedelta

class Config:
    # Basic Config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Auth
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-prod')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Uploads
    UPLOAD_FOLDER = 'app/static/uploads/inspiration'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    
    # CORS
    CORS_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']

    # --- Email notification settings ---
    MAIL_ENABLED = False
    SMTP_HOST = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USERNAME = 'your_email@gmail.com'
    SMTP_PASSWORD = 'your_app_password'
    SMTP_FROM_EMAIL = 'your_email@gmail.com'
    BAKERY_NOTIFY_EMAIL = 'cinderellacakes@gmail.com'

    # --- WhatsApp ---
    BAKERY_WHATSAPP_NUMBER = '256781470984'
    SERVER_BASE_URL = 'http://localhost:5000'

class DevelopmentConfig(Config):
    DEBUG = True
    # Default to MySQL, fallback to SQLite if needed
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'mysql+pymysql://root:@localhost/cinderella_cakes_db'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    DEBUG = False
    # In production, must provide a real database URL via env
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/cinderella_cakes_db'

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
