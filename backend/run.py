import os
from app import create_app

env_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(env_name)

if __name__ == '__main__':
    # In production, you would run this with gunicorn or similar
    app.run(debug=(env_name == 'development'), host='0.0.0.0')
