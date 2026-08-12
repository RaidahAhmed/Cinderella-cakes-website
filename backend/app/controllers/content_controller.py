from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.content import ContentSection, ContentBlock
from app.utils.decorators import permission_required

# Manages the dynamic content sections and blocks for pages.
content_bp = Blueprint('content', __name__, url_prefix='/api/content')

# Creates a new layout section on a page (e.g. a grid or banner).
@content_bp.route('/sections', methods=['POST'])
@permission_required('content_write')
def create_section():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'message': 'Request body must be valid JSON with Content-Type: application/json'}), 400
    section = ContentSection(
        page_id=data['page_id'],
        section_type=data['section_type'],
        order=data.get('order', 0),
        eyebrow=data.get('eyebrow'),
        heading=data.get('heading'),
        subheading=data.get('subheading')
    )
    db.session.add(section)
    db.session.commit()
    return jsonify(section.to_dict()), 201

# Updates the properties of an existing page section.
@content_bp.route('/sections/<int:id>', methods=['PUT'])
@permission_required('content_write')
def update_section(id):
    section = ContentSection.query.get_or_404(id)
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'message': 'Request body must be valid JSON with Content-Type: application/json'}), 400
    for key in ['section_type', 'order', 'eyebrow', 'heading', 'subheading']:
        if key in data:
            setattr(section, key, data[key])
    db.session.commit()
    return jsonify(section.to_dict())

# Removes a section from a page.
@content_bp.route('/sections/<int:id>', methods=['DELETE'])
@permission_required('content_write')
def delete_section(id):
    section = ContentSection.query.get_or_404(id)
    db.session.delete(section)
    db.session.commit()
    return '', 204

# Adds a new content block (text/image) inside a specific section.
@content_bp.route('/blocks', methods=['POST'])
@permission_required('content_write')
def create_block():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'message': 'Request body must be valid JSON with Content-Type: application/json'}), 400
    block = ContentBlock(
        section_id=data['section_id'],
        order=data.get('order', 0),
        title=data.get('title'),
        text=data.get('text'),
        icon_or_image_url=data.get('icon_or_image_url'),
        link_url=data.get('link_url'),
        link_text=data.get('link_text')
    )
    db.session.add(block)
    db.session.commit()
    return jsonify(block.to_dict()), 201

# Updates the content of an existing block.
@content_bp.route('/blocks/<int:id>', methods=['PUT'])
@permission_required('content_write')
def update_block(id):
    block = ContentBlock.query.get_or_404(id)
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'message': 'Request body must be valid JSON with Content-Type: application/json'}), 400
    for key in ['order', 'title', 'text', 'icon_or_image_url', 'link_url', 'link_text']:
        if key in data:
            setattr(block, key, data[key])
    db.session.commit()
    return jsonify(block.to_dict())

# Removes a content block from a section.
@content_bp.route('/blocks/<int:id>', methods=['DELETE'])
@permission_required('content_write')
def delete_block(id):
    block = ContentBlock.query.get_or_404(id)
    db.session.delete(block)
    db.session.commit()
    return '', 204
