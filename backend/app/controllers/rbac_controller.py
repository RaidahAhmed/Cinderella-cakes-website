from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.rbac import Role, Permission
from app.utils.decorators import role_required

# Manages Roles and Permissions to control who can access different admin features.
rbac_bp = Blueprint('rbac', __name__, url_prefix='/api/rbac')

# Retrieves all available user roles in the system.
@rbac_bp.route('/roles', methods=['GET'])
@role_required('super_admin')
def get_roles():
    roles = Role.query.all()
    return jsonify([role.to_dict() for role in roles])

# Creates a new role and assigns specific permissions to it.
@rbac_bp.route('/roles', methods=['POST'])
@role_required('super_admin')
def create_role():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'message': 'Request body must be valid JSON with Content-Type: application/json'}), 400
    role = Role(
        name=data['name'],
        description=data.get('description')
    )
    
    if 'permissions' in data:
        perms = Permission.query.filter(Permission.name.in_(data['permissions'])).all()
        role.permissions = perms
        
    db.session.add(role)
    db.session.commit()
    return jsonify(role.to_dict()), 201

# Modifies an existing role's name, description, or assigned permissions.
@rbac_bp.route('/roles/<int:id>', methods=['PUT'])
@role_required('super_admin')
def update_role(id):
    role = Role.query.get_or_404(id)
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'message': 'Request body must be valid JSON with Content-Type: application/json'}), 400
    
    if 'name' in data:
        role.name = data['name']
    if 'description' in data:
        role.description = data['description']
        
    if 'permissions' in data:
        perms = Permission.query.filter(Permission.name.in_(data['permissions'])).all()
        role.permissions = perms
        
    db.session.commit()
    return jsonify(role.to_dict())

# Retrieves all possible permissions that can be assigned to roles.
@rbac_bp.route('/permissions', methods=['GET'])
@role_required('super_admin')
def get_permissions():
    perms = Permission.query.all()
    return jsonify([perm.to_dict() for perm in perms])
