#Contains configuration settings for the Flask application, including database connection details, file upload settings, and email/WhatsApp notification settings.

class Config: # Creates a configuration class that stores various settings for the Flask application.
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/cinderella_cakes_db' #where the database is located and how to connect to it. In this case, it's a MySQL database running on localhost with the username root and no password, and the database name is cinderella_cakes_db.
    SQLALCHEMY_TRACK_MODIFICATIONS = False #This feature is turned off to save system resources, as it is not needed for this application.

    # Where uploaded inspiration photos are saved on disk.
    UPLOAD_FOLDER = 'app/static/uploads/inspiration'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

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

    # Base URL of the running Flask server - used to build full URLs for
    # uploaded images so they can be included as clickable links in WhatsApp messages.
    SERVER_BASE_URL = 'http://localhost:5000'
