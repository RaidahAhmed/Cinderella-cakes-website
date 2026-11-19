import { useEffect, useState } from 'react';
import { fetchAdminReviews, approveReview, deleteReview } from '../../lib/api';
import '../../styles/admin.css';

const PREVIEW_LENGTH = 160;

// Compact star row used inside the moderation table.
function Stars({ value }) {
  const filled = Math.round(Number(value) || 0);
  return (
    <span style={{ color: '#40BADA', letterSpacing: '2px', fontSize: '.95rem' }} aria-label={`${filled} out of 5 stars`}>
      {'★'.repeat(filled)}
      <span style={{ color: '#DED6E2' }}>{'★'.repeat(Math.max(0, 5 - filled))}</span>
    </span>
  );
}

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

// Admin moderation screen: lists every review so pending ones can be approved,
// hidden again, or removed permanently.
export default function Reviews() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState({});
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    loadReviews();
  }, []);

  async function loadReviews() {
    try {
      const data = await fetchAdminReviews();
      setReviews(data.reviews || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load reviews.');
    } finally {
      setLoading(false);
    }
  }

  function toggleExpanded(id) {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  async function handleToggleApproval(review) {
    setBusyId(review.id);
    try {
      const res = await approveReview(review.id);
      const nextApproved = res.review ? res.review.is_approved : !review.is_approved;
      setReviews((list) =>
        list.map((item) => (item.id === review.id ? { ...item, is_approved: nextApproved } : item))
      );
    } catch (err) {
      alert(err.message || 'Failed to update review');
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(review) {
    const confirmed = window.confirm(
      `Delete the review from ${review.customer_name}? This cannot be undone.`
    );
    if (!confirmed) return;

    setBusyId(review.id);
    try {
      await deleteReview(review.id);
      setReviews((list) => list.filter((item) => item.id !== review.id));
    } catch (err) {
      alert(err.message || 'Failed to delete review');
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <div>Loading reviews...</div>;

  if (error) {
    return (
      <div className="admin-page">
        <div className="admin-header">
          <h1>Manage Reviews</h1>
        </div>
        <div className="admin-card" style={{ color: '#A32A45' }}>
          {error}
        </div>
      </div>
    );
  }

  const pendingCount = reviews.filter((review) => !review.is_approved).length;

  return (
    <div className="admin-page">
      <div className="admin-header">
        <div>
          <h1 style={{ margin: 0 }}>Manage Reviews</h1>
          <p style={{ margin: '6px 0 0', fontSize: '.9rem', color: 'var(--ink-soft)' }}>
            {reviews.length} {reviews.length === 1 ? 'review' : 'reviews'} in total ·{' '}
            <strong style={{ color: pendingCount > 0 ? '#856404' : 'var(--ink-soft)' }}>
              {pendingCount} awaiting approval
            </strong>
          </p>
        </div>
      </div>

      <div className="admin-card">
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Rating</th>
                <th>Review</th>
                <th>Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((review) => {
                const text = review.review_text || '';
                const isLong = text.length > PREVIEW_LENGTH;
                const isOpen = !!expanded[review.id];
                const shown = isOpen || !isLong ? text : `${text.slice(0, PREVIEW_LENGTH).trimEnd()}…`;
                const busy = busyId === review.id;

                return (
                  <tr key={review.id}>
                    <td style={{ minWidth: 140 }}>
                      <strong>{review.customer_name}</strong>
                      <br />
                      <small style={{ color: '#888' }}>#{review.id}</small>
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      <Stars value={review.rating} />
                      <div style={{ fontSize: '.78rem', color: '#666', marginTop: 2 }}>
                        {review.rating} / 5
                      </div>
                    </td>
                    <td style={{ maxWidth: 360 }}>
                      <div style={{ lineHeight: 1.55 }}>{shown}</div>
                      {isLong && (
                        <button
                          type="button"
                          onClick={() => toggleExpanded(review.id)}
                          style={{
                            marginTop: 6,
                            background: 'none',
                            border: 'none',
                            padding: 0,
                            cursor: 'pointer',
                            color: 'var(--purple)',
                            fontSize: '.8rem',
                            fontWeight: 600,
                            textDecoration: 'underline',
                          }}
                        >
                          {isOpen ? 'Show less' : 'Read more'}
                        </button>
                      )}
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>{formatDate(review.created_at)}</td>
                    <td>
                      <span
                        className={`status-badge ${review.is_approved ? 'status-completed' : 'status-pending'}`}
                      >
                        {review.is_approved ? 'Approved' : 'Pending'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        <button
                          type="button"
                          className="admin-btn"
                          onClick={() => handleToggleApproval(review)}
                          disabled={busy}
                          style={{ padding: '8px 14px', fontSize: '.78rem' }}
                        >
                          {review.is_approved ? 'Unapprove' : 'Approve'}
                        </button>
                        <button
                          type="button"
                          className="admin-btn btn-danger"
                          onClick={() => handleDelete(review)}
                          disabled={busy}
                          style={{ padding: '8px 14px', fontSize: '.78rem' }}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {reviews.length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center' }}>
                    No reviews have been submitted yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
