import { useState } from 'react';
import { submitOrder } from '../lib/api';

const initialFormState = {
  fullName: '',
  phoneNumber: '',
  eventType: '',
  eventDate: '',
  flavor: '',
  cakeSize: '',
  specialInstructions: '',
  deliveryType: 'pickup',
  deliveryAddress: '',
};

// Handles the cake ordering process, capturing customer details and sending them to the backend.
export default function Order() {
  const [form, setForm] = useState(initialFormState);
  const [inspirationImage, setInspirationImage] = useState(null);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState(null);

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handleFileChange(e) {
    setInspirationImage(e.target.files?.[0] || null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErrors({});
    setStatus(null);
    setSubmitting(true);

    try {
      const { ok, data } = await submitOrder({ ...form, inspirationImage });

      if (ok && data.success) {
        setForm(initialFormState);
        setInspirationImage(null);
        setStatus({
          type: 'success',
          message: `${data.message} Your order reference is #${data.order_id}.`,
          whatsappLink: data.whatsapp_link,
        });

        if (data.whatsapp_link) {
          window.open(data.whatsapp_link, '_blank', 'noopener,noreferrer');
        }
      } else {
        setErrors(data.errors || {});
        setStatus({ type: 'error', message: data.message || 'Please check the form and try again.' });
      }
    } catch {
      setStatus({
        type: 'error',
        message:
          "Something went wrong reaching the server. Make sure your API is running.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <section className="page-banner">
        <h1>Place your order</h1>
        <p>Fill in the details below and we&rsquo;ll reach out via WhatsApp or call to confirm your custom cake</p>
      </section>

      <section className="section">
        <div className="container">
          <form className="order-card" onSubmit={handleSubmit} noValidate>
            <h2>Cake order details</h2>
            <hr className="form-divider" />

            {status && (
              <div className={`form-status visible ${status.type}`}>
                {status.message}
                {status.type === 'success' && status.whatsappLink && (
                  <a
                    href={status.whatsappLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-gradient"
                    style={{ marginTop: 16, display: 'flex', justifyContent: 'center' }}
                  >
                    📱 Send Order via WhatsApp
                  </a>
                )}
              </div>
            )}

            <div className="form-grid">
              <Field
                label="Full Name"
                id="fullName"
                error={errors.full_name}
              >
                <input
                  type="text"
                  placeholder="John Doe"
                  value={form.fullName}
                  onChange={(e) => updateField('fullName', e.target.value)}
                />
              </Field>

              <Field label="Phone number" id="phoneNumber" error={errors.phone_number}>
                <input
                  type="tel"
                  placeholder="+256 700 000 000"
                  value={form.phoneNumber}
                  onChange={(e) => updateField('phoneNumber', e.target.value)}
                />
              </Field>

              <Field label="Event type" id="eventType" error={errors.event_type}>
                <input
                  type="text"
                  placeholder="Birthday, wedding, anniversary..."
                  value={form.eventType}
                  onChange={(e) => updateField('eventType', e.target.value)}
                />
              </Field>

              <Field label="Event date" id="eventDate" error={errors.event_date}>
                <input
                  type="date"
                  value={form.eventDate}
                  onChange={(e) => updateField('eventDate', e.target.value)}
                />
              </Field>

              <Field label="Flavor" id="flavor" error={errors.flavor}>
                <input
                  type="text"
                  placeholder="Red velvet, vanilla, chocolate..."
                  value={form.flavor}
                  onChange={(e) => updateField('flavor', e.target.value)}
                />
              </Field>

              <Field label="Inspiration image" id="inspirationImage" error={null}>
                <label
                  htmlFor="inspirationImage"
                  className={`file-drop${inspirationImage ? ' has-file' : ''}`}
                >
                  {inspirationImage ? inspirationImage.name : 'Click to upload an inspiration photo (optional, max 5MB)'}
                  <input
                    type="file"
                    id="inspirationImage"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileChange}
                  />
                </label>
              </Field>

              <Field label="Cake size" id="cakeSize" error={errors.cake_size}>
                <input
                  type="text"
                  placeholder="e.g. Medium (serves 20)"
                  value={form.cakeSize}
                  onChange={(e) => updateField('cakeSize', e.target.value)}
                />
              </Field>

              <Field label="Delivery type" id="deliveryType" error={null}>
                <div style={{ display: 'flex', gap: '20px', alignItems: 'center', height: '100%', padding: '12px 14px', border: '1.5px solid #D9C4E8', borderRadius: 'var(--radius-sm)' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', margin: 0, fontStyle: 'normal', color: 'var(--ink)' }}>
                    <input
                      type="radio"
                      name="deliveryType"
                      value="pickup"
                      checked={form.deliveryType === 'pickup'}
                      onChange={(e) => updateField('deliveryType', e.target.value)}
                    />
                    Pickup
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', margin: 0, fontStyle: 'normal', color: 'var(--ink)' }}>
                    <input
                      type="radio"
                      name="deliveryType"
                      value="delivery"
                      checked={form.deliveryType === 'delivery'}
                      onChange={(e) => updateField('deliveryType', e.target.value)}
                    />
                    Delivery
                  </label>
                </div>
              </Field>

              {form.deliveryType === 'delivery' && (
                <Field label="Delivery address" id="deliveryAddress" error={errors.delivery_address}>
                  <input
                    type="text"
                    placeholder="e.g. Nsambya, Ave Maria Rd"
                    value={form.deliveryAddress}
                    onChange={(e) => updateField('deliveryAddress', e.target.value)}
                  />
                </Field>
              )}
            </div>

            <div className="form-field full" style={{ marginTop: 24 }}>
              <label htmlFor="specialInstructions">Special instructions or design notes</label>
              <textarea
                id="specialInstructions"
                placeholder="Describe your dream cake - colors, theme, inscriptions, decorations or any special dietary requirements."
                value={form.specialInstructions}
                onChange={(e) => updateField('specialInstructions', e.target.value)}
              />
            </div>

            <div className="form-note">
              After submitting, you'll be redirected to WhatsApp to send your order details directly to our bakers. We'll reply there to confirm your order and discuss pricing!
            </div>

            <button type="submit" className="btn btn-gradient btn-block" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Submit Order Request'}
            </button>
          </form>
        </div>
      </section>
    </>
  );
}

function Field({ label, id, error, children }) {
  return (
    <div className={`form-field${error ? ' has-error' : ''}`} id={`field-${id}`}>
      <label htmlFor={id}>{label}</label>
      {children}
      <span className="field-error">{error}</span>
    </div>
  );
}
