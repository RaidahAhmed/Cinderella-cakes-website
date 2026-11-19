import os
import re #Validating phone numbers and dates
import uuid #Generating unique filenames for uploaded images
from datetime import datetime, date

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename #Protect server from malicious file uploads

from app.extensions import db
from app.models.orders import Order, VALID_STATUSES, generate_order_reference
from app.models.order_tracking import OrderStatusHistory
from app.models.gallery import GalleryItem
from app.utils.notifications import send_order_email, build_whatsapp_link, build_baker_to_customer_whatsapp_link
from app.status_codes import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
)
from app.utils.decorators import permission_required

# orders blueprint which holds all the routes related to orders.
orders = Blueprint('orders', __name__, url_prefix='/api/v1/orders')

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

#Checks if the uploaded file has an allowed extension
def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_IMAGE_EXTENSIONS

#Generates a short public reference that is not yet used by another order.
def _generate_unique_reference():
    for _ in range(10):
        reference = generate_order_reference()
        if not Order.query.filter_by(order_reference=reference).first():
            return reference
    raise RuntimeError('Unable to allocate a unique order reference.')


def _is_reference_collision(error):
    """Only retry the reference's unique constraint, not unrelated failures."""
    message = str(error.orig).lower()
    sqlite_unique = getattr(error.orig, 'sqlite_errorname', '') == 'SQLITE_CONSTRAINT_UNIQUE'
    mysql_unique = getattr(error.orig, 'args', (None,))[0] == 1062
    return (sqlite_unique or mysql_unique) and 'order_reference' in message


#Parses the optional gallery_item_id sent with an order.
#Returns (gallery_item_id, error).
def _parse_gallery_item_id(raw_value):
    if raw_value is None or str(raw_value).strip() == '':
        return None, None

    value = str(raw_value).strip()
    if not re.fullmatch(r'[0-9]{1,10}', value):
        return None, 'The selected inspiration image is invalid.'
    gallery_item_id = int(value)
    if not 1 <= gallery_item_id <= 2147483647:
        return None, 'The selected inspiration image is invalid.'

    if not GalleryItem.query.get(gallery_item_id):
        return None, 'The selected inspiration image is no longer available.'

    return gallery_item_id, None

# Checks every required field is present.Returns (cleaned_data, errors_by_field). errors_by_field is empty when valid.
def _validate_order_input(form):
    errors = {}

    required = {
        'full_name': 'Full name',
        'phone_number': 'Phone number',
        'event_type': 'Event type',
        'event_date': 'Event date',
        'flavor': 'Flavor',
        'cake_size': 'Cake size',
    }

    cleaned = {}
    for field, label in required.items():
        value = (form.get(field) or '').strip()
        if not value:
            errors[field] = f"{label} is required."
        cleaned[field] = value

    cleaned['special_instructions'] = (form.get('special_instructions') or '').strip()

    # Delivery fields
    delivery_type = (form.get('delivery_type') or 'pickup').strip().lower()
    if delivery_type not in ('pickup', 'delivery'):
        delivery_type = 'pickup'
    cleaned['delivery_type'] = delivery_type

    delivery_address = (form.get('delivery_address') or '').strip()
    if delivery_type == 'delivery' and not delivery_address:
        errors['delivery_address'] = 'Delivery address is required for delivery orders.'
    cleaned['delivery_address'] = delivery_address or None

#Phone number validation: must be 7-20 characters, digits, spaces, + or - allowed
    if cleaned['phone_number'] and not re.match(r'^[0-9+\-\s]{7,20}$', cleaned['phone_number']):
        errors['phone_number'] = 'Phone number looks invalid.'

#Event date validation: must be a valid date and in the future
    if cleaned['event_date']:
        try:
            parsed_date = datetime.strptime(cleaned['event_date'], '%Y-%m-%d').date()
            if parsed_date < date.today():
                errors['event_date'] = 'Event date cannot be in the past.'
            else:
                cleaned['event_date'] = parsed_date
        except ValueError:
            errors['event_date'] = 'Event date must be a valid date (YYYY-MM-DD).'

    return cleaned, errors

#Validates and saves the optional inspiration photo.
def _save_inspiration_image(file):
    if file.filename == '':
        return None, None

    if not _allowed_file(file.filename):
        return None, 'Image must be a JPEG, PNG, or WEBP file.'

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"order_{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    file.save(os.path.join(upload_dir, filename))
    return filename, None


#creating an order - this route handles the creation of a new order. It validates the input, saves the order to the database, and sends notifications.
@orders.route('/create', methods=['POST'])
def create_order():
    try:
        cleaned, errors = _validate_order_input(request.form)

        if errors:
            return jsonify({
                "success": False,
                "message": "Please fix the errors below.",
                "errors": errors,
            }), HTTP_400_BAD_REQUEST

        inspiration_filename = None
        if 'inspiration_image' in request.files:
            inspiration_filename, upload_error = _save_inspiration_image(request.files['inspiration_image'])
            if upload_error:
                return jsonify({"success": False, "message": upload_error}), HTTP_400_BAD_REQUEST

        gallery_item_id, gallery_error = _parse_gallery_item_id(request.form.get('gallery_item_id'))
        if gallery_error:
            return jsonify({"success": False, "message": gallery_error}), HTTP_400_BAD_REQUEST

#Takes cleaned data and creates a new Order object, saves it to the database.
        for attempt in range(5):
            new_order = Order(
                full_name=cleaned['full_name'],
                phone_number=cleaned['phone_number'],
                event_type=cleaned['event_type'],
                event_date=cleaned['event_date'],
                flavor=cleaned['flavor'],
                cake_size=cleaned['cake_size'],
                special_instructions=cleaned['special_instructions'],
                inspiration_image=inspiration_filename,
                delivery_type=cleaned['delivery_type'],
                delivery_address=cleaned['delivery_address'],
            )

            # Public reference the customer uses to track the order later on.
            new_order.order_reference = _generate_unique_reference()
            new_order.gallery_item_id = gallery_item_id
            try:
                db.session.add(new_order)
                db.session.flush()

                # First entry of the order timeline shown on the tracking page.
                db.session.add(OrderStatusHistory(
                    order_id=new_order.id,
                    status=new_order.status or 'new',
                    note='Order received by the bakery.'
                ))
                db.session.commit()
                break
            except IntegrityError as error:
                db.session.rollback()
                if attempt == 4 or not _is_reference_collision(error):
                    raise

        #Send notifications: email (if enabled) and WhatsApp links
        send_order_email(current_app, new_order)
        whatsapp_link = build_whatsapp_link(current_app, new_order)
        baker_whatsapp_link = build_baker_to_customer_whatsapp_link(current_app, new_order)

        return jsonify({
            "success": True,
            "message": "Order received! Tap the button below to send your order details to the baker via WhatsApp.",
            "order_id": new_order.id,
            "order_reference": new_order.order_reference,
            "order": new_order.to_dict(),
            "whatsapp_link": whatsapp_link,
            "baker_whatsapp_link": baker_whatsapp_link,
        }), HTTP_201_CREATED

    except Exception:
        db.session.rollback()
        current_app.logger.exception('Order operation failed')
        return jsonify({"success": False, "message": "We could not process this order. Please try again."}), HTTP_500_INTERNAL_SERVER_ERROR


# getting all orders - this route retrieves all orders from the database and returns them in a JSON response.
@orders.route('', methods=['GET'])
@permission_required('orders_read')
def get_all_orders():
    try:
        all_orders = Order.query.order_by(Order.created_at.desc()).all()
        return jsonify({
            "success": True,
            "total": len(all_orders),
            "orders": [o.to_dict() for o in all_orders],
        }), HTTP_200_OK
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Order lookup failed')
        return jsonify({"success": False, "message": "We could not load orders. Please try again."}), HTTP_500_INTERNAL_SERVER_ERROR


# get a single order by id - this route retrieves a specific order based on the provided order ID. If the order is found, it returns the order details; otherwise, it returns a 404 error.
@orders.route('/<int:order_id>', methods=['GET'])
@permission_required('orders_read')
def get_order_by_id(order_id):
    try:
        order = Order.query.filter_by(id=order_id).first()

        if not order:
            return jsonify({"success": False, "message": "Order not found"}), HTTP_404_NOT_FOUND

        order_data = order.to_dict()

        # Include the gallery item that inspired the order, when there is one.
        order_data['gallery_item'] = order.gallery_item.to_dict() if order.gallery_item else None
        order_data['status_history'] = [entry.to_dict() for entry in order.status_history]

        return jsonify({"success": True, "order": order_data}), HTTP_200_OK
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Order lookup failed')
        return jsonify({"success": False, "message": "We could not load orders. Please try again."}), HTTP_500_INTERNAL_SERVER_ERROR

# update_order_status - changes the progress status of a specific order (e.g., pending -> completed). Requires 'orders_write' permission.
# Every valid change is appended to the order's status history so customers can follow it.
@orders.route('/<int:order_id>/status', methods=['PATCH'])
@permission_required('orders_write')
def update_order_status(order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"success": False, "message": "Order not found"}), HTTP_404_NOT_FOUND
            
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'success': False, 'message': 'Request body must be a JSON object with Content-Type: application/json'}), HTTP_400_BAD_REQUEST

        raw_status = data.get('status')
        if not isinstance(raw_status, str):
            return jsonify({"success": False, "message": "Status is required"}), HTTP_400_BAD_REQUEST

        new_status = str(raw_status).strip().lower()
        if new_status not in VALID_STATUSES:
            return jsonify({
                "success": False,
                "message": f"Invalid status. Allowed values: {', '.join(VALID_STATUSES)}"
            }), HTTP_400_BAD_REQUEST

        raw_note = data.get('note')
        if raw_note is not None and not isinstance(raw_note, str):
            return jsonify({"success": False, "message": "Note must be text"}), HTTP_400_BAD_REQUEST
        note = (raw_note or '').strip() or None
        if note and len(note) > 500:
            return jsonify({"success": False, "message": "Note must be 500 characters or fewer"}), HTTP_400_BAD_REQUEST

        if order.status != new_status:
            order.status = new_status
            db.session.add(OrderStatusHistory(
                order_id=order.id,
                status=new_status,
                note=note
            ))
        elif note:
            # Same status but a fresh update message - still useful on the timeline.
            db.session.add(OrderStatusHistory(
                order_id=order.id,
                status=new_status,
                note=note
            ))

        db.session.commit()
            
        return jsonify({"success": True, "order": order.to_dict()}), HTTP_200_OK
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Order operation failed')
        return jsonify({"success": False, "message": "We could not process this order. Please try again."}), HTTP_500_INTERNAL_SERVER_ERROR
