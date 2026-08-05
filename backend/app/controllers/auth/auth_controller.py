from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.user import AdminUser
from app.utils.auth import token_required
from app.status_codes import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR,
)

auth = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'success': False, 'message': 'Username and password required'}), HTTP_400_BAD_REQUEST

        user = AdminUser.query.filter_by(username=data.get('username')).first()

        if not user or not user.check_password(data.get('password')):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), HTTP_401_UNAUTHORIZED

        # Generate JWT token
        token = jwt.encode(
            {
                'user_id': user.id,
                'exp': datetime.now(timezone.utc) + timedelta(hours=24)
            },
            current_app.config['SECRET_KEY'],
            algorithm="HS256"
        )

        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict()
        }), HTTP_200_OK

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), HTTP_500_INTERNAL_SERVER_ERROR


@auth.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), HTTP_200_OK
