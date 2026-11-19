import os
import uuid
from pathlib import Path

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.blog import BlogPost, slugify
from app.utils.decorators import permission_required
from app.status_codes import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
)

# Public reading routes plus admin routes (under /admin) for writing articles.
blog_bp = Blueprint('blog', __name__, url_prefix='/api/v1/blog')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_IMAGE_EXTENSIONS


def _blog_dir():
    folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog')
    if os.path.islink(folder):
        raise RuntimeError('Blog upload directory must not be a symlink.')
    os.makedirs(folder, exist_ok=True)
    return folder


def _save_cover(file):
    """Stores an uploaded cover image and returns the value kept in the database."""
    filename = f"blog_{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    file.save(os.path.join(_blog_dir(), filename))
    return f'blog/{filename}'


def _delete_cover_file(stored):
    """Best-effort removal of an old cover image; never raises."""
    try:
        if not stored or not stored.startswith('blog/'):
            return
        root = Path(_blog_dir()).resolve()
        target = (root / stored[len('blog/'):]).resolve()
        if target.is_relative_to(root) and target.is_file():
            target.unlink()
    except Exception:
        current_app.logger.warning('Could not remove old blog cover %s', stored)


def _unique_slug(title, ignore_id=None):
    base = slugify(title)
    slug = base
    counter = 2
    while True:
        existing = BlogPost.query.filter(BlogPost.slug == slug).first()
        if existing is None or existing.id == ignore_id:
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def _as_bool(value, default):
    if value is None:
        return default
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _fail(message, status):
    return jsonify({"success": False, "message": message}), status


def _server_error(error):
    db.session.rollback()
    current_app.logger.exception('Blog request failed: %s', error)
    return _fail('Something went wrong on our side. Please try again.', HTTP_500_INTERNAL_SERVER_ERROR)


# ========================
# PUBLIC
# ========================

# Lists published articles, newest first. Optional ?limit=<n>.
@blog_bp.route('', methods=['GET'])
def list_posts():
    try:
        query = BlogPost.query.filter(BlogPost.published.is_(True))
        query = query.order_by(BlogPost.created_at.desc(), BlogPost.id.desc())

        limit = request.args.get('limit', type=int)
        if limit and limit > 0:
            query = query.limit(min(limit, 50))

        posts = query.all()
        return jsonify({
            "success": True,
            "total": len(posts),
            "posts": [post.to_dict() for post in posts],
        }), HTTP_200_OK
    except Exception as error:
        return _server_error(error)


# One published article plus a few other recent ones to keep readers browsing.
@blog_bp.route('/<string:slug>', methods=['GET'])
def get_post(slug):
    try:
        post = BlogPost.query.filter(BlogPost.slug == slug, BlogPost.published.is_(True)).first()
        if not post:
            return _fail('Article not found', HTTP_404_NOT_FOUND)

        more = (
            BlogPost.query
            .filter(BlogPost.published.is_(True), BlogPost.id != post.id)
            .order_by(BlogPost.created_at.desc(), BlogPost.id.desc())
            .limit(3)
            .all()
        )
        return jsonify({
            "success": True,
            "post": post.to_dict(include_content=True),
            "more": [item.to_dict() for item in more],
        }), HTTP_200_OK
    except Exception as error:
        return _server_error(error)


# ========================
# ADMIN
# ========================

# Every article, drafts included, with full text so the editor can open it.
@blog_bp.route('/admin/all', methods=['GET'])
@permission_required('content_write')
def admin_list_posts():
    try:
        posts = BlogPost.query.order_by(BlogPost.created_at.desc(), BlogPost.id.desc()).all()
        return jsonify({
            "success": True,
            "total": len(posts),
            "posts": [post.to_dict(include_content=True) for post in posts],
        }), HTTP_200_OK
    except Exception as error:
        return _server_error(error)


# Creates an article. Sent as multipart form data so a cover image can come along.
@blog_bp.route('/admin', methods=['POST'])
@permission_required('content_write')
def admin_create_post():
    try:
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        if not title:
            return _fail('Please give the article a title.', HTTP_400_BAD_REQUEST)
        if not content:
            return _fail('Please write something in the article body.', HTTP_400_BAD_REQUEST)

        cover_value = None
        file = request.files.get('cover')
        if file and file.filename:
            if not _allowed_file(file.filename):
                return _fail('Cover image must be a PNG, JPG or WEBP file.', HTTP_400_BAD_REQUEST)
            cover_value = _save_cover(file)

        post = BlogPost(
            title=title[:180],
            slug=_unique_slug(title),
            category=((request.form.get('category') or '').strip() or 'Cake notes')[:60],
            excerpt=((request.form.get('excerpt') or '').strip() or None),
            content=content,
            cover_image=cover_value,
            published=_as_bool(request.form.get('published'), True),
        )
        if post.excerpt:
            post.excerpt = post.excerpt[:400]

        db.session.add(post)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Article saved",
            "post": post.to_dict(include_content=True),
        }), HTTP_201_CREATED
    except Exception as error:
        return _server_error(error)


# Updates any of the article fields. Only fields that are sent are changed.
@blog_bp.route('/admin/<int:post_id>', methods=['PUT'])
@permission_required('content_write')
def admin_update_post(post_id):
    try:
        post = db.session.get(BlogPost, post_id)
        if not post:
            return _fail('Article not found', HTTP_404_NOT_FOUND)

        form = request.form

        if 'title' in form:
            title = (form.get('title') or '').strip()
            if not title:
                return _fail('The title cannot be empty.', HTTP_400_BAD_REQUEST)
            post.title = title[:180]

        if 'content' in form:
            content = (form.get('content') or '').strip()
            if not content:
                return _fail('The article body cannot be empty.', HTTP_400_BAD_REQUEST)
            post.content = content

        if 'category' in form:
            post.category = ((form.get('category') or '').strip() or 'Cake notes')[:60]

        if 'excerpt' in form:
            post.excerpt = ((form.get('excerpt') or '').strip() or None)
            if post.excerpt:
                post.excerpt = post.excerpt[:400]

        if 'published' in form:
            post.published = _as_bool(form.get('published'), post.published)

        old_cover = post.cover_image
        file = request.files.get('cover')
        if file and file.filename:
            if not _allowed_file(file.filename):
                return _fail('Cover image must be a PNG, JPG or WEBP file.', HTTP_400_BAD_REQUEST)
            post.cover_image = _save_cover(file)
        elif _as_bool(form.get('remove_cover'), False):
            post.cover_image = None

        db.session.commit()

        if old_cover and old_cover != post.cover_image:
            _delete_cover_file(old_cover)

        return jsonify({
            "success": True,
            "message": "Article updated",
            "post": post.to_dict(include_content=True),
        }), HTTP_200_OK
    except Exception as error:
        return _server_error(error)


# Permanently removes an article (and its cover image).
@blog_bp.route('/admin/<int:post_id>', methods=['DELETE'])
@permission_required('content_write')
def admin_delete_post(post_id):
    try:
        post = db.session.get(BlogPost, post_id)
        if not post:
            return _fail('Article not found', HTTP_404_NOT_FOUND)

        cover = post.cover_image
        db.session.delete(post)
        db.session.commit()
        _delete_cover_file(cover)

        return jsonify({"success": True, "message": "Article deleted"}), HTTP_200_OK
    except Exception as error:
        return _server_error(error)
