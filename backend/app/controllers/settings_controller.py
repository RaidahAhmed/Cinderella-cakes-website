from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.settings import SiteSettings
from app.utils.decorators import role_required

# Manages global configuration for the website like branding and contact info.
settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# Retrieves the current site settings, creating default ones if none exist.
@settings_bp.route('/', methods=['GET'])
@role_required('admin')
def get_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return jsonify(settings.to_dict())

# Updates the global site settings (e.g., changing the store phone number).
@settings_bp.route('/', methods=['PUT'])
@role_required('admin')
def update_settings():
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        
    data = request.json
    for key in ['site_name', 'logo_url', 'favicon_url', 'contact_email', 'contact_phone', 'address', 'primary_color', 'secondary_color']:
        if key in data:
            setattr(settings, key, data[key])
            
    db.session.commit()
    return jsonify(settings.to_dict())
