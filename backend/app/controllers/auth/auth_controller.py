from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.rbac import User
from app.status_codes import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
)

# Groups all login and user session routes under a common URL path.
auth = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Processes login requests by verifying the user's email and password.
@auth.route('/login', methods=['POST'])
def login():
    # Safely handle the login attempt, catching any unexpected system errors.
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'message': 'Email and password required'}), HTTP_400_BAD_REQUEST

        user = User.query.filter_by(email=data.get('email')).first()

        if not user or not user.check_password(data.get('password')):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), HTTP_401_UNAUTHORIZED

        if not user.is_active:
            return jsonify({'success': False, 'message': 'Account is disabled'}), HTTP_401_UNAUTHORIZED

        # Gathers the user's roles and permissions to embed inside their secure login token.
        roles = [user.role.name] if user.role else []
        permissions = [p.name for p in user.role.permissions] if user.role else []
        additional_claims = {
            "roles": roles,
            "permissions": permissions
        }

        # Creates secure digital keys (tokens) that confirm the user is logged in for a period of time.
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), HTTP_200_OK

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), HTTP_500_INTERNAL_SERVER_ERROR


# Provides a new access token to keep the user logged in without requiring a password again.
@auth.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # Ensures only users with a valid refresh token can access this.
def refresh():
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    
    if not user or not user.is_active:
        return jsonify({'success': False, 'message': 'Invalid user'}), HTTP_401_UNAUTHORIZED
        
    roles = [user.role.name] if user.role else []
    permissions = [p.name for p in user.role.permissions] if user.role else []
    additional_claims = {
        "roles": roles,
        "permissions": permissions
    }
    
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    return jsonify({
        'success': True,
        'access_token': access_token
    }), HTTP_200_OK


# Retrieves the profile details of the currently logged-in user.
@auth.route('/me', methods=['GET'])
@jwt_required() # Ensures only currently logged-in users can access this.
def get_current_user():
    identity = get_jwt_identity()
    user = User.query.get(int(identity))
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), HTTP_404_NOT_FOUND
        
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), HTTP_200_OK
