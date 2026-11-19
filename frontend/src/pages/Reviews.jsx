import { useEffect, useState } from 'react';
import { fetchReviews, submitReview } from '../lib/api';

const NAME_MAX_LENGTH = 60;
const TEXT_MAX_LENGTH = 800;

// Renders a five star row, filling the stars up to the given rating.
function Stars({ value, size = '1rem' }) {
  const rounded = Math.round(Number(value) || 0);
  return (
    <span className="stars" style={{ fontSize: size }} aria-label={`${rounded} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <span key={star} className={`star${star <= rounded ? ' filled' : ''}`} aria-hidden="true">
          ★
        </span>
      ))}
    </span>
  );
}

function formatDate(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
}

// Public testimonials page: shows approved reviews with the average rating and
// lets a visitor submit a new one for moderation.
export default function Reviews() {
  const [reviews, setReviews] = useState([]);
  const [summary, setSummary] = useState({ average_rating: 0, total: 0 });
  const [loading, setLoading] = useState(true);

  const [name, setName] = useState('');
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState(null);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    let active = true;

    fetchReviews()
      .then((data) => {
        if (!active) return;
        setReviews(data.reviews || []);
        setSummary({ average_rating: data.average_rating || 0, total: data.total || 0 });
      })
      .catch(() => {
        if (active) setStatus({ type: 'error', message: 'We could not load the reviews right now.' });
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus(null);

    const nextErrors = {};
    if (!name.trim()) nextErrors.customer_name = 'Please tell us your name.';
    if (!text.trim()) nextErrors.review_text = 'Please share a few words about your experience.';

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      setStatus({ type: 'error', message: 'Please fill in the fields highlighted below.' });
      return;
    }

    setErrors({});
    setSubmitting(true);

    try {
      await submitReview({
        customer_name: name.trim(),
        rating,
        review_text: text.trim(),
      });
      setStatus({ type: 'success', message: 'Thank you! Your review will appear after approval.' });
      setName('');
      setRating(5);
      setText('');
    } catch (err) {
      setErrors(err.errors || {});
      setStatus({
        type: 'error',
        message: err.message || 'Could not submit your review. Please try again.',
      });
    } finally {
      setSubmitting(false);
    }
  }

  const average = Number(summary.average_rating) || 0;
  const previewRating = hoverRating || rating;

  return (
    <>
      <section className="reviews-hero">
        <div className="container">
          <span className="eyebrow">Testimonials</span>
          <h1>Kind Words From Our Customers</h1>
          <p>
            Every cake carries a story. These are the notes families have shared with us after
            their celebrations.
          </p>

          <div className="review-summary">
            <span className="review-summary-score">{average.toFixed(1)}</span>
            <Stars value={average} size="1.25rem" />
            <span className="review-summary-meta">
              {average.toFixed(1)} out of 5 from {summary.total} {summary.total === 1 ? 'review' : 'reviews'}
            </span>
          </div>
        </div>
      </section>

      <section className="reviews-page">
        <div className="container">
          {loading ? (
            <p className="review-empty">Gathering our customers&rsquo; words…</p>
          ) : reviews.length > 0 ? (
            <div className="review-grid">
              {reviews.map((review) => (
                <article key={review.id} className="review-card">
                  <span className="review-quote-mark" aria-hidden="true">
                    &ldquo;
                  </span>
                  <Stars value={review.rating} size="1.05rem" />
                  <p className="review-card-text">{review.review_text}</p>
                  <div className="review-card-footer">
                    <div>
                      <span className="review-card-name">{review.customer_name}</span>
                      <span className="review-card-date">{formatDate(review.created_at)}</span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="review-empty">
              No reviews have been published yet. Be the first to share your experience below.
            </p>
          )}

          <div style={{ marginTop: 64 }}>
            <form className="review-form-card" onSubmit={handleSubmit} noValidate>
              <h2>Share Your Experience</h2>
              <p className="review-form-sub">
                We read every note. Your words help other families choose the cake for their
                celebration.
              </p>

              {status && (
                <div className={`review-alert ${status.type}`} role={status.type === 'error' ? 'alert' : 'status'}>
                  {status.message}
                </div>
              )}

              <div className="form-grid">
                <div className={`form-field full${errors.customer_name ? ' has-error' : ''}`}>
                  <label htmlFor="reviewName">Your name</label>
                  <input
                    id="reviewName"
                    type="text"
                    placeholder="e.g. Sandra N."
                    maxLength={NAME_MAX_LENGTH}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <span className="field-error">{errors.customer_name || ''}</span>
                </div>

                <div className={`form-field full${errors.rating ? ' has-error' : ''}`}>
                  <label id="ratingLabel">Your rating</label>
                  <div className="star-picker" role="radiogroup" aria-labelledby="ratingLabel">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        className={star <= previewRating ? 'active' : ''}
                        onClick={() => setRating(star)}
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                        onFocus={() => setHoverRating(star)}
                        onBlur={() => setHoverRating(0)}
                        role="radio"
                        aria-checked={rating === star}
                        aria-label={`${star} star${star > 1 ? 's' : ''}`}
                      >
                        ★
                      </button>
                    ))}
                    <span className="star-picker-value">{rating}.0 / 5</span>
                  </div>
                  <span className="field-error">{errors.rating || ''}</span>
                </div>

                <div className={`form-field full${errors.review_text ? ' has-error' : ''}`}>
                  <label htmlFor="reviewText">Your review</label>
                  <textarea
                    id="reviewText"
                    placeholder="Tell us about the cake, the flavour and how the celebration went…"
                    maxLength={TEXT_MAX_LENGTH}
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                  />
                  <span className="review-char-count">
                    {text.length} / {TEXT_MAX_LENGTH}
                  </span>
                  <span className="field-error">{errors.review_text || ''}</span>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-gradient btn-block"
                disabled={submitting}
                style={{ marginTop: 12 }}
              >
                {submitting ? 'Sending…' : 'Submit Review'}
              </button>
            </form>
          </div>
        </div>
      </section>
    </>
  );
}
