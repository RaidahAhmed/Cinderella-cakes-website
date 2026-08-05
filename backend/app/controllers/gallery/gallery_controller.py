import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.gallery import GalleryItem
from app.utils.auth import token_required
from app.status_codes import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
)

gallery = Blueprint('gallery', __name__, url_prefix='/api/v1/gallery')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_IMAGE_EXTENSIONS

@gallery.route('', methods=['GET'])
def get_all_gallery_items():
    try:
        items = GalleryItem.query.order_by(GalleryItem.created_at.desc()).all()
        return jsonify({
            "success": True,
            "total": len(items),
            "items": [item.to_dict() for item in items]
        }), HTTP_200_OK
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), HTTP_500_INTERNAL_SERVER_ERROR

@gallery.route('/create', methods=['POST'])
@token_required
def create_gallery_item(current_user):
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')

        if not title:
            return jsonify({"success": False, "message": "Title is required"}), HTTP_400_BAD_REQUEST

        if 'image' not in request.files:
            return jsonify({"success": False, "message": "Image is required"}), HTTP_400_BAD_REQUEST

        file = request.files['image']
        if file.filename == '':
            return jsonify({"success": False, "message": "No selected file"}), HTTP_400_BAD_REQUEST

        if not _allowed_file(file.filename):
            return jsonify({"success": False, "message": "Invalid file type"}), HTTP_400_BAD_REQUEST

        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"gallery_{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file.save(os.path.join(upload_dir, filename))

        new_item = GalleryItem(
            title=title.strip(),
            description=description.strip() if description else None,
            image_url=filename,
            category=category.strip() if category else None
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

@gallery.route('/<int:item_id>', methods=['DELETE'])
@token_required
def delete_gallery_item(current_user, item_id):
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
