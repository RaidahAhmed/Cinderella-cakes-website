from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.navigation import MenuItem
from app.utils.decorators import permission_required

# Manages the links that appear in the website's main navigation menu.
navigation_bp = Blueprint('navigation', __name__, url_prefix='/api/navigation')

# Retrieves all active menu items for the website.
@navigation_bp.route('/', methods=['GET'])
@permission_required('content_read')
def get_items():
    items = MenuItem.query.order_by(MenuItem.order).all()
    return jsonify([item.to_dict() for item in items])

# Adds a new link or button to the navigation menu.
@navigation_bp.route('/', methods=['POST'])
@permission_required('content_write')
def create_item():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'message': 'Request body must be valid JSON with Content-Type: application/json'}), 400
    item = MenuItem(
        label=data['label'],
        url=data['url'],
        order=data.get('order', 0),
        is_active=data.get('is_active', True),
        is_button=data.get('is_button', False)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

# Modifies an existing navigation link.
@navigation_bp.route('/<int:id>', methods=['PUT'])
@permission_required('content_write')
def update_item(id):
    item = MenuItem.query.get_or_404(id)
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'message': 'Request body must be valid JSON with Content-Type: application/json'}), 400
    for key in ['label', 'url', 'order', 'is_active', 'is_button']:
        if key in data:
            setattr(item, key, data[key])
    db.session.commit()
    return jsonify(item.to_dict())

# Removes a link from the navigation menu.
@navigation_bp.route('/<int:id>', methods=['DELETE'])
@permission_required('content_write')
def delete_item(id):
    item = MenuItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return '', 204
