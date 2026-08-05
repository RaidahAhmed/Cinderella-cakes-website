/**
 * Talks to the Flask backend.
 *
 * Flask has its own built-in dev server, so this does NOT go through XAMPP's
 * Apache - only XAMPP's MySQL needs to be running (start it in the Control
 * Panel). Start the API with:
 *   cd backend
 *   venv\Scripts\activate   (Mac/Linux: source venv/bin/activate)
 *   python run.py
 * It runs at http://localhost:5000 by default - update below if you change that.
 */
export const API_BASE_URL = 'http://localhost:5000';

/**
 * Submits a new cake order. Expects a plain object of form values plus an
 * optional `inspirationImage` File object. Returns the parsed JSON response
 * and throws only on network failure (never on validation errors - those
 * come back as normal JSON with success: false).
 */
export async function submitOrder(orderData) {
  const formData = new FormData();
  formData.append('full_name', orderData.fullName);
  formData.append('phone_number', orderData.phoneNumber);
  formData.append('event_type', orderData.eventType);
  formData.append('event_date', orderData.eventDate);
  formData.append('flavor', orderData.flavor);
  formData.append('cake_size', orderData.cakeSize);
  formData.append('special_instructions', orderData.specialInstructions || '');
  formData.append('delivery_type', orderData.deliveryType || 'pickup');
  formData.append('delivery_address', orderData.deliveryAddress || '');

  if (orderData.inspirationImage) {
    formData.append('inspiration_image', orderData.inspirationImage);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/orders/create`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();
  return { ok: response.ok, data };
}
