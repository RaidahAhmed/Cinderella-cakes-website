import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchGalleryItem, submitOrder } from '../lib/api';
import GalleryMedia from '../components/GalleryMedia';

const CATEGORY_LABELS = {
  wedding: 'Weddings & Introductions',
  birthday: 'Birthdays',
  kids: "Kids' Characters",
  baby: 'Baby Showers',
  graduation: 'Graduations',
  anniversary: 'Anniversaries & Love',
  corporate: 'Corporate & Events',
  holiday: 'Holidays & Seasons',
  sculpted: 'Sculpted & Sugar Art',
  cupcakes: 'Cupcakes & Treats',
  other: 'Other',
};

const CAKE_SIZES = [
  { value: '', label: 'Select a size...' },
  { value: '6" (serves 6-8)', label: '6″ — serves 6–8' },
  { value: '8" (serves 10-14)', label: '8″ — serves 10–14' },
  { value: '10" (serves 20-25)', label: '10″ — serves 20–25' },
  { value: '12" (serves 30-40)', label: '12″ — serves 30–40' },
  { value: '14" (serves 50-60)', label: '14″ — serves 50–60' },
  { value: '16" (serves 60-80)', label: '16″ — serves 60–80' },
];

const TIER_OPTIONS = [
  { value: '1', label: '1 Tier' },
  { value: '2', label: '2 Tiers' },
  { value: '3', label: '3 Tiers' },
  { value: '4', label: '4 Tiers' },
  { value: '5', label: '5 Tiers' },
];

const initialFormState = {
  fullName: '',
  phoneNumber: '',
  eventType: '',
  eventDate: '',
  flavor: '',
  cakeSize: '',
  tiers: '1',
  specialInstructions: '',
  deliveryType: 'pickup',
  deliveryAddress: '',
};

// Handles the cake ordering process, capturing customer details and sending them to the backend.
export default function Order() {
  const [searchParams, setSearchParams] = useSearchParams();
  const cakeId = searchParams.get('cake');

  const [form, setForm] = useState(initialFormState);
  const [inspirationImage, setInspirationImage] = useState(null);
  const [design, setDesign] = useState(null);
  const [designState, setDesignState] = useState({ loading: false, error: null });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState(null);

  // Load the gallery design the customer picked on the gallery page.
  useEffect(() => {
    if (!cakeId) {
      setDesign(null);
      setDesignState({ loading: false, error: null });
      return undefined;
    }

    let cancelled = false;
    setDesign(null);
    setDesignState({ loading: true, error: null });

    fetchGalleryItem(cakeId)
      .then((item) => {
        if (cancelled) return;
        setDesign(item);
        setDesignState({ loading: false, error: null });
      })
      .catch((err) => {
        if (cancelled) return;
        setDesign(null);
        setDesignState({
          loading: false,
          error: err.message || 'That design is no longer available.',
        });
      });

    return () => {
      cancelled = true;
    };
  }, [cakeId]);

  function clearDesign() {
    setDesign(null);
    setDesignState({ loading: false, error: null });
    if (cakeId) setSearchParams({}, { replace: true });
  }

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
    if (cakeId && (designState.loading || !design || String(design.id) !== String(Number(cakeId)))) {
      setStatus({ type: 'error', message: 'Wait for the selected design, or remove it before submitting.' });
      return;
    }
    setSubmitting(true);

    // Combine size + tiers into the cake_size field for the backend
    const combinedSize = `${form.cakeSize} — ${form.tiers} tier${form.tiers !== '1' ? 's' : ''}`;

    try {
      const data = await submitOrder({
        ...form,
        cakeSize: form.cakeSize ? combinedSize : '',
        inspirationImage,
        galleryItemId: design ? design.id : undefined,
      });

      if (data.success) {
        const reference = data.order_reference || (data.order_id ? `#${data.order_id}` : null);
        setForm(initialFormState);
        setInspirationImage(null);
        clearDesign();
        setStatus({
          type: 'success',
          message: data.message || 'Order received!',
          orderReference: reference,
          whatsappLink: data.whatsapp_link,
        });

        if (data.whatsapp_link) {
          window.open(data.whatsapp_link, '_blank', 'noopener,noreferrer');
        }
      } else {
        setErrors(data.errors || {});
        setStatus({ type: 'error', message: data.message || 'Please check the form and try again.' });
      }
    } catch (err) {
      // The API attaches validation details to rejected requests; without them it was a connection problem.
      if (err.data || err.errors) {
        setErrors(err.errors || {});
        setStatus({ type: 'error', message: err.message || 'Please check the form and try again.' });
      } else {
        setStatus({
          type: 'error',
          message: err.message || 'Something went wrong reaching the server. Make sure your API is running.',
        });
      }
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

            {designState.loading && (
              <div className="order-design-loading">Fetching your selected design&hellip;</div>
            )}

            {!designState.loading && designState.error && (
              <div className="order-design-alert">
                {designState.error}{' '}
                <Link to="/gallery">Browse the gallery</Link>{' '}
                <button type="button" className="btn btn-outline" onClick={clearDesign}>Remove selection</button>
              </div>
            )}

            {!designState.loading && design && (
              <div className="order-design-card">
                <GalleryMedia item={design} className="order-design-thumb" />
                <div className="order-design-info">
                  <span className="order-design-eyebrow">Selected design</span>
                  <h3 className="order-design-title">{design.title || 'Signature cake'}</h3>
                  <p className="order-design-meta">
                    {CATEGORY_LABELS[design.category] || 'Gallery pick'}
                    {design.description ? ` — ${design.description}` : ''}
                  </p>
                </div>
                <div className="order-design-actions">
                  <Link to="/gallery" className="order-design-change">Change</Link>
                  <button
                    type="button"
                    className="order-design-remove"
                    onClick={clearDesign}
                    aria-label="Remove selected design"
                  >
                    <span aria-hidden="true">&times;</span>
                  </button>
                </div>
              </div>
            )}

            {errors.gallery_item_id && (
              <div className="order-design-alert" role="alert">
                {errors.gallery_item_id}{' '}
                <button type="button" className="btn btn-outline" onClick={clearDesign}>Remove selection</button>
              </div>
            )}

            {status && (
              <div className={`form-status visible ${status.type}`}>
                {status.message}
                {status.type === 'success' && status.orderReference && (
                  <div className="order-ref-block">
                    <span className="order-ref-label">Your order reference</span>
                    <span className="order-ref-value">{status.orderReference}</span>
                    <Link
                      to={`/track?ref=${encodeURIComponent(status.orderReference)}`}
                      className="order-ref-link"
                    >
                      Track your order &rarr;
                    </Link>
                  </div>
                )}
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

              <Field label="Cake size (base diameter)" id="cakeSize" error={errors.cake_size}>
                <select
                  value={form.cakeSize}
                  onChange={(e) => updateField('cakeSize', e.target.value)}
                >
                  {CAKE_SIZES.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </Field>

              <Field label="Number of tiers" id="tiers" error={null}>
                <select
                  value={form.tiers}
                  onChange={(e) => updateField('tiers', e.target.value)}
                >
                  {TIER_OPTIONS.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </Field>

              <Field label="Delivery type" id="deliveryType" error={null}>
                <div className="radio-group-wrap">
                  <label>
                    <input
                      type="radio"
                      name="deliveryType"
                      value="pickup"
                      checked={form.deliveryType === 'pickup'}
                      onChange={(e) => updateField('deliveryType', e.target.value)}
                    />
                    Pickup
                  </label>
                  <label>
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

            <button type="submit" className="btn btn-gradient btn-block" disabled={submitting || Boolean(cakeId && (designState.loading || !design))}>
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
