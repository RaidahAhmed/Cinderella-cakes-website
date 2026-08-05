from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.rbac import User, Role
from app.utils.decorators import role_required

# Manages admin user accounts and their assigned roles.
user_bp = Blueprint('users', __name__, url_prefix='/api/users')

# Retrieves a list of all registered admin users.
@user_bp.route('/', methods=['GET'])
@role_required('super_admin')
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

# Creates a new admin account with a specified password and role.
@user_bp.route('/', methods=['POST'])
@role_required('super_admin')
def create_user():
    data = request.json
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
        
    user = User(
        email=data['email'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        is_active=data.get('is_active', True)
    )
    user.set_password(data['password'])
    
    if 'role_id' in data:
        user.role_id = data['role_id']
        
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

# Updates an admin's profile, role, or resets their password.
@user_bp.route('/<int:id>', methods=['PUT'])
@role_required('super_admin')
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.json
    
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        user.email = data['email']
        
    for key in ['first_name', 'last_name', 'is_active', 'role_id']:
        if key in data:
            setattr(user, key, data[key])
            
    if 'password' in data and data['password']:
        user.set_password(data['password'])
        
    db.session.commit()
    return jsonify(user.to_dict())

# Removes an admin user from the system.
@user_bp.route('/<int:id>', methods=['DELETE'])
@role_required('super_admin')
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
