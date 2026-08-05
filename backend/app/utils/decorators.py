from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.models.rbac import User

def permission_required(permission_name):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            
            # Allow super_admin to do everything
            roles = claims.get("roles", [])
            if "super_admin" in roles:
                return fn(*args, **kwargs)
                
            # Check for specific permission
            permissions = claims.get("permissions", [])
            if permission_name not in permissions:
                return jsonify({"message": f"Missing permission: {permission_name}"}), 403
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def role_required(role_name):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            
            roles = claims.get("roles", [])
            if "super_admin" in roles or role_name in roles:
                return fn(*args, **kwargs)
                
            return jsonify({"message": f"Missing role: {role_name}"}), 403
        return decorator
    return wrapper
