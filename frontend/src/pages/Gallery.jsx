import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchGallery, fetchGalleryCategories, isVideoMedia } from '../lib/api';
import GalleryMedia from '../components/GalleryMedia';

// Fallback labels so a card always shows something readable while the
// category request is still in flight (or if it fails entirely).
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

function labelFor(key, categories) {
  const match = categories.find((category) => category.key === key);
  if (match) return match.label;
  return CATEGORY_LABELS[key] || 'Other';
}

// API-driven gallery: browse cakes by category, open any cake on its own
// shareable page (/gallery/<id>), or jump straight into the order form.
export default function Gallery() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeCategory = searchParams.get('c') || 'all';

  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const galleryRef = useRef(null);

  // Load the category list once — it also powers the counts on the pills.
  useEffect(() => {
    let cancelled = false;

    fetchGalleryCategories()
      .then((data) => {
        if (!cancelled) setCategories(data);
      })
      .catch(() => {
        if (!cancelled) setCategories([]);
      });

    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  // Reload the grid whenever the category in the URL changes.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setSlow(false);
    setError(null);

    // If the server is still waking up, tell the visitor instead of showing a blank page.
    const slowTimer = setTimeout(() => {
      if (!cancelled) setSlow(true);
    }, 6000);

    fetchGallery(activeCategory)
      .then((data) => {
        if (cancelled) return;
        setItems(data);
      })
      .catch((err) => {
        if (cancelled) return;
        setItems([]);
        setError(err.message || 'We could not load the gallery right now.');
      })
      .finally(() => {
        clearTimeout(slowTimer);
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      clearTimeout(slowTimer);
    };
  }, [activeCategory, reloadKey]);

  const totalCount = useMemo(
    () => categories.reduce((sum, category) => sum + (category.count || 0), 0),
    [categories],
  );

  // Only show pills that actually hold cakes (plus "All").
  const visibleCategories = useMemo(
    () => categories.filter((category) => category.count > 0),
    [categories],
  );

  function selectCategory(key) {
    if (key === activeCategory) return;
    setSearchParams(key === 'all' ? {} : { c: key });
  }

  return (
    <>
      <header className="gallery-hero">
        <div className="container gallery-hero-inner">
          <span className="eyebrow">Our Work</span>
          <h1 className="gallery-hero-title">Our Cake Gallery</h1>
          <p className="gallery-hero-sub">
            Tap any cake to read its story, share it, and order that exact design.
          </p>
          <span className="gallery-hero-rule" aria-hidden="true" />
        </div>
      </header>

      <section className="section gallery-section">
        <div className="container">
          <div className="gallery-filters" role="group" aria-label="Filter cakes by occasion">
            <button
              type="button"
              className={`gallery-pill${activeCategory === 'all' ? ' is-active' : ''}`}
              aria-pressed={activeCategory === 'all'}
              onClick={() => selectCategory('all')}
            >
              All
              <span className="gallery-pill-count">{totalCount || items.length}</span>
            </button>

            {visibleCategories.map((category) => (
              <button
                key={category.key}
                type="button"
                className={`gallery-pill${activeCategory === category.key ? ' is-active' : ''}`}
                aria-pressed={activeCategory === category.key}
                onClick={() => selectCategory(category.key)}
              >
                {category.label}
                <span className="gallery-pill-count">{category.count}</span>
              </button>
            ))}
          </div>

          {loading && (
            <div className="gallery-state" role="status" aria-live="polite">
              <span className="gallery-spinner" aria-hidden="true" />
              <p>{slow ? 'Our kitchen is waking up — the cakes are on their way…' : 'Gathering the cakes…'}</p>
            </div>
          )}

          {!loading && error && (
            <div className="gallery-state">
              <p>{error}</p>
              <button type="button" className="btn btn-outline" onClick={() => setReloadKey((key) => key + 1)}>
                Try again
              </button>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="gallery-state">
              <p>
                {activeCategory === 'all'
                  ? 'The gallery is being frosted — please check back shortly.'
                  : 'No cakes in this category just yet. Try another occasion!'}
              </p>
              {activeCategory !== 'all' && (
                <button type="button" className="btn btn-outline" onClick={() => selectCategory('all')}>
                  View all cakes
                </button>
              )}
            </div>
          )}

          {!loading && !error && items.length > 0 && (
            <div className="cake-masonry" ref={galleryRef}>
              {items.map((item, index) => (
                <article
                  key={item.id}
                  className="cake-card"
                  style={{ animationDelay: `${Math.min(index, 11) * 55}ms` }}
                >
                  {isVideoMedia(item) ? (
                    <div className="cake-card-media cake-card-media-video">
                      <GalleryMedia item={item} className="cake-card-img" />
                    </div>
                  ) : (
                    <Link
                      to={`/gallery/${item.id}`}
                      className="cake-card-media"
                      aria-label={`Open ${item.title || 'this cake'}`}
                    >
                      <GalleryMedia item={item} className="cake-card-img" />
                      <span className="cake-card-veil" aria-hidden="true">
                        <span className="cake-card-zoom">View story</span>
                      </span>
                    </Link>
                  )}

                  <div className="cake-card-body">
                    <span className="cake-card-cat">{labelFor(item.category, categories)}</span>
                    <h3 className="cake-card-title">
                      <Link to={`/gallery/${item.id}`}>{item.title || 'Signature cake'}</Link>
                    </h3>
                    {item.description && <p className="cake-card-desc">{item.description}</p>}
                    <div className="cake-card-actions">
                      <Link className="cake-card-cta" to={`/gallery/${item.id}`}>
                        View &amp; share
                      </Link>
                      <Link className="btn btn-gradient cake-card-order" to={`/order?cake=${item.id}`}>
                        Order this design
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          <div className="gallery-cta">
            <p>Didn&rsquo;t find your dream cake? Dream it and we&rsquo;ll bake it.</p>
            <Link to="/order" className="btn btn-gradient">
              Start a Custom Order
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
