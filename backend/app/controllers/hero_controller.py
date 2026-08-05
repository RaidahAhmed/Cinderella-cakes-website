from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.hero import HeroSection
from app.models.page import Page
from app.utils.decorators import permission_required

# Manages the large banner (hero) sections typically found at the top of pages.
hero_bp = Blueprint('heroes', __name__, url_prefix='/api/heroes')

# Creates a new hero banner for a page. Ensures only one hero exists per page.
@hero_bp.route('/', methods=['POST'])
@permission_required('content_write')
def create_hero():
    data = request.json
    page_id = data.get('page_id')
    
    # Check if page already has a hero
    existing = HeroSection.query.filter_by(page_id=page_id).first()
    if existing:
        return jsonify({'message': 'Page already has a hero section'}), 400
        
    hero = HeroSection(
        page_id=page_id,
        eyebrow=data.get('eyebrow'),
        heading=data['heading'],
        heading_accent=data.get('heading_accent'),
        subheading=data.get('subheading'),
        primary_image_url=data.get('primary_image_url'),
        secondary_image_url=data.get('secondary_image_url'),
        primary_button_text=data.get('primary_button_text'),
        primary_button_url=data.get('primary_button_url'),
        secondary_button_text=data.get('secondary_button_text'),
        secondary_button_url=data.get('secondary_button_url')
    )
    db.session.add(hero)
    db.session.commit()
    return jsonify(hero.to_dict()), 201

# Updates the text, images, or buttons in an existing hero banner.
@hero_bp.route('/<int:id>', methods=['PUT'])
@permission_required('content_write')
def update_hero(id):
    hero = HeroSection.query.get_or_404(id)
    data = request.json
    
    for key in ['eyebrow', 'heading', 'heading_accent', 'subheading', 'primary_image_url', 'secondary_image_url', 'primary_button_text', 'primary_button_url', 'secondary_button_text', 'secondary_button_url']:
        if key in data:
            setattr(hero, key, data[key])
            
    db.session.commit()
    return jsonify(hero.to_dict())

# Deletes a hero banner from a page.
@hero_bp.route('/<int:id>', methods=['DELETE'])
@permission_required('content_write')
def delete_hero(id):
    hero = HeroSection.query.get_or_404(id)
    db.session.delete(hero)
    db.session.commit()
    return '', 204
