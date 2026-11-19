import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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

// API-driven gallery: browse pastry work by category, open a design in a
// lightbox, and jump straight into the order form with that design attached.
export default function Gallery() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeCategory = searchParams.get('c') || 'all';

  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [activeItem, setActiveItem] = useState(null);
  const closeLightbox = useCallback(() => setActiveItem(null), []);
  const galleryRef = useRef(null);

  function openLightbox(item) {
    galleryRef.current?.querySelectorAll('video').forEach((video) => video.pause());
    setActiveItem(item);
  }

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
  }, []);

  // Reload the grid whenever the category in the URL changes.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

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
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
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
            Love a design? Click &ldquo;Order This Design&rdquo; on any cake to start your order!
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
              <p>Gathering the cakes&hellip;</p>
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
                    <div className="cake-card-media">
                      <GalleryMedia item={item} className="cake-card-img" />
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="cake-card-media"
                      onClick={() => openLightbox(item)}
                      aria-label={`View ${item.title || 'this cake'} in full`}
                    >
                      <GalleryMedia item={item} className="cake-card-img" />
                      <span className="cake-card-veil" aria-hidden="true">
                        <span className="cake-card-zoom">View design</span>
                      </span>
                    </button>
                  )}

                  <div className="cake-card-body">
                    <span className="cake-card-cat">{labelFor(item.category, categories)}</span>
                    <h3 className="cake-card-title">{item.title || 'Signature cake'}</h3>
                    {item.description && <p className="cake-card-desc">{item.description}</p>}
                    {isVideoMedia(item) && (
                      <button type="button" className="btn btn-outline" onClick={() => openLightbox(item)}>
                        View video design
                      </button>
                    )}
                    <Link className="cake-card-cta" to={`/order?cake=${item.id}`}>
                      Order This Design
                      <span aria-hidden="true">&rarr;</span>
                    </Link>
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

      {activeItem && (
        <Lightbox
          item={activeItem}
          categoryLabel={labelFor(activeItem.category, categories)}
          onClose={closeLightbox}
        />
      )}
    </>
  );
}

// Accessible detail overlay: Escape closes, Tab stays inside, and the
// element that opened it regains focus afterwards.
function Lightbox({ item, categoryLabel, onClose }) {
  const panelRef = useRef(null);
  const closeRef = useRef(null);

  useEffect(() => {
    const previouslyFocused = document.activeElement;
    closeRef.current?.focus();
    document.body.style.overflow = 'hidden';

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key !== 'Tab' || !panelRef.current) return;

      const focusables = panelRef.current.querySelectorAll(
        'a[href], button:not([disabled]), input, select, textarea, video[controls]',
      );
      if (focusables.length === 0) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
      if (previouslyFocused instanceof HTMLElement) previouslyFocused.focus();
    };
  }, [onClose]);

  return (
    <div className="lightbox" role="presentation" onClick={onClose}>
      <div
        className="lightbox-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lightbox-title"
        ref={panelRef}
        onClick={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          className="lightbox-close"
          onClick={onClose}
          aria-label="Close design preview"
          ref={closeRef}
        >
          <span aria-hidden="true">&times;</span>
        </button>

        <div className="lightbox-media">
          <GalleryMedia item={item} />
        </div>

        <div className="lightbox-body">
          <span className="lightbox-cat">{categoryLabel}</span>
          <h2 className="lightbox-title" id="lightbox-title">
            {item.title || 'Signature cake'}
          </h2>
          {item.description ? (
            <p className="lightbox-desc">{item.description}</p>
          ) : (
            <p className="lightbox-desc">
              Handcrafted by our bakers — tell us your colours, tiers and flavour on the order form.
            </p>
          )}
          <Link className="btn btn-gradient lightbox-cta" to={`/order?cake=${item.id}`}>
            Order This Design
          </Link>
          <p className="lightbox-hint">Cake designs can be recoloured and resized to suit your celebration.</p>
        </div>
      </div>
    </div>
  );
}
