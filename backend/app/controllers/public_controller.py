from flask import Blueprint, jsonify
from app.models.page import Page
from app.models.navigation import MenuItem
from app.models.footer import FooterColumn
from app.models.settings import SiteSettings
from app.models.gallery import GalleryItem

# Provides read-only access to published content for regular website visitors.
public_bp = Blueprint('public', __name__, url_prefix='/api/public')

# Retrieves a specific page by its URL slug if it is published.
@public_bp.route('/pages/<slug>', methods=['GET'])
def get_page(slug):
    page = Page.query.filter_by(slug=slug, is_published=True).first()
    if not page:
        return jsonify({'message': 'Page not found'}), 404
    return jsonify(page.to_dict())

# Returns all active links for the main navigation menu.
@public_bp.route('/navigation', methods=['GET'])
def get_navigation():
    items = MenuItem.query.filter_by(is_active=True).order_by(MenuItem.order).all()
    return jsonify([item.to_dict() for item in items])

# Retrieves the column and link structure for the website footer.
@public_bp.route('/footer', methods=['GET'])
def get_footer():
    columns = FooterColumn.query.order_by(FooterColumn.order).all()
    return jsonify([col.to_dict() for col in columns])

# Fetches global site settings like the store name and contact details.
@public_bp.route('/settings', methods=['GET'])
def get_settings():
    settings = SiteSettings.query.first()
    if not settings:
        return jsonify({})
    return jsonify(settings.to_dict())

# Returns all images approved for the public gallery.
@public_bp.route('/gallery', methods=['GET'])
def get_gallery():
    items = GalleryItem.query.order_by(GalleryItem.created_at.desc()).all()
    return jsonify([item.to_dict() for item in items])
