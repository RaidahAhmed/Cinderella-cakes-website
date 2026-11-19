import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { trackOrder } from '../lib/api';

// The five milestones a customer sees on the public tracker. Several backend
// statuses collapse into one milestone (for example new/pending → Received).
const STAGES = ['Received', 'Confirmed', 'Baking', 'Ready', 'Delivered'];

const STATUS_STAGE = {
  new: 0,
  pending: 0,
  contacted: 1,
  confirmed: 1,
  baking: 2,
  in_progress: 2,
  ready: 3,
  out_for_delivery: 3,
  delivered: 4,
  completed: 4,
};

// Maps a backend status onto one of the badge colour tones.
const STATUS_TONE = {
  new: 'pending',
  pending: 'pending',
  contacted: 'confirmed',
  confirmed: 'confirmed',
  baking: 'baking',
  in_progress: 'baking',
  ready: 'ready',
  out_for_delivery: 'ready',
  delivered: 'delivered',
  completed: 'delivered',
  cancelled: 'cancelled',
};

const STATUS_LABEL = {
  new: 'Received',
  pending: 'Pending',
  contacted: 'Confirmed',
  confirmed: 'Confirmed',
  baking: 'Baking',
  in_progress: 'In progress',
  ready: 'Ready',
  out_for_delivery: 'Out for delivery',
  delivered: 'Delivered',
  completed: 'Completed',
  cancelled: 'Cancelled',
};

// Formats an ISO date (YYYY-MM-DD or full timestamp) for display.
function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatDateTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Converts snake_case backend values into readable labels.
function humanise(value) {
  if (!value) return '—';
  return String(value).replace(/_/g, ' ');
}

function StatusBadge({ status }) {
  return (
    <span className={`track-badge track-badge--${STATUS_TONE[status] || 'pending'}`}>
      {STATUS_LABEL[status] || humanise(status)}
    </span>
  );
}

// Five horizontal milestones joined by a line: finished steps are purple,
// the current step is teal and everything ahead stays neutral.
function ProgressTracker({ status }) {
  const current = STATUS_STAGE[status] ?? 0;

  return (
    <div className="track-progress" role="list" aria-label="Order progress">
      {STAGES.map((label, index) => {
        const state = index < current ? 'done' : index === current ? 'active' : 'upcoming';
        return (
          <div
            key={label}
            className={`track-step ${state}`}
            role="listitem"
            aria-current={state === 'active' ? 'step' : undefined}
          >
            <span className="track-dot" aria-hidden="true">
              {index < current ? '✓' : index + 1}
            </span>
            <span className="track-label">
              {index === 3 && status === 'out_for_delivery' ? 'On the way' : label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div>
      <span className="track-detail-label">{label}</span>
      <span className="track-detail-value">{value}</span>
    </div>
  );
}

// Public page where a customer follows the progress of their cake order using
// the reference from their confirmation plus the phone number they ordered with.
export default function Track() {
  const [searchParams] = useSearchParams();

  const [orderReference, setOrderReference] = useState(searchParams.get('ref') || '');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [order, setOrder] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const resultRef = useRef(null);

  // Bring the result into view once an order has been found.
  useEffect(() => {
    if (order && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [order]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    const reference = orderReference.trim();
    const phone = phoneNumber.trim();

    if (!reference || !phone) {
      setOrder(null);
      setError('Please enter both your order reference and the phone number you ordered with.');
      return;
    }

    setOrder(null);
    setLoading(true);
    try {
      const data = await trackOrder(reference, phone);
      setOrder(data);
    } catch (err) {
      setOrder(null);
      setError(err.message || 'We could not find that order. Please check your details and try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="track-hero">
        <div className="container">
          <span className="eyebrow">Order status</span>
          <h1>Track Your Order</h1>
          <p>
            Enter the reference from your order confirmation together with the phone number you
            ordered with, and follow your cake from our kitchen to your celebration.
          </p>
        </div>
      </section>

      <section className="track-page">
        <div className="container">
          <form className="track-card" onSubmit={handleSubmit} noValidate>
            <div className="track-form">
              <div className="form-field">
                <label htmlFor="orderReference">Order Reference</label>
                <input
                  id="orderReference"
                  type="text"
                  placeholder="CC-XXXXX"
                  autoComplete="off"
                  value={orderReference}
                  onChange={(e) => setOrderReference(e.target.value.toUpperCase())}
                />
                <span className="track-hint">
                  Your reference starts with CC- and was shown when you placed the order.
                </span>
              </div>

              <div className="form-field">
                <label htmlFor="phoneNumber">Phone Number</label>
                <input
                  id="phoneNumber"
                  type="tel"
                  placeholder="+256 700 000 000"
                  autoComplete="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                />
                <span className="track-hint">Use the same number you gave us on the order form.</span>
              </div>

              {error && (
                <div className="track-alert" role="alert">
                  {error}{' '}
                  <Link to="/contact">Contact the bakery</Link> if you need a hand.
                </div>
              )}

              <button type="submit" className="btn btn-gradient btn-block" disabled={loading}>
                {loading ? 'Searching…' : 'Track Order'}
              </button>
            </div>
          </form>

          {order && (
            <section className="track-result" aria-live="polite" ref={resultRef}>
              <div className="track-result-head">
                <div>
                  <span className="track-ref-label">Order reference</span>
                  <span className="track-ref">{order.order_reference}</span>
                </div>
                <StatusBadge status={order.status} />
              </div>

              {order.status === 'cancelled' ? (
                <div className="track-cancelled" role="alert">
                  This order has been cancelled. If this was not expected, please call us on
                  +256 781 470984 and we will sort it out with you right away.
                </div>
              ) : (
                <ProgressTracker status={order.status} />
              )}

              <h2 className="track-block-title">Order details</h2>
              <div className="track-details">
                <Detail label="Customer" value={order.full_name || '—'} />
                <Detail label="Event type" value={humanise(order.event_type)} />
                <Detail label="Event date" value={formatDate(order.event_date)} />
                <Detail label="Flavor" value={humanise(order.flavor)} />
                <Detail label="Cake size" value={humanise(order.cake_size)} />
                <Detail label="Delivery" value={humanise(order.delivery_type)} />
              </div>

              <h2 className="track-block-title">Status history</h2>
              {order.status_history && order.status_history.length > 0 ? (
                <ul className="track-timeline">
                  {order.status_history.map((entry, index) => (
                    <li key={`${entry.created_at}-${entry.status}-${index}`} className="track-timeline-item">
                      <div className="track-timeline-head">
                        <StatusBadge status={entry.status} />
                        <span className="track-timeline-date">{formatDateTime(entry.created_at)}</span>
                      </div>
                      {entry.note && <p className="track-timeline-note">{entry.note}</p>}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="track-hint">No status updates have been recorded yet.</p>
              )}
            </section>
          )}
        </div>
      </section>
    </>
  );
}
