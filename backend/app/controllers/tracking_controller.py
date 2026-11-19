import re
import secrets

from flask import Blueprint, request, jsonify, current_app

from app.extensions import db
from app.models.orders import Order
from app.status_codes import (
    HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
)

# Public order tracking - lets a customer follow the progress of an order
# using the reference they were given plus the phone number on the order.
tracking_bp = Blueprint('tracking', __name__, url_prefix='/api/v1')


def _normalize_phone(value):
    """Compare formatting variants without changing the stored customer number."""
    if not isinstance(value, str) or len(value) > 40:
        return None
    compact = re.sub(r'[\s-]', '', value)
    if not re.fullmatch(r'\+?[0-9]{7,15}', compact):
        return None
    digits = compact.lstrip('+')
    if re.fullmatch(r'0[1-9][0-9]{8}', digits):
        return '256' + digits[1:]
    return digits


def _not_found():
    return jsonify({
        'success': False,
        'message': 'No order found. Please check your order reference and phone number.',
    }), HTTP_404_NOT_FOUND


@tracking_bp.route('/track', methods=['POST'])
def track_order():
    """Look up a single order by public reference and phone number."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'success': False, 'message': 'Request body must be a JSON object.'}), HTTP_400_BAD_REQUEST

    raw_reference = data.get('order_reference')
    raw_phone = data.get('phone_number')
    if (not isinstance(raw_reference, str) or not isinstance(raw_phone, str)
            or not raw_reference.strip() or not raw_phone.strip()):
        return jsonify({
            'success': False,
            'message': 'Order reference and phone number are required'
        }), HTTP_400_BAD_REQUEST

    reference = raw_reference.strip().upper()
    phone = _normalize_phone(raw_phone)
    if not re.fullmatch(r'CC-[A-Z0-9]{5}', reference) or not phone:
        return _not_found()

    try:
        order = Order.query.filter_by(order_reference=reference).first()
        stored_phone = _normalize_phone(order.phone_number) if order else None
        matched = secrets.compare_digest(stored_phone or '', phone)
        if not order or not matched:
            return _not_found()

        # The status_history backref is already ordered newest first.
        history = [{
            'status': entry.status,
            'note': entry.note,
            'created_at': entry.created_at.isoformat() if entry.created_at else None,
        } for entry in order.status_history]

        return jsonify({
            'success': True,
            'order_reference': order.order_reference,
            'status': order.status,
            'full_name': order.full_name,
            'event_date': order.event_date.isoformat() if order.event_date else None,
            'event_type': order.event_type,
            'flavor': order.flavor,
            'cake_size': order.cake_size,
            'delivery_type': order.delivery_type,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'status_history': history,
        }), HTTP_200_OK
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Public order tracking failed')
        return jsonify({
            'success': False, 'message': 'Order tracking is temporarily unavailable. Please try again.',
        }), HTTP_500_INTERNAL_SERVER_ERROR
