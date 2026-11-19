import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { fetchGalleryDetail, isVideoMedia } from '../lib/api';
import GalleryMedia from '../components/GalleryMedia';

// One cake on its own page: the picture, its short story, a button to order that
// exact design, a way to share it, and more cakes from the same category.
// The address (/gallery/<id>) is what gets shared, so it works when opened later.
export default function CakeDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [shareNote, setShareNote] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setSlow(false);
    setError(null);
    setShareNote('');
    window.scrollTo({ top: 0 });

    const slowTimer = setTimeout(() => {
      if (!cancelled) setSlow(true);
    }, 6000);

    fetchGalleryDetail(id)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (cancelled) return;
        setData(null);
        setError(err.message || 'We could not load this cake right now.');
      })
      .finally(() => {
        clearTimeout(slowTimer);
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
    };
  }, [id, reloadKey]);

  // Keep the browser tab title meaningful while a cake is open.
  const title = data?.item?.title;
  useEffect(() => {
    if (!title) return undefined;
    const previous = document.title;
    document.title = `${title} | Cinderella Cakes`;
    return () => {
      document.title = previous;
    };
  }, [title]);

  if (loading) {
    return (
      <section className="section gallery-section">
        <div className="container">
          <div className="gallery-state" role="status" aria-live="polite">
            <span className="gallery-spinner" aria-hidden="true" />
            <p>{slow ? 'Our kitchen is waking up — one moment…' : 'Opening this cake…'}</p>
          </div>
        </div>
      </section>
    );
  }

  if (error || !data?.item) {
    return (
      <section className="section gallery-section">
        <div className="container">
          <div className="gallery-state">
            <p>{error || 'We could not find this cake.'}</p>
            <div className="cake-detail-actions">
              <button type="button" className="btn btn-outline" onClick={() => setReloadKey((key) => key + 1)}>
                Try again
              </button>
              <Link to="/gallery" className="btn btn-gradient">
                Back to the gallery
              </Link>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const { item, categoryLabel, related } = data;
  const shareUrl = `${window.location.origin}/gallery/${item.id}`;
  const shareText = `Look at this cake from Cinderella Cakes: ${item.title || 'Signature cake'}`;
  const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(`${shareText} ${shareUrl}`)}`;

  async function handleShare() {
    if (navigator.share) {
      try {
        await navigator.share({ title: item.title || 'Cinderella Cakes', text: shareText, url: shareUrl });
        return;
      } catch (err) {
        if (err?.name === 'AbortError') return; // The person closed the share sheet.
      }
    }
    try {
      await navigator.clipboard.writeText(shareUrl);
      setShareNote('Link copied. Paste it anywhere to share this cake.');
    } catch {
      setShareNote(`Copy this link to share: ${shareUrl}`);
    }
  }

  return (
    <section className="section gallery-section cake-detail">
      <div className="container">
        <nav className="cake-detail-crumbs" aria-label="Breadcrumb">
          <Link to="/gallery">Gallery</Link>
          <span aria-hidden="true">/</span>
          <Link to={`/gallery?c=${encodeURIComponent(item.category || 'other')}`}>{categoryLabel}</Link>
        </nav>

        <div className="cake-detail-grid">
          <div className="cake-detail-media">
            <GalleryMedia item={item} />
          </div>

          <div className="cake-detail-body">
            <span className="cake-card-cat">{categoryLabel}</span>
            <h1 className="cake-detail-title">{item.title || 'Signature cake'}</h1>

            <h2 className="cake-detail-sub">The story</h2>
            <p className="cake-detail-story">
              {item.description ||
                'Handcrafted by our bakers in Nsambya. Tell us your colours, tiers and flavour on the order form and we will make it yours.'}
            </p>

            <div className="cake-detail-actions">
              <Link className="btn btn-gradient" to={`/order?cake=${item.id}`}>
                Order this design
              </Link>
              <button type="button" className="btn btn-outline" onClick={handleShare}>
                Share this cake
              </button>
              <a className="btn btn-outline" href={whatsappUrl} target="_blank" rel="noopener noreferrer">
                Send on WhatsApp
              </a>
            </div>

            {shareNote && (
              <p className="cake-detail-note" role="status" aria-live="polite">
                {shareNote}
              </p>
            )}

            <p className="lightbox-hint">Cake designs can be recoloured and resized to suit your celebration.</p>
          </div>
        </div>

        {related.length > 0 && (
          <div className="cake-related">
            <div className="cake-related-head">
              <h2>More like this</h2>
              <Link to={`/gallery?c=${encodeURIComponent(item.category || 'other')}`} className="cake-card-cta">
                See all {categoryLabel}
                <span aria-hidden="true">&rarr;</span>
              </Link>
            </div>

            <div className="cake-related-grid">
              {related.map((cake) => (
                <Link key={cake.id} to={`/gallery/${cake.id}`} className="cake-related-card">
                  {isVideoMedia(cake) ? (
                    <span className="cake-related-video">Watch video</span>
                  ) : (
                    <GalleryMedia item={cake} />
                  )}
                  <span className="cake-related-title">{cake.title || 'Signature cake'}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
