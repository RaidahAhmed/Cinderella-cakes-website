from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.page import Page
from app.utils.decorators import permission_required

# Manages the creation and configuration of web pages (e.g. Home, About).
page_bp = Blueprint('pages', __name__, url_prefix='/api/pages')

# Retrieves a list of all pages configured in the system.
@page_bp.route('/', methods=['GET'])
@permission_required('content_read')
def get_pages():
    pages = Page.query.all()
    return jsonify([page.to_dict() for page in pages])

# Gets the configuration details of a specific page.
@page_bp.route('/<int:id>', methods=['GET'])
@permission_required('content_read')
def get_page(id):
    page = Page.query.get_or_404(id)
    return jsonify(page.to_dict())

# Creates a new web page.
@page_bp.route('/', methods=['POST'])
@permission_required('content_write')
def create_page():
    data = request.json
    page = Page(
        slug=data['slug'],
        title=data['title'],
        meta_description=data.get('meta_description'),
        is_published=data.get('is_published', True)
    )
    db.session.add(page)
    db.session.commit()
    return jsonify(page.to_dict()), 201

# Updates a page's URL slug, title, or publication status.
@page_bp.route('/<int:id>', methods=['PUT'])
@permission_required('content_write')
def update_page(id):
    page = Page.query.get_or_404(id)
    data = request.json
    if 'slug' in data: page.slug = data['slug']
    if 'title' in data: page.title = data['title']
    if 'meta_description' in data: page.meta_description = data['meta_description']
    if 'is_published' in data: page.is_published = data['is_published']
    
    db.session.commit()
    return jsonify(page.to_dict())

# Permanently deletes a page.
@page_bp.route('/<int:id>', methods=['DELETE'])
@permission_required('content_write')
def delete_page(id):
    page = Page.query.get_or_404(id)
    db.session.delete(page)
    db.session.commit()
    return '', 204
