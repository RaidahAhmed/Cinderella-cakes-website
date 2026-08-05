from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.footer import FooterColumn, FooterLink, SocialLink
from app.utils.decorators import permission_required

# Manages the structure and links of the website footer.
footer_bp = Blueprint('footer_admin', __name__, url_prefix='/api/footer_admin')

# Creates a new column group in the footer layout.
@footer_bp.route('/columns', methods=['POST'])
@permission_required('content_write')
def create_column():
    data = request.json
    column = FooterColumn(
        title=data['title'],
        order=data.get('order', 0)
    )
    db.session.add(column)
    db.session.commit()
    return jsonify(column.to_dict()), 201

# Updates the title or order of a footer column.
@footer_bp.route('/columns/<int:id>', methods=['PUT'])
@permission_required('content_write')
def update_column(id):
    column = FooterColumn.query.get_or_404(id)
    data = request.json
    if 'title' in data: column.title = data['title']
    if 'order' in data: column.order = data['order']
    db.session.commit()
    return jsonify(column.to_dict())

# Removes a footer column and all its associated links.
@footer_bp.route('/columns/<int:id>', methods=['DELETE'])
@permission_required('content_write')
def delete_column(id):
    column = FooterColumn.query.get_or_404(id)
    db.session.delete(column)
    db.session.commit()
    return '', 204

# Adds a new clickable link into a specific footer column.
@footer_bp.route('/links', methods=['POST'])
@permission_required('content_write')
def create_link():
    data = request.json
    link = FooterLink(
        column_id=data['column_id'],
        label=data['label'],
        url=data['url'],
        order=data.get('order', 0),
        is_external=data.get('is_external', False)
    )
    db.session.add(link)
    db.session.commit()
    return jsonify(link.to_dict()), 201

# Updates a footer link's text, URL, or ordering.
@footer_bp.route('/links/<int:id>', methods=['PUT'])
@permission_required('content_write')
def update_link(id):
    link = FooterLink.query.get_or_404(id)
    data = request.json
    for key in ['label', 'url', 'order', 'is_external']:
        if key in data:
            setattr(link, key, data[key])
    db.session.commit()
    return jsonify(link.to_dict())

# Removes a specific link from the footer.
@footer_bp.route('/links/<int:id>', methods=['DELETE'])
@permission_required('content_write')
def delete_link(id):
    link = FooterLink.query.get_or_404(id)
    db.session.delete(link)
    db.session.commit()
    return '', 204
