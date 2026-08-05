# helpers for notifying the bakery when a new order comes in.

import re #Cleaning phone numbers for WhatsApp links
import smtplib #Helps send emails to the bakery when a new order is placed.
from email.mime.text import MIMEText #Creates the email message to be sent to the bakery.
from urllib.parse import quote #URL encoding for the WhatsApp link.

# Emails the bakery about a new order using smtplib directly. Returns True on success, False on failure.
def send_order_email(app, order):

    if not app.config['MAIL_ENABLED']:
        app.logger.info(
            f"MAIL_ENABLED is False; skipping email for order #{order.id}")
        return False

    body = (
        f"New Cake Order #{order.id}\n"
        f"Name: {order.full_name}\n"
        f"Phone: {order.phone_number}\n"
        f"Event type: {order.event_type}\n"
        f"Event date: {order.event_date}\n"
        f"Flavor: {order.flavor}\n"
        f"Cake size: {order.cake_size}\n"
        f"Delivery: {order.delivery_type}\n"
        f"Address: {order.delivery_address or '(pickup)'}\n"
        f"Instructions: {order.special_instructions or '(none provided)'}\n"
    )

    msg = MIMEText(body)
    msg['Subject'] = f"New cake order #{order.id} - {order.full_name}"
    msg['From'] = app.config['SMTP_FROM_EMAIL']
    msg['To'] = app.config['BAKERY_NOTIFY_EMAIL']

    try:
        with smtplib.SMTP(app.config['SMTP_HOST'], app.config['SMTP_PORT']) as server:
            server.starttls()
            server.login(app.config['SMTP_USERNAME'],
                         app.config['SMTP_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        app.logger.warning(f"Email send failed for order #{order.id}: {e}")
        return False

# Builds a wa.me link pre-filled with the order summary, addressed to the bakery's WhatsApp number.
# The customer taps this link to send their order details to the baker via WhatsApp.
# If an inspiration image was uploaded, a clickable URL to the hosted image is included.
def build_whatsapp_link(app, order):
    
    # Build delivery line
    if order.delivery_type == 'delivery' and order.delivery_address:
        delivery_line = f"🚚 Delivery to: {order.delivery_address}"
    else:
        delivery_line = "🏪 Pickup from bakery"

    message = (
        f"🎂 New Cake Order (#{order.id})\n\n"
        f"👤 Name: {order.full_name}\n"
        f"📞 Phone: {order.phone_number}\n"
        f"🎉 Event: {order.event_type} on {order.event_date}\n"
        f"🍰 Flavor: {order.flavor}, Size: {order.cake_size}\n"
        f"{delivery_line}\n"
        f"📝 Notes: {order.special_instructions or 'none'}"
    )

    # If an inspiration image was uploaded, add a clickable link to view it
    if order.inspiration_image:
        base_url = app.config.get('SERVER_BASE_URL', 'http://localhost:5000')
        image_url = f"{base_url}/static/uploads/inspiration/{order.inspiration_image}"
        message += f"\n\n🖼️ Inspiration photo: {image_url}"

    number = app.config['BAKERY_WHATSAPP_NUMBER']
    return f"https://wa.me/{number}?text={quote(message)}"


# Builds a wa.me link pointing to the CUSTOMER's phone number so the baker
# can initiate a WhatsApp chat with the customer directly.
def build_baker_to_customer_whatsapp_link(app, order):

    # Clean customer phone number: keep only digits and leading +
    clean_phone = re.sub(r'[^\d+]', '', order.phone_number)
    # Remove leading + if present (wa.me expects digits only)
    clean_phone = clean_phone.lstrip('+')

    greeting = (
        f"Hi {order.full_name}, thank you for your cake order (#{order.id}) "
        f"with Cinderella Cakes! 🎂\n\n"
        f"We received your request for a {order.flavor} cake ({order.cake_size}) "
        f"for your {order.event_type} on {order.event_date}.\n\n"
        f"Let's discuss the details and confirm your order!"
    )
    return f"https://wa.me/{clean_phone}?text={quote(greeting)}"
