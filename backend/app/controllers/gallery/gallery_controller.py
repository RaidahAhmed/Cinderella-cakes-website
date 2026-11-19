import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.gallery import GalleryItem, CATEGORY_CHOICES, CATEGORY_LABELS
from app.utils.decorators import permission_required
from app.status_codes import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
)

# Group for all gallery-related endpoints.
gallery = Blueprint('gallery', __name__, url_prefix='/api/v1/gallery')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Checks if the uploaded file has a permitted image extension.
def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_IMAGE_EXTENSIONS

# Normalises a category value and validates it against CATEGORY_CHOICES.
# Returns (category, error). An empty value falls back to 'other'.
def _clean_category(raw_category):
    category = (raw_category or '').strip().lower()

    if not category:
        return 'other', None

    if category not in CATEGORY_CHOICES:
        return None, f"Category must be one of: {', '.join(CATEGORY_CHOICES)}."

    return category, None

# Retrieves all items in the gallery, sorted by newest first.
# Optional ?category=<key> narrows the result to a single category.
@gallery.route('', methods=['GET'])
def get_all_gallery_items():
    try:
        query = GalleryItem.query

        category = (request.args.get('category') or '').strip().lower()
        if category and category not in ('all', 'any'):
            if category not in CATEGORY_CHOICES:
                return jsonify({
                    "success": False,
                    "message": f"Unknown category '{category}'"
                }), HTTP_400_BAD_REQUEST
            query = query.filter(GalleryItem.category == category)

        items = query.order_by(GalleryItem.created_at.desc(), GalleryItem.id.desc()).all()

        # to_dict() already prefixes image_url with the uploads path, so the
        # response is used as-is by the frontend (never prefix it twice).
        return jsonify({
            "success": True,
            "total": len(items),
            "items": [item.to_dict() for item in items]
        }), HTTP_200_OK
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), HTTP_500_INTERNAL_SERVER_ERROR

# Lists every gallery category with the number of items it holds.
@gallery.route('/categories', methods=['GET'])
def get_gallery_categories():
    try:
        rows = db.session.query(
            GalleryItem.category, func.count(GalleryItem.id)
        ).group_by(GalleryItem.category).all()

        counts = {}
        for category, count in rows:
            key = (category or 'other').strip().lower() or 'other'
            counts[key] = counts.get(key, 0) + count

        categories = [
            {
                "key": key,
                "label": CATEGORY_LABELS.get(key, key.replace('_', ' ').title()),
                "count": counts.get(key, 0),
            }
            for key in CATEGORY_CHOICES
        ]

        # Surface any categories stored in the DB that are not in the canonical list.
        for key, count in counts.items():
            if key not in CATEGORY_CHOICES:
                categories.append({
                    "key": key,
                    "label": key.replace('_', ' ').title(),
                    "count": count,
                })

        return jsonify({
            "success": True,
            "total": sum(counts.values()),
            "categories": categories,
        }), HTTP_200_OK
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), HTTP_500_INTERNAL_SERVER_ERROR

# Returns one cake with its story, plus other cakes from the same category
# ("More like this"). Used by the shareable /gallery/<id> page.
RELATED_LIMIT = 6

@gallery.route('/<int:item_id>', methods=['GET'])
def get_gallery_item(item_id):
    try:
        item = db.session.get(GalleryItem, item_id)
        if not item:
            return jsonify({"success": False, "message": "Gallery item not found"}), HTTP_404_NOT_FOUND

        category = (item.category or 'other').strip().lower() or 'other'
        related = (
            GalleryItem.query
            .filter(GalleryItem.category == item.category, GalleryItem.id != item.id)
            .order_by(GalleryItem.created_at.desc(), GalleryItem.id.desc())
            .limit(RELATED_LIMIT)
            .all()
        )

        return jsonify({
            "success": True,
            "item": item.to_dict(),
            "category_label": CATEGORY_LABELS.get(category, category.replace('_', ' ').title()),
            "related": [entry.to_dict() for entry in related],
        }), HTTP_200_OK
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), HTTP_500_INTERNAL_SERVER_ERROR

# Uploads and saves a new image to the gallery. Requires content write permission.
@gallery.route('/create', methods=['POST'])
@permission_required('content_write')
def create_gallery_item():
    try:
        title = request.form.get('title')
        description = request.form.get('description')

        category, category_error = _clean_category(request.form.get('category'))
        if category_error:
            return jsonify({"success": False, "message": category_error}), HTTP_400_BAD_REQUEST

        if not title:
            return jsonify({"success": False, "message": "Title is required"}), HTTP_400_BAD_REQUEST

        if 'image' not in request.files:
            return jsonify({"success": False, "message": "Image is required"}), HTTP_400_BAD_REQUEST

        file = request.files['image']
        if file.filename == '':
            return jsonify({"success": False, "message": "No selected file"}), HTTP_400_BAD_REQUEST

        if not _allowed_file(file.filename):
            return jsonify({"success": False, "message": "Invalid file type"}), HTTP_400_BAD_REQUEST

        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'gallery')
        if os.path.islink(upload_dir):
            raise RuntimeError('Gallery upload directory must not be a symlink.')
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"gallery_{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file.save(os.path.join(upload_dir, filename))

        # image_url stores only the file name; to_dict() adds the static prefix.
        new_item = GalleryItem(
            title=title.strip(),
            description=description.strip() if description else None,
            image_url=f'gallery/{filename}',
            category=category
        )

        db.session.add(new_item)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Gallery item added successfully",
            "item": new_item.to_dict()
        }), HTTP_201_CREATED

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), HTTP_500_INTERNAL_SERVER_ERROR

# Updates the editable details of an existing gallery item.
@gallery.route('/<int:item_id>', methods=['PUT'])
@permission_required('content_write')
def update_gallery_item(item_id):
    try:
        item = GalleryItem.query.get(item_id)
        if not item:
            return jsonify({"success": False, "message": "Gallery item not found"}), HTTP_404_NOT_FOUND

        data = request.get_json(silent=True)
        if data is None:
            return jsonify({
                "success": False,
                "message": "Request body must be valid JSON with Content-Type: application/json"
            }), HTTP_400_BAD_REQUEST

        if 'title' in data:
            title = (data.get('title') or '').strip()
            if not title:
                return jsonify({"success": False, "message": "Title cannot be empty"}), HTTP_400_BAD_REQUEST
            item.title = title

        if 'description' in data:
            description = (data.get('description') or '').strip()
            item.description = description or None

        if 'category' in data:
            category, category_error = _clean_category(data.get('category'))
            if category_error:
                return jsonify({"success": False, "message": category_error}), HTTP_400_BAD_REQUEST
            item.category = category

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Gallery item updated successfully",
            "item": item.to_dict()
        }), HTTP_200_OK

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), HTTP_500_INTERNAL_SERVER_ERROR

# Removes a specific item from the gallery and database.
@gallery.route('/<int:item_id>', methods=['DELETE'])
@permission_required('content_write')
def delete_gallery_item(item_id):
    try:
        item = GalleryItem.query.get(item_id)
        if not item:
            return jsonify({"success": False, "message": "Gallery item not found"}), HTTP_404_NOT_FOUND

        db.session.delete(item)
        db.session.commit()

        return jsonify({"success": True, "message": "Gallery item deleted successfully"}), HTTP_200_OK

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), HTTP_500_INTERNAL_SERVER_ERROR
