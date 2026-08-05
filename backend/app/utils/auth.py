from functools import wraps
from flask import request, jsonify, current_app
import jwt
from app.models.user import AdminUser
from app.status_codes import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Extract token from the Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing', 'success': False}), HTTP_401_UNAUTHORIZED

        try:
            # Decode token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            # Fetch user
            current_user = AdminUser.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'Invalid token, user not found', 'success': False}), HTTP_401_UNAUTHORIZED
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired', 'success': False}), HTTP_401_UNAUTHORIZED
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid', 'success': False}), HTTP_401_UNAUTHORIZED
        except Exception as e:
            return jsonify({'message': str(e), 'success': False}), HTTP_500_INTERNAL_SERVER_ERROR

        return f(current_user, *args, **kwargs)

    return decorated
