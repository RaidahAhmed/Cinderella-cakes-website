from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func

from app.extensions import db
from app.models.review import Review
from app.utils.decorators import permission_required
from app.status_codes import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
)

# Customer testimonials: public visitors read approved reviews and submit new
# ones, admins moderate them from the dashboard.
review_bp = Blueprint('reviews', __name__, url_prefix='/api/v1')

NAME_MAX_LENGTH = 60
TEXT_MAX_LENGTH = 800


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

# Returns approved reviews (newest first) together with the rating summary
# used to render the star average on the website.
@review_bp.route('/reviews', methods=['GET'])
def get_approved_reviews():
    try:
        approved = Review.query.filter_by(is_approved=True)

        reviews = approved.order_by(Review.created_at.desc()).all()
        average = db.session.query(func.avg(Review.rating)).filter(
            Review.is_approved.is_(True)
        ).scalar()

        return jsonify({
            'success': True,
            'total': len(reviews),
            'average_rating': round(float(average), 1) if average else 0,
            'reviews': [review.to_dict() for review in reviews],
        }), HTTP_200_OK

    except Exception:
        db.session.rollback()
        current_app.logger.exception('Review lookup failed')
        return jsonify({'success': False, 'message': 'Reviews are temporarily unavailable. Please try again.'}), HTTP_500_INTERNAL_SERVER_ERROR


# Accepts a new testimonial from a visitor. It stays invisible until an admin
# approves it.
@review_bp.route('/reviews', methods=['POST'])
def create_review():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({
                'success': False,
                'message': 'Request body must be a JSON object.'
            }), HTTP_400_BAD_REQUEST

        name_raw = data.get('customer_name')
        text_raw = data.get('review_text')
        customer_name = name_raw.strip() if isinstance(name_raw, str) else ''
        review_text = text_raw.strip() if isinstance(text_raw, str) else ''
        rating_raw = data.get('rating')

        errors = {}

        if not customer_name:
            errors['customer_name'] = 'Your name is required.'
        elif len(customer_name) > NAME_MAX_LENGTH:
            errors['customer_name'] = f'Name must be {NAME_MAX_LENGTH} characters or fewer.'

        rating = None
        if type(rating_raw) is int:
            rating = rating_raw
        elif isinstance(rating_raw, str) and rating_raw.strip() in ('1', '2', '3', '4', '5'):
            rating = int(rating_raw.strip())

        if rating is None or rating < 1 or rating > 5:
            errors['rating'] = 'Please choose a rating between 1 and 5.'

        if not review_text:
            errors['review_text'] = 'Please tell us about your experience.'
        elif len(review_text) > TEXT_MAX_LENGTH:
            errors['review_text'] = f'Review must be {TEXT_MAX_LENGTH} characters or fewer.'

        if errors:
            return jsonify({
                'success': False,
                'message': 'Please fix the errors below.',
                'errors': errors,
            }), HTTP_400_BAD_REQUEST

        review = Review(
            customer_name=customer_name,
            rating=rating,
            review_text=review_text,
            is_approved=False,
        )
        db.session.add(review)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Thank you! Your review will appear once it has been approved.',
            'review': review.to_dict(),
        }), HTTP_201_CREATED

    except Exception:
        db.session.rollback()
        current_app.logger.exception('Review operation failed')
        return jsonify({'success': False, 'message': 'Reviews are temporarily unavailable. Please try again.'}), HTTP_500_INTERNAL_SERVER_ERROR


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

# Lists every review, approved or not, so admins can moderate them.
@review_bp.route('/admin/reviews', methods=['GET'])
@permission_required('content_read')
def get_all_reviews():
    try:
        reviews = Review.query.order_by(Review.created_at.desc()).all()
        pending = sum(1 for review in reviews if not review.is_approved)

        return jsonify({
            'success': True,
            'total': len(reviews),
            'pending': pending,
            'reviews': [review.to_dict() for review in reviews],
        }), HTTP_200_OK

    except Exception:
        db.session.rollback()
        current_app.logger.exception('Review lookup failed')
        return jsonify({'success': False, 'message': 'Reviews are temporarily unavailable. Please try again.'}), HTTP_500_INTERNAL_SERVER_ERROR


# Toggles the approval flag of a review, publishing or hiding it on the site.
@review_bp.route('/admin/reviews/<int:review_id>/approve', methods=['PATCH'])
@permission_required('content_write')
def toggle_review_approval(review_id):
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({'success': False, 'message': 'Review not found'}), HTTP_404_NOT_FOUND

        review.is_approved = not review.is_approved
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Review approved.' if review.is_approved else 'Review hidden.',
            'review': review.to_dict(),
        }), HTTP_200_OK

    except Exception:
        db.session.rollback()
        current_app.logger.exception('Review operation failed')
        return jsonify({'success': False, 'message': 'Reviews are temporarily unavailable. Please try again.'}), HTTP_500_INTERNAL_SERVER_ERROR


# Permanently removes a review.
@review_bp.route('/admin/reviews/<int:review_id>', methods=['DELETE'])
@permission_required('content_write')
def delete_review(review_id):
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({'success': False, 'message': 'Review not found'}), HTTP_404_NOT_FOUND

        db.session.delete(review)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Review deleted successfully'}), HTTP_200_OK

    except Exception:
        db.session.rollback()
        current_app.logger.exception('Review operation failed')
        return jsonify({'success': False, 'message': 'Reviews are temporarily unavailable. Please try again.'}), HTTP_500_INTERNAL_SERVER_ERROR
